import pytest
import os
import json
import tempfile
import numpy as np
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime
from app.services.analysis.satellite_data import download_sentinel_data, preprocess_sentinel_data

# Test fixtures
@pytest.fixture
def mock_geojson_point():
    """Create a temporary GeoJSON file with a Point geometry."""
    geojson_content = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Point",
                    "coordinates": [10.0, 45.0]
                }
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.geojson', delete=False) as temp_file:
        json.dump(geojson_content, temp_file)
        temp_path = temp_file.name
    
    yield temp_path
    
    # Cleanup
    os.unlink(temp_path)

@pytest.fixture
def mock_geojson_polygon():
    """Create a temporary GeoJSON file with a Polygon geometry."""
    geojson_content = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [10.0, 45.0],
                            [11.0, 45.0],
                            [11.0, 46.0],
                            [10.0, 46.0],
                            [10.0, 45.0]
                        ]
                    ]
                }
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.geojson', delete=False) as temp_file:
        json.dump(geojson_content, temp_file)
        temp_path = temp_file.name
    
    yield temp_path
    
    # Cleanup
    os.unlink(temp_path)

@pytest.fixture
def mock_invalid_geojson():
    """Create a temporary GeoJSON file with invalid content."""
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.geojson', delete=False) as temp_file:
        temp_file.write("This is not valid JSON")
        temp_path = temp_file.name
    
    yield temp_path
    
    # Cleanup
    os.unlink(temp_path)

# Tests for download_sentinel_data
@patch('app.services.analysis.satellite_data.OAuth2Session')
@patch('app.services.analysis.satellite_data.BackendApplicationClient')
@patch.dict(os.environ, {
    'COPERNICUS_CLIENT_ID': 'test_client_id',
    'COPERNICUS_CLIENT_SECRET': 'test_client_secret'
})
def test_download_sentinel_data_success(mock_client, mock_oauth, mock_geojson_point, tmp_path):
    # Mock OAuth2Session and its methods
    mock_oauth_instance = MagicMock()
    mock_oauth.return_value = mock_oauth_instance
    mock_oauth_instance.fetch_token.return_value = {"access_token": "test_token"}
    
    # Mock successful search response
    mock_search_response = MagicMock()
    mock_search_response.status_code = 200
    mock_search_response.json.return_value = {
        "features": [
            {
                "id": "S2A_MSIL2A_20230101T123456_N0000_R123_T12ABC_20230101T150000",
                "assets": {
                    "download": {
                        "href": "https://example.com/download/test.zip"
                    }
                }
            }
        ]
    }
    mock_oauth_instance.post.return_value = mock_search_response
    
    # Mock successful download response
    mock_download_response = MagicMock()
    mock_download_response.status_code = 200
    mock_download_response.iter_content.return_value = [b"test data"]
    mock_oauth_instance.get.return_value.__enter__.return_value = mock_download_response
    
    # Call the function
    output_dir = str(tmp_path)
    result = download_sentinel_data(mock_geojson_point, "20230101", "20230131", output_dir)
    
    # Assertions
    assert len(result) == 1
    assert result[0].endswith(".zip")
    assert mock_oauth_instance.fetch_token.called
    assert mock_oauth_instance.post.called
    assert mock_oauth_instance.get.called

@patch('app.services.analysis.satellite_data.OAuth2Session')
@patch('app.services.analysis.satellite_data.BackendApplicationClient')
@patch.dict(os.environ, {
    'COPERNICUS_CLIENT_ID': 'test_client_id',
    'COPERNICUS_CLIENT_SECRET': 'test_client_secret'
})
def test_download_sentinel_data_polygon(mock_client, mock_oauth, mock_geojson_polygon, tmp_path):
    # Mock OAuth2Session and its methods
    mock_oauth_instance = MagicMock()
    mock_oauth.return_value = mock_oauth_instance
    mock_oauth_instance.fetch_token.return_value = {"access_token": "test_token"}
    
    # Mock successful search response
    mock_search_response = MagicMock()
    mock_search_response.status_code = 200
    mock_search_response.json.return_value = {
        "features": [
            {
                "id": "S2A_MSIL2A_20230101T123456_N0000_R123_T12ABC_20230101T150000",
                "assets": {
                    "download": {
                        "href": "https://example.com/download/test.zip"
                    }
                }
            }
        ]
    }
    mock_oauth_instance.post.return_value = mock_search_response
    
    # Mock successful download response
    mock_download_response = MagicMock()
    mock_download_response.status_code = 200
    mock_download_response.iter_content.return_value = [b"test data"]
    mock_oauth_instance.get.return_value.__enter__.return_value = mock_download_response
    
    # Call the function
    output_dir = str(tmp_path)
    result = download_sentinel_data(mock_geojson_polygon, "20230101", "20230131", output_dir)
    
    # Assertions
    assert len(result) == 1
    assert result[0].endswith(".zip")

