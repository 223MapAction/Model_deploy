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
    Performs multi-label image classification using a preloaded ResNet50 model.
    
    Args:
        image (bytes): The image data in bytes format.
    
    Returns:
        tuple: A tuple containing a list of predicted tags and a list of probabilities.
    """
    model.eval()  # Set model to evaluation mode to disable dropout and batch normalization layers.
    input_data = preprocess_image(image)   # Preprocess the image to the format required by the model.

    # Disable gradient computation to reduce memory usage and speed up computations during inference.
    with torch.no_grad():
        output = model(input_data)  # Perform a forward pass through the model to get the raw output.
        probabilities = torch.sigmoid(output[0])  # Apply sigmoid activation to get probabilities for each tag.

        # The probabilities represent the likelihood of each tag being associated with the input image.
        # A value closer to 1 indicates a higher confidence that the tag applies to the image.

        # Filter out predictions with probability less than 0.4 and sort the rest in descending order.
        top_predictions = [(tags[i], prob.item()) for i, prob in enumerate(probabilities) if prob.item() > 0.4]
        top_predictions.sort(key=lambda x: x[1], reverse=True) # Sort predictions by probability in descending order.
        top_predictions = top_predictions[:3] # Get the top 3 predictions based on probability.

        # Return both the top predictions and the raw probabilities for all tags.
        return top_predictions, probabilities.tolist()

