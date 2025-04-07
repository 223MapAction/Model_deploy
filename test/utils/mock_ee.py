"""Utilities for mocking Google Earth Engine in tests"""
import os
from unittest.mock import patch, MagicMock

def setup_ee_mock():
    """
    Set up environment variables and create a mock for Earth Engine.
    This should be called at the start of test files that interact with Earth Engine.
    """
    # Set environment variable to skip Earth Engine initialization
    os.environ['SKIP_GEE_INIT'] = 'true'
    
def get_ee_mock():
    """
    Create a patch for Earth Engine to be used in tests.
    
    Usage:
    with get_ee_mock() as mock_ee:
        # Test code that uses Earth Engine
    """
    ee_patch = patch('app.services.celery.celery_task.ee')
    
    def _setup_mock(mock_ee):
        # Setup basic Earth Engine mocks
        mock_ee.ServiceAccountCredentials.return_value = MagicMock()
        mock_ee.Initialize.return_value = None
        mock_ee.Geometry.Point.return_value = MagicMock()
        mock_point = MagicMock()
        mock_ee.Geometry.Point.return_value = mock_point
        mock_point.buffer.return_value = MagicMock()
        return mock_ee
    
    # Set up the mock before yielding
    mock = ee_patch.start()
    _setup_mock(mock)
    
    yield mock
    
    # Clean up
    ee_patch.stop() 