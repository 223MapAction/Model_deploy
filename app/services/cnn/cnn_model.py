import torch
from torchvision.models import resnet50, ResNet50_Weights
import torch.nn as nn

def m_a_model(num_tags: int):
    """
    Initializes and modifies a ResNet50 model for multi-label classification.
    
    Args:
        num_tags (int): The number of tags to predict.
    
    Returns:
        torch.nn.Module: A PyTorch model configured for multi-label classification.
    """
    # Load ResNet50 model with default weights
    resnet50_weights = ResNet50_Weights.DEFAULT
    model = resnet50(weights=resnet50_weights)
    
    # Freeze all parameters in the model
    for param in model.parameters():
        param.requires_grad = False
    
    # Modify the classifier (fully connected) layer to match the training architecture
    num_ftrs = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Linear(num_ftrs, 1024),
        nn.ReLU(),
        nn.Dropout(0.5),
        nn.Linear(1024, num_tags)
    )
    
    return model
