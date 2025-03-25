# import pytest
# from fastapi.testclient import TestClient
# from unittest.mock import patch, MagicMock
# from httpx import AsyncClient
# from fastapi import HTTPException
# from fastapi.websockets import WebSocketDisconnect
# from app.apis.main_router import router, construct_image_url, fetch_image, sanitize_error_message, BASE_URL
# from app.models import ImageModel
# from app.main import app  # Add this import at the top of the file
# import os
# # import requests  # Add this import


# client = TestClient(router)

# def test_index():
#     response = client.get("/")
#     assert response.status_code == 200
#     assert response.json() == {"message": "Map Action classification model"}

# def test_construct_image_url():
#     # Set up the BASE_URL environment variable
#     os.environ['SERVER_URL'] = 'http://example.com'
    
#     # Test with a mock image path
#     mock_image_path = "mock/path/to/image.jpg"
#     expected_url = f"{BASE_URL}/image.jpg"
#     assert construct_image_url(mock_image_path) == expected_url

#     # Test with another mock image path to ensure consistency
#     another_mock_path = "another/mock/path/image.png"
#     expected_url_2 = f"{BASE_URL}/image.png"
#     assert construct_image_url(another_mock_path) == expected_url_2

# # @patch('app.apis.main_router.requests.get')
# # def test_fetch_image_success(mock_get):
# #     mock_response = MagicMock()
# #     mock_response.content = b"image_content"
# #     mock_get.return_value = mock_response

# #     result = fetch_image("http://example.com/image.jpg")
# #     assert result == b"image_content"

# # @patch('app.apis.main_router.requests.get')
# # def test_fetch_image_failure(mock_get):
# #     mock_get.side_effect = Exception("Network error")

# #     with pytest.raises(HTTPException) as exc_info:
# #         fetch_image("http://example.com/image.jpg")
# #     assert exc_info.value.status_code == 500
# #     assert "Failed to fetch image" in str(exc_info.value.detail)

# def test_sanitize_error_message():
#     message = "Error: Invalid API key 'abc123' in request"
#     sensitive_structures = ['abc123']
#     sanitized = sanitize_error_message(message, sensitive_structures)
#     assert sanitized == "Error: Invalid API key '***' in request"

# # @patch('app.apis.main_router.perform_prediction')
# # @patch('app.apis.main_router.fetch_contextual_information')
# # @patch('app.apis.main_router.analyze_incident_zone')
# # @patch('app.apis.main_router.upload_file_to_blob')
# # @patch('app.apis.main_router.database.execute')
# # @patch('app.apis.main_router.fetch_image')
# # def test_predict_incident_type(mock_fetch_image, mock_db_execute, mock_upload_blob, 
# #                                mock_analyze_zone, mock_fetch_context, mock_perform_prediction):
# #     # Mock the responses
# #     mock_fetch_image.return_value = b"image_content"
# #     mock_perform_prediction.return_value.get.return_value = (["Flood"], [0.9])
# #     mock_fetch_context.return_value.get.return_value = ("Analysis", "Solution")
# #     mock_analyze_zone.return_value.get.return_value = {
# #         'textual_analysis': 'Satellite analysis',
# #         'ndvi_ndwi_plot': 'plot1.png',
# #         'ndvi_heatmap': 'plot2.png',
# #         'landcover_plot': 'plot3.png'
# #     }
# #     mock_upload_blob.side_effect = ['url1', 'url2', 'url3']

# #     # Test data
# #     test_data = ImageModel(
# #         image_name="test.jpg",
# #         sensitive_structures=["structure1"],
# #         zone="Zone A",
# #         incident_id="123",
# #         latitude=0,
# #         longitude=0
# #     )

# #     response = client.post("/image/predict", json=test_data.dict())
    
