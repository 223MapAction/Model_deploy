# Convolutional Neural Network (CNN) Components

This document provides an overview of the CNN components used in the Map Action project. These components are responsible for preprocessing images, configuring the CNN model, and performing image classification.

## Preprocessing

The preprocessing of images is handled by the `cnn_preprocess.py` file. It defines a function `preprocess_image` that resizes images to 224x224 pixels, converts them to PyTorch tensors, and optionally normalizes them. This preprocessing is tailored for models expecting input images in this format.

## Model Configuration

The CNN model is configured in the `cnn_model.py` file. It defines a function `m_a_model` that initializes and modifies a ResNet50 model for multi-label classification. The model's fully connected layer is adjusted to match the number of tags to predict.

## Image Classification

The image classification process is managed by the `cnn.py` file. It integrates the preprocessing and model components to perform multi-label image classification using the ResNet50 model. The file includes functions to load the model and perform predictions on images, returning the top predictions and their probabilities.

### Key Functions

-   **preprocess_image**:

    -   **Args**: `image` (bytes) - The image data to be processed.
    -   **Returns**: A PyTorch tensor representing the processed image.

-   **m_a_model**:

    -   **Args**: `num_tags` (int) - The number of tags to predict.
    -   **Returns**: A PyTorch model configured for multi-label classification.

-   **predict**:
    -   **Args**: `image` (bytes) - The image data to be classified.
    -   **Returns**: A tuple containing a list of predicted tags and a list of probabilities.

For more detailed information on each component, refer to the respective files in the `app/services/cnn/` directory.
