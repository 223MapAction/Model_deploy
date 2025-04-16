import logging
import os
from urllib.parse import quote_plus
import re

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
    redis_url = os.getenv('REDIS_URL')
    
    if not redis_url:
        # Construct Redis URL from individual components if REDIS_URL is not provided
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = os.getenv('REDIS_PORT', '6379')
        redis_password = os.getenv('REDIS_PASSWORD')

        if redis_password:
            # Password exists, quote it and build URL
            quoted_password = quote_plus(redis_password)
            redis_url = f'redis://:{quoted_password}@{redis_host}:{redis_port}/0'
            # Log with masking using the original password
            logger.info(f"Configuring Celery with Redis URL: {redis_url.replace(redis_password, '***')}")
        else:
            # No password, build simple URL
            redis_url = f'redis://{redis_host}:{redis_port}/0'
            # Log without masking
            logger.info(f"Configuring Celery with Redis URL: {redis_url}")
    else:
        # REDIS_URL was provided, try to mask if password pattern is detected
        # Basic pattern matching for password in URL (adjust if needed)
        match = re.match(r"redis://:(?P<password>[^@]+)@", redis_url)
        if match:
            password_to_mask = match.group("password")
            masked_url = redis_url.replace(password_to_mask, "***")
            logger.info(f"Configuring Celery with Redis URL: {masked_url}")
        else:
            # Assume no password or couldn't detect it, log as is
            logger.info(f"Configuring Celery with Redis URL: {redis_url}")

    celery = Celery(
        'worker',
        backend=redis_url,
        broker=redis_url
    )
    
    # Configure Celery
    celery.conf.update(
        task_serializer='json',
        result_serializer='json',
        accept_content=['json'],
        broker_connection_retry=True,
        broker_connection_max_retries=10,
        broker_connection_retry_on_startup=True,
        broker_transport_options={
            'visibility_timeout': 3600,  # 1 hour
            'socket_timeout': 30,        # 30 seconds
            'socket_connect_timeout': 30,
        },
        result_backend_transport_options={
            'socket_timeout': 30,
            'socket_connect_timeout': 30,
        }
    )
    
    return celery

# Try to import the real Celery
try:
    from celery import Celery
    celery_app = make_celery()
    logger.info("Celery initialized successfully")
except ImportError:
    logger.warning("Celery module not found. Using dummy implementation.")
    Celery = DummyCelery
    celery_app = DummyCelery('map_action_api')
