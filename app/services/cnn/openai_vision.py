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

# Define the environmental issue tags and descriptions
TAGS_WITH_DESCRIPTIONS = {
    "Puits abîmé": "Puits effondré, pompe cassée, borne-fontaine non fonctionnelle",
    "Fosse pleine": "Eaux noires visibles dans la rue ou près des maisons",
    "Latrines bouchées": "Infrastructures sanitaires endommagées ou inutilisables",
    "Eaux stagnantes": "Mares, flaques ou canaux immobiles favorisant les moustiques",
    "Décharge illégale": "Accumulation visible de déchets dans un espace non autorisé",
    "Déchets biomédicaux": "Sacs médicaux, seringues ou équipements jetés à l'air libre",
    "Plastiques épars": "Sachets, bouteilles, bidons dans la nature",
    "Feu déchets": "Brûlage à ciel ouvert de détritus",
    "Ordures non collectées": "Poubelles non ramassées, amas de déchets en attente",
    "Déchets électroniques": "Téléphones, ordinateurs, batteries jetés dans des lieux publics",
    "Arbres coupés": "Troncs fraîchement coupés, zones déboisées illégalement",
    "Feux de brousse": "Fumée, cendres, végétation brûlée",
    "Sol Nu": "Sols nus, sans végétation, sable emporté par le vent",
    "Sol érodé": "Fissures, ravines ou glissements visibles",
    "Fumées industrielles": "Colonnes de fumée provenant de cheminées ou brûlis illégaux",
    "Eaux sales": "Eaux souillées ou mousseuses rejetées dans les cours d'eau ou dans les zones urbaines",
    "Pollution plastique": "Présence massive de plastique dans la nature ou les cours d'eau",
    "Pollution visuelle": "Affiches anarchiques, véhicules abandonnés, murs sales",
    "Inondation": "Rues, champs, maisons submergés par l'eau",
    "Sécheresse": "Terres asséchées, végétation flétrie, fissures visibles",
    "Glissement de terrain": "Sol effondré, routes ou maisons endommagées",
    "Animal mort": "Carcasses de poissons, oiseaux ou autres espèces protégées",
    "Zone humide agréssée": "Assèchement ou remblayage d'une zone végétalisée humide",
    "Espèces invasives": "Plantes ou animaux non natifs envahissant l'espace local",
    "Surpâturage": "Sols appauvris par la surconcentration de troupeaux",
    "Caniveaux bouchés": "Tuyaux visibles, débordements d'eau usée, canaux d'écoulement bouchés ou dégradés",
    "Équipement HS": "Site abandonné ou matériel détérioré",
    "Déversement illégal": "Versement de carburant, d'huile ou de liquides toxiques dans la nature"
}
ENVIRONMENTAL_TAGS = list(TAGS_WITH_DESCRIPTIONS.keys())

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
        prompt_tags_with_desc = "\n".join([f"{i+1}. {tag}: {desc}" for i, (tag, desc) in enumerate(TAGS_WITH_DESCRIPTIONS.items())])
        prompt = f"""
        Analyze this image and identify if it contains any of the following environmental issues. Use the provided descriptions to help your analysis:
        
{prompt_tags_with_desc}
        
        If none of these environmental issues are present, respond with "Aucun problème environnemental" (No environmental problem).
        
        For each identified issue, assign a probability between 0 and 1 indicating your confidence.
        Only return issues with a probability greater than 0.4.
        Limit your response to the top 3 most probable issues.
        
        Format your response as a JSON object with fields:
        - identified_issues: array of objects with "tag" (use the exact tag name provided above) and "probability" fields
        - all_probabilities: array of probability values for all {len(ENVIRONMENTAL_TAGS)} issues in the order listed above
        """
        
        # Call the OpenAI API
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY is not set in the environment")
            raise ValueError("OPENAI_API_KEY is not set. Please set it in your environment.")
            
        client = openai.OpenAI(api_key=api_key)
        response = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_image",
                            "image_url": f"data:image/jpeg;base64,{base64_image}"
                        },
                        {
                            "type": "input_text",
                            "text": prompt
                        }
                    ]
                }
            ],
            text={
                "format": {
                    "type": "text"
                }
            },
            reasoning={},
            tools=[],
            temperature=1,
            max_output_tokens=2048,
            top_p=1,
            store=True
        )
        
        # Extract and parse the response
        # The response structure has the output in response.output[0].content[0].text
        result = response.output[0].content[0].text
        try:
            # Remove any markdown formatting if present (e.g., ```json\n...\n```)
            if result.startswith('```json'):
                result = result[7:-3]  # Remove ```json and ``` markers
            elif result.startswith('```'):
                result = result[3:-3]  # Remove ``` markers
                
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