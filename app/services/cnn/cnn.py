import os
import logging
from app.services.cnn.openai_vision import predict as openai_predict, predict_structured as openai_predict_structured
from app.services.cnn.models import PredictionResult

# Set up logging
logger = logging.getLogger(__name__)

# Define the environmental issue tags
tags = ["Caniveau obstrué", "Déchets", "Déforestation",
        "Feux de brousse", "Pollution de leau", "Pollution de lair", "Sécheresse", "Sol dégradé"]

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

