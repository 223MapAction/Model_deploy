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
def fetch_contextual_information(prediction, sensitive_structures, zone):
    """
    A Celery task that fetches contextual information based on the prediction, sensitive structures, and additional data.

    Args:
        prediction (str): The predicted classification.
        sensitive_structures (list): A list of sensitive structures related to the prediction.
        zone (str): The geographic zone related to the prediction.

    Returns:
        tuple: A tuple containing analysis and piste_solution.
    """
    try:
        logger.info("Starting contextual information task.")
        system_message = f"""
        <system>
            <role>assistant AI</role>
            <task>analyse des incidents environnementaux</task>
            <location>Mali</location>
            <incident>
                <type>{prediction}</type>
                <zone>{zone}</zone>
                <sensitive_structures>{', '.join(sensitive_structures)}</sensitive_structures>
            </incident>
            <instructions>
                <instruction>Analysez la nature du problème et ses conséquences immédiates dans la zone spécifiée.</instruction>
                <instruction>Identifiez les risques spécifiques aux infrastructures locales (routes, hôpitaux, écoles) dans la zone indiquée.</instruction>
                <instruction>Évaluez les conséquences environnementales dans la zone, telles que la pollution, la contamination des eaux, et la perte de biodiversité.</instruction>
                <instruction>Déterminez les acteurs locaux à mobiliser dans la zone pour résoudre ce problème.</instruction>
                <instruction>Évaluez les impacts économiques et sociaux à long terme en tenant compte des caractéristiques spécifiques de la zone.</instruction>
                <response_formatting>
                    <formatting_rule>Répondez de manière concise, mais développez suffisamment pour fournir une analyse complète et précise.</formatting_rule>
                    <formatting_rule>Commencez par le problème principal dans la zone spécifiée, puis énoncez les solutions proposées ou les impacts analysés.</formatting_rule>
                    <formatting_rule>Utilisez des mots simples et clairs, évitez le jargon technique inutile.</formatting_rule>
                    <formatting_rule>Donnez des informations essentielles en utilisant un langage direct et précis.</formatting_rule>
                    <formatting_rule>Si une recommandation est faite, assurez-vous qu'elle est faisable et contextualisée pour la zone en question.</formatting_rule>
                </response_formatting>
            </instructions>
            <examples>
                <example>
                    <prompt>Analysez l'impact de la pollution de l'eau sur les infrastructures locales dans la région de Bamako.</prompt>
                    <response>La pollution de l'eau dans la région de Bamako affecte directement les infrastructures locales, notamment les systèmes d'approvisionnement en eau potable. Les rejets industriels non contrôlés contaminent les sources d'eau, ce qui entraîne des coûts supplémentaires pour le traitement de l'eau et des risques sanitaires pour les habitants. Les écoles et hôpitaux dépendent également de cette eau, rendant nécessaire une intervention rapide pour éviter des conséquences sanitaires graves.</response>
                </example>
                <example>
                    <prompt>Quels sont les risques pour la biodiversité dans la zone touchée par la déforestation ?</prompt>
                    <response>La déforestation dans cette zone entraîne une perte significative d'habitats pour de nombreuses espèces, ce qui réduit la biodiversité locale. Les espèces animales, en particulier celles qui dépendent des forêts pour se nourrir et se reproduire, sont menacées. De plus, la perte de végétation perturbe les écosystèmes environnants, augmentant l'érosion des sols et diminuant la capacité de régénération de la flore.</response>
                </example>
                <example>
                    <prompt>Quelles seraient les conséquences économiques de la pollution de l'air dans cette région ?</prompt>
                    <response>La pollution de l'air dans cette région a des conséquences économiques importantes, notamment en augmentant les dépenses de santé publique en raison des maladies respiratoires. Les pertes de productivité dues aux absences liées aux problèmes de santé, ainsi que la baisse de l'attractivité touristique, constituent également des impacts économiques négatifs. Pour atténuer ces effets, des mesures de réduction des émissions doivent être rapidement mises en œuvre.</response>
                </example>
            </examples>
        </system>
        """

        solution_prompt = f"""
        <system>
            <role>assistant AI</role>
            <task>recommandations de solutions pour des incidents environnementaux</task>
            <incident>
                <type>{prediction}</type>
                <zone>{zone}</zone>
                <sensitive_structures>{', '.join(sensitive_structures)}</sensitive_structures>
            </incident>
            <instructions>
                <instruction>Recommandez des solutions spécifiques en tenant compte du type de terrain, des infrastructures à proximité, et des écosystèmes sensibles dans la zone spécifiée.</instruction>
                <instruction>Proposez des mesures préventives et curatives adaptées à la zone pour éviter que le problème ne se reproduise.</instruction>
                <instruction>Suggérez des collaborations entre les autorités locales, les ONG, et les entreprises pour mettre en œuvre les solutions dans la zone concernée.</instruction>
                <response_formatting>
                    <formatting_rule>Répondez de manière concise, mais développez suffisamment pour expliquer clairement chaque solution.</formatting_rule>
                    <formatting_rule>Commencez par la solution la plus immédiate et pertinente pour la zone spécifiée.</formatting_rule>
                    <formatting_rule>Utilisez des mots simples et clairs, évitez le jargon technique inutile.</formatting_rule>
                </response_formatting>
                <examples>
                    <example>
                        <prompt>Quelles sont les mesures préventives à mettre en place pour éviter la déforestation dans la zone de Sikasso ?</prompt>
                        <response>Pour éviter la déforestation dans la zone de Sikasso, il est recommandé de renforcer les politiques de gestion durable des forêts, incluant la régulation stricte des coupes d'arbres. La sensibilisation des communautés locales à l'importance des forêts et l'encouragement à l'agroforesterie sont également essentiels. De plus, des partenariats avec des ONG peuvent permettre de reboiser les zones déjà affectées.</response>
                    </example>
                    <example>
                        <prompt>Comment réduire l'impact de la pollution de l'eau sur les écosystèmes locaux de la zone de Mopti ?</prompt>
                        <response>Pour réduire l'impact de la pollution de l'eau dans la zone de Mopti, il est crucial d'installer des stations de traitement des eaux usées dans les zones industrielles. La création de zones tampons végétales le long des cours d'eau peut également limiter la contamination. Une collaboration entre les autorités locales et les industries est nécessaire pour assurer le respect des normes environnementales.</response>
                    </example>
                </examples>
            </instructions>
        </system>
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
