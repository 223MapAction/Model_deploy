import pytest
from unittest.mock import patch, MagicMock
import torch
import numpy as np
from app.models.image_model import load_model, preprocess_image, predict

@pytest.fixture
def mock_model():
    model = MagicMock()
    model.eval.return_value = None
    model.return_value = torch.rand(1, 10)  # Assuming 10 classes
    return model

@pytest.fixture
def mock_image():
    return np.random.rand(224, 224, 3).astype(np.uint8)

class TestImageModel:
    @patch('app.image_model.torch.load')
    def test_load_model(self, mock_torch_load, mock_model):
        mock_torch_load.return_value = mock_model
        model = load_model('path/to/model.pth')
        assert model == mock_model
        mock_torch_load.assert_called_once_with('path/to/model.pth', map_location=torch.device('cpu'))

    @patch('app.image_model.transforms')
    def test_preprocess_image(self, mock_transforms, mock_image):
        mock_transforms.Compose.return_value = lambda x: torch.rand(3, 224, 224)
        result = preprocess_image(mock_image)
        assert isinstance(result, torch.Tensor)
        assert result.shape == (3, 224, 224)

    @patch('app.image_model.load_model')
    @patch('app.image_model.preprocess_image')
    def test_predict(self, mock_preprocess, mock_load_model, mock_model, mock_image):
        mock_load_model.return_value = mock_model
        mock_preprocess.return_value = torch.rand(1, 3, 224, 224)
        
        class_names = ['class1', 'class2', 'class3', 'class4', 'class5', 
                       'class6', 'class7', 'class8', 'class9', 'class10']
        
        with patch('app.image_model.class_names', class_names):
            result = predict(mock_image)
        
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)
        assert isinstance(result[1], float)
        assert 0 <= result[1] <= 1

    @patch('app.image_model.load_model')
    def test_predict_model_error(self, mock_load_model, mock_image):
        mock_load_model.side_effect = Exception("Model loading error")
        
        with pytest.raises(Exception, match="Model loading error"):
            predict(mock_image)

    @patch('app.image_model.load_model')
    @patch('app.image_model.preprocess_image')
    def test_predict_preprocessing_error(self, mock_preprocess, mock_load_model, mock_model, mock_image):
        mock_load_model.return_value = mock_model
        mock_preprocess.side_effect = Exception("Preprocessing error")
        
        with pytest.raises(Exception, match="Preprocessing error"):
            predict(mock_image)
