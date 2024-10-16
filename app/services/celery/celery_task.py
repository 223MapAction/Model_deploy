# app/services/celery/celery_task.py

from app.services.celery.celery_config import celery_app
from app.services.cnn import predict
from app.services.llm import get_response
from app.services.analysis import analyze_vegetation_and_water, analyze_land_cover, generate_ndvi_ndwi_plot, generate_ndvi_heatmap, generate_landcover_plot
from app.services.llm import generate_satellite_analysis
import ee
import logging
import locale
from datetime import datetime, timedelta
import os

def initialize_earth_engine():
    """
    Initialize Earth Engine with service account credentials.
    """
    try:
        credentials = ee.ServiceAccountCredentials(
            email=os.environ['GEE_SERVICE_ACCOUNT_EMAIL'],
            key_file=os.environ['GEE_SERVICE_ACCOUNT_KEY_FILE']
        )
        ee.Initialize(credentials)
        logging.info("Earth Engine initialized successfully.")
    except Exception as e:
        logging.error(f"Failed to initialize Earth Engine: {str(e)}")
        raise
    
initialize_earth_engine()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Try to set locale to French
try:
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
except locale.Error:
    pass

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
        tuple: A tuple containing analysis and piste_solution, both formatted in markdown.
    """
    try:
        logger.info("Starting contextual information task.")
        system_message = f"""
        <system>
            <role>assistant AI</role>
            <task>analyse des incidents environnementaux avec formatage markdown</task>
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
                <instruction>Formatez la réponse en utilisant la syntaxe markdown appropriée.</instruction>
            </instructions>
            <response_formatting>
                <formatting_rule>Utilisez '**' pour les titres principaux ex: **Titre**.</formatting_rule>
                <formatting_rule>Utilisez '***texte***' pour mettre en gras et en italique les chiffres, pourcentages ex: ***100***.</formatting_rule>
                <formatting_rule>Utilisez '- ' au début d'une ligne pour les listes à puces.</formatting_rule>
                <formatting_rule>Laissez une ligne vide entre chaque paragraphe pour bien espacer le contenu.</formatting_rule>
                <formatting_rule>Structurez la réponse en sections claires avec des titres appropriés.</formatting_rule>
                <formatting_rule>Commencez par le problème principal dans la zone spécifiée, puis énoncez les solutions proposées ou les impacts analysés.</formatting_rule>
                <formatting_rule>Utilisez des mots simples et clairs, évitez le jargon technique inutile.</formatting_rule>
                <formatting_rule>Donnez des informations essentielles en utilisant un langage direct et précis.</formatting_rule>
                <formatting_rule>Si une recommandation est faite, assurez-vous qu'elle est faisable et contextualisée pour la zone en question.</formatting_rule>
            </response_formatting>
            <examples>
                <example>
                    <prompt>Analysez l'impact de la pollution de l'eau sur les infrastructures locales dans la région de Bamako.</prompt>
                    <response>
** Impact de la pollution de l'eau à Bamako **

La pollution de l'eau dans la région de Bamako affecte directement les infrastructures locales, notamment les systèmes d'approvisionnement en eau potable. Les conséquences principales sont :

- ***Contamination des sources d'eau*** par des rejets industriels non contrôlés
- ***Coûts supplémentaires*** pour le traitement de l'eau
- ***Risques sanitaires*** accrus pour les habitants

** Impacts sur les infrastructures sensibles **

- ***Écoles et hôpitaux*** : Dépendance à l'eau contaminée, nécessitant une intervention rapide
- ***Systèmes de distribution*** : Détérioration accélérée due aux polluants

