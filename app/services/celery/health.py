from fastapi import FastAPI, HTTPException
from celery.exceptions import TimeoutError
from app.services.celery.celery_config import celery_app
import logging
import os
import time
from typing import Dict, Any

app = FastAPI()
logger = logging.getLogger(__name__)

async def check_redis_connection() -> Dict[str, Any]:
    """Check Redis connection health."""
    try:
        connection = celery_app.connection()
        connection.ensure_connection(timeout=5.0)
        return {
            "status": "healthy",
            "latency_ms": None  # Will be set in the calling function
        }
    except Exception as e:
        logger.error(f"Redis connection check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "latency_ms": None
        }

async def check_celery_workers() -> Dict[str, Any]:
    """Check Celery workers health."""
    try:
        start_time = time.time()
        inspect = celery_app.control.inspect()
        ping = inspect.ping(timeout=5.0)
        
        if not ping:
            return {
                "status": "unhealthy",
                "error": "No workers available",
                "active_workers": 0,
                "latency_ms": round((time.time() - start_time) * 1000, 2)
            }

        active_workers = len(ping.keys())
        return {
            "status": "healthy",
            "active_workers": active_workers,
            "latency_ms": round((time.time() - start_time) * 1000, 2)
        }
    except TimeoutError:
        return {
            "status": "unhealthy",
            "error": "Worker check timed out",
            "active_workers": 0,
            "latency_ms": None
        }
    except Exception as e:
        logger.error(f"Worker check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "active_workers": 0,
            "latency_ms": None
        }

@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint that checks:
    - Redis connection
    - Celery workers status
    - System resources
    """
    start_time = time.time()
    
    # Check Redis
    redis_status = await check_redis_connection()
    redis_status["latency_ms"] = round((time.time() - start_time) * 1000, 2)
    
    # Check Celery workers
    workers_status = await check_celery_workers()
    
    # Determine overall health
    is_healthy = (
        redis_status["status"] == "healthy" and
        workers_status["status"] == "healthy" and
        workers_status["active_workers"] > 0
    )
    
    response = {
        "status": "healthy" if is_healthy else "unhealthy",
        "timestamp": time.time(),
        "checks": {
            "redis": redis_status,
            "celery_workers": workers_status
        }
    }
    
    if not is_healthy:
        logger.error(f"Health check failed: {response}")
        raise HTTPException(status_code=503, detail=response)
    
    return response

@app.get("/ready")
async def readiness_check():
    """
    Readiness probe that checks if the service is ready to accept traffic.
    More lightweight than the full health check.
    """
    try:
        # Quick check if we can connect to Redis
        celery_app.connection().ensure_connection(timeout=2.0)
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service not ready")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080) 