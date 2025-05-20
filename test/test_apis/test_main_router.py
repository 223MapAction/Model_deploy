import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.websockets import WebSocketDisconnect
import os
import json

# Import only what is used in the tests we're running
from app.apis.main_router import router, construct_image_url, sanitize_error_message, BASE_URL

# Create test client
client = TestClient(router)

def test_index():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Map Action classification model"}

def test_construct_image_url():
    # Set up the BASE_URL environment variable
    os.environ['SERVER_URL'] = 'http://example.com'
    
    # Test with a mock image path
    mock_image_path = "mock/path/to/image.jpg"
    expected_url = f"{BASE_URL}/image.jpg"
    assert construct_image_url(mock_image_path) == expected_url

    # Test with another mock image path to ensure consistency
    another_mock_path = "another/mock/path/image.png"
    expected_url_2 = f"{BASE_URL}/image.png"
    assert construct_image_url(another_mock_path) == expected_url_2

@pytest.mark.asyncio
@patch('app.apis.main_router.requests.get')
async def test_fetch_image_success(mock_get):
    # Import the function here to avoid circular imports
    from app.apis.main_router import fetch_image
    
    mock_response = MagicMock()
    mock_response.content = b"image_content"
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = await fetch_image("http://example.com/image.jpg")
    assert result == b"image_content"
    mock_get.assert_called_once_with("http://example.com/image.jpg")

@pytest.mark.asyncio
@patch('app.apis.main_router.requests.get')
@patch('app.apis.main_router.logger')
async def test_fetch_image_failure(mock_logger, mock_get):
    # Import the function here to avoid circular imports
    from app.apis.main_router import fetch_image
    import requests
    
    mock_get.side_effect = requests.RequestException("Network error")

    with pytest.raises(HTTPException) as exc_info:
        await fetch_image("http://example.com/image.jpg")
    assert exc_info.value.status_code == 500
    assert "Failed to fetch image" in str(exc_info.value.detail)
    mock_logger.error.assert_called_once()

def test_sanitize_error_message():
    message = "Error: Invalid API key 'abc123' in request"
    sensitive_structures = ['abc123']
    sanitized = sanitize_error_message(message, sensitive_structures)
    assert sanitized == "Error: Invalid API key '[REDACTED]' in request"

# @pytest.mark.asyncio
# @patch('app.apis.main_router.perform_prediction')
# @patch('app.apis.main_router.fetch_contextual_information')
# @patch('app.apis.main_router.analyze_incident_zone')
# @patch('app.apis.main_router.upload_file_to_s3')  # Changed to AWS S3
# @patch('app.apis.main_router.database.execute')
# @patch('app.apis.main_router.fetch_image')
# @patch('app.apis.main_router.logger')
# async def test_predict_incident_type(mock_logger, mock_fetch_image, mock_db_execute, mock_upload_s3, 
#                               mock_analyze_zone, mock_fetch_context, mock_perform_prediction):
#     # Import the prediction endpoint function to test
#     from app.apis.main_router import predict_incident_type
#     from app.models.image_model import ImageModel
#     from fastapi.responses import JSONResponse
#     import numpy as np
    
#     # Setup proper mocking for predict_incident_type
#     # First, we need to make fetch_image a coroutine that returns image content
#     mock_fetch_image.return_value = b"image_content"
    
#     # Create properly mocked task results
#     prediction_task = MagicMock()
#     prediction_task.get.return_value = ("Déchets", [0.0, 0.9, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
#     mock_perform_prediction.delay.return_value = prediction_task
    
#     context_task = MagicMock()
#     context_task.get.return_value = ("Analysis", "Solution")
#     mock_fetch_context.delay.return_value = context_task
    
#     satellite_task = MagicMock()
#     satellite_task.get.return_value = {
#         'textual_analysis': 'Satellite analysis',
#         'ndvi_ndwi_plot': 'plot1.png',
#         'ndvi_heatmap': 'plot2.png',
#         'landcover_plot': 'plot3.png'
#     }
#     mock_analyze_zone.delay.return_value = satellite_task
    