@patch('app.services.analysis.satellite_data.OAuth2Session')
@patch('app.services.analysis.satellite_data.BackendApplicationClient')
@patch.dict(os.environ, {
    'COPERNICUS_CLIENT_ID': 'test_client_id',
    'COPERNICUS_CLIENT_SECRET': 'test_client_secret'
})
def test_download_sentinel_data_no_results(mock_client, mock_oauth, mock_geojson_point, tmp_path):
    # Mock OAuth2Session and its methods
    mock_oauth_instance = MagicMock()
    mock_oauth.return_value = mock_oauth_instance
    mock_oauth_instance.fetch_token.return_value = {"access_token": "test_token"}
    
    # Mock search response with no features
    mock_search_response = MagicMock()
    mock_search_response.status_code = 200
    mock_search_response.json.return_value = {"features": []}
    mock_oauth_instance.post.return_value = mock_search_response
    
    # Call the function
    output_dir = str(tmp_path)
    result = download_sentinel_data(mock_geojson_point, "20230101", "20230131", output_dir)
    
    # Assertions
    assert len(result) == 0

@patch('app.services.analysis.satellite_data.OAuth2Session')
@patch('app.services.analysis.satellite_data.BackendApplicationClient')
@patch.dict(os.environ, {
    'COPERNICUS_CLIENT_ID': 'test_client_id',
    'COPERNICUS_CLIENT_SECRET': 'test_client_secret'
})
def test_download_sentinel_data_search_error(mock_client, mock_oauth, mock_geojson_point, tmp_path):
    # Mock OAuth2Session and its methods
    mock_oauth_instance = MagicMock()
    mock_oauth.return_value = mock_oauth_instance
    mock_oauth_instance.fetch_token.return_value = {"access_token": "test_token"}
    
    # Mock search response with error
    mock_search_response = MagicMock()
    mock_search_response.status_code = 500
    mock_search_response.raise_for_status.side_effect = Exception("API Error")
    mock_search_response.text = "Internal Server Error"
    mock_oauth_instance.post.return_value = mock_search_response
    
    # Call the function
    output_dir = str(tmp_path)
    result = download_sentinel_data(mock_geojson_point, "20230101", "20230131", output_dir)
    
    # Assertions
    assert len(result) == 0

def test_download_sentinel_data_missing_credentials(mock_geojson_point, tmp_path, monkeypatch):
    # Explicitly remove the environment variables
    monkeypatch.delenv('COPERNICUS_CLIENT_ID', raising=False)
    monkeypatch.delenv('COPERNICUS_CLIENT_SECRET', raising=False)
    
    # Call the function with missing credentials
    output_dir = str(tmp_path)
    
    with pytest.raises(ValueError, match="Copernicus API credentials not found"):
        download_sentinel_data(mock_geojson_point, "20230101", "20230131", output_dir)

@patch('app.services.analysis.satellite_data.OAuth2Session')
@patch('app.services.analysis.satellite_data.BackendApplicationClient')
@patch('app.services.analysis.satellite_data.open', create=True)
def test_download_sentinel_data_invalid_geojson(mock_open, mock_client, mock_oauth, mock_invalid_geojson, tmp_path):
    # Setup environment variables
    os.environ['COPERNICUS_CLIENT_ID'] = 'test_client_id'
    os.environ['COPERNICUS_CLIENT_SECRET'] = 'test_client_secret'
    
    # Mock OAuth2Session and its methods
    mock_oauth_instance = MagicMock()
    mock_oauth.return_value = mock_oauth_instance
    mock_oauth_instance.fetch_token.return_value = {"access_token": "test_token"}
    
    # Mock open to raise an exception when trying to open the GeoJSON file
    mock_file = MagicMock()
    mock_file.__enter__.return_value = mock_file
    mock_file.read.return_value = "This is not valid JSON"
    mock_open.return_value = mock_file
    
    # Call the function with invalid GeoJSON
    output_dir = str(tmp_path)
    # Update to expect a ValueError since the implementation raises this error for invalid GeoJSON
    with pytest.raises(ValueError, match="Invalid GeoJSON file"):
        download_sentinel_data(mock_invalid_geojson, "20230101", "20230131", output_dir)
    
    # Clean up environment variables
    del os.environ['COPERNICUS_CLIENT_ID']
    del os.environ['COPERNICUS_CLIENT_SECRET']

