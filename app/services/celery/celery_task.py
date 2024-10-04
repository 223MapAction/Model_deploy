# from .celery_config import celery_app
# from ..cnn import predict  # Ensure these are adapted to work as standalone functions
# from ..llm import get_response
# import logging

# Correct import in celery_task.py
from app.services.celery.celery_config import celery_app
from app.services.cnn import predict
from app.services.llm import get_response
import logging


# Set up logging
logger = logging.getLogger(__name__)

@celery_app.task
def perform_prediction(image):
    """
    A Celery task that performs image prediction using a convolutional neural network.
    This function processes an image to predict its content and calculate the probabilities of different classifications.

    Args:
        image (bytes): The image data in bytes format, ready to be processed by the prediction model.

    Returns:
        tuple: A tuple containing the predicted classification and a list of probabilities associated with each class.
    """
    try:
        prediction, probabilities = predict(image)
        logger.info(f"Prediction: {prediction}, Probabilities: {probabilities}")

        # Ensure `probabilities` is a list
        if isinstance(probabilities, list):
            return prediction, probabilities
        else:
            return prediction, probabilities.tolist()

    except Exception as e:
        logger.error(f"Prediction task failed: {str(e)}")
        return {"error": str(e)}, []

# If async behavior for get_response is needed
import asyncio

# Convert the async task to a synchronous one for Celery
@celery_app.task
def fetch_contextual_information(prediction, sensitive_structures):
    """
    Non-async version for environments where async handling is not required.
    Fetches contextual information, impact, and possible solutions in a tailored manner.
    """
    try:
        # Improved prompts using contextual details
        context_prompt = f"Vous êtes un expert en environnement. Expliquez le contexte et l'importance de {prediction} au Mali en mettant en évidence les différents types de terrains et leurs caractéristiques spécifiques."
        impact_prompt = f"En tant qu'expert en environnement, décrivez les impacts potentiels de {prediction} sur les structures sensibles comme {sensitive_structures} au Mali."
        solution_prompt = f"En tant qu'expert en gestion environnementale, proposez des solutions pratiques et durables pour gérer les impacts de {prediction} au Mali. Incluez des mesures préventives et correctives."

        # Fetching responses from the model
        get_context = get_response(context_prompt)
        impact = get_response(impact_prompt)
        piste_solution = get_response(solution_prompt)

        # Logging the fetched information
        logger.info(f"Context: {get_context}, Impact: {impact}, Solution: {piste_solution}")
        return get_context, impact, piste_solution

    except Exception as e:
        logger.error(f"Contextual information task failed: {str(e)}")
        return {"error": str(e)}, None, None



# Task chaining example for sequential execution:
@celery_app.task
def run_prediction_and_context(image, sensitive_structures):
    """
    Chain the prediction task with the contextual information task.
    """
    prediction, probabilities = perform_prediction(image)

    # Proceed with fetching contextual information only if prediction is successful
    if prediction and not isinstance(prediction, dict):  # Make sure it's not an error dict
        return fetch_contextual_information_sync(prediction, sensitive_structures)
    else:
        logger.error(f"Failed to proceed due to prediction error: {prediction}")
        return {"error": "Prediction failed, unable to fetch contextual information."}
