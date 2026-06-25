import asyncio
import logging
import time
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from typing import Optional, Dict

from fastapi.staticfiles import StaticFiles
import os

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

# Servir les fichiers statiques (logos, images)
if not os.path.exists("assets"):
    os.makedirs("assets")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

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

import json

# ============================================================
# Interface Web Intégrée
# ============================================================

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Map Action Impact Engine</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0a0e1a;
            --bg-secondary: #111827;
            --bg-card: rgba(17, 24, 39, 0.8);
            --bg-glass: rgba(255, 255, 255, 0.03);
            --border: rgba(255, 255, 255, 0.08);
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --accent-green: #10b981;
            --accent-green-glow: rgba(16, 185, 129, 0.15);
            --accent-blue: #3b82f6;
            --accent-orange: #f59e0b;
            --accent-red: #ef4444;
            --accent-purple: #8b5cf6;
            --gradient-main: linear-gradient(135deg, #10b981 0%, #3b82f6 100%);
            --radius: 16px;
            --radius-sm: 10px;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
        }

        /* Animated background */
        body::before {
            content: '';
            position: fixed;
            top: -50%; left: -50%;
            width: 200%; height: 200%;
            background: radial-gradient(circle at 20% 50%, rgba(16, 185, 129, 0.04) 0%, transparent 50%),
                        radial-gradient(circle at 80% 20%, rgba(59, 130, 246, 0.04) 0%, transparent 50%),
                        radial-gradient(circle at 40% 80%, rgba(139, 92, 246, 0.03) 0%, transparent 50%);
            animation: bgFloat 20s ease-in-out infinite;
            z-index: -1;
        }

        @keyframes bgFloat {
            0%, 100% { transform: translate(0, 0) rotate(0deg); }
            33% { transform: translate(30px, -20px) rotate(1deg); }
            66% { transform: translate(-20px, 20px) rotate(-1deg); }
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 60px 20px 20px 20px;
        }

        /* Header */
        .header {
            display: flex; align-items: center; gap: 16px;
            padding: 20px 0 32px; border-bottom: 1px solid var(--border);
            margin-bottom: 32px;
        }
        .header-icon {
            width: 48px; height: 48px; border-radius: 14px;
            background: var(--gradient-main);
            display: flex; align-items: center; justify-content: center;
            font-size: 24px; box-shadow: 0 8px 32px rgba(16, 185, 129, 0.3);
        }
        .header h1 { font-size: 24px; font-weight: 700; letter-spacing: -0.5px; }
        .header p { color: var(--text-secondary); font-size: 14px; margin-top: 2px; }

        /* Layout */
        .layout { display: grid; grid-template-columns: 420px 1fr; gap: 24px; }

        /* Card */
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 24px;
            backdrop-filter: blur(20px);
        }
        .card-title {
            font-size: 14px; font-weight: 600; text-transform: uppercase;
            letter-spacing: 1px; color: var(--text-secondary);
            margin-bottom: 20px; display: flex; align-items: center; gap: 8px;
        }
        .card-title span { font-size: 16px; }

        /* Form */
        .form-group { margin-bottom: 20px; }
        .form-label { display: block; font-size: 13px; font-weight: 500; color: var(--text-secondary); margin-bottom: 8px; }

        .form-input {
            width: 100%; padding: 12px 16px; border-radius: var(--radius-sm);
            background: var(--bg-glass); border: 1px solid var(--border);
            color: var(--text-primary); font-size: 14px; font-family: inherit;
            transition: all 0.2s;
        }
        .form-input:focus { outline: none; border-color: var(--accent-green); box-shadow: 0 0 0 3px var(--accent-green-glow); }
        .form-input::placeholder { color: var(--text-muted); }

        .coord-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

        /* Upload Zone */
        .upload-zone {
            border: 2px dashed var(--border); border-radius: var(--radius);
            padding: 32px; text-align: center; cursor: pointer;
            transition: all 0.3s; position: relative; overflow: hidden;
        }
        .upload-zone:hover, .upload-zone.dragover {
            border-color: var(--accent-green);
            background: var(--accent-green-glow);
        }
        .upload-zone.has-file { border-color: var(--accent-green); border-style: solid; }
        .upload-icon { font-size: 40px; margin-bottom: 8px; }
        .upload-text { font-size: 14px; color: var(--text-secondary); }
        .upload-text strong { color: var(--accent-green); }
        .upload-preview {
            max-height: 180px; border-radius: 8px; margin-top: 12px;
            display: none; object-fit: cover; width: 100%;
        }
        .upload-zone input { display: none; }

        /* Button */
        .btn-analyze {
            width: 100%; padding: 14px 24px; border: none; border-radius: var(--radius-sm);
            background: var(--gradient-main); color: white;
            font-size: 15px; font-weight: 600; font-family: inherit;
            cursor: pointer; transition: all 0.3s; position: relative; overflow: hidden;
        }
        .btn-analyze:hover { transform: translateY(-1px); box-shadow: 0 8px 32px rgba(16, 185, 129, 0.3); }
        .btn-analyze:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .btn-analyze .spinner {
            display: none; width: 20px; height: 20px;
            border: 2px solid rgba(255,255,255,0.3); border-top-color: white;
            border-radius: 50%; animation: spin 0.8s linear infinite;
            margin-right: 8px;
        }
        .btn-analyze.loading .spinner { display: inline-block; }
        .btn-analyze.loading .btn-text { display: none; }
        .btn-analyze.loading .btn-loading-text { display: inline; }
        .btn-loading-text { display: none; }

        @keyframes spin { to { transform: rotate(360deg); } }

        /* Results Panel */
        .results-panel { display: none; }
        .results-panel.visible { display: block; }

        .results-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }

        /* Metric Cards */
        .metric {
            background: var(--bg-glass); border: 1px solid var(--border);
            border-radius: var(--radius-sm); padding: 20px; text-align: center;
            transition: all 0.3s;
        }
        .metric:hover { border-color: rgba(255,255,255,0.15); transform: translateY(-2px); }
        .metric-icon { font-size: 28px; margin-bottom: 8px; }
        .metric-value { font-size: 28px; font-weight: 800; letter-spacing: -1px; }
        .metric-label { font-size: 12px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px; }

        .severity-low { color: var(--accent-green); }
        .severity-medium { color: var(--accent-orange); }
        .severity-high { color: var(--accent-red); }

        /* Detail sections */
        .detail-section { margin-bottom: 20px; }
        .detail-section h3 {
            font-size: 14px; font-weight: 600; color: var(--text-secondary);
            margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid var(--border);
            display: flex; align-items: center; gap: 8px;
        }
        .detail-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
        .detail-item {
            background: var(--bg-glass); padding: 12px; border-radius: 8px;
            border: 1px solid var(--border);
        }
        .detail-item-label { font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }
        .detail-item-value { font-size: 16px; font-weight: 600; margin-top: 4px; }

        /* AI Description Box */
        .ai-description {
            background: linear-gradient(135deg, rgba(16,185,129,0.05), rgba(59,130,246,0.05));
            border: 1px solid rgba(16,185,129,0.15); border-radius: var(--radius-sm);
            padding: 20px; line-height: 1.7; font-size: 14px; color: var(--text-secondary);
        }
        .ai-description .ai-badge {
            display: inline-flex; align-items: center; gap: 6px; background: var(--gradient-main);
            color: white; padding: 4px 10px; border-radius: 20px; font-size: 11px;
            font-weight: 600; margin-bottom: 12px;
        }

        /* Recommendation */
        .recommendation {
            background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.2);
            border-radius: var(--radius-sm); padding: 16px;
            font-size: 14px; color: var(--accent-orange); font-weight: 500;
        }

        /* Spread Vectors Tags */
        .tags { display: flex; flex-wrap: wrap; gap: 8px; }
        .tag {
            padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 500;
            background: rgba(139, 92, 246, 0.1); color: var(--accent-purple);
            border: 1px solid rgba(139, 92, 246, 0.2);
        }

        /* Placeholder */
        .placeholder {
            text-align: center; padding: 80px 40px; color: var(--text-muted);
        }
        .placeholder-icon { font-size: 64px; margin-bottom: 16px; opacity: 0.5; }
        .placeholder h3 { font-size: 18px; font-weight: 500; color: var(--text-secondary); margin-bottom: 8px; }

        /* Responsive */
        @media (max-width: 900px) { .layout { grid-template-columns: 1fr; } }
        /* --- Floating Chat Widget --- */
        .chat-widget {
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 1000;
            display: flex;
            flex-direction: column;
            align-items: flex-end;
        }

        .chat-button {
            width: 60px;
            height: 60px;
            border-radius: 30px;
            background: var(--accent-orange);
            box-shadow: 0 8px 24px rgba(245, 158, 11, 0.4);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            font-size: 24px;
        }

        .chat-button:hover { transform: scale(1.1); }

        .chat-window {
            width: 400px;
            max-height: 600px;
            height: calc(100vh - 120px);
            background: rgba(26, 27, 38, 0.95);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            margin-bottom: 20px;
            display: none;
            flex-direction: column;
            box-shadow: 0 12px 48px rgba(0, 0, 0, 0.5);
            overflow: hidden;
            animation: slideIn 0.3s ease-out;
        }

        @keyframes slideIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .chat-header {
            padding: 16px;
            background: rgba(245, 158, 11, 0.1);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .chat-messages {
            flex: 1;
            padding: 16px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .message {
            max-width: 85%;
            padding: 12px 16px;
            border-radius: 15px;
            font-size: 14px;
            line-height: 1.5;
            position: relative;
            white-space: pre-wrap; /* Respecte les sauts de ligne */
        }

        .message-user {
            align-self: flex-end;
            background: var(--accent-orange);
            color: white;
            border-bottom-right-radius: 2px;
        }

        .message-assistant {
            align-self: flex-start;
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-main);
            border-bottom-left-radius: 2px;
        }

        /* Typing Indicator */
        .typing-indicator {
            display: flex;
            align-items: center;
            gap: 4px;
            padding: 12px 16px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            border-bottom-left-radius: 2px;
            align-self: flex-start;
            color: var(--text-muted);
            font-size: 13px;
        }
        .typing-indicator span {
            width: 6px;
            height: 6px;
            background: var(--text-muted);
            border-radius: 50%;
            animation: typingBounce 1.4s infinite ease-in-out both;
        }
        .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
        .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
        @keyframes typingBounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }

        .chat-input-area {
            padding: 16px;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            display: flex;
            gap: 8px;
        }

        .chat-input {
            flex: 1;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 10px 14px;
            color: white;
            outline: none;
        }

        .chat-input:focus { border-color: var(--accent-orange); }

        .chat-send {
            background: var(--accent-orange);
            border: none; border-radius: 12px;
            width: 42px; height: 42px;
            cursor: pointer; display: flex;
            align-items: center; justify-content: center;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-logo">
                <img src="assets/Icone%20Map%20Action.png" alt="Map Action Pin" style="height: 55px; margin-right: 15px;">
            </div>
            <div>
                <img src="assets/Logo-blanc-map-action.png" alt="Map Action Logo" style="height: 40px; margin-bottom: 5px; display: block;">
                <p style="margin:0; font-size: 13px; opacity: 0.7;">Moteur de Calcul d'Impact Environnemental — Expertise IA Multimodale</p>
            </div>
        </div>

        <div class="layout">
            <!-- Left Panel: Input Form -->
            <div>
                <div class="card" style="margin-bottom: 16px;">
                    <div class="card-title"><span>📷</span> Image de l'incident</div>
                    <div class="upload-zone" id="uploadZone" onclick="document.getElementById('fileInput').click()">
                        <input type="file" id="fileInput" accept="image/*">
                        <div class="upload-icon">📤</div>
                        <div class="upload-text">Glissez votre image ici ou <strong>cliquez pour parcourir</strong></div>
                        <div class="upload-text" style="font-size:12px; margin-top:4px;">JPG, PNG, WebP — Max 10 MB</div>
                        <img class="upload-preview" id="uploadPreview">
                    </div>
                </div>

                <div class="card" style="margin-bottom: 16px;">
                    <div class="card-title"><span>📍</span> Coordonnées GPS</div>
                    <div class="coord-row">
                        <div class="form-group">
                            <label class="form-label">Latitude</label>
                            <input type="number" step="any" class="form-input" id="latitude" placeholder="ex: 14.4958" value="14.4958">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Longitude</label>
                            <input type="number" step="any" class="form-input" id="longitude" placeholder="ex: -4.1986" value="-4.1986">
                        </div>
                    </div>
                    <div class="form-group" style="margin-bottom: 0;">
                        <label class="form-label">ID Incident (optionnel)</label>
                        <input type="text" class="form-input" id="incidentId" placeholder="ex: INC-2026-0042">
                    </div>
                </div>

                <button class="btn-analyze" id="btnAnalyze" onclick="runAnalysis()" disabled>
                    <span class="spinner"></span>
                    <span class="btn-text">🔬 Lancer l'Analyse d'Impact</span>
                    <span class="btn-loading-text">Analyse en cours...</span>
                </button>
            </div>

            <!-- Right Panel: Results -->
            <div>
                <div class="placeholder" id="placeholder">
                    <div class="placeholder-icon">🛰️</div>
                    <h3>En attente d'analyse</h3>
                    <p>Uploadez une image et renseignez les coordonnées GPS pour lancer le moteur d'impact.</p>
                </div>

                <div class="results-panel" id="resultsPanel">
                    <!-- Top Metrics -->
                    <div class="results-grid" style="grid-template-columns: repeat(3, 1fr);" id="metricsGrid"></div>

                    <!-- AI Analysis -->
                    <div class="card" style="margin-bottom: 16px;">
                        <div class="card-title"><span>🧠</span> Analyse IA Vision</div>
                        <div class="ai-description" id="aiDescription"></div>
                        <div style="margin-top: 16px;">
                            <div class="detail-item-label" style="margin-bottom: 8px;">VECTEURS DE PROPAGATION</div>
                            <div class="tags" id="spreadTags"></div>
                        </div>
                        <div style="margin-top: 16px;">
                            <div class="detail-item-label" style="margin-bottom: 8px;">TAGS D'IMPACT SECONDAIRES</div>
                            <div class="tags" id="impactTags"></div>
                        </div>
                    </div>

                    <!-- Impact sections -->
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 16px;">
                        <!-- Populations -->
                        <div class="card" style="margin-bottom: 0;">
                            <div class="detail-section">
                                <h3><span>👥</span> Populations</h3>
                                <div id="socialPillarGrid"></div>
                            </div>
                        </div>

                        <!-- Milieu -->
                        <div class="card" style="margin-bottom: 0;">
                            <div class="detail-section">
                                <h3><span>🌿</span> Milieu</h3>
                                <div id="envPillarGrid"></div>
                            </div>
                        </div>

                        <!-- Infrastructures -->
                        <div class="card" style="margin-bottom: 0;">
                            <div class="detail-section">
                                <h3 style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:4px;">
                                    <span>🏘️ Infrastructures</span>
                                </h3>
                                <div id="ecoPillarGrid"></div>
                            </div>
                        </div>
                    </div>

                    <div id="potentialRiskContainer"></div>
 
                    <!-- Recommendation -->
                    <div class="recommendation" id="recommendation"></div>
                </div>
            </div>
        </div>
    </div>

    <!-- Floating Chat Widget -->
    <div class="chat-widget">
        <div class="chat-window" id="chatWindow">
            <div class="chat-header">
                <div style="font-size: 20px;">🧠</div>
                <div>
                    <div style="font-weight: 600; font-size: 14px;">Assistant Stratégique</div>
                    <div style="font-size: 11px; color: var(--text-muted);">Expert en aide à la décision</div>
                </div>
            </div>
            <div class="chat-messages" id="chatMessages">
                <div class="message message-assistant">
                    Bonjour ! Je suis l'assistant Map Action. Effectuez une analyse pour que je puisse vous conseiller stratégiquement sur l'incident.
                </div>
            </div>
            <div class="chat-input-area">
                <input type="text" class="chat-input" id="chatInput" placeholder="Posez une question..." onkeypress="if(event.key === 'Enter') sendMessage()">
                <button class="chat-send" onclick="sendMessage()">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg>
                </button>
            </div>
        </div>
        <div class="chat-button" onclick="toggleChat()">💬</div>
    </div>

    <script>
        const uploadZone = document.getElementById('uploadZone');
        const fileInput = document.getElementById('fileInput');
        const preview = document.getElementById('uploadPreview');
        const btn = document.getElementById('btnAnalyze');

        // Drag & Drop
        uploadZone.addEventListener('dragover', e => { e.preventDefault(); uploadZone.classList.add('dragover'); });
        uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('dragover'));
        uploadZone.addEventListener('drop', e => {
            e.preventDefault(); uploadZone.classList.remove('dragover');
            if (e.dataTransfer.files.length) { fileInput.files = e.dataTransfer.files; handleFile(); }
        });
        fileInput.addEventListener('change', handleFile);

        function handleFile() {
            const file = fileInput.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = e => { preview.src = e.target.result; preview.style.display = 'block'; };
            reader.readAsDataURL(file);
            uploadZone.classList.add('has-file');
            btn.disabled = false;
        }

        async function runAnalysis() {
            const file = fileInput.files[0];
            const lat = document.getElementById('latitude').value;
            const lon = document.getElementById('longitude').value;
            const incId = document.getElementById('incidentId').value;

            if (!file || !lat || !lon) { alert('Veuillez remplir tous les champs obligatoires.'); return; }

            btn.classList.add('loading'); btn.disabled = true;
            document.getElementById('placeholder').style.display = 'none';
            document.getElementById('resultsPanel').classList.remove('visible');

            const formData = new FormData();
            formData.append('image', file);
            formData.append('latitude', lat);
            formData.append('longitude', lon);
            if (incId) formData.append('incident_id', incId);

            try {
                const res = await fetch('/analyze/upload', { method: 'POST', body: formData });
                if (!res.ok) throw new Error(`Erreur ${res.status}: ${await res.text()}`);
                const data = await res.json();
                renderResults(data);
            } catch (err) {
                alert('Erreur: ' + err.message);
            } finally {
                btn.classList.remove('loading'); btn.disabled = false;
            }
        }

        function getSeverityClass(score) {
            if (score <= 3.5) return 'severity-low';
            if (score <= 6.5) return 'severity-medium';
            return 'severity-high';
        }

        function renderResults(d) {
            // Top Metrics
            document.getElementById('metricsGrid').innerHTML = `
                <div class="metric">
                    <div class="metric-icon">⚠️</div>
                    <div class="metric-value ${getSeverityClass(d.global_impact_score)}">${d.global_impact_score}</div>
                    <div class="metric-label">Score d'Impact Global</div>
                </div>
                <div class="metric">
                    <div class="metric-icon">📐</div>
                    <div class="metric-value">${Math.round(d.impact_radius_meters)}m</div>
                    <div class="metric-label">Rayon Direct</div>
                    <div style="font-size:10px; color:var(--text-muted); margin-top:4px; line-height:1.2;">${d.radius_explanation}</div>
                </div>
                ${d.indirect_vigilance_radius_meters ? `
                <div class="metric">
                    <div class="metric-icon">🛡️</div>
                    <div class="metric-value">${Math.round(d.indirect_vigilance_radius_meters)}m</div>
                    <div class="metric-label">Rayon de Vigilance</div>
                    <div style="font-size:10px; color:var(--text-muted); margin-top:4px; line-height:1.2;">${d.indirect_vigilance_explanation}</div>
                </div>` : ''}
                <div class="metric">
                    <div class="metric-icon">🔥</div>
                    <div class="metric-value ${getSeverityClass(d.base_severity)}">${d.base_severity}/10</div>
                    <div class="metric-label">Sévérité Initiale</div>
                </div>
            `;

            // Potential Risk Alert
            const riskContainer = document.getElementById('potentialRiskContainer');
            if (d.potential_risk) {
                const stats = d.potential_risk.stats || { total_pop: 0, infrastructures: 0 };
                riskContainer.innerHTML = `
                    <div style="margin-top:0px; margin-bottom:16px; padding:16px; background:rgba(245,158,11,0.1); border:1px solid rgba(245,158,11,0.3); border-radius:12px; display:flex; flex-direction:column; gap:10px;">
                        <div style="display:flex; align-items:center; gap:12px;">
                            <span style="font-size:20px;">⚠️</span>
                            <div style="font-size:13px; color:var(--accent-orange); line-height:1.4; font-weight:bold;">
                                ALERTE PROPAGATION : ${d.potential_risk.message}
                            </div>
                        </div>
                        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px; padding-left:36px; border-top:1px solid rgba(245,158,11,0.2); pt:10px; margin-top:5px;">
                            <div>
                                <div style="font-size:10px; color:var(--text-muted); text-transform:uppercase;">Population Potentielle</div>
                                <div style="font-size:16px; color:var(--accent-orange); font-weight:bold;">${stats.total_pop.toLocaleString()} pers.</div>
                            </div>
                            <div>
                                <div style="font-size:10px; color:var(--text-muted); text-transform:uppercase;">Infrastructures à risque</div>
                                <div style="font-size:16px; color:var(--accent-orange); font-weight:bold;">${stats.infrastructures} sites</div>
                            </div>
                        </div>
                    </div>
                `;
            } else {
                riskContainer.innerHTML = '';
            }

            // AI Description
            document.getElementById('aiDescription').innerHTML = `
                <div class="ai-badge">✨ IA Vision Engine</div>
                <div style="font-size: 16px; margin-bottom: 8px; color: var(--accent-orange); font-weight: 700;">
                    📍 ${d.geocoding ? d.geocoding.city : 'Zone rurale'} (${d.geocoding ? d.geocoding.region : 'Secteur inconnu'})
                </div>
                <div><strong>${d.ai_analysis.macro_category}</strong> — ${d.ai_analysis.sub_category}</div>
                <div style="margin-top:10px">${d.ai_analysis.description}</div>
            `;

            // Spread Tags & Impact Tags
            document.getElementById('spreadTags').innerHTML = d.ai_analysis.spread_vectors.map(v => `<span class="tag">${v}</span>`).join('');
            document.getElementById('impactTags').innerHTML = d.impact_tags.map(v => `<span class="tag" style="background: rgba(16,185,129,0.1); color: var(--accent-green); border-color: rgba(16,185,129,0.2);">${v}</span>`).join('');

            // Populations
            const indirectImpact = d.indirect_human_impact || {
                total_population_exposed: 0,
                adult_women_exposed: 0,
                adult_men_exposed: 0,
                children_exposed: 0
            };
            document.getElementById('socialPillarGrid').innerHTML = `
                <div class="detail-item"><div class="detail-item-label">Population directement exposée</div><div class="detail-item-value ${getSeverityClass(d.human_impact.total_population_exposed / 100)}">${d.human_impact.total_population_exposed.toLocaleString()}</div></div>
                <div class="detail-item"><div class="detail-item-label">Population indirectement concernée</div><div class="detail-item-value" style="color: var(--accent-orange)">${indirectImpact.total_population_exposed.toLocaleString()}</div></div>
                <div class="detail-item"><div class="detail-item-label">Femmes adultes exposées</div><div class="detail-item-value" style="color: var(--accent-purple)">${d.human_impact.adult_women_exposed.toLocaleString()}</div></div>
                <div class="detail-item"><div class="detail-item-label">Hommes adultes exposés</div><div class="detail-item-value" style="color: var(--accent-blue)">${d.human_impact.adult_men_exposed.toLocaleString()}</div></div>
                <div class="detail-item"><div class="detail-item-label">Enfants exposés (<15 ans)</div><div class="detail-item-value" style="color: var(--accent-orange)">${d.human_impact.children_exposed.toLocaleString()}</div></div>
                <div class="detail-item"><div class="detail-item-label">Femmes indirectement concernées</div><div class="detail-item-value" style="color: var(--accent-purple)">${indirectImpact.adult_women_exposed.toLocaleString()}</div></div>
                <div class="detail-item"><div class="detail-item-label">Hommes indirectement concernés</div><div class="detail-item-value" style="color: var(--accent-blue)">${indirectImpact.adult_men_exposed.toLocaleString()}</div></div>
                <div class="detail-item"><div class="detail-item-label">Enfants indirectement concernés</div><div class="detail-item-value" style="color: var(--accent-orange)">${indirectImpact.children_exposed.toLocaleString()}</div></div>
            `;

            // Milieu
            document.getElementById('envPillarGrid').innerHTML = `
                <div class="detail-item"><div class="detail-item-label">Température</div><div class="detail-item-value">${d.topography.temperature_celsius}°C</div></div>
                <div class="detail-item"><div class="detail-item-label">Précipitations</div><div class="detail-item-value">${d.topography.precipitation} mm</div></div>
                <div class="detail-item"><div class="detail-item-label">Vent</div><div class="detail-item-value">${d.topography.wind_speed} km/h</div></div>
                <div class="detail-item"><div class="detail-item-label">Pente</div><div class="detail-item-value">${d.topography.slope_percent}%</div></div>
                <div class="detail-item"><div class="detail-item-label">NDVI</div><div class="detail-item-value">${d.satellite.ndvi !== null ? d.satellite.ndvi.toFixed(3) : 'N/A'}</div></div>
                <div class="detail-item"><div class="detail-item-label">NDWI</div><div class="detail-item-value">${d.satellite.ndwi !== null ? d.satellite.ndwi.toFixed(3) : 'N/A'}</div></div>
                <div class="detail-item"><div class="detail-item-label">Occupation du Sol</div><div class="detail-item-value">${d.satellite.land_use}</div></div>
            `;

            // Infrastructures
            const ecoLabels = {
                health_centers: "Centres de santé",
                maternities: "Maternités",
                schools: "Écoles",
                nurseries: "Crèches",
                markets: "Marchés",
                water_points: "Points d'eau",
                main_roads_bridges: "Routes / Ponts",
                residential_buildings: "Bâtiments"
            };

            function renderStructureItems(counts, emptyText, isProbabilistic) {
                return Object.entries(counts || {})
                    .filter(([k,v]) => v > 0)
                    .map(([k,v]) => {
                    const isEstimated = isProbabilistic && ["health_centers", "schools", "markets", "water_points"].includes(k);
                    const label = ecoLabels[k] || k;
                    const badge = isEstimated ? '<span style="font-size:9px; background:rgba(245,158,11,0.2); color:var(--accent-orange); padding:1px 4px; border-radius:3px; margin-left:4px;">ESTIMÉ</span>' : '';
                    return `<div class="detail-item">
                        <div class="detail-item-label">${label}${badge}</div>
                        <div class="detail-item-value">${v}</div>
                    </div>`;
                    }).join('') || `<div style="color:var(--text-muted);font-size:13px">${emptyText}</div>`;
            }

            const directStructuresTotal = Object.values(d.social_data || {}).reduce((sum, value) => sum + value, 0);
            const indirectStructures = d.indirect_social_data || {};
            const indirectStructuresTotal = Object.values(indirectStructures).reduce((sum, value) => sum + value, 0);
            document.getElementById('ecoPillarGrid').innerHTML = `
                <div style="font-size:11px; color:var(--accent-green); font-weight:700; text-transform:uppercase; letter-spacing:.5px; margin:4px 0 8px;">Structures directement exposées</div>
                ${renderStructureItems(d.social_data, 'Aucune infrastructure dans le rayon direct', d.is_social_probabilistic)}
                <div style="font-size:11px; color:var(--accent-orange); font-weight:700; text-transform:uppercase; letter-spacing:.5px; margin:14px 0 8px;">Structures indirectement concernées</div>
                ${renderStructureItems(indirectStructures, 'Aucune infrastructure dans la zone de vigilance', d.is_indirect_social_probabilistic)}
            `;

            // Recommendation
            document.getElementById('recommendation').innerHTML = `
                <div style="margin-bottom:12px">⚡ ${d.recommendation}</div>
                <div style="display:flex;gap:16px;flex-wrap:wrap;margin-top:12px;padding-top:12px;border-top:1px solid rgba(245,158,11,0.2)">
                    <div><span style="font-size:18px">👥</span> <strong>${d.human_impact.total_population_exposed.toLocaleString()}</strong> directement exposés</div>
                    <div><span style="font-size:18px">🛡️</span> <strong>${indirectImpact.total_population_exposed.toLocaleString()}</strong> indirectement concernés</div>
                    <div><span style="font-size:18px">🏥</span> <strong>${directStructuresTotal.toLocaleString()}</strong> structures directement exposées</div>
                    <div><span style="font-size:18px">🏘️</span> <strong>${indirectStructuresTotal.toLocaleString()}</strong> structures indirectement concernées</div>
                    <div><span style="font-size:18px">👩</span> <strong>${d.human_impact.adult_women_exposed.toLocaleString()}</strong> femmes adultes exposées</div>
                    <div><span style="font-size:18px">👨</span> <strong>${d.human_impact.adult_men_exposed.toLocaleString()}</strong> hommes adultes exposés</div>
                    <div><span style="font-size:18px">👦</span> <strong>${d.human_impact.children_exposed.toLocaleString()}</strong> enfants exposés (<15 ans)</div>
                    ${d.human_impact.maternities_count > 0 ? `<div><span style="font-size:18px">🤱</span> <strong>${d.human_impact.maternities_count}</strong> maternité(s) exposée(s)</div>` : ''}
                    ${d.human_impact.nurseries_count > 0 ? `<div><span style="font-size:18px">👶</span> <strong>${d.human_impact.nurseries_count}</strong> crèche(s) exposée(s)</div>` : ''}
                </div>
            `;

            document.getElementById('resultsPanel').classList.add('visible');
            
            // Re-init chat context
            lastAnalysisData = d;
            addMessage("assistant", "Analyse terminée. Je suis prêt à répondre à vos questions stratégiques sur cet incident.");
        }

        // --- CHAT LOGIC ---
        let chatHistory = [];
        let lastAnalysisData = null;

        function toggleChat() {
            const win = document.getElementById('chatWindow');
            win.style.display = win.style.display === 'flex' ? 'none' : 'flex';
        }

        function addMessage(role, content) {
            const container = document.getElementById('chatMessages');
            const msgDiv = document.createElement('div');
            msgDiv.className = `message message-${role}`;
            msgDiv.textContent = content;
            container.appendChild(msgDiv);
            container.scrollTop = container.scrollHeight;
            if (role !== "system") {
                chatHistory.push({ role, content });
            }
        }

        function showTypingIndicator() {
            const container = document.getElementById('chatMessages');
            const div = document.createElement('div');
            div.id = 'typingIndicator';
            div.className = 'typing-indicator';
            div.innerHTML = `L'Expert Map Action analyse<span></span><span></span><span></span>`;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        }

        function removeTypingIndicator() {
            const ind = document.getElementById('typingIndicator');
            if (ind) ind.remove();
        }

        async function sendMessage() {
            const input = document.getElementById('chatInput');
            const text = input.value.trim();
            if (!text) return;

            if (!lastAnalysisData) {
                addMessage("assistant", "Veuillez d'abord lancer une analyse d'incident pour me donner du contexte.");
                input.value = '';
                return;
            }

            addMessage("user", text);
            input.value = '';
            
            showTypingIndicator();

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        messages: chatHistory,
                        context: lastAnalysisData
                    })
                });

                if (!response.body) {
                    removeTypingIndicator();
                    throw new Error("No readable stream");
                }

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let fullResponse = "";
                let firstChunkReceived = false;

                // Create assistant message div
                const container = document.getElementById('chatMessages');
                const msgDiv = document.createElement('div');
                msgDiv.className = `message message-assistant`;
                // On ne l'ajoute pas encore au container, on attend le premier chunk

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    const chunk = decoder.decode(value, { stream: true });
                    if (chunk && chunk.trim().length > 0) {
                        if (!firstChunkReceived) {
                            removeTypingIndicator();
                            container.appendChild(msgDiv);
                            firstChunkReceived = true;
                        }
                        fullResponse += chunk;
                        msgDiv.textContent = fullResponse;
                        container.scrollTop = container.scrollHeight;
                    }
                }
                
                if (!firstChunkReceived) removeTypingIndicator();
                chatHistory.push({ role: "assistant", content: fullResponse });
            } catch (err) {
                removeTypingIndicator();
                addMessage("assistant", "Erreur lors de la communication avec l'assistant.");
            }
        }
    </script>
</body>
</html>
"""

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Sert l'interface web du moteur d'impact."""
    return DASHBOARD_HTML
