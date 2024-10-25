# import pytest
# from unittest.mock import patch, MagicMock
# import os
# from databases import Database

# # Mock the database module to avoid actual database connections during tests
# with patch('app.database.Database') as MockDatabase:
#     from app.database import database, postgres_url

# @pytest.fixture
# def mock_env_vars():
#     with patch.dict(os.environ, {'POSTGRES_URL': 'postgresql://user:pass@localhost/testdb'}):
#         yield

# @pytest.fixture
# def mock_load_dotenv():
#     with patch('app.database.load_dotenv') as mock:
#         yield mock

# @pytest.fixture
# def mock_database():
#     with patch('app.database.Database') as mock:
#         yield mock

# class TestDatabase:
#     @patch('app.database.load_dotenv')
#     def test_load_dotenv_called(self, mock_load_dotenv):
#         import app.database
#         mock_load_dotenv.assert_called_once()

#     @patch.dict(os.environ, {'POSTGRES_URL': 'mock://postgres/url'})
#     def test_postgres_url_retrieved(self):
#         assert postgres_url == 'mock://postgres/url'

#     @patch.dict(os.environ, {'POSTGRES_URL': 'mock://postgres/url'})
#     def test_database_initialized(self):
#         MockDatabase.assert_called_once_with('mock://postgres/url')

#     def test_database_instance_created(self):
#         assert isinstance(database, MagicMock)

#     @patch.dict(os.environ, {}, clear=True)
#     def test_missing_postgres_url(self):
#         with pytest.raises(TypeError):
#             import app.database

#     @patch.dict(os.environ, {'POSTGRES_URL': ''})
#     def test_empty_postgres_url(self):
#         with pytest.raises(ValueError):
#             import app.database
