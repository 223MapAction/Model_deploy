import pytest
from unittest.mock import patch, MagicMock
import os

@pytest.fixture
def mock_env_vars():
    with patch.dict(os.environ, {'POSTGRES_URL': 'postgresql://user:pass@localhost/testdb'}):
        yield

@pytest.fixture
def mock_load_dotenv():
    with patch('app.database.load_dotenv') as mock:
        yield mock

@pytest.fixture
def mock_database():
    with patch('app.database.Database') as mock:
        yield mock

class TestDatabase:
    def test_load_dotenv_called(self, mock_load_dotenv, mock_env_vars, mock_database):
        import app.database
        mock_load_dotenv.assert_called_once()

    def test_postgres_url_retrieved(self, mock_env_vars, mock_database):
        import app.database
        assert app.database.postgres_url == 'postgresql://user:pass@localhost/testdb'

    def test_database_initialized(self, mock_env_vars, mock_database):
        import app.database
        mock_database.assert_called_once_with('postgresql://user:pass@localhost/testdb')

    def test_database_instance_created(self, mock_env_vars, mock_database):
        import app.database
        assert isinstance(app.database.database, MagicMock)

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_postgres_url(self, mock_load_dotenv, mock_database):
        with pytest.raises(TypeError):
            import app.database

    @patch('app.database.os.getenv')
    def test_empty_postgres_url(self, mock_getenv, mock_load_dotenv, mock_database):
        mock_getenv.return_value = ''
        with pytest.raises(ValueError):
            import app.database
