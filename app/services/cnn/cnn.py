import os
import torch
from ..cnn.cnn_preprocess import preprocess_image
from ..cnn.cnn_model import m_a_model

# Initialize the VGG16 model with batch-normalized weights for 7 classes
num_classes = 7
model = m_a_model(num_classes)

# Load the state dict from a pre-trained model
state_dict_path = os.environ.get('MODEL_PATH')

if not state_dict_path:
    raise ValueError("The MODEL_PATH environment variable is not set.")

if not os.path.isfile(state_dict_path):
    raise FileNotFoundError(f"Model file not found at {state_dict_path}")

loaded_state_dict = torch.load(state_dict_path, map_location=torch.device('cpu'))

# Adjust the model to ensure compatibility with the loaded state dict
model_dict = model.state_dict()
# Exclude the classifier's final layer parameters from the pretrained_dict
pretrained_dict = {k: v for k, v in loaded_state_dict.items()
                  if k in model_dict and not k.startswith('classifier.6')}

# Update the model's state dictionary except the classifier's final layer
model_dict.update(pretrained_dict)
model.load_state_dict(model_dict)

# List of categories for prediction
categories = ["Caniveau obstrué", "Déchet dans l'eau", "Déchet solide",
              "Déforestation", "Pollution de l’eau", "Sécheresse", "Sol dégradé"]

def predict(image):
    """
    Performs image classification using a pre-trained VGG16 model modified for seven specific categories.
    This function processes an input image, applies a pre-trained model, and returns the predicted category and
    probability distribution over all categories.

    Args:
        image (bytes): The image data in bytes format.

    Returns:
        tuple: A tuple containing the predicted category as a string and the probabilities of all categories as a list.
    """
    model.eval()  # Set the model to evaluation mode
    input_data = preprocess_image(image)  # Preprocess the image
    with torch.no_grad():  # Disable gradient calculation
        output = model(input_data)  # Get the model output
        probabilities = torch.nn.functional.softmax(
            output[0], dim=0)  # Calculate probabilities
        # Determine the predicted class
        predicted_class = torch.argmax(probabilities, dim=0)

        predict_label_index = predicted_class.item()
        # Get the category name from the index
        predict_label = categories[predict_label_index]

        # Return the predicted category and probabilities
        return predict_label, probabilities.tolist()
