import math
from typing import Dict, Any
from app.config import settings

DIRECT_MIN_RADIUS_BY_SUBCATEGORY = {
    "Accumulation d'ordures": 25.0,
    "Décharge sauvage": 50.0,
    "Déchets biomédicaux": 75.0,
    "Caniveaux bouchés / mauvais drainage": 30.0,
    "Égouts à ciel ouvert": 30.0,
    "Insalubrité publique": 40.0,
}

VECTOR_VIGILANCE_SUBCATEGORY_BONUS = {
    "Accumulation d'ordures": 25.0,
    "Décharge sauvage": 75.0,
    "Déchets biomédicaux": 75.0,
    "Eaux usées stagnantes": 75.0,
    "Caniveaux bouchés / mauvais drainage": 50.0,
    "Égouts à ciel ouvert": 50.0,
    "Insalubrité publique": 50.0,
}

def _get_taxonomy_data(macro: str, sub: str) -> dict:
    macro_data = settings.INCIDENT_TAXONOMY.get(macro, {})
    return macro_data.get(sub, settings.INCIDENT_TAXONOMY.get("Autre", {}).get("Incident non répertorié", {
        "base_severity": 5, 
        "base_radius": 500, 
        "expected_vectors": [], 
        "impact_tags": ["Divers"]
    }))

def _calculate_vector_vigilance_distance(sub_category: str, is_urban: bool, temp: float, precip: float) -> float:
    """
    Distance operationnelle de vigilance indirecte pour nuisances/vectoriel.
    Elle applique le principe OMS de gestion vectorielle integree: contexte local,
    reduction des gites et priorisation rationnelle, sans presenter une distance
    fixe comme exposition directe.
    """
    distance = 50.0
    distance += VECTOR_VIGILANCE_SUBCATEGORY_BONUS.get(sub_category, 25.0)
    if is_urban:
        distance += 25.0
    if temp >= 30.0:
        distance += 25.0
    if precip > 0.0:
        distance += 25.0
    return min(distance, 200.0)