# #     assert response.status_code == 200
# #     response_data = response.json()
# #     assert response_data["prediction"] == ["Flood"]
# #     assert response_data["probabilities"] == [0.9]
# #     assert "Analysis" in response_data["analysis"]
# #     assert "Satellite analysis" in response_data["analysis"]
# #     assert response_data["piste_solution"] == "Solution"
# #     assert all(key in response_data for key in ['ndvi_ndwi_plot', 'ndvi_heatmap', 'landcover_plot'])

# # @pytest.mark.asyncio
# # async def test_chat_endpoint():
# #     async with AsyncClient(app=app, base_url="http://test") as client:
# #         with pytest.raises(WebSocketDisconnect):
# #             async with client.websocket_connect("/ws/chat") as websocket:
# #                 # Test connection
# #                 assert websocket.client.host == "testclient"
                
# #                 # Test sending a message
# #                 await websocket.send_json({"message": "Hello", "session_id": "test_session"})
                
# #                 # Test receiving a response
# #                 response = await websocket.receive_json()
# #                 assert "message" in response
# #                 assert isinstance(response["message"], str)
                
# #                 # Test chat history
# #                 await websocket.send_json({"action": "get_history", "session_id": "test_session"})
# #                 history = await websocket.receive_json()
# #                 assert isinstance(history, list)
# #                 assert len(history) > 0
                
# #                 # Test deleting chat history
# #                 await websocket.send_json({"action": "delete_history", "session_id": "test_session"})
# #                 delete_response = await websocket.receive_json()
# #                 assert delete_response["status"] == "success"
                
# #                 # Verify history is deleted
# #                 await websocket.send_json({"action": "get_history", "session_id": "test_session"})
# #                 empty_history = await websocket.receive_json()
# #                 assert len(empty_history) == 0
                
# #                 # Test invalid action
# #                 await websocket.send_json({"action": "invalid_action"})
# #                 error_response = await websocket.receive_json()
# #                 assert "error" in error_response

# @pytest.mark.asyncio
# @patch('app.apis.main_router.database.execute')
# async def test_save_chat_history(mock_db_execute):
#     from app.apis.main_router import save_chat_history
    
#     await save_chat_history("test_key", "test question", "test answer")
    
#     mock_db_execute.assert_called_once()
#     call_args = mock_db_execute.call_args[1]
#     assert "test_key" in call_args['values'].values()
#     assert "test question" in call_args['values'].values()
#     assert "test answer" in call_args['values'].values()

# @pytest.mark.asyncio
# @patch('app.apis.main_router.database.fetch_all')
# async def test_get_chat_history(mock_db_fetch_all):
#     from app.apis.main_router import get_chat_history
    
#     mock_db_fetch_all.return_value = [
#         {"question": "Q1", "answer": "A1"},
#         {"question": "Q2", "answer": "A2"}
#     ]

#     result = await get_chat_history("test_key")
    
#     assert len(result) == 4  # 2 questions + 2 answers
#     assert result[0] == {"role": "user", "content": "Q1"}
#     assert result[1] == {"role": "assistant", "content": "A1"}
#     assert result[2] == {"role": "user", "content": "Q2"}
#     assert result[3] == {"role": "assistant", "content": "A2"}

# # @pytest.mark.asyncio
# # async def test_fetch_image_success():
# #     mock_response = MagicMock()
# #     mock_response.content = b"mock image content"
# #     mock_response.raise_for_status.return_value = None

# #     with patch('app.apis.main_router.requests.get', return_value=mock_response):
# #         image_content = await fetch_image("http://example.com/image.jpg")
# #         assert image_content == b"mock image content"

# # @pytest.mark.asyncio
# # async def test_fetch_image_failure():
# #     with patch('app.apis.main_router.requests.get') as mock_get:
# #         mock_get.side_effect = requests.RequestException("Network error")
        
# #         with pytest.raises(HTTPException) as exc_info:
# #             await fetch_image("http://example.com/image.jpg")
        
# #         assert exc_info.value.status_code == 500
# #         assert "Failed to fetch image" in str(exc_info.value.detail)

# __all__ = ['router', 'construct_image_url', 'BASE_URL']
