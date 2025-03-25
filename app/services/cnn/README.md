# Environmental Issue Detection Service

This service provides environmental issue detection from images using OpenAI's GPT-4o mini vision model.

## Overview

The service analyzes images to detect the following environmental issues:

-   Caniveau obstrué (Blocked drain/gutter)
-   Déchets (Waste)
-   Déforestation (Deforestation)
-   Feux de brousse (Bush fires)
-   Pollution de l'eau (Water pollution)
-   Pollution de l'air (Air pollution)
-   Sécheresse (Drought)
-   Sol dégradé (Degraded soil)

## Requirements

-   Python 3.8+
-   OpenAI Python SDK
-   Pydantic
-   Pillow (PIL)

## Environment Variables

The following environment variables are required:

-   `OPENAI_API_KEY`: Your OpenAI API key for accessing the GPT-4o mini API

## Usage

```python
from app.services.cnn import predict, predict_structured, PredictionResult

# Basic prediction
image_bytes = open("path/to/image.jpg", "rb").read()
top_predictions, all_probabilities = predict(image_bytes)

# Structured prediction with Pydantic model
prediction_result: PredictionResult = predict_structured(image_bytes)

# Access the top predictions
for pred in prediction_result.top_predictions:
    print(f"Tag: {pred.tag}, Probability: {pred.probability}")
```

## Implementation Notes

This implementation uses OpenAI's GPT-4o mini model for vision tasks. The model is provided with a prompt that asks it to identify environmental issues in the image and return a JSON response with detected issues and probability scores.

The service is designed to match the output format of the previous CNN-based implementation to maintain backward compatibility.