#     # Mock S3 upload
#     mock_upload_s3.side_effect = ['url1', 'url2', 'url3']
    
#     # Set environment variables
#     os.environ['S3_BUCKET_NAME'] = 'test-bucket'
#     os.environ['AWS_REGION'] = 'us-west-2'

#     # Test data
#     test_data = ImageModel(
#         image_name="test.jpg",
#         sensitive_structures=["structure1"],
#         zone="Zone A",
#         incident_id="123",
#         latitude=0,
#         longitude=0
#     )

#     # Call the endpoint directly
#     response = await predict_incident_type(test_data)
    
#     # Assert the response
#     assert isinstance(response, JSONResponse)
#     response_data = json.loads(response.body)
#     assert response_data["prediction"] == "Déchets"
#     assert response_data["probabilities"] == [0.0, 0.9, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
#     assert "Analysis" in response_data["analysis"]
#     assert "Satellite analysis" in response_data["analysis"]
#     assert response_data["piste_solution"] == "Solution"
#     assert all(key in response_data for key in ['ndvi_ndwi_plot', 'ndvi_heatmap', 'landcover_plot'])
    
#     # Test the calls to the mocked functions
#     mock_fetch_image.assert_called_once()
#     mock_perform_prediction.assert_called_once()
#     mock_fetch_context.assert_called_once()
#     mock_analyze_zone.assert_called_once()
#     assert mock_upload_s3.call_count == 3  # One call for each plot
    
@pytest.mark.asyncio
@patch('app.apis.main_router.perform_prediction')
@patch('app.apis.main_router.fetch_image')
@patch('app.apis.main_router.logger')
async def test_predict_incident_type_prediction_error(mock_logger, mock_fetch_image, mock_perform_prediction):
    # Import the prediction endpoint function to test
    from app.apis.main_router import predict_incident_type
    from app.models.image_model import ImageModel
    
    # Setup the prediction task to fail properly
    failing_task = MagicMock()
    failing_task.get.side_effect = Exception("Prediction failed")
    mock_perform_prediction.delay.return_value = failing_task
    
    # Need to mock fetch_image to work correctly
    mock_fetch_image.return_value = b"image_content"
    
    # Test data
    test_data = ImageModel(
        image_name="test.jpg",
        sensitive_structures=["structure1"],
        zone="Zone A",
        incident_id="123",
        latitude=0,
        longitude=0
    )
    
    # Test the error handling
    with pytest.raises(HTTPException) as exc_info:
        await predict_incident_type(test_data)
    
    assert exc_info.value.status_code == 500
    assert "Error during prediction" in str(exc_info.value.detail)
    mock_logger.error.assert_called_once_with("Error during prediction task: Prediction failed")

# @pytest.mark.asyncio
# async def test_chat_endpoint():
#     # Import necessary components
#     from app.apis.main_router import chat_endpoint
#     from fastapi import WebSocket, WebSocketDisconnect
#     from unittest.mock import AsyncMock
#     import json
    
#     # Create a mock WebSocket
#     mock_websocket = AsyncMock(spec=WebSocket)
#     # Add client attribute with host
#     mock_websocket.client = MagicMock()
#     mock_websocket.client.host = "127.0.0.1"
    
#     # Mock the headers attribute with a valid origin
#     mock_websocket.headers = MagicMock()
#     mock_websocket.headers.get.return_value = "http://localhost:3000"    # This is one of the allowed origins
    
#     # Mock the receive_json and send_json methods to match the expected format in the implementation
#     mock_websocket.receive_json.side_effect = [
#         {"action": "message", "incident_id": "test123", "session_id": "session456", "question": "Test question"},
#         WebSocketDisconnect() # Force exit after one message
#     ]
    
