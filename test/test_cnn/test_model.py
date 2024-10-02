# import pytest
# import torch
# from torchvision.models import vgg16_bn

# # Adjust this import based on your project structure
# from app.services.cnn.cnn_model import m_a_model


# def test_m_a_model():
#     num_classes = 10
#     model = m_a_model(num_classes)

#     # Verify that the classifier's output layer has the correct number of output features
#     assert model.classifier[-1].out_features == num_classes

#     # Verify that all parameters in the feature extractor layers are frozen
#     for param in model.features.parameters():
#         assert not param.requires_grad

#     # Optionally, you can also check the overall structure of the modified model
#     # Print the model structure or save it to a string to
