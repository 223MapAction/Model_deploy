import pytest
from unittest.mock import patch, MagicMock
import json
import base64
import os
from app.services.cnn.openai_vision import predict, predict_structured, encode_image_to_base64, ENVIRONMENTAL_TAGS

@pytest.fixture
def mock_image_bytes():
    return b"fake_image_data"

@pytest.fixture
def mock_openai_client():
    with patch.dict(os.environ, {"OPENAI_API_KEY": "fake-api-key"}):
        with patch('app.services.cnn.openai_vision.openai.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            yield mock_client

@pytest.fixture
def mock_openai_response():
    mock_response = MagicMock()
    
    # Create the nested structure matching the actual API response
    mock_output_message = MagicMock()
    mock_content = MagicMock()
    mock_content.text = '''```json
{
    "identified_issues": [
        {"tag": "Plastiques épars", "probability": 0.9}
    ],
    "all_probabilities": [0.1] * {len(ENVIRONMENTAL_TAGS)}
}
```'''
    mock_output_message.content = [mock_content]
    mock_response.output = [mock_output_message]
    
    return mock_response

def test_encode_image_to_base64(mock_image_bytes):
    result = encode_image_to_base64(mock_image_bytes)
    assert isinstance(result, str)
    # Try to decode it back to verify it's valid base64
    decoded = base64.b64decode(result)
    assert decoded == mock_image_bytes

def test_predict_with_successful_response(mock_openai_client, mock_image_bytes, mock_openai_response):
    # Set up the mock client
    mock_openai_client.responses.create.return_value = mock_openai_response
    
    # Call the function
    result, probabilities = predict(mock_image_bytes)
    
    # Assert the results
    assert result == [("Plastiques épars", 0.9)]
    assert len(probabilities) == len(ENVIRONMENTAL_TAGS)
    # Example check - adjust if needed based on the mock response
    assert probabilities[6] == 0.9 # Assuming Plastiques épars is at index 6
    
    # Verify the API was called correctly
    mock_openai_client.responses.create.assert_called_once()
    call_args = mock_openai_client.responses.create.call_args[1]
    
    # Check model and main parameters
    assert call_args['model'] == "gpt-4o-mini"
    assert call_args['temperature'] == 1
    assert call_args['max_output_tokens'] == 2048
    assert call_args['top_p'] == 1
    assert call_args['store'] is True
    
    # Check input structure
    assert len(call_args['input']) == 1
    input_msg = call_args['input'][0]
    assert input_msg['role'] == "user"
    assert len(input_msg['content']) == 2
    
    # Check image input
    assert input_msg['content'][0]['type'] == "input_image"
    assert "data:image/jpeg;base64," in input_msg['content'][0]['image_url']
    
    # Check text input
    assert input_msg['content'][1]['type'] == "input_text"
    assert isinstance(input_msg['content'][1]['text'], str)
    
    # Check format settings
    assert call_args['text'] == {"format": {"type": "text"}}
    assert call_args['reasoning'] == {}

def test_predict_with_no_issues(mock_openai_client, mock_image_bytes):
    # Set up the mock client with a response that has no identified issues
    mock_response = MagicMock()
    mock_output_message = MagicMock()
    mock_content = MagicMock()
    mock_content.text = '''```json
{
    "identified_issues": [],
    "all_probabilities": [0.1] * {len(ENVIRONMENTAL_TAGS)}
}
```'''
    mock_output_message.content = [mock_content]
    mock_response.output = [mock_output_message]
    
    mock_openai_client.responses.create.return_value = mock_response
    
    # Call the function
    result, probabilities = predict(mock_image_bytes)
    
    # Assert the results - should return "Aucun problème environnemental" with probability 1.0
    assert result == [("Aucun problème environnemental", 1.0)]
    assert probabilities == [0.0] * len(ENVIRONMENTAL_TAGS)

def test_predict_with_api_error(mock_openai_client, mock_image_bytes):
    # Set up the mock client to raise an exception
    mock_openai_client.responses.create.side_effect = Exception("API Error")
    
    # Call the function
    result, probabilities = predict(mock_image_bytes)
    
    # Assert we get an error response
    assert result == [("Error in prediction", 0.0)]
    assert probabilities == [0.0] * len(ENVIRONMENTAL_TAGS)

@patch('app.services.cnn.openai_vision.predict')
def test_predict_structured(mock_predict, mock_image_bytes):
    # Set up the mock
    mock_predict.return_value = (
        [("Plastiques épars", 0.9)], 
        ([0.0] * 6) + [0.9] + ([0.0] * (len(ENVIRONMENTAL_TAGS) - 7))
    )
    
    # Call the function
    result = predict_structured(mock_image_bytes)
    
    # Assert the result is a PredictionResult
    from app.services.cnn.models import PredictionResult
    assert isinstance(result, PredictionResult)
    
    # Check the values
    assert len(result.top_predictions) == 1
    assert result.top_predictions[0].tag == "Plastiques épars"
    assert result.top_predictions[0].probability == 0.9
    assert len(result.all_probabilities) == len(ENVIRONMENTAL_TAGS)
    assert result.all_probabilities[6] == 0.9 # Check specific index