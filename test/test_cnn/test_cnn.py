import pytest
import torch
from unittest.mock import patch, MagicMock
from app.services.cnn.cnn import load_model, predict, tags

@pytest.fixture
def mock_environment(monkeypatch):
    monkeypatch.setenv('MODEL_PATH', '/path/to/model.pth')

@pytest.fixture
def mock_torch_load():
    with patch('torch.load') as mock_load:
        mock_load.return_value = {'fc.weight': torch.randn(8, 2048), 'fc.bias': torch.randn(8)}
        yield mock_load

@pytest.fixture
def mock_model():
    with patch('app.services.cnn.cnn.m_a_model') as mock_model_class:
        mock_model_instance = MagicMock()
        mock_model_class.return_value = mock_model_instance
        yield mock_model_instance

class TestLoadModel:
    def test_load_model_success(self, mock_environment, mock_torch_load, mock_model):
        model = load_model()
        assert model == mock_model
        mock_model.load_state_dict.assert_called_once()

    def test_load_model_no_env_var(self, monkeypatch):
        monkeypatch.delenv('MODEL_PATH', raising=False)
        with pytest.raises(ValueError, match="MODEL_PATH is not set"):
            load_model()

    @patch('os.path.isfile', return_value=False)
    def test_load_model_file_not_found(self, mock_isfile, mock_environment):
        with pytest.raises(FileNotFoundError, match="Model file not found"):
            load_model()

    def test_load_model_exception(self, mock_environment, mock_torch_load, mock_model):
        mock_model.load_state_dict.side_effect = RuntimeError("Loading failed")
        with pytest.raises(RuntimeError, match="Loading failed"):
            load_model()

class TestPredict:
    @pytest.fixture
    def mock_preprocess_image(self):
        with patch('app.services.cnn.cnn.preprocess_image') as mock:
            mock.return_value = torch.randn(1, 3, 224, 224)
            yield mock

    @pytest.fixture
    def mock_model_predict(self, mock_model):
        mock_model.return_value = torch.randn(1, 8)
        return mock_model

    def test_predict_success(self, mock_preprocess_image, mock_model_predict):
        image_bytes = b'fake_image_data'
        predictions, probabilities = predict(image_bytes)
        
        assert isinstance(predictions, list)
        assert len(predictions) <= 3
        assert all(isinstance(pred, tuple) and len(pred) == 2 for pred in predictions)
        assert all(pred[0] in tags for pred in predictions)
        assert all(0 <= prob <= 1 for _, prob in predictions)
        
        assert isinstance(probabilities, list)
        assert len(probabilities) == 8
        assert all(0 <= prob <= 1 for prob in probabilities)

        mock_preprocess_image.assert_called_once_with(image_bytes)
        mock_model_predict.assert_called_once()

    def test_predict_no_high_confidence(self, mock_preprocess_image, mock_model_predict):
        mock_model_predict.return_value = torch.tensor([[-10.0] * 8])  # All low probabilities
        
        image_bytes = b'fake_image_data'
        predictions, probabilities = predict(image_bytes)
        
        assert len(predictions) == 0
        assert len(probabilities) == 8
        assert all(prob < 0.4 for prob in probabilities)

