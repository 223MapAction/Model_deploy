import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app, startup, shutdown, database
from app.apis.main_router import sanitize_error_message
from fastapi import HTTPException

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_database():
    with patch('app.main.database') as mock:
        yield mock

class TestMain:
    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Welcome to the Map Action API"}

    def test_health_check_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    @patch('app.main.logger')
    def test_startup_event(self, mock_logger, mock_database):
        startup()
        mock_database.connect.assert_called_once()
        mock_logger.info.assert_called_with("Connected to the database successfully.")

    @patch('app.main.logger')
    def test_startup_event_failure(self, mock_logger, mock_database):
        mock_database.connect.side_effect = Exception("Connection failed")
        with pytest.raises(Exception, match="Connection failed"):
            startup()
        mock_logger.error.assert_called_with("Failed to connect to the database: Connection failed")

    @patch('app.main.logger')
    def test_shutdown_event(self, mock_logger, mock_database):
        shutdown()
        mock_database.disconnect.assert_called_once()
        mock_logger.info.assert_called_with("Disconnected from the database successfully.")

    @patch('app.main.logger')
    def test_shutdown_event_failure(self, mock_logger, mock_database):
        mock_database.disconnect.side_effect = Exception("Disconnection failed")
        with pytest.raises(Exception, match="Disconnection failed"):
            shutdown()
        mock_logger.error.assert_called_with("Failed to disconnect from the database: Disconnection failed")

    def test_cors_middleware(self, client):
        response = client.options("/", headers={"Origin": "https://testorigin.com"})
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    @patch('app.main.logger')
    def test_log_requests_middleware(self, mock_logger, client):
        client.get("/")
        mock_logger.info.assert_called()

    def test_custom_exception_handler(self, client):
        @app.get("/test_exception")
        async def test_exception():
            raise HTTPException(status_code=400, detail="Test error")

        response = client.get("/test_exception")
        assert response.status_code == 400
        assert "detail" in response.json()

    @pytest.mark.parametrize("input_message,sensitive_structures,expected_output", [
        ("Error with password123", ["password"], "Error with [REDACTED]123"),
        ("Normal message", [], "Normal message"),
        ("Secret key: abc123", ["key"], "Secret [REDACTED]: abc123"),
    ])
    def test_sanitize_error_message(self, input_message, sensitive_structures, expected_output):
        assert sanitize_error_message(input_message, sensitive_structures) == expected_output
