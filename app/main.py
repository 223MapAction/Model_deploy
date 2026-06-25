import asyncio
import logging
import time
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import Optional, Dict

from app.schemas import AnalyzeRequest, AnalyzeResponse, SpatialData, SatelliteData, HumanImpact, ChatRequest
from app.config import settings
from app.services.ai_service import analyze_image_with_gemini, analyze_image_bytes_with_gemini, call_deepseek_chat
from app.services.spatial_calculator import (
    get_slope_data, 
    get_osm_data, 
    get_weather_data,
    filter_osm_by_radius,
    calculate_social_vulnerability,
    calculate_human_impact,
    get_satellite_analysis,
    get_geocoding_context
)
from app.impact_logic import calculate_dynamic_radius, calculate_global_impact

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Map Action Impact Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to Map Action Impact Engine"}

def _subtract_human_impact(total: Dict[str, int], direct: Dict[str, int]) -> Dict[str, int]:
    """Retourne la population de l'anneau indirect sans double compter le rayon direct."""
    keys = [
        "total_population_exposed",
        "adult_men_exposed",
        "adult_women_exposed",
        "children_exposed",
        "maternities_count",
        "nurseries_count",
    ]
    return {key: max(0, total.get(key, 0) - direct.get(key, 0)) for key in keys}

def _subtract_structure_counts(total: Dict[str, int], direct: Dict[str, int]) -> Dict[str, int]:
    """Retourne les structures de l'anneau indirect sans double compter le rayon direct."""
    keys = set(total) | set(direct)
    return {key: max(0, total.get(key, 0) - direct.get(key, 0)) for key in keys}

async def _run_analysis(ai_data, latitude: float, longitude: float, incident_id: str = None) -> AnalyzeResponse:
    """Logique d'analyse partagée entre les endpoints URL et Upload."""
    
    # 1. Phase 1 : Collecte du contexte Macro (Rayon fixe 5km pour OSM)
    slope_result, osm_macro_result, sat_result, weather_result, geo_context = await asyncio.gather(
        asyncio.to_thread(get_slope_data, latitude, longitude),
        asyncio.to_thread(get_osm_data, latitude, longitude, 5000), # 5km macro scan
        asyncio.to_thread(get_satellite_analysis, latitude, longitude),
        asyncio.to_thread(get_weather_data, latitude, longitude),
        asyncio.to_thread(get_geocoding_context, latitude, longitude)
    )

    spatial_data = {
        "elevation": 0.0,
        "slope_percent": slope_result,
        "wind_speed": weather_result["wind_speed"],
        "precipitation": weather_result["precipitation"],
        "temperature_celsius": weather_result["temperature_celsius"]
    }

    # 2. Phase 2 : Calcul dynamique du rayon final (Analyse Croisée)
    radius_data = calculate_dynamic_radius(
        ai_data=ai_data,
        spatial_data=spatial_data,
        macro_osm_counts=osm_macro_result["counts"],
        sat_data=sat_result
    )
    final_radius = radius_data["final_radius"]
    radius_exp = radius_data.get("radius_explanation", "")

    # 3. Phase 3 : Calcul des scores sociaux et humains
    osm_micro_counts = filter_osm_by_radius(osm_macro_result, latitude, longitude, final_radius)
    social_data = calculate_social_vulnerability(
        osm_micro_counts,
        land_use=sat_result.get("land_use", "Inconnu"),
        radius_meters=final_radius,
    )
    social_score = social_data["score"]
    is_probabilistic = social_data["is_probabilistic"]
    estimated_buildings = social_data.get("estimated_buildings", 0)
    human_impact_data = calculate_human_impact(osm_micro_counts, estimated_buildings=estimated_buildings)

    # 4. Phase 4 : Calcul de la population indirectement concernée par vigilance sanitaire
    indirect_vigilance_data = radius_data.get("indirect_vigilance")
    indirect_human_impact_data = None
    indirect_social_counts = None
    is_indirect_probabilistic = False
    indirect_radius = None
    indirect_exp = None
    if indirect_vigilance_data:
        indirect_radius = indirect_vigilance_data["potential_radius"]
        indirect_exp = indirect_vigilance_data["message"]
        osm_indirect_counts = filter_osm_by_radius(osm_macro_result, latitude, longitude, indirect_radius)
        social_indirect = calculate_social_vulnerability(
            osm_indirect_counts,
            land_use=sat_result.get("land_use", "Inconnu"),
            radius_meters=indirect_radius,
        )
        is_indirect_probabilistic = social_indirect["is_probabilistic"]
        human_indirect_total = calculate_human_impact(
            osm_indirect_counts,
            estimated_buildings=social_indirect.get("estimated_buildings"),
        )
        indirect_human_impact_data = _subtract_human_impact(human_indirect_total, human_impact_data)
        indirect_social_counts = _subtract_structure_counts(osm_indirect_counts, osm_micro_counts)

    # 5. Phase 5 : Calcul du risque potentiel (Si détecté)
    potential_risk_data = radius_data.get("potential_risk")
    if potential_risk_data:
        pot_radius = potential_risk_data["potential_radius"]
        osm_pot_counts = filter_osm_by_radius(osm_macro_result, latitude, longitude, pot_radius)
        social_pot = calculate_social_vulnerability(
            osm_pot_counts,
            land_use=sat_result.get("land_use", "Inconnu"),
            radius_meters=pot_radius,
        )
        human_pot = calculate_human_impact(osm_pot_counts, estimated_buildings=social_pot.get("estimated_buildings"))
        
        potential_risk_data["stats"] = {
            "total_pop": human_pot["total_population_exposed"],
            "infrastructures": sum(v for k,v in osm_pot_counts.items() if k != "residential_buildings")
        }

    # 6. Phase 6 : Calcul du score d'impact global et réponse
    impact_data = calculate_global_impact(
        ai_data=ai_data,
        sat_data=sat_result,
        spatial_data=spatial_data,
        social_score=social_score
    )

    return AnalyzeResponse(
        incident_id=incident_id,
        latitude=latitude,
        longitude=longitude,
        ai_analysis=ai_data,
        topography=SpatialData(**spatial_data),
        satellite=SatelliteData(**sat_result),
        social_data=osm_micro_counts,
        indirect_social_data=indirect_social_counts,
        social_vulnerability_score=social_score,
        is_social_probabilistic=is_probabilistic,
        is_indirect_social_probabilistic=is_indirect_probabilistic,
        human_impact=HumanImpact(**human_impact_data),
        indirect_human_impact=HumanImpact(**indirect_human_impact_data) if indirect_human_impact_data else None,
        impact_radius_meters=final_radius,
        indirect_vigilance_radius_meters=indirect_radius,
        indirect_vigilance_explanation=indirect_exp,
        radius_explanation=radius_exp,
        global_impact_score=impact_data["impact_score"],
        base_severity=settings.INCIDENT_TAXONOMY.get(ai_data.macro_category, {}).get(ai_data.sub_category, {}).get("base_severity", 5),
        impact_tags=settings.INCIDENT_TAXONOMY.get(ai_data.macro_category, {}).get(ai_data.sub_category, {}).get("impact_tags", []),
        geocoding=geo_context,
        potential_risk=potential_risk_data,
        recommendation=f"Intervention directe recommandée dans un rayon de {final_radius}m. Score de gravité: {impact_data['impact_score']}/10."
    )

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_incident(request: AnalyzeRequest):
    """Endpoint pour analyser un incident via URL d'image."""
    start_time = time.time()
    logger.info(f"Analyse via URL pour incident: {request.incident_id}")

    ai_data = await asyncio.to_thread(analyze_image_with_gemini, request.image_url)
    result = await _run_analysis(ai_data, request.latitude, request.longitude, request.incident_id)

    logger.info(f"Analyse terminée en {time.time() - start_time:.2f}s")
    return result

