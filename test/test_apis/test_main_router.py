from httpx import AsyncClient
import pytest
from fastapi import FastAPI
from app.apis.main_router import router  # Adjust this import based on your project structure

# Setup FastAPI app for testing
app = FastAPI()
app.include_router(router)

@pytest.mark.asyncio
async def test_index():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {'message': 'Map Action classification model'}
