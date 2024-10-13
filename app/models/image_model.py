from pydantic import BaseModel
from typing import List

class ImageModel(BaseModel):
    """
    A model representing image data for processing and prediction in the API.

    Attributes:
        image_name (str): The name or path where the image is stored. This is used to fetch the image for analysis.
        sensitive_structures (List[str]): A list of structures or areas in the image that are considered sensitive. This information is used to provide contextual analysis based on the prediction results.
        incident_id (str): A unique identifier for the incident depicted in the image. This is used for tracking and storing results in the database.
    """
    #Id: int  # Uncomment if an ID attribute is necessary
    image_name: str
    sensitive_structures: List[str]
    incident_id: str
    zone: str
    latitude: float
    longitude: float