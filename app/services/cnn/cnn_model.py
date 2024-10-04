import torch
from torchvision.models import vgg16_bn, VGG16_BN_Weights
import torch.nn as nn

def m_a_model(num_classes: int):
    """
    Initializes and modifies a VGG16 model with batch normalization to classify a specified number of classes.
    This function loads a pretrained VGG16 model, freezes its parameters to prevent further training of the feature extractor layers,
    and then adapts the classifier part of the model to the specified number of classes for new training tasks.

    Args:
        num_classes (int): The number of target classes for the model to classify.

    Returns:
        torch.nn.Module: A PyTorch model configured for the specified number of classes with all parameters of the
                         feature extractor layers frozen and the classifier layers tailored to the target task.
    """
    # Load VGG16 model with batch normalization weights
    vgg16_bn_weights = VGG16_BN_Weights.DEFAULT
    model = vgg16_bn(weights=vgg16_bn_weights)
    
    # Freeze all parameters in the model
    for param in model.parameters():
        param.requires_grad = False
        
    # Modify the classifier to adapt to the number of classes
    # Correctly access the last layer using negative indexing
    num_features = model.classifier[-1].in_features  # Access the last layer
    model.classifier[-1] = nn.Linear(num_features, num_classes)  # Replace the last layer
    
    return model
