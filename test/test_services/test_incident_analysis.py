import pytest
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from unittest.mock import patch, MagicMock
import ee
import uuid
import json
from datetime import datetime
from app.services.analysis.incident_analysis import (
    analyze_vegetation_and_water,
    analyze_land_cover,
    generate_ndvi_ndwi_plot,
    generate_ndvi_heatmap,
    generate_landcover_plot,
    create_geojson_from_location
)

# Setup fixtures
@pytest.fixture
def mock_ee_point():
    return MagicMock()

@pytest.fixture
def mock_ee_buffered_point():
    return MagicMock()

@pytest.fixture
def mock_ndvi_data():
    # Create sample NDVI data for testing
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='M')
    ndvi_values = np.random.uniform(low=-1.0, high=1.0, size=len(dates))
    return pd.DataFrame({'Date': dates, 'NDVI': ndvi_values})

@pytest.fixture
def mock_ndwi_data():
    # Create sample NDWI data for testing
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='M')
    ndwi_values = np.random.uniform(low=-1.0, high=1.0, size=len(dates))
    return pd.DataFrame({'Date': dates, 'NDWI': ndwi_values})

@pytest.fixture
def mock_landcover_data():
    # Sample landcover data for testing
    return {
        'Couverture arboru00e9e': 40,
        'Arbustes': 20,
        'Prairies': 15,
        'Terres cultivu00e9es': 10,
        'Zones bu00e2ties': 5,
        'Vu00e9gu00e9tation clairsemu00e9e/nue': 10
    }

# Test cases for analyze_vegetation_and_water
@patch('app.services.analysis.incident_analysis.ee.ImageCollection')
def test_analyze_vegetation_and_water(mock_image_collection, mock_ee_point, mock_ee_buffered_point):
    # Mock Earth Engine Image Collection
    mock_collection = MagicMock()
    mock_image_collection.return_value = mock_collection
    mock_collection.filterBounds.return_value = mock_collection
    mock_collection.filterDate.return_value = mock_collection
    mock_collection.filter.return_value = mock_collection
    
    # Mock mapping NDVI and NDWI
    mock_collection.map.side_effect = lambda func: mock_collection
    
    # Mock getRegion for time series data
    mock_region_info = [
        ['id', 'longitude', 'latitude', 'time', 'NDVI'],
        [0, -74.0, 40.7, 1609459200000, 0.5],
        [1, -74.0, 40.7, 1612137600000, 0.6],
        [2, -74.0, 40.7, 1614556800000, 0.7]
    ]
    mock_collection.getRegion.return_value.getInfo.return_value = mock_region_info
    
    # Mock mean values for buffered area
    mean_image = MagicMock()
    mock_collection.mean.return_value = mean_image
    mean_reducer = MagicMock()
    mean_image.reduceRegion.return_value.getInfo.return_value = {'NDVI': 0.65, 'NDWI': 0.45}
    
    # Mock ee.Date for formatting
    mock_date = MagicMock()
    mock_date.format.return_value.getInfo.side_effect = ['2021-01-01', '2021-02-01', '2021-03-01']
    with patch('app.services.analysis.incident_analysis.ee.Date', return_value=mock_date):
        # Call function
        ndvi_df, ndwi_df = analyze_vegetation_and_water(
            mock_ee_point, mock_ee_buffered_point, '2021-01-01', '2021-12-31'
        )
        
        # Assertions
        assert isinstance(ndvi_df, pd.DataFrame)
        assert isinstance(ndwi_df, pd.DataFrame)
        assert 'Date' in ndvi_df.columns
        assert 'NDVI' in ndvi_df.columns
        assert 'Date' in ndwi_df.columns
        assert 'NDWI' in ndwi_df.columns

# Test cases for analyze_land_cover
@patch('app.services.analysis.incident_analysis.ee.Image')
def test_analyze_land_cover(mock_ee_image, mock_ee_buffered_point):
    # Mock Earth Engine Image
    mock_image = MagicMock()
    mock_ee_image.return_value = mock_image
    mock_image.select.return_value = mock_image
    
    # Mock sample method and histogram
    mock_sample = MagicMock()
    mock_image.sample.return_value = mock_sample
    mock_sample.aggregate_histogram.return_value.getInfo.return_value = {
        '10': 400,
        '20': 200,
        '30': 150,
        '40': 100,
        '50': 50,
        '60': 100
    }
    
    # Call function
    result = analyze_land_cover(mock_ee_buffered_point)
    
    # Assertions
    assert isinstance(result, dict)
    # Use a more flexible approach to check for the key
    couverture_key = [k for k in result.keys() if 'Couverture arbo' in k][0]
    assert result[couverture_key] == 400
    assert 'Arbustes' in result
    assert result['Arbustes'] == 200

