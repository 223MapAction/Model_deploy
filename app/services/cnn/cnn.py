import os
import torch
import torch.nn as nn
from ..cnn.cnn_preprocess import preprocess_image
from ..cnn.cnn_model import m_a_model

# Initialize the VGG16 model with batch-normalized weights for 7 classes
model = m_a_model(7)

# Load the state dict from a pre-trained model
state_dict_path = os.environ.get('MODEL_PATH')

if not os.path.isfile(state_dict_path):
    raise FileNotFoundError(f"Model file not found at {state_dict_path}")

loaded_state_dict = torch.load(state_dict_path)

# Adjust the model to ensure compatibility with the loaded state dict
model_dict = model.state_dict()
pretrained_dict = {k: v for k, v in loaded_state_dict.items(
) if k in model_dict and 'classifier.7' not in k}

# Update the model's state dictionary except the classifier's final layer
model_dict.update(pretrained_dict)
model.load_state_dict(model_dict)

# Modify the classifier to match the number of classes (7 in this case)
num_classes = 7
model.classifier[7] = nn.Linear(model.classifier[7].in_features, num_classes)

# List of categories for prediction
categories = ["Caniveau obstrué", "Déchet dans l'eau", "Déchet solide",
              "Déforestation", "Pollution de l’eau", "Sécheresse", "Sol dégradé"]


def predict(image):
    """
    Performs image classification using a pre-trained VGG16 model modified for six specific categories.
    This function processes an input image, applies a pre-trained model, and returns the predicted category and
    probability distribution over all categories.

    Args:
        image (bytes): The image data in bytes format.

    Returns:
        tuple: A tuple containing the predicted category as a string and the probabilities of all categories as a tensor.
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
        predict_label = categories[int(predict_label_index)]

        # Return the predicted category and probabilities
        return predict_label, probabilities.tolist()