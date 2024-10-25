import os
import pytest
from unittest.mock import patch, MagicMock
from app.services.azure_blob_storage import upload_file_to_blob

@pytest.fixture
def mock_blob_service_client():
    with patch('app.services.azure_blob_storage.BlobServiceClient') as mock_client:
        yield mock_client

@pytest.fixture
def mock_open(mocker):
    return mocker.patch('builtins.open', mocker.mock_open(read_data=b'test data'))

def test_upload_file_to_blob(mock_blob_service_client, mock_open, tmp_path):
    # Create a temporary file
    test_file = tmp_path / "test_file.txt"
    test_file.write_text("test content")

    # Mock the blob client
    mock_blob_client = MagicMock()
    mock_blob_service_client.return_value.get_blob_client.return_value = mock_blob_client
    mock_blob_client.url = "https://example.com/test_file.txt"

    # Call the function
    result = upload_file_to_blob("test-container", str(test_file))

    # Assertions
    assert result == "https://example.com/test_file.txt"
    mock_blob_client.upload_blob.assert_called_once()
    assert not test_file.exists()  # Check if the file was deleted after upload