# Test for generate_ndvi_ndwi_plot
@patch('app.services.analysis.incident_analysis.uuid.uuid4')
@patch('app.services.analysis.incident_analysis.plt')
def test_generate_ndvi_ndwi_plot(mock_plt, mock_uuid, mock_ndvi_data, mock_ndwi_data):
    # Mock UUID for filename
    mock_uuid.return_value = 'test-uuid'
    
    # Call function
    result = generate_ndvi_ndwi_plot(mock_ndvi_data, mock_ndwi_data)
    
    # Assertions
    assert isinstance(result, str)
    assert 'test-uuid.png' in result
    mock_plt.figure.assert_called_once()
    mock_plt.plot.assert_called() # Called for both NDVI and NDWI
    mock_plt.savefig.assert_called_once()
    mock_plt.close.assert_called_once()

# Test for generate_ndvi_heatmap
@patch('app.services.analysis.incident_analysis.uuid.uuid4')
@patch('app.services.analysis.incident_analysis.plt')
@patch('app.services.analysis.incident_analysis.sns')
def test_generate_ndvi_heatmap(mock_sns, mock_plt, mock_uuid, mock_ndvi_data):
    # Mock UUID for filename
    mock_uuid.return_value = 'test-uuid-heatmap'
    
    # Call function
    result = generate_ndvi_heatmap(mock_ndvi_data)
    
    # Assertions
    assert isinstance(result, str)
    assert 'test-uuid-heatmap.png' in result
    mock_plt.figure.assert_called_once()
    mock_sns.heatmap.assert_called_once()
    mock_plt.savefig.assert_called_once()
    mock_plt.close.assert_called_once()

# Test for generate_landcover_plot
@patch('app.services.analysis.incident_analysis.uuid.uuid4')
@patch('app.services.analysis.incident_analysis.plt')
def test_generate_landcover_plot(mock_plt, mock_uuid, mock_landcover_data):
    # Mock UUID for filename
    mock_uuid.return_value = 'test-uuid-landcover'
    
    # Mock plt.pie to return the expected tuple
    mock_wedges = MagicMock()
    mock_texts = MagicMock()
    mock_autotexts = MagicMock()
    mock_plt.pie.return_value = (mock_wedges, mock_texts, mock_autotexts)
    
    # Call function
    result = generate_landcover_plot(mock_landcover_data)
    
    # Assertions
    assert isinstance(result, str)
    assert 'test-uuid-landcover.png' in result
    mock_plt.figure.assert_called_once()
    mock_plt.pie.assert_called_once()
    mock_plt.savefig.assert_called_once()
    mock_plt.close.assert_called_once()

# Test for create_geojson_from_location
@patch('app.services.analysis.incident_analysis.requests.get')
def test_create_geojson_from_location_success(mock_get):
    # Mock successful response from Nominatim
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{
        'lat': '40.7128',
        'lon': '-74.0060',
        'display_name': 'New York, USA'
    }]
    mock_get.return_value = mock_response
    
    # Temporary output directory
    output_dir = '/tmp'
    
    # Call function
    result = create_geojson_from_location('New York', output_dir)
    
    # Assertions
    assert isinstance(result, str)
    assert result.endswith('.geojson')
    assert os.path.basename(result).startswith('New York')
    
@patch('app.services.analysis.incident_analysis.requests.get')
def test_create_geojson_from_location_failure(mock_get):
    # Mock failed response from Nominatim
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response
    
    # Temporary output directory
    output_dir = '/tmp'
    
    # Call function with non-existent location
    result = create_geojson_from_location('NonExistentLocation', output_dir)
    
    # Assertions
    assert isinstance(result, str)
    assert result.endswith('.geojson')
    assert 'NonExistentLocation' in result

@patch('app.services.analysis.incident_analysis.requests.get')
def test_create_geojson_from_location_empty_results(mock_get):
    # Mock successful response but with empty results
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = []
    mock_get.return_value = mock_response
    
    # Temporary output directory
    output_dir = '/tmp'
    
    # Call function
    result = create_geojson_from_location('Unknown place', output_dir)
    
    # Assertions
    assert isinstance(result, str)
    assert result.endswith('.geojson')
    assert 'Unknown place' in result
