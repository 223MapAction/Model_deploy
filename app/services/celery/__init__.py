import logging

# Set up fallback objects in case imports fail
celery_app = None
perform_prediction = None
fetch_contextual_information = None
analyze_incident_zone = None

try:
    from .celery_task import perform_prediction, fetch_contextual_information, analyze_incident_zone
    from .celery_config import celery_app
except ImportError as e:
    logging.warning(f"Failed to import Celery modules: {e}. Celery functionality will be disabled.")
    
    # Create dummy functions as fallbacks
    def perform_prediction(*args, **kwargs):
        return {"error": "Celery not available"}, []
        
    def fetch_contextual_information(*args, **kwargs):
        return {"error": "Celery not available"}, None
        
    def analyze_incident_zone(*args, **kwargs):
        return {"error": "Celery not available"}