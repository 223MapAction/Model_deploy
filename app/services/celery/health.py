from fastapi import FastAPI, HTTPException
import logging
import time

app = FastAPI()
logger = logging.getLogger(__name__)

# Keep commented out or remove if not needed for this test
# from celery.exceptions import TimeoutError
# from app.services.celery.celery_config import celery_app
# from typing import Dict, Any

@app.get("/health")
async def health_check():
    """Minimal health check endpoint for testing Uvicorn startup."""
    logger.info("Minimal /health endpoint hit")
    return {"status": "ok"}

# Keep commented out or remove if not needed for this test
# @app.get("/ready")
# async def readiness_check():
#     """Minimal readiness check."""
#     logger.info("Minimal /ready endpoint hit")
#     return {"status": "ready"}

if __name__ == "__main__":
    # Keep the main block for potential local testing if needed
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080) 