#     # Mock the database and other dependencies
#     with patch('app.apis.main_router.database') as mock_db, \
#          patch('app.apis.main_router.chat_response') as mock_chat, \
#          patch('app.apis.main_router.manager') as mock_manager, \
#          patch('app.apis.main_router.impact_area_storage') as mock_impact_storage:
        
#         # Set up async methods for manager since they will be awaited
#         mock_manager.connect = AsyncMock()
        
#         # Set up async database methods since they will be awaited
#         mock_db.fetch_one = AsyncMock()
#         mock_db.fetch_one.return_value = {
#             "incident_type": "test_type", 
#             "analysis": "test_analysis", 
#             "piste_solution": "test_solution"
#         }
#         mock_db.fetch_all = AsyncMock()
#         mock_db.fetch_all.return_value = []
#         mock_db.execute = AsyncMock()
        
#         # Set up mock response
#         mock_chat.return_value = "This is a test response"
#         mock_impact_storage.get.return_value = "test_impact_area"
        
#         # Run the chat endpoint directly
#         try:
#             await chat_endpoint(mock_websocket)
#         except WebSocketDisconnect:
#             pass
        
#         # Verify the mocks were called with the right parameters
#         mock_manager.connect.assert_called_once_with(mock_websocket)
        
#         # Verify chat_response was called with appropriate parameters including our context
#         # The chat_response function should be called with: question, context (JSON string), history, impact_area
#         assert mock_chat.called
#         call_args = mock_chat.call_args[0]
#         assert call_args[0] == "Test question"  # First arg should be the question
#         # Verify send_json was called with the expected response
#         mock_websocket.send_json.assert_called_once()
        
#         # Test history retrieval
#         with patch('app.apis.main_router.get_chat_history') as mock_get_history, patch('app.apis.main_router.manager') as mock_manager:
#             mock_get_history.return_value = [
#                 {"role": "user", "content": "Hello"},
#                 {"role": "assistant", "content": "This is a test response"}
#             ]
            
#             mock_websocket.receive_json.side_effect = [
#                 {"action": "get_history", "incident_id": "test123", "session_id": "test_session"}
#             ]
#             await chat_endpoint(mock_websocket)
#             history = mock_websocket.send_json.call_args[0][0]
            
#             assert len(history) == 2
#             assert history[0]["role"] == "user"
#             assert history[1]["role"] == "assistant"
            
#         # Test history deletion
#         with patch('app.apis.main_router.database.execute') as mock_execute, patch('app.apis.main_router.manager') as mock_manager:
#             mock_websocket.receive_json.side_effect = [
#                 {"action": "delete_chat", "incident_id": "test123", "session_id": "test_session"}
#             ]
#             await chat_endpoint(mock_websocket)
#             delete_response = mock_websocket.send_json.call_args[0][0]
#             assert delete_response["status"] == "success"
#             mock_execute.assert_called_once()

# @pytest.mark.asyncio
# async def test_chat_endpoint_invalid_action():
#     # Import necessary components
#     from app.apis.main_router import chat_endpoint
#     from fastapi import WebSocket, WebSocketDisconnect
#     from unittest.mock import AsyncMock
    
#     # Create a mock WebSocket
#     mock_websocket = AsyncMock(spec=WebSocket)
#     # Add client attribute with host
#     mock_websocket.client = MagicMock()
#     mock_websocket.client.host = "127.0.0.1"
    
#     # Mock the headers attribute with a valid origin
#     mock_websocket.headers = MagicMock()
#     mock_websocket.headers.get.return_value = "http://localhost:3000"    # This is one of the allowed origins
    
#     # Mock the receive_json method to return invalid action with required fields
#     # Make sure to include a question field as the implementation expects it
#     mock_websocket.receive_json.return_value = {"action": "invalid_action", "incident_id": "test123", "session_id": "session456", "question": "test question"}
    
