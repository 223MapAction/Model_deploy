import pytest
import io
import torch
from PIL import Image
from unittest.mock import patch, MagicMock
from app.services.cnn.cnn_preprocess import preprocess_image, transform

@pytest.fixture
def mock_image():
    # Create a small red square image
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

class TestPreprocessImage:
    def test_preprocess_image_output_shape(self, mock_image):
        result = preprocess_image(mock_image)
        assert isinstance(result, torch.Tensor)
        assert result.shape == (1, 3, 224, 224)

    def test_preprocess_image_normalization(self, mock_image):
        result = preprocess_image(mock_image)
        # Check if the values are normalized (approximately)
        assert -3 < result.min() < -2
        assert 2 < result.max() < 3

    @patch('app.services.cnn.cnn_preprocess.Image.open')
    def test_preprocess_image_calls(self, mock_open, mock_image):
        mock_img = MagicMock()
        mock_open.return_value = mock_img

        preprocess_image(mock_image)

        mock_open.assert_called_once()
        mock_img.convert.assert_called_once_with('RGB')

    def test_preprocess_image_with_different_sizes(self):
        for size in [(50, 50), (100, 200), (300, 150)]:
            img = Image.new('RGB', size, color='blue')
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()

            result = preprocess_image(img_bytes)
            assert result.shape == (1, 3, 224, 224)

    def test_transform_components(self):
        assert len(transform.transforms) == 3
        assert isinstance(transform.transforms[0], torch.nn.modules.module.Module)
        assert isinstance(transform.transforms[1], torch.nn.modules.module.Module)
        assert isinstance(transform.transforms[2], torch.nn.modules.module.Module)

    @pytest.mark.parametrize("image_format", ['PNG', 'JPEG', 'GIF'])
    def test_preprocess_image_different_formats(self, image_format):
        img = Image.new('RGB', (100, 100), color='green')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format=image_format)
        img_bytes = img_byte_arr.getvalue()

        result = preprocess_image(img_bytes)
        assert result.shape == (1, 3, 224, 224)
