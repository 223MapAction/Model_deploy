import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import CNN prediction service
try:
    from .cnn import predict
except ImportError as e:
    logger.warning(f"Failed to import CNN module: {e}")
    
    def predict(*args, **kwargs):
        return "Prediction unavailable", []

# Import Celery tasks 
try:
    from .celery import fetch_contextual_information, perform_prediction, celery_app, analyze_incident_zone
except ImportError as e:
    logger.warning(f"Failed to import Celery services: {e}")
    
    # Create dummy objects
    celery_app = None
    
    def perform_prediction(*args, **kwargs):
        return {"error": "Celery service unavailable"}, []
    
    def fetch_contextual_information(*args, **kwargs):
        return {"error": "Celery service unavailable"}, None
        
    def analyze_incident_zone(*args, **kwargs):
        return {"error": "Celery service unavailable"}

from .llm import chat_response, get_response
from .websockets import *
from .analysis.satellite_data import download_sentinel_data, preprocess_sentinel_data

