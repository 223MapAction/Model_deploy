import pytest
from unittest.mock import patch, MagicMock
from app.services.celery.celery_task import perform_prediction, fetch_contextual_information, analyze_incident_zone
import pandas as pd
import ee

@pytest.fixture
def mock_predict():
    with patch('app.services.celery.celery_task.predict') as mock:
        yield mock

@pytest.fixture
def mock_get_response():
    with patch('app.services.celery.celery_task.get_response') as mock:
        yield mock

@pytest.fixture
def mock_analyze_vegetation_and_water():
    with patch('app.services.celery.celery_task.analyze_vegetation_and_water') as mock:
        yield mock

@pytest.fixture
def mock_analyze_land_cover():
    with patch('app.services.celery.celery_task.analyze_land_cover') as mock:
        yield mock

@pytest.fixture
def mock_generate_plots():
    with patch('app.services.celery.celery_task.generate_ndvi_ndwi_plot') as mock_ndvi_ndwi:
        with patch('app.services.celery.celery_task.generate_ndvi_heatmap') as mock_heatmap:
            with patch('app.services.celery.celery_task.generate_landcover_plot') as mock_landcover:
                yield mock_ndvi_ndwi, mock_heatmap, mock_landcover

@pytest.fixture
def mock_generate_satellite_analysis():
    with patch('app.services.celery.celery_task.generate_satellite_analysis') as mock:
        yield mock

def test_perform_prediction(mock_predict):
    # Setup mock
    mock_predict.return_value = (
        [("Déchets", 0.9)], 
        [0.1, 0.9, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    )

    # Call the task
    image_data = b"fake_image_data"
    result = perform_prediction(image_data)

    # Assertions
    assert result[0] == [("Déchets", 0.9)]
    assert result[1] == [0.1, 0.9, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    mock_predict.assert_called_once_with(image_data)

def test_fetch_contextual_information(mock_get_response):
    # Setup mock
    mock_get_response.side_effect = [
        "Analysis of the environmental incident",
        "Proposed solutions for the incident"
    ]

    # Call the task
    prediction = "wildfire"
    sensitive_structures = ["forest", "residential area"]
    zone = "Northern region"
    result = fetch_contextual_information(prediction, sensitive_structures, zone)

    # Assertions
    assert result == (
        "Analysis of the environmental incident",
        "Proposed solutions for the incident"
    )
    assert mock_get_response.call_count == 2

def test_analyze_incident_zone(mock_analyze_vegetation_and_water, mock_analyze_land_cover, mock_generate_plots, mock_generate_satellite_analysis):
    # Setup mocks
    mock_analyze_vegetation_and_water.return_value = (pd.DataFrame(), pd.DataFrame())
    mock_analyze_land_cover.return_value = {}
    mock_generate_plots[0].return_value = "ndvi_ndwi_plot"
    mock_generate_plots[1].return_value = "ndvi_heatmap"
    mock_generate_plots[2].return_value = "landcover_plot"
    mock_generate_satellite_analysis.return_value = "Textual analysis of satellite data"

    # Call the task
    result = analyze_incident_zone(12.34, 56.78, "Test Location", "wildfire", "20230101", "20230131")

    # Assertions
    assert isinstance(result, dict)
    assert "textual_analysis" in result
    assert "ndvi_ndwi_plot" in result
    assert "ndvi_heatmap" in result
    assert "landcover_plot" in result
    assert "raw_data" in result

    mock_analyze_vegetation_and_water.assert_called_once()
    mock_analyze_land_cover.assert_called_once()
    mock_generate_plots[0].assert_called_once()
    mock_generate_plots[1].assert_called_once()
    mock_generate_plots[2].assert_called_once()
    mock_generate_satellite_analysis.assert_called_once()

# @pytest.mark.parametrize("prediction_result, expected_result", [
#     (("Incident Type", [0.8, 0.2]), ("Analysis", "Solution")),
#     ({"error": "Prediction failed"}, {"error": "Prediction failed, unable to fetch contextual information."})
# ])
# def test_run_prediction_and_context(prediction_result, expected_result):
#     with patch('app.services.celery.celery_task.perform_prediction') as mock_perform_prediction, \
#          patch('app.services.celery.celery_task.fetch_contextual_information') as mock_fetch_contextual_information:
        
#         # Set up the mock for perform_prediction
#         mock_perform_prediction.delay.return_value.get.return_value = prediction_result
        
#         # Set up the mock for fetch_contextual_information
#         if not isinstance(prediction_result, dict):
#             mock_fetch_contextual_information.delay.return_value.get.return_value = expected_result
        
#         # Call the function
#         result = run_prediction_and_context(b"image_data", ["sensitive_structure"])
        
#         # Assert the result
#         assert result == expected_result
        
#         # Check if the mocks were called correctly
#         mock_perform_prediction.delay.assert_called_once_with(b"image_data")
#         if not isinstance(prediction_result, dict):
#             mock_fetch_contextual_information.delay.assert_called_once_with(prediction_result[0], ["sensitive_structure"])
#         else:
#             mock_fetch_contextual_information.delay.assert_not_called()

if __name__ == "__main__":
    pytest.main()
