from celery import Celery
import os

def make_celery():
    """
    Create and configure a Celery application instance with Redis as the message broker and backend.
    
    This function sets up Celery with Redis, specifying the same URI for both the backend and broker. 
    This configuration is necessary for task queueing and result storage for distributed task processing.

    Returns:
        Celery: A Celery application instance configured to use Redis for queuing tasks and storing results.
    """
    # Retrieve Redis connection details from environment variables
    redis_host = os.getenv('REDIS_HOST', 'redis')
    redis_port = os.getenv('REDIS_PORT', 6379)
    redis_username = os.getenv('REDIS_USERNAME', '')
    redis_password = os.getenv('REDIS_PASSWORD', '')

    redis_url = os.getenv('REDIS_URL')  # Fetch the Redis URL from the environment variable

    celery = Celery(
        'worker',  # Name of the worker
        backend=redis_url,  # Use Redis URL from environment
        broker=redis_url    # Use Redis URL from environment
    )
    return celery

celery_app = make_celery()
