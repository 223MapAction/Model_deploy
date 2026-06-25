from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class AnalyzeRequest(BaseModel):
    image_url: str = Field(..., description="URL of the image or base64 data to analyze")
    latitude: float = Field(..., description="Latitude of the incident")
    longitude: float = Field(..., description="Longitude of the incident")
    incident_id: Optional[str] = Field(None, description="Optional ID for tracking")

class DeepSeekResponse(BaseModel):
    macro_category: str = Field(..., description="Macro-category of the incident from the taxonomy")
    sub_category: str = Field(..., description="Specific sub-category of the incident from the taxonomy")
    source_size_meters: float = Field(..., description="La taille physique directe visible de la source de l'incident en mètres")
    spread_vectors: List[str] = Field(..., description="Factors spreading the impact observed in the image")
    description: str = Field(..., description="Detailed explanation of the visual analysis")

class SpatialData(BaseModel):
    elevation: float
    slope_percent: float
    wind_speed: float
    precipitation: float
    temperature_celsius: float

class MacroContext(BaseModel):
    is_urban: bool
    is_agricultural: bool
    is_arid: bool
    building_count: int

class SatelliteData(BaseModel):
    ndvi: Optional[float]
    ndwi: Optional[float]
    land_use: str
    raw_data: Optional[Dict[str, Any]] = None

class HumanImpact(BaseModel):
    """Estimation de l'impact humain différencié dans le rayon final."""
    total_population_exposed: int
    adult_men_exposed: int
    adult_women_exposed: int
    children_exposed: int
    maternities_count: int
    nurseries_count: int

class AnalyzeResponse(BaseModel):
    incident_id: Optional[str]
    latitude: float
    longitude: float
    ai_analysis: DeepSeekResponse
    topography: SpatialData
    satellite: SatelliteData
    social_data: Dict[str, int]
    indirect_social_data: Optional[Dict[str, int]] = None
    social_vulnerability_score: float
    is_social_probabilistic: bool
    is_indirect_social_probabilistic: bool = False
    human_impact: HumanImpact
    indirect_human_impact: Optional[HumanImpact] = None
    impact_radius_meters: float
    indirect_vigilance_radius_meters: Optional[float] = None
    indirect_vigilance_explanation: Optional[str] = None
    radius_explanation: str
    global_impact_score: float
    base_severity: int
    impact_tags: List[str] = Field(default_factory=list)
    geocoding: Optional[Dict[str, str]] = None
    recommendation: str
    potential_risk: Optional[Dict[str, Any]] = None

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    context: Dict[str, Any]
