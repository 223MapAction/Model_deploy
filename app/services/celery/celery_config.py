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

# For test compatibility - add back the original function
def make_celery():
    """
    Create and configure a Celery application instance with Redis as the message broker and backend.
    
    This function sets up Celery with Redis, specifying the same URI for both the backend and broker. 
    This configuration is necessary for task queueing and result storage for distributed task processing.

    Returns:
        Celery: A Celery application instance configured to use Redis for queuing tasks and storing results.
    """
    # Try to import Celery if not already imported
    try:
        from celery import Celery
    except ImportError:
        logger.warning("Celery not installed, returning dummy Celery instance")
        return DummyCelery('map_action_api')
        
    # Retrieve Redis connection details from environment variables 
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    celery = Celery(
        'worker',  # Name of the worker
        backend=redis_url,  # Use Redis URL from environment 
        broker=redis_url    # Use Redis URL from environment
    )
    
    # Configure serialization (previous version used json)
    celery.conf.task_serializer = 'json'
    celery.conf.result_serializer = 'json'
    celery.conf.accept_content = ['json']
    
    return celery

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
