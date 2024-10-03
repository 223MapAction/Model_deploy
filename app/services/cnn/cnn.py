import os
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import io
from dotenv import load_dotenv


load_dotenv()
# Define the list of categories as per your fine-tuned model
categories = [
    "Caniveau obstrué",
    "Déchet dans l'eau",
    "Déchet solide",
    "Déforestation",
    "Pollution de l'eau",
    "Sol dégradé",
    "Sécheresse"
]

# Initialize the ResNet50 model
num_classes = len(categories)
model = models.resnet50(pretrained=False)  # Do not load pretrained ImageNet weights
model.fc = nn.Linear(model.fc.in_features, num_classes)  # Adjust the final layer

# Load the fine-tuned model weights from MODEL_PATH
MODEL_PATH = os.environ.get('MODEL_PATH')  # Ensure MODEL_PATH is set in your environment
if MODEL_PATH is None:
    raise ValueError("MODEL_PATH is not set in the environment variables.")

# Load the state dictionary into the model
model.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device('cpu')))
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
    Performs image classification using the fine-tuned ResNet50 model.

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

    # Map the predicted class index to the corresponding category
    predict_label = categories[predicted_class]

    # Convert probabilities tensor to list for easier handling
    probabilities = probabilities.cpu().tolist()

    # Return the predicted category and probabilities
    return predict_label, probabilities