def calculate_dynamic_radius(ai_data: Any, spatial_data: Dict[str, Any], macro_osm_counts: Dict[str, int], sat_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Moteur de Propagation Physique : Calcule le rayon d'impact factuel basé sur la source et les vecteurs de propagation (IA + Taxonomie).
    """
    is_urban = macro_osm_counts.get("residential_buildings", 0) > 100
    temp = spatial_data.get("temperature_celsius", 25.0)
    precip = spatial_data.get("precipitation", 0.0)
    wind = spatial_data.get("wind_speed", 0.0)
    slope = spatial_data.get("slope_percent", 0.0)
    
    is_arid = temp > 35.0 and precip < 1.0
    land_use = sat_data.get("land_use", "").lower()
    is_agricultural = "cultivated" in land_use or "agricole" in land_use
    if "urban" in land_use or "bâti" in land_use:
        is_urban = True

    tax_data = _get_taxonomy_data(ai_data.macro_category, ai_data.sub_category)
    base_radius = max(
        float(ai_data.source_size_meters),
        DIRECT_MIN_RADIUS_BY_SUBCATEGORY.get(ai_data.sub_category, 0.0)
    )
    
    ai_vectors = [v.lower() for v in getattr(ai_data, "spread_vectors", [])]
    expected_vectors = tax_data.get("expected_vectors", [])
    vectors = list(set(ai_vectors + expected_vectors))
    
    max_spread = 0.0
    explanation_parts = []
    indirect_vigilance = None
    
    # 1. Vecteur Insectes / Rongeurs : vigilance indirecte, pas exposition directe.
    if "vectors_insects_rodents" in vectors:
        vigilance_distance = _calculate_vector_vigilance_distance(
            sub_category=ai_data.sub_category,
            is_urban=is_urban,
            temp=temp,
            precip=precip,
        )
        indirect_vigilance = {
            "vector": "Insectes / Rongeurs",
            "distance": round(vigilance_distance),
            "message": (
                "Zone de vigilance indirecte pour nuisances et risque vectoriel "
                f"estimee a +{round(vigilance_distance)}m."
            ),
        }
            
    # 2. Vecteur Courant d'eau (Inondation, Lixiviation)
    potential_risk = None
    if "water_current" in vectors:
        # On ne l'ajoute plus au rayon principal (à la demande de l'utilisateur)
        # Mais on le note comme un risque potentiel
        potential_spread_distance = 600.0 + (precip * max(slope, 1.0) * 5.0)
        potential_risk = {
            "vector": "Courant d'eau / Ruissellement",
            "distance": round(potential_spread_distance),
            "message": f"Risque de propagation secondaire par courant d'eau estimé à +{round(potential_spread_distance)}m."
        }
        spread = 0.0 # Pas d'impact immédiat sur le rayon visible
        
        if spread > max_spread:
            max_spread = spread
            explanation_parts = ["propagation par courant (potentiel uniquement)"]
                
    # 3. Vecteur Vent (Feu, Fumée, Gaz, Odeurs)
    if "wind" in vectors:
        spread = wind * 10.0
        if spread > max_spread:
            max_spread = spread
            explanation_parts = [f"propagation éolienne (vent {wind}km/h, +{round(spread)}m)"]
            
    # 4. Vecteur Contact Humain (Densité)
    if "human_contact" in vectors:
        spread = 50.0 if is_urban else 20.0
        if spread > max_spread:
            max_spread = spread
            explanation_parts = [f"contact humain direct en zone dense (+{spread}m)"]
            
    # 5. Vecteur Pente (Glissement de terrain, érosion)
    if "slope" in vectors and "water_current" not in vectors:
        spread = slope * 8.0
        if spread > max_spread:
            max_spread = spread
            explanation_parts = [f"dégradation par la pente ({slope}%, +{round(spread)}m)"]

    # Si aucun vecteur ne s'applique ou max_spread = 0
    if max_spread == 0.0 and not explanation_parts:
        explanation_parts = ["emprise directe de la source et marge sanitaire locale"]

    final_radius = base_radius + max_spread
    
    # 6. Finalisation du risque potentiel (après calcul du final_radius)
    if potential_risk:
        potential_radius = final_radius + potential_risk["distance"]
        potential_risk["potential_radius"] = round(potential_radius)

    if indirect_vigilance:
        indirect_radius = final_radius + indirect_vigilance["distance"]
        indirect_vigilance["potential_radius"] = round(indirect_radius)

    explanation = f"Rayon direct calculé depuis l'emprise source ({base_radius}m) et {explanation_parts[0]}."

    return {
        "final_radius": round(final_radius, 2),
        "radius_explanation": explanation,
        "indirect_vigilance": indirect_vigilance,
        "potential_risk": potential_risk,
        "is_urban": is_urban,
        "is_arid": is_arid,
        "is_agricultural": is_agricultural
    }

def calculate_global_impact(ai_data: Any, sat_data: Dict[str, Any], spatial_data: Dict[str, Any], social_score: float) -> Dict[str, float]:
    """
    Phase 2: Calcule le score final d'impact (0-10) une fois la vulnérabilité sociale locale connue.
    Inclut un amortisseur météo si l'incident est latent.
    """
    tax_data = _get_taxonomy_data(ai_data.macro_category, ai_data.sub_category)
    severity = tax_data.get("base_severity", 5)
    
    contexte_env = 5.0
    if sat_data.get("ndvi") is not None and sat_data.get("ndvi") > 0.6:
        contexte_env += 2.0
    land_use = sat_data.get("land_use", "").lower()
    if "water" in land_use or "eau" in land_use:
        contexte_env += 3.0
    contexte_env = min(10.0, contexte_env)
    
    impact_score = (severity * 0.4) + (social_score * 0.4) + (contexte_env * 0.2)
    
    # Neutralisation pour les tests (chaussures, etc.) ou zone saine
    if severity == 0:
        impact_score = 0.0
    
    # Amortisseur Météo (Péril Latent vs Péril Immédiat)
    category = ai_data.macro_category.lower()
    precipitation = spatial_data.get("precipitation", 0.0)
    
    if ("inondation" in category or "eau" in category) and precipitation < 1.0:
        # Le danger principal (crue) n'est pas actif à la minute T.
        # On réduit le score global de 15% pour éviter la panique artificielle, 
        # tout en gardant une note élevée pour le risque sanitaire (maladies).
        impact_score *= 0.85
        
    impact_score = min(10.0, impact_score)
    
    return {
        "impact_score": round(impact_score, 2),
        "environmental_context_score": round(contexte_env, 2)
    }