Une action immédiate est nécessaire pour éviter des conséquences sanitaires graves et des coûts à long terme pour la municipalité.
                    </response>
                </example>
            </examples>
        </system>
        """

        solution_prompt = f"""
        <system>
            <role>assistant AI</role>
            <task>recommandations de solutions pour des incidents environnementaux avec formatage markdown</task>
            <incident>
                <type>{prediction}</type>
                <zone>{zone}</zone>
                <sensitive_structures>{', '.join(sensitive_structures)}</sensitive_structures>
            </incident>
            <instructions>
                <instruction>Recommandez des solutions spécifiques en tenant compte du type de terrain, des infrastructures à proximité, et des écosystèmes sensibles dans la zone spécifiée.</instruction>
                <instruction>Proposez des mesures préventives et curatives adaptées à la zone pour éviter que le problème ne se reproduise.</instruction>
                <instruction>Suggérez des collaborations entre les autorités locales, les ONG, et les entreprises pour mettre en œuvre les solutions dans la zone concernée.</instruction>
                <instruction>Formatez la réponse en utilisant la syntaxe markdown appropriée.</instruction>
            </instructions>
            <response_formatting>
                <formatting_rule>Utilisez '**' suivi d'un espace pour les titres principaux.</formatting_rule>
                <formatting_rule>Utilisez '***texte***' pour mettre en gras et en italique les chiffres, pourcentages et termes clés.</formatting_rule>
                <formatting_rule>Utilisez '- ' au début d'une ligne pour les listes à puces.</formatting_rule>
                <formatting_rule>Laissez une ligne vide entre chaque paragraphe pour bien espacer le contenu.</formatting_rule>
                <formatting_rule>Structurez la réponse en sections claires avec des titres appropriés.</formatting_rule>
                <formatting_rule>Commencez par la solution la plus immédiate et pertinente pour la zone spécifiée.</formatting_rule>
                <formatting_rule>Utilisez des mots simples et clairs, évitez le jargon technique inutile.</formatting_rule>
            </response_formatting>
            <examples>
                <example>
                    <prompt>Quelles sont les mesures préventives à mettre en place pour éviter la déforestation dans la zone de Sikasso ?</prompt>
                    <response>
** Mesures préventives contre la déforestation à Sikasso **

** Renforcement des politiques forestières **

- Mise en place d'une ***régulation stricte des coupes d'arbres***
- Développement de ***programmes de gestion durable des forêts***

** Sensibilisation et éducation **

- ***Campagnes d'information*** sur l'importance des forêts pour les communautés locales
- Promotion de l'***agroforesterie*** comme alternative durable

** Partenariats et reboisement **

- Collaboration avec des ***ONG spécialisées*** pour des projets de reboisement
- Création de ***pépinières communautaires*** pour la production de jeunes arbres

Ces mesures, adaptées au contexte local de Sikasso, visent à préserver les forêts existantes tout en encourageant des pratiques durables pour l'avenir.
                    </response>
                </example>
            </examples>
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
def analyze_incident_zone(lat, lon, incident_location, incident_type, start_date, end_date) -> dict:
    """
    Analyze the incident zone using satellite data.

    Returns:
    dict: A dictionary containing analysis results and plot data.
    """
    logging.info(f"Analyzing incident zone for {incident_type} at {incident_location}")
    
    # Create Earth Engine point and buffered area
    point = ee.Geometry.Point([lon, lat])
    buffered_point = point.buffer(500)  # 500-meter buffer

    # Convert dates to datetime objects
    start_date = datetime.strptime(start_date, '%Y%m%d')
    end_date = datetime.strptime(end_date, '%Y%m%d')

    # Perform satellite data analysis
    ndvi_data, ndwi_data = analyze_vegetation_and_water(point, buffered_point, start_date, end_date)
    landcover_data = analyze_land_cover(buffered_point)

    # Generate plots
    ndvi_ndwi_plot = generate_ndvi_ndwi_plot(ndvi_data, ndwi_data)
    ndvi_heatmap = generate_ndvi_heatmap(ndvi_data)
    landcover_plot = generate_landcover_plot(landcover_data)

    # Generate textual analysis using the new LLM function
    textual_analysis = generate_satellite_analysis(ndvi_data, ndwi_data, landcover_data, incident_type)

    # Prepare return dictionary
    result = {
        'textual_analysis': textual_analysis,
        'ndvi_ndwi_plot': ndvi_ndwi_plot,
        'ndvi_heatmap': ndvi_heatmap,
        'landcover_plot': landcover_plot,
        'raw_data': {
            'ndvi': ndvi_data.to_dict(),
            'ndwi': ndwi_data.to_dict(),
            'landcover': landcover_data
        }
    }

    return result

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
