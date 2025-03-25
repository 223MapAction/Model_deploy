import os
import io
import base64
import logging
from typing import List, Tuple, Optional
import json
from PIL import Image
import openai
from app.services.cnn.models import PredictionTag, PredictionResult

# Set up logging
logger = logging.getLogger(__name__)

# Define the environmental issue tags
ENVIRONMENTAL_TAGS = [
    "Caniveau obstrué",  # Blocked drain/gutter
    "Déchets",           # Waste
    "Déforestation",     # Deforestation
    "Feux de brousse",   # Bush fires
    "Pollution de leau", # Water pollution
    "Pollution de lair", # Air pollution
    "Sécheresse",        # Drought
    "Sol dégradé"        # Degraded soil
]

def encode_image_to_base64(image_bytes):
    """Convert image bytes to base64 encoding for OpenAI API."""
    return base64.b64encode(image_bytes).decode('utf-8')

def predict(image_bytes) -> Tuple[List[Tuple[str, float]], List[float]]:
    """
    Performs image classification using OpenAI's GPT-4o mini model.
    
    Args:
        image_bytes (bytes): The image data in bytes format.
    
    Returns:
        tuple: A tuple containing a list of predicted tags and a list of probabilities.
    """
    try:
        # Encode the image to base64
        base64_image = encode_image_to_base64(image_bytes)
        
        # Prepare the prompt for environmental issue classification
        prompt = """
        Analyze this image and identify if it contains any of the following environmental issues:
        
        1. Caniveau obstrué
        2. Déchets
        3. Déforestation
        4. Feux de brousse
        5. Pollution de leau
        6. Pollution de lair 
        7. Sécheresse
        8. Sol dégradé
        
        If none of these environmental issues are present, respond with "Aucun problème environnemental" (No environmental problem).
        
        For each identified issue, assign a probability between 0 and 1 indicating your confidence.
        Only return issues with a probability greater than 0.4.
        Limit your response to the top 3 most probable issues.
        
        Format your response as a JSON object with fields:
        - identified_issues: array of objects with "tag" and "probability" fields
        - all_probabilities: array of probability values for all 8 issues in the order listed above
        """
        
        # Call the OpenAI API
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY is not set in the environment")
            raise ValueError("OPENAI_API_KEY is not set. Please set it in your environment.")
            
        client = openai.OpenAI(api_key=api_key)
        response = client.responses.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are an environmental issue detection assistant."},
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}
            ]
        )
        
        # Extract and parse the response
        result = response.content[0].text
        try:
            parsed_result = json.loads(result)
            
            # Extract identified issues
            identified_issues = parsed_result.get("identified_issues", [])
            
            # If "Aucun problème environnemental" is identified, handle it specially
            if not identified_issues or any(issue.get("tag") == "Aucun problème environnemental" for issue in identified_issues):
                # Return a special case for no environmental issues
                all_probs = [0.0] * len(ENVIRONMENTAL_TAGS)
                return [("Aucun problème environnemental", 1.0)], all_probs
            
            # Extract all probabilities or provide zeros if not available
            all_probabilities = parsed_result.get("all_probabilities", [0.0] * len(ENVIRONMENTAL_TAGS))
            
            # Ensure all_probabilities has the correct length
            if len(all_probabilities) != len(ENVIRONMENTAL_TAGS):
                all_probabilities = all_probabilities[:len(ENVIRONMENTAL_TAGS)] + [0.0] * (len(ENVIRONMENTAL_TAGS) - len(all_probabilities))
            
            # Convert to the expected format
            top_predictions = [(issue.get("tag"), issue.get("probability", 0.0)) for issue in identified_issues]
            
            return top_predictions, all_probabilities
            
        except Exception as e:
            logger.error(f"Failed to parse model response: {e}")
            logger.error(f"Raw response: {result}")
            # Return a default response in case of parsing error
            return [("Error in parsing response", 0.0)], [0.0] * len(ENVIRONMENTAL_TAGS)
    
    except Exception as e:
        logger.error(f"Error in OpenAI prediction: {e}")
        # Return a default response in case of error
        return [("Error in prediction", 0.0)], [0.0] * len(ENVIRONMENTAL_TAGS)

def predict_structured(image_bytes) -> PredictionResult:
    """
    Performs image classification using OpenAI's GPT-4o mini model and returns a structured result.
    
    Args:
        image_bytes (bytes): The image data in bytes format.
    
    Returns:
        PredictionResult: A structured prediction result.
    """
    prediction_tuple = predict(image_bytes)
    return PredictionResult.from_prediction_tuple(prediction_tuple) 