@app.post("/analyze/upload", response_model=AnalyzeResponse)
async def analyze_incident_upload(
    image: UploadFile = File(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    incident_id: Optional[str] = Form(None)
):
    """Endpoint pour analyser un incident via upload direct d'image."""
    start_time = time.time()
    logger.info(f"Analyse via Upload pour ({latitude}, {longitude})")

    image_bytes = await image.read()
    mime_type = image.content_type or "image/jpeg"

    ai_data = await asyncio.to_thread(analyze_image_bytes_with_gemini, image_bytes, mime_type)
    result = await _run_analysis(ai_data, latitude, longitude, incident_id)

    logger.info(f"Analyse terminée en {time.time() - start_time:.2f}s")
    return result

@app.post("/chat")
async def chat_with_assistant(request: ChatRequest):
    """Endpoint de chat contextuel avec DeepSeek."""
    try:
        # On prépare un résumé textuel clair au lieu du JSON brut
        ctx = request.context
        human = ctx.get('human_impact', {})
        indirect_human = ctx.get('indirect_human_impact') or {}
        topo = ctx.get('topography', {})
        sat = ctx.get('satellite', {})
        ai = ctx.get('ai_analysis', {})
        
        context_text = f"""RAPPORT D'INCIDENT MAP ACTION
- Position : Latitude {ctx.get('latitude')}, Longitude {ctx.get('longitude')}
- Localisation : {ctx.get('geocoding', {}).get('display_name', 'Inconnue')}
- Ville/Village : {ctx.get('geocoding', {}).get('city', 'Inconnu')} | Région : {ctx.get('geocoding', {}).get('region', 'Inconnue')} | Pays : {ctx.get('geocoding', {}).get('country', 'Inconnu')}
- Incident : {ai.get('macro_category')} - {ai.get('sub_category')}
- Tags d'impact : {', '.join(ctx.get('impact_tags', []))}
- Gravité Initiale: {ctx.get('base_severity')}/10 | Gravité Globale : {ctx.get('global_impact_score')}/10
- Rayon d'impact direct : {ctx.get('impact_radius_meters')} mètres
- Justification : {ctx.get('radius_explanation')}
- Population directement exposée : {human.get('total_population_exposed')} personnes
  (Hommes: {human.get('adult_men_exposed')}, Femmes: {human.get('adult_women_exposed')}, Enfants: {human.get('children_exposed')})
- Rayon de vigilance indirecte : {ctx.get('indirect_vigilance_radius_meters') or 'Non applicable'} mètres
- Population indirectement concernée : {indirect_human.get('total_population_exposed', 0)} personnes
- Météo : {topo.get('temperature_celsius')}°C, Vent {topo.get('wind_speed')}km/h, Pluie {topo.get('precipitation')}mm
- Sol : Pente {topo.get('slope_percent')}%, Occupation: {sat.get('land_use')}
- Structures directement exposées : {ctx.get('social_data')}
- Structures indirectement concernées : {ctx.get('indirect_social_data') or {}}
- Risque potentiel : {ctx.get('potential_risk', {}).get('message') if ctx.get('potential_risk') else 'Aucun risque de propagation majeure détecté.'}
"""
        # On renvoie le générateur de texte encapsulé dans une StreamingResponse
        # Le content_type="text/event-stream" permet au client de lire au fur et à mesure
        return StreamingResponse(call_deepseek_chat(request.messages, context_text), media_type="text/event-stream")
    except Exception as e:
        logger.error(f"Erreur API Chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))
