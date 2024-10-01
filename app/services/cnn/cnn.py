import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import io

# Define the list of categories as per main.py
categories = [
    "Caniveau bouché",
    "Déchets solides",
    "Déchets solides dans les caniveaux",
    "Pollution de l’eau (matière en suspension)",
    "Pollution de l’eau (présence de déchets plastiques)",
    "Sol aride"
]

# Initialize the ResNet50 model
# Set pretrained=True to use ImageNet weights, or False if you prefer to train from scratch
model = models.resnet50(pretrained=True)
model.eval()  # Set the model to evaluation mode

# Define the image preprocessing pipeline
def preprocess_image(image_bytes):
    """
    Preprocesses the input image for ResNet50.

    Args:
        image_bytes (bytes): The image data in bytes format.

    Returns:
        torch.Tensor: The preprocessed image tensor ready for model input.
    """
    my_transforms = transforms.Compose([
        transforms.Resize(256),                # Resize the shorter side to 256 pixels
        transforms.CenterCrop(224),            # Center crop to 224x224 pixels as expected by ResNet50
        transforms.ToTensor(),                 # Convert PIL Image to tensor
        transforms.Normalize(                  # Normalize using ImageNet's mean and std
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        ),
    ])
    image = Image.open(io.BytesIO(image_bytes)).convert('RGB')  # Ensure image is in RGB format
    return my_transforms(image).unsqueeze(0)  # Add batch dimension

def predict(image):
    """
    Performs image classification using the pretrained ResNet50 model.

    This function processes an input image, applies the ResNet50 model, and returns the predicted category and
    probability distribution over all categories.

    Args:
        image (bytes): The image data in bytes format.

    Returns:
        tuple: A tuple containing the predicted category as a string and the probabilities of all categories as a list.
    """
    model.eval()  # Ensure the model is in evaluation mode
    input_data = preprocess_image(image)  # Preprocess the image
    with torch.no_grad():  # Disable gradient calculation
        output = model(input_data)  # Get the model output
        probabilities = torch.nn.functional.softmax(output[0], dim=0)  # Calculate probabilities
        # Determine the predicted class index
        predicted_class = torch.argmax(probabilities, dim=0).item()

    # Map the predicted class index to one of the six custom categories
    # Note: This mapping is arbitrary since ResNet50 is trained on ImageNet classes.
    # For meaningful predictions, consider fine-tuning the model on your specific dataset.
    predict_label = categories[predicted_class % len(categories)]  # Using modulo for mapping

    # Convert probabilities tensor to list for easier handling
    probabilities = probabilities.cpu().tolist()

    # Return the predicted category and probabilities
    return predict_label, probabilities
