# services/cnn.py

import os
import time
import logging
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import io
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Expand user path and verify file existence
MODEL_PATH = os.path.expanduser(MODEL_PATH)
if not os.path.isfile(MODEL_PATH):
    raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")

# Load the state dictionary into the model
model.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device('cpu')))
model.eval()  # Set the model to evaluation mode
logger.info("Model loaded and set to evaluation mode.")

# Define the image preprocessing pipeline
def preprocess_image(image_bytes):
    """
    Preprocesses the input image for ResNet50.

    Args:
        image_bytes (bytes): The image data in bytes format.

    Returns:
        torch.Tensor: The preprocessed image tensor ready for model input.
    """
    try:
        logger.info("Starting image preprocessing.")
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
        logger.info("Image opened and converted to RGB.")
        processed_image = my_transforms(image).unsqueeze(0)  # Add batch dimension
        logger.info("Image transformed successfully.")
        return processed_image
    except Exception as e:
        logger.error(f"Error during image preprocessing: {e}", exc_info=True)
        raise

def predict(image):
    """
    Performs image classification using the fine-tuned ResNet50 model.

    Args:
        image (bytes): The image data in bytes format.

    Returns:
        tuple: A tuple containing the predicted category as a string and the probabilities of all categories as a list.
    """
    try:
        start_time = time.time()
        logger.info("Starting prediction.")

        model.eval()  # Ensure the model is in evaluation mode
        logger.info("Model set to evaluation mode.")

        # Preprocess the image
        preprocess_start = time.time()
        input_data = preprocess_image(image)  # Preprocess the image
        preprocess_end = time.time()
        logger.info(f"Image preprocessed in {preprocess_end - preprocess_start:.4f} seconds.")

        with torch.no_grad():  # Disable gradient calculation
            inference_start = time.time()
            output = model(input_data)  # Get the model output
            inference_end = time.time()
            logger.info(f"Model inference completed in {inference_end - inference_start:.4f} seconds.")

            # Calculate probabilities
            probabilities = torch.nn.functional.softmax(output[0], dim=0)  # Calculate probabilities
            logger.info("Probabilities calculated.")

            # Determine the predicted class index
            predicted_class = torch.argmax(probabilities, dim=0).item()
            logger.info(f"Predicted class index: {predicted_class}")

        # Map the predicted class index to the corresponding category
        predict_label = categories[predicted_class]
        logger.info(f"Predicted label: {predict_label}")

        # Convert probabilities tensor to list for easier handling
        probabilities = probabilities.cpu().tolist()

        total_time = time.time() - start_time
        logger.info(f"Total prediction time: {total_time:.4f} seconds.")

        # Return the predicted category and probabilities
        return predict_label, probabilities
    except Exception as e:
        logger.error(f"Error during prediction: {e}", exc_info=True)
        raise
