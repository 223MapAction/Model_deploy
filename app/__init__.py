# from .apis import prediction_endpoint
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import services with error handling
try:
    from .services import predict, perform_prediction, fetch_contextual_information, celery_app, analyze_incident_zone
    logger.info("Successfully imported services")
except ImportError as e:
    logger.warning(f"Failed to import some services: {e}. Some functionality may be limited.")
    
    # Set up dummy objects if imports failed
    predict = lambda *args, **kwargs: ("Prediction unavailable", [])
    perform_prediction = lambda *args, **kwargs: ({"error": "Service unavailable"}, [])
    fetch_contextual_information = lambda *args, **kwargs: ({"error": "Service unavailable"}, None)
    celery_app = None
    analyze_incident_zone = lambda *args, **kwargs: {"error": "Service unavailable"}

from .models import ImageModel
