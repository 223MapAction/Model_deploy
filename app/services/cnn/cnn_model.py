# app/services/cnn/cnn_model.py

import torch
from torchvision.models import resnet50, ResNet50_Weights
import torch.nn as nn

def m_a_model(num_classes: int):
    """
    Initializes and modifies a ResNet50 model for the specified number of classes.
    
    Args:
        num_classes (int): The number of target classes for the model to classify.
    
    Returns:
        torch.nn.Module: A PyTorch model configured for the specified number of classes with
                         the classifier layer tailored to the target task.
    """
    # Load ResNet50 model with default weights
    resnet50_weights = ResNet50_Weights.DEFAULT
    model = resnet50(weights=resnet50_weights)
    
    # Freeze all parameters in the model
    for param in model.parameters():
        param.requires_grad = False
    
    # Modify the classifier (fully connected) layer to match num_classes
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, num_classes)
    
    return model
