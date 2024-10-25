import pytest
import torch
import torch.nn as nn
from unittest.mock import patch, MagicMock
from app.services.cnn.cnn_model import m_a_model

@pytest.fixture
def mock_resnet50():
    with patch('app.services.cnn.cnn_model.resnet50') as mock:
        mock_model = MagicMock()
        mock_model.fc.in_features = 2048
        mock.return_value = mock_model
        yield mock

@pytest.fixture
def mock_resnet50_weights():
    with patch('app.services.cnn.cnn_model.ResNet50_Weights') as mock:
        mock.DEFAULT = 'default_weights'
        yield mock

class TestMAModel:
    def test_m_a_model_initialization(self, mock_resnet50, mock_resnet50_weights):
        num_tags = 8
        model = m_a_model(num_tags)

        # Check if ResNet50 was initialized correctly
        mock_resnet50.assert_called_once_with(weights='default_weights')

        # Check if all parameters are frozen except for the final layer
        for name, param in model.named_parameters():
            if 'fc' not in name:
                assert not param.requires_grad
            else:
                assert param.requires_grad

        # Check if the final layer is correctly modified
        assert isinstance(model.fc, nn.Sequential)
        assert len(model.fc) == 1
        assert isinstance(model.fc[0], nn.Linear)
        assert model.fc[0].in_features == 2048
        assert model.fc[0].out_features == num_tags

    @pytest.mark.parametrize("num_tags", [1, 5, 10])
    def test_m_a_model_output_size(self, mock_resnet50, mock_resnet50_weights, num_tags):
        model = m_a_model(num_tags)
        
        # Create a dummy input
        dummy_input = torch.randn(1, 3, 224, 224)
        
        # Get the output
        output = model(dummy_input)
        
        # Check if the output size matches the number of tags
        assert output.shape == (1, num_tags)

    def test_m_a_model_forward_pass(self, mock_resnet50, mock_resnet50_weights):
        num_tags = 8
        model = m_a_model(num_tags)

        # Create a dummy input
        dummy_input = torch.randn(1, 3, 224, 224)

        # Perform a forward pass
        output = model(dummy_input)

        # Check if the output is a tensor and has the correct shape
        assert isinstance(output, torch.Tensor)
        assert output.shape == (1, num_tags)

    def test_m_a_model_gradient_flow(self, mock_resnet50, mock_resnet50_weights):
        num_tags = 8
        model = m_a_model(num_tags)

        # Create a dummy input and target
        dummy_input = torch.randn(1, 3, 224, 224)
        dummy_target = torch.randn(1, num_tags)

        # Perform a forward pass
        output = model(dummy_input)

        # Compute loss and perform backward pass
        loss = nn.functional.mse_loss(output, dummy_target)
        loss.backward()

        # Check if gradients are zero for all layers except the final layer
        for name, param in model.named_parameters():
            if 'fc' not in name:
                assert param.grad is None or torch.all(param.grad == 0)
            else:
                assert param.grad is not None
                assert not torch.all(param.grad == 0)
