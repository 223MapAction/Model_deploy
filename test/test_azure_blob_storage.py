import os
import pytest
from unittest.mock import Mock, patch
from app.services.azure_blob_storage import upload_file_to_blob

@pytest.fixture
def mock_blob_service_client():
    with patch('app.services.azure_blob_storage.BlobServiceClient') as mock:
        yield mock

@pytest.fixture
def mock_default_credential():
    with patch('app.services.azure_blob_storage.DefaultAzureCredential') as mock:
        yield mock

def test_upload_file_to_blob(mock_blob_service_client, mock_default_credential, tmp_path):
    # Arrange
    container_name = 'test-container'
    file_content = b'Test file content'
    file_path = tmp_path / 'test_file.txt'
    file_path.write_bytes(file_content)

    mock_blob_client = Mock()
    mock_blob_client.url = 'https://test.blob.core.windows.net/test-container/test_file.txt'
    mock_blob_service_client.return_value.get_blob_client.return_value = mock_blob_client

    # Act
    result = upload_file_to_blob(container_name, str(file_path))

    # Assert
    assert result == 'https://test.blob.core.windows.net/test-container/test_file.txt'
    mock_blob_service_client.return_value.get_blob_client.assert_called_once_with(container=container_name, blob='test_file.txt')
    mock_blob_client.upload_blob.assert_called_once_with(file_content, blob_type="BlockBlob", overwrite=True)
    assert not file_path.exists()

@pytest.mark.parametrize("env_var", [
    "BLOB_ACCOUNT_URL",
])
def test_environment_variables(env_var):
    assert env_var in os.environ, f"{env_var} is not set in the environment"

