"""
Global pytest fixtures and setup.
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from test.utils.mock_ee import setup_ee_mock, get_ee_mock

# Setup Earth Engine mock for all tests
setup_ee_mock()

@pytest.fixture(scope="session", autouse=True)
def mock_earth_engine():
    """
    Global fixture to mock Earth Engine for all tests.
    This ensures Earth Engine API calls don't try to access real credentials.
    """
    # Set environment variable to skip Earth Engine initialization
    os.environ['SKIP_GEE_INIT'] = 'true'
    
    # Create a mock for Earth Engine
    with get_ee_mock() as mock:
        yield mock 