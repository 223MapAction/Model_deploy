import logging
import requests
import ee
import os
from typing import Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

# Initialisation de Earth Engine (Service Account ou Default)
try:
    if os.path.exists(settings.GEE_SERVICE_ACCOUNT_FILE):
        logger.info(f"Initialisation de GEE via le compte de service: {settings.GEE_SERVICE_ACCOUNT_FILE}")
        credentials = ee.ServiceAccountCredentials(
            "", # L'email est lu dans le JSON
            key_file=settings.GEE_SERVICE_ACCOUNT_FILE
        )
        ee.Initialize(credentials=credentials, project=settings.GEE_PROJECT_ID)
    else:
        logger.info("Initialisation de GEE via les identifiants par défaut...")
        ee.Initialize(project=settings.GEE_PROJECT_ID)
    GEE_INITIALIZED = True
except Exception as e:
    logger.warning(f"Google Earth Engine non initialisé. Erreur: {e}")
    GEE_INITIALIZED = False

def get_geocoding_context(lat: float, lon: float) -> Dict[str, str]:
    """Récupère le contexte administratif (Ville, Région, Pays) via Nominatim (OpenStreetMap)."""
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&accept-language=fr"
        headers = {"User-Agent": "MapActionImpactEngine/1.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        address = data.get("address", {})
        
        return {
            "city": address.get("city") or address.get("town") or address.get("village") or address.get("hamlet") or "Zone non habitée",
            "region": address.get("state") or address.get("region") or "Inconnue",
            "country": address.get("country", "Inconnu"),
            "display_name": data.get("display_name", "Lieu inconnu")
        }
    except Exception as e:
        logger.error(f"Erreur Géocodage : {e}")
        return {"city": "Inconnu", "region": "Inconnue", "country": "Inconnu", "display_name": "Lieu inconnu"}

def get_slope_data(lat: float, lon: float) -> float:
    """
    Récupère l'altitude et calcule une estimation de la pente (slope) via Open-Meteo Elevation API.
    Note: Open-Meteo Elevation donne l'altitude. Pour la pente précise, il faudrait plusieurs points,
    mais on va simuler ou récupérer l'élévation pour ce point.
    """
    try:
        # Open-Meteo Elevation
        url = f"{settings.OPEN_METEO_ELEVATION_URL}?latitude={lat}&longitude={lon}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "elevation" in data and len(data["elevation"]) > 0:
            elevation = data["elevation"][0]
            # Pour calculer une vraie pente (slope) en %, il faut normalement un DEM (Digital Elevation Model) local.
            # Ici, nous retournons une valeur simulée basée sur des heuristiques géographiques ou un appel météo si la pente y est exposée.
            # Pour l'instant, on retourne 0.0 et on laisse une logique future affiner.
            # Si on voulait une vraie pente, on interrogerait un DEM via GEE.
            
            # Utilisons GEE pour la pente si disponible, sinon on simule
            if GEE_INITIALIZED:
                point = ee.Geometry.Point(lon, lat)
                dem = ee.Image("USGS/SRTMGL1_003")
                slope_img = ee.Terrain.slope(dem)
                slope_val = slope_img.reduceRegion(reducer=ee.Reducer.mean(), geometry=point, scale=30).get('slope').getInfo()
                return float(slope_val) if slope_val is not None else 0.0

            return 5.0 # Valeur de pente par défaut (5%) si GEE n'est pas dispo
            
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des données topographiques: {e}")
        return 0.0

import math

def get_weather_data(lat: float, lon: float) -> Dict[str, float]:
    """Récupère les données météo actuelles via Open-Meteo."""
    try:
        url = f"{settings.OPEN_METEO_FORECAST_URL}?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation,wind_speed_10m"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        current = data.get("current", {})
        return {
            "temperature_celsius": float(current.get("temperature_2m", 25.0)),
            "precipitation": float(current.get("precipitation", 0.0)),
            "wind_speed": float(current.get("wind_speed_10m", 0.0))
        }
    except Exception as e:
        logger.error(f"Erreur météo: {e}")
        return {"temperature_celsius": 25.0, "precipitation": 0.0, "wind_speed": 10.0}

def get_osm_data(lat: float, lon: float, radius: int) -> Dict[str, Any]:
    """
    Récupère les infrastructures sensibles dans un rayon donné via Overpass API.
    Retourne les décomptes et les éléments bruts pour un filtrage ultérieur.
    """
    overpass_query = f"""
    [out:json];
    (
      node["amenity"~"hospital|clinic|maternity"](around:{radius},{lat},{lon});
      way["amenity"~"hospital|clinic|maternity"](around:{radius},{lat},{lon});
      
      node["amenity"~"school|kindergarten|college|nursery|childcare"](around:{radius},{lat},{lon});
      way["amenity"~"school|kindergarten|college|nursery|childcare"](around:{radius},{lat},{lon});
      
      node["amenity"~"market|marketplace"](around:{radius},{lat},{lon});
      way["amenity"~"market|marketplace"](around:{radius},{lat},{lon});
      
      node["amenity"~"drinking_water|water_point"](around:{radius},{lat},{lon});
      node["man_made"~"water_well|water_tap"](around:{radius},{lat},{lon});
      
      way["highway"~"primary|secondary|bridge"](around:{radius},{lat},{lon});
      
      way["building"](around:{radius},{lat},{lon});
      node["building"](around:{radius},{lat},{lon});
    );
    out center;
    """
    
    counts = {
        "health_centers": 0,
        "maternities": 0,
        "schools": 0,
        "nurseries": 0,
        "markets": 0,
        "water_points": 0,
        "main_roads_bridges": 0,
        "residential_buildings": 0
    }
    
    try:
        headers = {"User-Agent": "MapActionImpactEngine/1.0"}
        response = requests.post(settings.OVERPASS_API_URL, data={"data": overpass_query}, headers=headers, timeout=30)
        response.raise_for_status()
        elements = response.json().get("elements", [])
        
        for el in elements:
            tags = el.get("tags", {})
            amenity = tags.get("amenity", "")
            highway = tags.get("highway", "")
            building = tags.get("building", "")
            
            if amenity in ["hospital", "clinic"]:
                counts["health_centers"] += 1
            elif amenity == "maternity":
                counts["maternities"] += 1
                counts["health_centers"] += 1  # Comptée aussi en santé générale
            elif amenity in ["school", "college"]:
                counts["schools"] += 1
            elif amenity in ["kindergarten", "nursery", "childcare"]:
                counts["nurseries"] += 1
                counts["schools"] += 1  # Comptée aussi en éducation
            elif amenity in ["market", "marketplace"]:
                counts["markets"] += 1
            elif amenity in ["drinking_water", "water_point"]:
                counts["water_points"] += 1
            
            man_made = tags.get("man_made", "")
            if man_made in ["water_well", "water_tap"]:
                counts["water_points"] += 1
                
            if highway in ["primary", "secondary", "bridge"]:
                counts["main_roads_bridges"] += 1
                
            # Tous les bâtiments (building=* y compris building=yes)
            if building and building not in ["", "no"]:
                counts["residential_buildings"] += 1
                
    except Exception as e:
        logger.error(f"Erreur lors de la requête Overpass API: {e}")
        elements = []
        
    return {"counts": counts, "elements": elements}

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcule la distance en mètres entre deux points GPS."""
    R = 6371000 # Rayon de la terre en mètres
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def filter_osm_by_radius(osm_data: Dict[str, Any], origin_lat: float, origin_lon: float, final_radius: float) -> Dict[str, int]:
    """Filtre les éléments OSM pour ne garder que ceux strictement dans le rayon final."""
    counts = {
        "health_centers": 0, "maternities": 0, "schools": 0, "nurseries": 0,
        "markets": 0, "water_points": 0, "main_roads_bridges": 0, "residential_buildings": 0
    }
    
    elements = osm_data.get("elements", [])
    logger.info(f"Filtrage Micro : {len(elements)} éléments macro reçus pour un rayon de {final_radius}m")
    
    for el in elements:
        el_lat = el.get("lat") or (el.get("center", {}).get("lat"))
        el_lon = el.get("lon") or (el.get("center", {}).get("lon"))
        
        if el_lat is None or el_lon is None:
            continue
            
        dist = haversine_distance(origin_lat, origin_lon, el_lat, el_lon)
        if dist <= final_radius:
            tags = el.get("tags", {})
            # Debug: logger.debug(f"Element in radius: {el.get('id')} type={el.get('type')} tags={tags}")
            
            amenity = tags.get("amenity", "")
            highway = tags.get("highway", "")
            building = tags.get("building", "")
            man_made = tags.get("man_made", "")
            
            if amenity in ["hospital", "clinic"]: counts["health_centers"] += 1
            elif amenity == "maternity":
                counts["maternities"] += 1
                counts["health_centers"] += 1
            elif amenity in ["school", "college"]: counts["schools"] += 1
            elif amenity in ["kindergarten", "nursery", "childcare"]:
                counts["nurseries"] += 1
                counts["schools"] += 1
            elif amenity in ["market", "marketplace"]: counts["markets"] += 1
            elif amenity in ["drinking_water", "water_point"]: counts["water_points"] += 1
            if man_made in ["water_well", "water_tap"]: counts["water_points"] += 1
            if highway in ["primary", "secondary", "bridge"]: counts["main_roads_bridges"] += 1
            if building and building not in ["", "no"]: counts["residential_buildings"] += 1
            
    logger.info(f"Résultats filtrés : {counts['residential_buildings']} bâtiments trouvés dans {final_radius}m")
    return counts

def calculate_social_vulnerability(osm_data: dict, land_use: str = "Inconnu") -> Dict[str, Any]:
    """
    Calcule le score de vulnérabilité sociale sur 10.
    Utilise une approche probabiliste si les données OSM sont vides en zone dense ou urbaine.
    """
    raw_score = 0.0
    is_probabilistic = False
    
    buildings = osm_data.get('residential_buildings', 0)
    
    # Correction : Si le satellite dit "Urbain" mais OSM est pauvre (< 5 bâtiments)
    if buildings < 5 and land_use == "Urbain / Bâti":
        # On injecte une densité par défaut pour réveiller les compteurs
        # On passe à 150 bâtiments pour garantir un impact chiffré visible
        buildings = 150 
        osm_data['residential_buildings'] = buildings
        is_probabilistic = True
        logger.info(f"OSM vide en zone Urbaine. Injection de 150 bâtiments (estimation satellite).")
    
    # 1. Infrastructures Avérées (OSM)
    health = osm_data.get('health_centers', 0)
    schools = osm_data.get('schools', 0)
    markets = osm_data.get('markets', 0)
    water = osm_data.get('water_points', 0)
    
    # 2. Logique Probabiliste (si zone dense mais vide sur OSM)
    # Plus de 10 bâtiments (env. 65+ habitants) mais 0 école et 0 santé
    if buildings >= 10 and health == 0 and schools == 0:
        is_probabilistic = True
        estimated_pop = buildings * 6.5
        # Ratios (probables) : 1 centre santé/2000 hab, 1 école/1000 hab, 1 marché/1500 hab, 1 pt eau/500 hab
        prob_health = int(estimated_pop / 2000)
        prob_schools = int(estimated_pop / 1000)
        prob_markets = int(estimated_pop / 1500)
        prob_water = int(estimated_pop / 500)
        
        # Pondération réduite (50% de la valeur d'une infrastructure avérée)
        raw_score += prob_health * (settings.SOCIAL_WEIGHTS["health_centers"] * 0.5)
        raw_score += prob_schools * (settings.SOCIAL_WEIGHTS["schools"] * 0.5)
        raw_score += prob_markets * (settings.SOCIAL_WEIGHTS["markets"] * 0.5)
        raw_score += prob_water * (settings.SOCIAL_WEIGHTS["water_points"] * 0.5)
        
        # Injecter dans les données pour l'affichage UI
        osm_data['health_centers'] = prob_health
        osm_data['schools'] = prob_schools
        osm_data['markets'] = prob_markets
        osm_data['water_points'] = prob_water
    else:
        # Valeurs avérées pleines
        raw_score += health * settings.SOCIAL_WEIGHTS["health_centers"]
        raw_score += schools * settings.SOCIAL_WEIGHTS["schools"]
        raw_score += markets * settings.SOCIAL_WEIGHTS["markets"]
        raw_score += water * settings.SOCIAL_WEIGHTS["water_points"]

    # Infras spécifiques avec poids fort (toujours basées sur OSM)
    raw_score += osm_data.get('maternities', 0) * 4.0
    raw_score += osm_data.get('nurseries', 0) * 3.0
    
    raw_score += osm_data.get('main_roads_bridges', 0) * settings.SOCIAL_WEIGHTS["main_roads_bridges"]
    raw_score += buildings * settings.SOCIAL_WEIGHTS["residential_buildings"]
    
    return {
        "score": min(10.0, raw_score),
        "is_probabilistic": is_probabilistic,
        "estimated_buildings": buildings # On renvoie le nombre (éventuellement estimé)
    }

def calculate_human_impact(osm_micro: dict, estimated_buildings: int = None) -> dict:
    """
    Estime la population exposée. Utilise les bâtiments estimés si fournis.
    """
    buildings = estimated_buildings if estimated_buildings is not None else osm_micro.get('residential_buildings', 0)
    total_population = int(buildings * 6.5)
    
    children = int(total_population * 0.47)
    adult_women = int(total_population * 0.27)
    # L'homme adulte prend le reste pour assurer une somme parfaite
    adult_men = total_population - children - adult_women
    
    return {
        "total_population_exposed": total_population,
        "adult_men_exposed": adult_men,
        "adult_women_exposed": adult_women,
        "children_exposed": children,
        "maternities_count": osm_micro.get('maternities', 0),
        "nurseries_count": osm_micro.get('nurseries', 0)
    }

def get_satellite_analysis(lat: float, lon: float) -> Dict[str, Any]:
    """
    Analyse satellite avec Google Earth Engine (NDVI, NDWI, Land Use).
    Retourne des valeurs par défaut si GEE n'est pas initialisé ou en cas d'erreur.
    """
    result = {
        "ndvi": None,
        "ndwi": None,
        "land_use": "Inconnu"
    }
    
    if not GEE_INITIALIZED:
        logger.warning("get_satellite_analysis appelé mais GEE_INITIALIZED est False. Retour des valeurs nulles.")
        return result
        
    logger.info("Début de l'analyse GEE...")
        
    try:
        point = ee.Geometry.Point(lon, lat)
        
        # NDVI (Sentinel-2)
        s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
            .filterBounds(point) \
            .filterDate('2020-01-01', '2026-01-01') \
            .sort('CLOUDY_PIXEL_PERCENTAGE') \
            .first()
            
        if s2:
            ndvi = s2.normalizedDifference(['B8', 'B4'])
            ndwi = s2.normalizedDifference(['B3', 'B8'])
            
            ndvi_val = ndvi.reduceRegion(reducer=ee.Reducer.mean(), geometry=point, scale=10).get('nd').getInfo()
            ndwi_val = ndwi.reduceRegion(reducer=ee.Reducer.mean(), geometry=point, scale=10).get('nd').getInfo()
            
            result["ndvi"] = float(ndvi_val) if ndvi_val is not None else None
            result["ndwi"] = float(ndwi_val) if ndwi_val is not None else None

        # Land Cover (Copernicus Global Land Cover)
        lc = ee.Image("COPERNICUS/Landcover/100m/Proba-V-C3/Global/2019")
        lc_val = lc.select('discrete_classification').reduceRegion(reducer=ee.Reducer.first(), geometry=point, scale=100).get('discrete_classification').getInfo()
        
        # Mapping des classes en Français
        lc_map = {
            20: "Arbustes", 
            30: "Végétation herbacée", 
            40: "Terres agricoles / cultivées",
            50: "Urbain / Bâti", 
            60: "Végétation rare / Sols nus", 
            80: "Plans d'eau permanents",
            111: "Forêt dense (feuillage persistant)", 
            112: "Forêt dense (feuillus)"
        }
        if lc_val in lc_map:
            result["land_use"] = lc_map[lc_val]
            
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse GEE: {e}")
        
    return result
