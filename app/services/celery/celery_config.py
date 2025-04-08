import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define a dummy Celery class as fallback
class DummyCelery:
    def __init__(self, *args, **kwargs):
        logger.warning("Using dummy Celery implementation")
        
    def task(self, *args, **kwargs):
        # Return a function that returns the function it decorates
        def decorator(func):
            return func
        return decorator

# Try to import the real Celery
try:
    from celery import Celery
    
    # Create Celery instance
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    celery_app = Celery('map_action_api', broker=redis_url, backend=redis_url)
    
    # Configure Celery
    celery_app.conf.task_serializer = 'pickle'
    celery_app.conf.result_serializer = 'pickle'
    celery_app.conf.accept_content = ['pickle', 'json']
    
    logger.info(f"Celery initialized with Redis URL: {redis_url}")
    
except ImportError:
    logger.warning("Celery module not found. Using dummy implementation.")
    Celery = DummyCelery
    celery_app = DummyCelery('map_action_api')
