# health_check_minimal.py
from fastapi import FastAPI
import logging

app = FastAPI()
logger = logging.getLogger(__name__)

@app.get("/health")
async def health_check():
    # This should only log if Uvicorn actually starts successfully
    logger.info("Minimal health check endpoint hit (isolated)")
    return {"status": "ok"}

# No __main__ block needed as Uvicorn imports the 'app' object 