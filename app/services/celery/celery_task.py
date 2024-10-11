# app/services/celery/celery_task.py

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
        logger.info("Starting prediction task.")
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

@celery_app.task
def fetch_contextual_information(prediction, sensitive_structures, data):
    """
    A Celery task that fetches contextual information based on the prediction, sensitive structures, and additional data.

    Args:
        prediction (str): The predicted classification.
        sensitive_structures (list): A list of sensitive structures related to the prediction.
        data (object): An object containing additional context information.

    Returns:
        tuple: A tuple containing analysis and piste_solution.
    """
    try:
        logger.info("Starting contextual information task.")
        system_message = f"""
        Vous êtes un assistant AI spécialisé dans l'analyse des incidents environnementaux au Mali.
        Voici le contexte détaillé de l'incident actuel:
        - Type d'incident: {prediction}
        - Contexte géographique: {data.zone}
        - Infrastructures locales à risque: (à prendre dans) {sensitive_structures}
        - Écosystèmes sensibles à proximité: (à prendre dans) {sensitive_structures}
        - Impact potentiel sur les habitants: à analyser
        
        Analyse détaillée:
        - Quelle est la nature du problème et ses conséquences immédiates ?
        - Quels sont les risques pour les infrastructures locales (routes, hôpitaux, écoles) ?
        - Quelles seraient les conséquences environnementales (pollution, contamination des eaux, perte de biodiversité) ?
        - Quels acteurs locaux devraient être mobilisés pour résoudre ce problème ?
        - Quels sont les impacts économiques et sociaux à long terme ?
        """

        solution_prompt = f"""
        Pistes de solution:
        - Recommandez des solutions **spécifiques** en tenant compte du type de terrain, des infrastructures à proximité et des écosystèmes sensibles.
        - Proposez des mesures préventives et curatives pour éviter que le problème ne se reproduise.
        - Suggérez des collaborations entre les autorités locales, les ONG, et les entreprises pour mettre en œuvre les solutions.
        """

        # Fetching responses from the model
        analysis = get_response(system_message)
        piste_solution = get_response(solution_prompt)

        logger.info(f"Analysis: {analysis}, Solution: {piste_solution}")
        return analysis, piste_solution

    except Exception as e:
        logger.error(f"Contextual information task failed: {str(e)}")
        return {"error": str(e)}, None

@celery_app.task
def run_prediction_and_context(image, sensitive_structures):
    """
    Chain the prediction task with the contextual information task.
    """
    try:
        logger.info("Starting chained task: run_prediction_and_context.")
        prediction, probabilities = perform_prediction(image)
        
        # Proceed with fetching contextual information only if prediction is successful
        if prediction and not isinstance(prediction, dict):  # Ensure it's not an error dict
            context_info = fetch_contextual_information.delay(prediction, sensitive_structures)
            return context_info.get(timeout=120)
        else:
            logger.error(f"Failed to proceed due to prediction error: {prediction}")
            return {"error": "Prediction failed, unable to fetch contextual information."}
    except Exception as e:
        logger.error(f"Chained task failed: {e}")
        return {"error": str(e)}
