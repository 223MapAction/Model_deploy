import pytest
import os
import boto3
from unittest.mock import patch, mock_open, MagicMock
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError

from app.services.aws_s3_storage import upload_file_to_s3


# Test successful upload with file deletion
@patch('boto3.Session')
@patch('os.remove')
@patch('builtins.open', new_callable=mock_open, read_data='test file content')
@patch.dict('os.environ', {'AWS_REGION': 'us-east-1'})
def test_upload_file_to_s3_with_deletion(mock_file, mock_remove, mock_session):
    # Set up the mock session and client
    mock_session_instance = MagicMock()
    mock_session.return_value = mock_session_instance
    mock_session_instance.region_name = 'us-east-1'  # Will be used if os.environ['AWS_REGION'] not set
    
    mock_s3_client = MagicMock()
    mock_session_instance.client.return_value = mock_s3_client
    
    # Call the function
    result = upload_file_to_s3('test-bucket', 'test_file.txt')
    
    # Verify the file was uploaded
    mock_s3_client.upload_fileobj.assert_called_once()
    
    # Verify the file was deleted after upload
    mock_remove.assert_called_once_with('test_file.txt')
    
    # Verify the function returned the correct URL
    assert result == 'https://test-bucket.s3.amazonaws.com/test_file.txt'


# Test URL formatting for non-us-east-1 regions
@patch('boto3.Session')
@patch('os.remove')
@patch('builtins.open', new_callable=mock_open, read_data='test file content')
@patch.dict('os.environ', {'AWS_REGION': 'eu-west-1'})
def test_upload_file_to_s3_non_default_region_url(mock_file, mock_remove, mock_session):
    # Set up the mock session and client
    mock_session_instance = MagicMock()
    mock_session.return_value = mock_session_instance
    mock_session_instance.region_name = None  # Force it to use the environment variable
    
    mock_s3_client = MagicMock()
    mock_session_instance.client.return_value = mock_s3_client
    
    # Call the function
    result = upload_file_to_s3('test-bucket', 'test_file.txt')
    
    # Verify the URL includes the region for non-us-east-1 regions
    assert result == 'https://test-bucket.s3.eu-west-1.amazonaws.com/test_file.txt'


# Test handling of file not found error
@patch('boto3.Session')
def test_upload_file_to_s3_file_not_found(mock_session):
    # Set up the mock session and client
    mock_session_instance = MagicMock()
    mock_session.return_value = mock_session_instance
    mock_session_instance.region_name = 'us-east-1'
    
    mock_s3_client = MagicMock()
    mock_session_instance.client.return_value = mock_s3_client
    
    # Make open raise FileNotFoundError
    with patch('builtins.open', side_effect=FileNotFoundError()):
        # Call the function
        result = upload_file_to_s3('test-bucket', 'non_existent_file.txt')
    
    # Verify that the function handled the error properly
    assert result is None
    # Verify that upload_fileobj was not called
    mock_s3_client.upload_fileobj.assert_not_called()


# Test handling of generic exceptions during upload
@patch('boto3.Session')
@patch('builtins.open', new_callable=mock_open, read_data='test file content')
def test_upload_file_to_s3_generic_exception(mock_file, mock_session):
    # Set up the mock session and client
    mock_session_instance = MagicMock()
    mock_session.return_value = mock_session_instance
    mock_session_instance.region_name = 'us-east-1'
    
    mock_s3_client = MagicMock()
    mock_session_instance.client.return_value = mock_s3_client
    
    # Make upload_fileobj raise a generic exception
    mock_s3_client.upload_fileobj.side_effect = Exception('Generic error')
    
    # Call the function
    result = upload_file_to_s3('test-bucket', 'test_file.txt')
    
    # Verify that the function handled the error properly
    assert result is None


# Test handling of os.remove exception
@patch('boto3.Session')
@patch('os.remove', side_effect=OSError('Permission denied'))
@patch('builtins.open', new_callable=mock_open, read_data='test file content')
@patch.dict('os.environ', {'AWS_REGION': 'us-east-1'})
def test_upload_file_to_s3_deletion_error(mock_file, mock_remove, mock_session):
    # Set up the mock session and client
    mock_session_instance = MagicMock()
    mock_session.return_value = mock_session_instance
    mock_session_instance.region_name = 'us-east-1'
    
    mock_s3_client = MagicMock()
    mock_session_instance.client.return_value = mock_s3_client
    
    # Call the function
    result = upload_file_to_s3('test-bucket', 'test_file.txt')
    
    # Verify that the function still completes successfully even if deletion fails
    assert result == 'https://test-bucket.s3.amazonaws.com/test_file.txt'
    
    # Verify that the deletion was attempted
    mock_remove.assert_called_once_with('test_file.txt')


# Test behavior when bucket name is empty
def test_upload_file_to_s3_empty_bucket_name():
    # Call the function with an empty bucket name
    result = upload_file_to_s3('', 'test_file.txt')
    
    # Verify that the function returns None
    assert result is None