#     # Also mock the database to avoid actual DB calls
#     with patch('app.apis.main_router.database') as mock_db, patch('app.apis.main_router.manager') as mock_manager, patch('app.apis.main_router.chat_response') as mock_chat_response, patch('app.apis.main_router.impact_area_storage') as mock_impact_storage:
#         # Set up async methods for manager since they will be awaited
#         mock_manager.connect = AsyncMock()
        
#         # Set up mock returns for database queries
#         mock_db.fetch_one.return_value = {
#             "incident_type": "test_type", 
#             "analysis": "test_analysis", 
#             "piste_solution": "test_solution"
#         }
#         mock_db.fetch_all.return_value = []
#         mock_chat_response.return_value = "Test chat response"
#         mock_impact_storage.get.return_value = "test_impact_area"

#         # Run the chat endpoint and verify it handles the message
#         try:
#             await chat_endpoint(mock_websocket)
#         except WebSocketDisconnect:
#             pass
#         except Exception as e:
#             print(f"Test caught exception: {e}")
        
#         # Verify the manager's connect method was called with the websocket
#         mock_manager.connect.assert_called_once_with(mock_websocket)
        
#         # The implementation should process this as a regular chat message
#         # and send back a response
#         assert mock_websocket.send_json.called

@pytest.mark.asyncio
@patch('app.apis.main_router.database.execute')
async def test_save_chat_history(mock_db_execute):
    from app.apis.main_router import save_chat_history
    
    await save_chat_history("test_key", "test question", "test answer")
    
    mock_db_execute.assert_called_once()
    call_args = mock_db_execute.call_args[1]
    assert "test_key" in call_args['values'].values()
    assert "test question" in call_args['values'].values()
    assert "test answer" in call_args['values'].values()

@pytest.mark.asyncio
@patch('app.apis.main_router.database.fetch_all')
async def test_get_chat_history(mock_db_fetch_all):
    from app.apis.main_router import get_chat_history
    
    mock_db_fetch_all.return_value = [
        {"question": "Q1", "answer": "A1"},
        {"question": "Q2", "answer": "A2"}
    ]

    result = await get_chat_history("test_key")
    
    assert len(result) == 4  # 2 questions + 2 answers
    assert result[0] == {"role": "user", "content": "Q1"}
    assert result[1] == {"role": "assistant", "content": "A1"}
    assert result[2] == {"role": "user", "content": "Q2"}
    assert result[3] == {"role": "assistant", "content": "A2"}

# Additional tests for expire_impact_area and other functionality
@pytest.mark.asyncio
@patch('app.apis.main_router.impact_area_storage')
@patch('asyncio.sleep')
async def test_expire_impact_area(mock_sleep, mock_storage):
    # Import the function
    from app.apis.main_router import expire_impact_area
    
    # Setup mock
    mock_storage.get.return_value = {"key": "value"}
    
    # Call the function
    await expire_impact_area("incident123", 1)
    
    # Assert behavior
    mock_sleep.assert_called_once_with(1)
    assert "incident123" not in mock_storage

@pytest.mark.asyncio
@patch('app.apis.main_router.impact_area_storage')
@patch('asyncio.sleep')
async def test_expire_impact_area_not_found(mock_sleep, mock_storage):
    # Import the function
    from app.apis.main_router import expire_impact_area
    
    # Setup mock - incident not in storage
    mock_storage.get.return_value = None
    
    # Call the function - should not error even if incident not found
    await expire_impact_area("nonexistent", 1)
    
    # Assert behavior
    mock_sleep.assert_called_once_with(1)

# Test API root endpoint
def test_api_root():
    from app.apis.main_router import index
    
    response = index()
    assert response == {"message": "Map Action classification model"}

# Ensure the imports at the top include what we need for testing
from app.apis.main_router import router, construct_image_url, BASE_URL, sanitize_error_message

__all__ = ['router', 'construct_image_url', 'BASE_URL', 'sanitize_error_message']
