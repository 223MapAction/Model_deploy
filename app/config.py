import os
from dotenv import load_dotenv

load_dotenv(override=True)

class Settings:
    # Gemini (Vision - Primary)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your_gemini_api_key")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-preview-04-17")

    @property
    def GEMINI_API_URL(self):
        return f"https://generativelanguage.googleapis.com/v1beta/models/{self.GEMINI_MODEL}:generateContent"

    # DeepSeek (Text reasoning - Optional/Future)
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "your_deepseek_api_key")
    DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro")

    # External APIs
    OPEN_METEO_ELEVATION_URL = "https://api.open-meteo.com/v1/elevation"
    OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
    OVERPASS_API_URL = "http://overpass-api.de/api/interpreter"
    
    # Earth Engine
    # Earth Engine
    GEE_PROJECT_ID = os.getenv("GEE_PROJECT_ID", "votre-id-de-projet")
    GEE_SERVICE_ACCOUNT_FILE = os.getenv("GEE_SERVICE_ACCOUNT_FILE", "gee-key.json")

    # Social Vulnerability Weights
    SOCIAL_WEIGHTS = {
        "health_centers": 3.0,
        "schools": 2.5,
        "markets": 2.0,
        "water_points": 1.5,
        "main_roads_bridges": 1.0,
        "residential_buildings": 0.1
    }

    # Taxonomie Hiérarchique des Incidents Environnementaux (V2)
    INCIDENT_TAXONOMY = {
        "Eau & Assainissement": {
            "Pollution de cours d'eau / puits / marigot": {"base_severity": 8, "base_radius": 1500, "expected_vectors": ["water_current", "human_contact"], "impact_tags": ["Eau", "Santé Publique"]},
            "Eaux usées stagnantes": {"base_severity": 7, "base_radius": 500, "expected_vectors": ["vectors_insects_rodents", "human_contact"], "impact_tags": ["Eau", "Santé Publique"]},
            "Déversement toxique dans l'eau": {"base_severity": 9, "base_radius": 2000, "expected_vectors": ["water_current"], "impact_tags": ["Eau", "Santé Publique", "Biodiversité"]},
            "Caniveaux bouchés / mauvais drainage": {"base_severity": 6, "base_radius": 300, "expected_vectors": ["vectors_insects_rodents"], "impact_tags": ["Eau", "Santé Publique", "Insalubrité"]}
        },
        "Déchets & Insalubrité": {
            "Décharge sauvage": {"base_severity": 6, "base_radius": 500, "expected_vectors": ["vectors_insects_rodents", "human_contact"], "impact_tags": ["Déchets", "Sols", "Santé Publique"]},
            "Accumulation d'ordures": {"base_severity": 5, "base_radius": 200, "expected_vectors": ["vectors_insects_rodents"], "impact_tags": ["Déchets", "Insalubrité"]},
            "Déchets biomédicaux": {"base_severity": 8, "base_radius": 500, "expected_vectors": ["human_contact", "vectors_insects_rodents"], "impact_tags": ["Déchets", "Santé Publique"]},
            "Déchets dangereux / toxiques": {"base_severity": 9, "base_radius": 1000, "expected_vectors": ["water_current", "wind"], "impact_tags": ["Déchets", "Sols", "Eau", "Santé Publique"]},
            "Brûlage de déchets": {"base_severity": 7, "base_radius": 1000, "expected_vectors": ["wind"], "impact_tags": ["Déchets", "Air", "Santé Publique"]}
        },
        "Qualité de l'Air": {
            "Fumées industrielles": {"base_severity": 7, "base_radius": 3000, "expected_vectors": ["wind"], "impact_tags": ["Air", "Santé Publique"]},
            "Poussières excessives": {"base_severity": 5, "base_radius": 2000, "expected_vectors": ["wind"], "impact_tags": ["Air"]},
            "Odeurs/gaz toxiques": {"base_severity": 7, "base_radius": 1500, "expected_vectors": ["wind"], "impact_tags": ["Air", "Santé Publique"]},
            "Pollution liée aux chantiers/carrières": {"base_severity": 6, "base_radius": 1000, "expected_vectors": ["wind"], "impact_tags": ["Air", "Nuisances"]}
        },
        "Risques Naturels & Climatiques": {
            "Inondation": {"base_severity": 8, "base_radius": 3000, "expected_vectors": ["water_current", "slope"], "impact_tags": ["Eau", "Infrastructures", "Sécurité"]},
            "Sécheresse extrême": {"base_severity": 7, "base_radius": 10000, "expected_vectors": ["wind"], "impact_tags": ["Climat", "Agriculture", "Eau"]},
            "Incendie / feu de brousse": {"base_severity": 9, "base_radius": 5000, "expected_vectors": ["wind", "slope"], "impact_tags": ["Air", "Biodiversité", "Sécurité"]},
            "Vents violents / tempête de poussière": {"base_severity": 6, "base_radius": 10000, "expected_vectors": ["wind"], "impact_tags": ["Climat", "Air"]}
        },
        "Dégradation des Terres": {
            "Déforestation / coupe abusive": {"base_severity": 7, "base_radius": 2000, "expected_vectors": [], "impact_tags": ["Forêt", "Biodiversité", "Sols"]},
            "Érosion / ravinement": {"base_severity": 7, "base_radius": 500, "expected_vectors": ["water_current", "slope"], "impact_tags": ["Sols", "Infrastructures"]},
            "Ensablement": {"base_severity": 6, "base_radius": 1000, "expected_vectors": ["wind"], "impact_tags": ["Sols", "Agriculture"]},
            "Glissement / effondrement de terrain": {"base_severity": 8, "base_radius": 500, "expected_vectors": ["slope"], "impact_tags": ["Sols", "Sécurité", "Infrastructures"]}
        },
        "Activités minières & extractives": {
            "Orpaillage à impact environnemental": {"base_severity": 9, "base_radius": 1500, "expected_vectors": ["water_current", "human_contact"], "impact_tags": ["Sols", "Eau", "Biodiversité"]},
            "Carrière non contrôlée": {"base_severity": 7, "base_radius": 1000, "expected_vectors": ["wind", "slope"], "impact_tags": ["Sols", "Air", "Nuisances"]},
            "Pollution minière / mercure / cyanure": {"base_severity": 10, "base_radius": 3000, "expected_vectors": ["water_current"], "impact_tags": ["Sols", "Eau", "Santé Publique", "Biodiversité"]}
        },
        "Biodiversité & Écosystèmes": {
            "Dégradation de zone humide": {"base_severity": 8, "base_radius": 2000, "expected_vectors": ["water_current"], "impact_tags": ["Biodiversité", "Eau"]},
            "Mort de poissons / animaux": {"base_severity": 8, "base_radius": 1000, "expected_vectors": ["water_current"], "impact_tags": ["Biodiversité", "Santé Publique"]},
            "Destruction d'habitat naturel": {"base_severity": 7, "base_radius": 2000, "expected_vectors": [], "impact_tags": ["Biodiversité", "Forêt"]},
            "Pression sur espèces sensibles": {"base_severity": 7, "base_radius": 5000, "expected_vectors": [], "impact_tags": ["Biodiversité"]}
        },
        "Nuisances & Cadre de vie": {
            "Mauvaises odeurs": {"base_severity": 4, "base_radius": 500, "expected_vectors": ["wind"], "impact_tags": ["Nuisances", "Air"]},
            "Bruit excessif": {"base_severity": 3, "base_radius": 500, "expected_vectors": ["wind"], "impact_tags": ["Nuisances"]},
            "Égouts à ciel ouvert": {"base_severity": 6, "base_radius": 300, "expected_vectors": ["vectors_insects_rodents", "human_contact"], "impact_tags": ["Insalubrité", "Santé Publique"]},
            "Insalubrité publique": {"base_severity": 5, "base_radius": 500, "expected_vectors": ["vectors_insects_rodents"], "impact_tags": ["Insalubrité", "Santé Publique"]}
        },
        "Autre": {
            "Incident non répertorié": {"base_severity": 5, "base_radius": 500, "expected_vectors": [], "impact_tags": ["Divers"]}
        },
        "Hors Contexte / Image Invalide": {
            "Objet non environnemental (Test)": {"base_severity": 0, "base_radius": 0, "expected_vectors": [], "impact_tags": ["Test"]},
            "Image floue ou illisible": {"base_severity": 0, "base_radius": 0, "expected_vectors": [], "impact_tags": ["Test"]}
        },
        "Statut Normal": {
            "Zone saine / Aucun incident": {"base_severity": 0, "base_radius": 0, "expected_vectors": [], "impact_tags": ["Sain"]}
        }
    }

settings = Settings()
