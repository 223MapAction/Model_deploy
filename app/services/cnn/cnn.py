import os
import torch
from app.services.cnn.cnn_preprocess import preprocess_image
from app.services.cnn.cnn_model import m_a_model
import logging

# Set up logging
logger = logging.getLogger(__name__)

def load_model():
    """
    Loads the ResNet50 model with the specified state dictionary.
    
    Returns:
        torch.nn.Module: The loaded ResNet50 model.
    """
    num_classes = 8
    model = m_a_model(num_tags=num_classes)
    state_dict_path = os.environ.get('MODEL_PATH')

    if not state_dict_path:
        logger.error("MODEL_PATH is not set.")
        raise ValueError("MODEL_PATH is not set.")

    if not os.path.isfile(state_dict_path):
        logger.error(f"Model file not found at {state_dict_path}")
        raise FileNotFoundError(f"Model file not found at {state_dict_path}")

    loaded_state_dict = torch.load(state_dict_path, map_location=torch.device('cpu'))
    
    # Adjust state_dict keys to match the model architecture
    adjusted_state_dict = {}
    for key, value in loaded_state_dict.items():
        if key.startswith('fc.'):
            new_key = 'fc.0.' + key[3:]  # Corrected slicing and added period
            adjusted_state_dict[new_key] = value
        else:
            adjusted_state_dict[key] = value


    try:
        model.load_state_dict(adjusted_state_dict)
        logger.info("Model loaded successfully.")
    except Exception as e:
        logger.error(f"Model loading failed: {e}")
        raise e

    return model

# Initialize the model once
model = load_model()

tags = ["Caniveau obstrué", "Déchets", "Déforestation",
        "Feux de brousse", "Pollution de leau", "Pollution de lair", "Sécheresse", "Sol dégradé"]

def predict(image):
    """
    Performs multi-label image classification using a pre-loaded ResNet50 model.
    
    Args:
        image (bytes): The image data in bytes format.
    
    Returns:
        tuple: A tuple containing a list of predicted tags and a list of probabilities.
    """
    model.eval()  # Set model to evaluation mode
    input_data = preprocess_image(image)  # Preprocess the image
    with torch.no_grad():  # Disable gradient computation
        output = model(input_data)  # Forward pass
        probabilities = torch.sigmoid(output[0])  # Apply sigmoid to get probabilities
        predictions = (probabilities > 0.5).float()  # Threshold predictions
        
        results = []
        for i, (prob, pred) in enumerate(zip(probabilities, predictions)):
            if pred.item() == 1:
                results.append((tags[i], prob.item()))
        
        # Return both the predictions and the raw probabilities
        return results, probabilities.tolist()
