import os
import logging
from app.services.cnn.openai_vision import predict as openai_predict, predict_structured as openai_predict_structured
from app.services.cnn.models import PredictionResult

# Set up logging
logger = logging.getLogger(__name__)

# Define the environmental issue tags
tags = [
    "Puits abîmé",
    "Fosse pleine",
    "Latrines bouchées",
    "Eaux stagnantes",
    "Décharge illégale",
    "Déchets biomédicaux",
    "Plastiques épars",
    "Feu déchets",
    "Ordures non collectées",
    "Déchets électroniques",
    "Arbres coupés",
    "Feux de brousse",
    "Sol Nu",
    "Sol érodé",
    "Fumées industrielles",
    "Eaux sales",
    "Pollution plastique",
    "Pollution visuelle",
    "Inondation",
    "Sécheresse",
    "Glissement de terrain",
    "Animal mort",
    "Zone humide agréssée",
    "Espèces invasives",
    "Surpâturage",
    "Caniveaux bouchés",
    "Équipement HS",
    "Déversement illégal"
]

def predict(image):
    """
    Performs multi-label image classification using OpenAI's vision model.
    
    Args:
        image (bytes): The image data in bytes format.
    
    Returns:
        tuple: A tuple containing a list of predicted tags and a list of probabilities.
    """
    logger.info("Using OpenAI model for prediction")
    return openai_predict(image)

def predict_structured(image) -> PredictionResult:
    """
    Performs multi-label image classification and returns a structured Pydantic model.
    
    Args:
        image (bytes): The image data in bytes format.
    
    Returns:
        PredictionResult: A structured prediction result.
    """
    return openai_predict_structured(image)