# # Tests for preprocess_sentinel_data
# @patch('app.services.analysis.satellite_data.rasterio')
# @patch('zipfile.ZipFile')
# def test_preprocess_sentinel_data_success(mock_zipfile, mock_rasterio, tmp_path):
#     # Mock zipfile
#     mock_zip_instance = MagicMock()
#     mock_zipfile.return_value.__enter__.return_value = mock_zip_instance
    
#     # Mock file list in zip
#     mock_zip_instance.namelist.return_value = [
#         "GRANULE/L2A_123456_12345/IMG_DATA/R10m/T12ABC_20230101T123456_B02_10m.jp2",
#         "GRANULE/L2A_123456_12345/IMG_DATA/R10m/T12ABC_20230101T123456_B03_10m.jp2",
#         "GRANULE/L2A_123456_12345/IMG_DATA/R10m/T12ABC_20230101T123456_B04_10m.jp2",
#         "GRANULE/L2A_123456_12345/IMG_DATA/R10m/T12ABC_20230101T123456_B08_10m.jp2"
#     ]
    
#     # Mock extracted files
#     mock_extracted_files = {}
#     for band in ['B02', 'B03', 'B04', 'B08']:
#         filename = f"GRANULE/L2A_123456_12345/IMG_DATA/R10m/T12ABC_20230101T123456_{band}_10m.jp2"
#         mock_extracted_files[filename] = MagicMock()
    
#     def mock_extract(name, path):
#         os.makedirs(os.path.dirname(os.path.join(path, name)), exist_ok=True)
#         with open(os.path.join(path, name), 'wb') as f:
#             f.write(b"test data")
#         return os.path.join(path, name)
    
#     mock_zip_instance.extract.side_effect = mock_extract
    
#     # Mock rasterio operations
#     mock_dataset = MagicMock()
#     mock_dataset.profile = {"driver": "GTiff", "height": 100, "width": 100, "count": 1}
#     mock_dataset.read.return_value = np.zeros((1, 100, 100))
#     mock_rasterio.open.return_value.__enter__.return_value = mock_dataset
    
#     # Input and output directories
#     input_files = [str(tmp_path / "test_sentinel.zip")]
#     output_dir = str(tmp_path / "output")
#     os.makedirs(output_dir, exist_ok=True)
    
#     # Call the function
#     with patch('os.path.exists', return_value=True):
#         result = preprocess_sentinel_data(input_files, output_dir)
    
#     # Assertions
#     assert len(result) == 1
#     assert result[0].endswith(".tif")
#     assert mock_zip_instance.namelist.called
#     assert mock_zip_instance.extract.called
#     assert mock_rasterio.open.called

@patch('app.services.analysis.satellite_data.rasterio')
@patch('zipfile.ZipFile')
def test_preprocess_sentinel_data_missing_bands(mock_zipfile, mock_rasterio, tmp_path):
    # Mock zipfile
    mock_zip_instance = MagicMock()
    mock_zipfile.return_value.__enter__.return_value = mock_zip_instance
    
    # Mock file list in zip with missing bands
    mock_zip_instance.namelist.return_value = [
        "GRANULE/L2A_123456_12345/IMG_DATA/R10m/T12ABC_20230101T123456_B02_10m.jp2",
        # Missing B03, B04, B08
    ]
    
    # Input and output directories
    input_files = [str(tmp_path / "test_sentinel.zip")]
    output_dir = str(tmp_path / "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Call the function
    result = preprocess_sentinel_data(input_files, output_dir)
    
    # Assertions
    assert len(result) == 0  # No output file produced due to missing bands
    assert mock_zip_instance.namelist.called

@patch('app.services.analysis.satellite_data.rasterio')
@patch('zipfile.ZipFile')
def test_preprocess_sentinel_data_no_granules(mock_zipfile, mock_rasterio, tmp_path):
    # Mock zipfile
    mock_zip_instance = MagicMock()
    mock_zipfile.return_value.__enter__.return_value = mock_zip_instance
    
    # Mock empty file list in zip
    mock_zip_instance.namelist.return_value = []
    
    # Input and output directories
    input_files = [str(tmp_path / "test_sentinel.zip")]
    output_dir = str(tmp_path / "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Call the function
    result = preprocess_sentinel_data(input_files, output_dir)
    
    # Assertions
    assert len(result) == 0  # No output file produced due to no granules
    assert mock_zip_instance.namelist.called
