# app/services/cnn/cnn.py

# app/services/cnn/cnn.py

import os
import torch
from app.services.cnn.cnn_preprocess import preprocess_image
from app.services.cnn.cnn_model import m_a_model
import logging

# Rest of the code remains unchanged

# Set up logging
logger = logging.getLogger(__name__)

def load_model():
    """
    Loads the ResNet50 model with the specified state dictionary.
    
    Returns:
        torch.nn.Module: The loaded ResNet50 model.
    """
    num_classes = 7
    model = m_a_model(num_classes)
    state_dict_path = os.environ.get('MODEL_PATH')

    if not state_dict_path:
        logger.error("MODEL_PATH is not set.")
        raise ValueError("MODEL_PATH is not set.")

    if not os.path.isfile(state_dict_path):
        logger.error(f"Model file not found at {state_dict_path}")
        raise FileNotFoundError(f"Model file not found at {state_dict_path}")

    loaded_state_dict = torch.load(state_dict_path, map_location=torch.device('cpu'))
    try:
        model.load_state_dict(loaded_state_dict)
        logger.info("Model loaded successfully.")
    except Exception as e:
        logger.error(f"Model loading failed: {e}")
        raise e

    return model

# Initialize the model once
model = load_model()

categories = ["Caniveau obstrué", "Déchet dans l'eau", "Déchet solide",
              "Déforestation", "Pollution de l’eau", "Sécheresse", "Sol dégradé"]

def predict(image):
    """
    Performs image classification using a pre-loaded ResNet50 model.
    
    Args:
        image (bytes): The image data in bytes format.
    
    Returns:
        tuple: A tuple containing the predicted category and probabilities.
    """
    model.eval()  # Set model to evaluation mode
    input_data = preprocess_image(image)  # Preprocess the image
    with torch.no_grad():  # Disable gradient computation
        output = model(input_data)  # Forward pass
        probabilities = torch.nn.functional.softmax(output[0], dim=0)  # Compute probabilities
        predicted_class = torch.argmax(probabilities, dim=0).item()  # Get predicted class index
        predict_label = categories[predicted_class]  # Get category name
        return predict_label, probabilities.tolist()
