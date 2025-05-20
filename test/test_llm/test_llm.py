import pytest
from unittest.mock import patch, MagicMock
import json
import pandas as pd
from app.services.llm.llm import display_chat_history, get_assistant_response, get_response, chat_response, generate_satellite_analysis

@pytest.fixture(autouse=True)
def mock_openai_client():
    # Use autouse=True to ensure this mock is applied to all tests
    with patch('app.services.llm.llm.client', autospec=True) as mock_client:
        # Set up the responses attribute
        mock_client.responses = MagicMock()
        yield mock_client

@pytest.fixture
def mock_responses_output():
    # Create a structure that matches the OpenAI Responses API output
    mock_content = MagicMock()
    mock_content.text = "Mock response"
    
    mock_output_item = MagicMock()
    mock_output_item.content = [mock_content]
    
    mock_response = MagicMock()
    mock_response.output = [mock_output_item]
    
    return mock_response

class TestLLM:
    def test_display_chat_history(self, capsys):
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        display_chat_history(messages)
        captured = capsys.readouterr()
        assert "User: Hello" in captured.out
        assert "Assistant: Hi there!" in captured.out

    def test_get_assistant_response_success(self, mock_openai_client, mock_responses_output):
        # Set up the mock for the responses API
        mock_openai_client.responses.create.return_value = mock_responses_output
        messages = [{"role": "user", "content": "Test message"}]
        response = get_assistant_response(messages)
        assert response == "Mock response"
        # Verify the mock was called with expected parameters
        mock_openai_client.responses.create.assert_called_once()

    def test_get_assistant_response_error(self, mock_openai_client):
        # Set up the mock to raise an exception
        mock_openai_client.responses.create.side_effect = Exception("API Error")
        messages = [{"role": "user", "content": "Test message"}]
        response = get_assistant_response(messages)
        assert response == "Sorry, I can't process your request right now."
        # Verify the mock was called
        mock_openai_client.responses.create.assert_called_once()

    @patch('app.services.llm.llm.get_assistant_response')
    @patch('app.services.llm.llm.display_chat_history')
    def test_get_response(self, mock_display, mock_get_assistant):
        mock_get_assistant.return_value = "Assistant response"
        response = get_response("User prompt")
        assert response == "Assistant response"
        mock_display.assert_called_once()

    def test_chat_response(self, mock_openai_client, mock_responses_output):
        mock_openai_client.responses.create.return_value = mock_responses_output
        context = json.dumps({
            "type_incident": "Test Incident",
            "analysis": "Test Analysis",
            "piste_solution": "Test Solution"
        })
        response = chat_response("Test prompt", context)
        assert response == "Mock response"
        # Verify the mock was called
        mock_openai_client.responses.create.assert_called_once()

    def test_generate_satellite_analysis(self, mock_openai_client, mock_responses_output):
        mock_openai_client.responses.create.return_value = mock_responses_output
        ndvi_data = pd.DataFrame({'NDVI': [0.1, 0.2, 0.3]})
        ndwi_data = pd.DataFrame({'NDWI': [0.4, 0.5, 0.6]})
        landcover_data = {'Forest': 60, 'Urban': 40}
        incident_type = "Deforestation"
        
        analysis = generate_satellite_analysis(ndvi_data, ndwi_data, landcover_data, incident_type)
        assert analysis == "Mock response"
        # Verify the mock was called
        mock_openai_client.responses.create.assert_called_once()

    def test_chat_response_error(self, mock_openai_client):
        mock_openai_client.responses.create.side_effect = Exception("API Error")
        # Need to provide a valid context as JSON string
        context = json.dumps({
            "type_incident": "Test Incident",
            "analysis": "Test Analysis",
            "piste_solution": "Test Solution"
        })
        response = chat_response("Test prompt", context)
        assert response == "Désolé, je ne peux pas traiter votre demande pour le moment."
        # Verify the mock was called
        mock_openai_client.responses.create.assert_called_once()

    def test_generate_satellite_analysis_error(self, mock_openai_client):
        mock_openai_client.responses.create.side_effect = Exception("API Error")
        ndvi_data = pd.DataFrame({'NDVI': [0.1, 0.2, 0.3]})
        ndwi_data = pd.DataFrame({'NDWI': [0.4, 0.5, 0.6]})
        landcover_data = {'Forest': 60, 'Urban': 40}
        incident_type = "Deforestation"
        
        analysis = generate_satellite_analysis(ndvi_data, ndwi_data, landcover_data, incident_type)
        assert analysis == "Désolé, une erreur s'est produite lors de l'analyse des données satellitaires."
        # Verify the mock was called
        mock_openai_client.responses.create.assert_called_once()
