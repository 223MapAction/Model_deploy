# app/services/celery/celery_task.py

import logging
import locale
from datetime import datetime, timedelta
import os
import base64
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.services.celery.celery_config import celery_app
from app.services.cnn import predict
from app.services.llm import get_response
try:
    from app.services.analysis import analyze_vegetation_and_water, analyze_land_cover, generate_ndvi_ndwi_plot, generate_ndvi_heatmap, generate_landcover_plot
    from app.services.llm import generate_satellite_analysis
    ANALYSIS_AVAILABLE = True
except ImportError:
    logging.warning("Analysis modules could not be imported - satellite analysis features will be disabled")
    ANALYSIS_AVAILABLE = False

try:
    import ee
    EARTH_ENGINE_AVAILABLE = True
except ImportError:
    logging.warning("Earth Engine package not installed - GEE features will be disabled")
    EARTH_ENGINE_AVAILABLE = False

# Try to set locale to French
try:
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
except locale.Error:
    pass

def initialize_earth_engine():
    """
    Initialize Earth Engine with service account credentials.
    """
    # If Earth Engine is not available, skip initialization
    if not EARTH_ENGINE_AVAILABLE:
        logging.warning("Earth Engine package not installed - skipping initialization")
        return
        
    # Skip initialization if SKIP_GEE_INIT environment variable is set (for tests)
    if os.environ.get('SKIP_GEE_INIT', '').lower() == 'true':
        logging.info("Skipping Earth Engine initialization due to SKIP_GEE_INIT flag")
        return
        
    try:
        # Get the key file path from environment
        key_file_path = os.environ.get('GEE_SERVICE_ACCOUNT_KEY_FILE')
        if not key_file_path:
            logging.warning("GEE_SERVICE_ACCOUNT_KEY_FILE environment variable not set, using default path")
            key_file_path = "/tmp/gee_key.json"
        
        # Check if we need to create the key file from environment variable content
        if not os.path.exists(key_file_path):
            logging.info(f"Key file {key_file_path} does not exist, attempting to create it")
            # Ensure directory exists
            os.makedirs(os.path.dirname(key_file_path), exist_ok=True)
            
            # First, check if the key JSON is provided by AWS Secrets Manager
            if 'GEE_KEY_JSON' in os.environ:
                logging.info("Getting GEE credentials from AWS Secrets Manager")
                # AWS Secrets Manager automatically injects the secret value into this env var
                gee_key_json = os.environ['GEE_KEY_JSON']
                with open(key_file_path, 'w') as f:
                    f.write(gee_key_json)
                logging.info(f"Created GEE service account key file from AWS Secrets Manager at {key_file_path}")
            # Fall back to regular environment variable if not found
            elif 'GEE_SERVICE_ACCOUNT_KEY_CONTENT' in os.environ:
                # Use the raw content
                with open(key_file_path, 'w') as f:
                    f.write(os.environ['GEE_SERVICE_ACCOUNT_KEY_CONTENT'])
                logging.info(f"Created GEE service account key file from environment variable at {key_file_path}")
            else:
                logging.warning(f"No GEE service account key content found in environment variables - Earth Engine functionality will be limited")
        
        # Check if the key file exists now
        if not os.path.exists(key_file_path):
            logging.error(f"GEE service account key file does not exist at {key_file_path} and could not be created")
            return
        
        # Check if GEE_SERVICE_ACCOUNT_EMAIL is set
        if 'GEE_SERVICE_ACCOUNT_EMAIL' not in os.environ:
            logging.error("GEE_SERVICE_ACCOUNT_EMAIL environment variable not set")
            return
            
        # Initialize Earth Engine with credentials
        logging.info(f"Initializing Earth Engine with key file {key_file_path} and service account {os.environ['GEE_SERVICE_ACCOUNT_EMAIL']}")
        credentials = ee.ServiceAccountCredentials(
            email=os.environ['GEE_SERVICE_ACCOUNT_EMAIL'],
            key_file=key_file_path
        )
        
        # Retry Earth Engine initialization up to 3 times with exponential backoff
        for attempt in range(3):
            try:
                ee.Initialize(credentials)
                logging.info("Earth Engine initialized successfully.")
                return
            except Exception as e:
                backoff_time = 2 ** attempt
                logging.warning(f"Earth Engine initialization attempt {attempt+1} failed: {str(e)}. Retrying in {backoff_time} seconds...")
                time.sleep(backoff_time)
        
        # If we get here, all retries failed
        logging.error("All Earth Engine initialization attempts failed")
        
    except Exception as e:
        logging.error(f"Failed to initialize Earth Engine: {str(e)}")
        logging.warning("Application will continue without Earth Engine functionality")
    
initialize_earth_engine()

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
            <task>analyse des incidents environnementaux avec formatage markdown, **incluant une évaluation spécifique de l'impact sur les enfants et populations vulnérables**</task>
            <location>Mali</location>
            <incident>
                <type>{prediction}</type>
                <zone>{zone}</zone>
                <sensitive_structures>{', '.join(sensitive_structures)}</sensitive_structures>
            </incident>
            <instructions>
                <instruction>**IMPÉRATIF : Votre analyse DOIT inclure une section spécifique évaluant l'impact de l'incident sur les enfants et les populations vulnérables.**</instruction>
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
                <formatting_rule>**Structure Requise :** Incluez impérativement une section intitulée '**Impact sur les Enfants et Populations Vulnérables**'.</formatting_rule>
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

** Impact sur les Enfants et Populations Vulnérables **

Les enfants sont particulièrement exposés aux risques de maladies hydriques comme la diarrhée et la typhoïde. Les femmes enceintes et les personnes âgées souffrent davantage des effets de la contamination, avec des conséquences potentiellement graves pour leur santé.

Une action immédiate est nécessaire pour éviter des conséquences sanitaires graves et des coûts à long terme pour la municipalité.
                    </response>
                </example>
            </examples>
        </system>
        """

        solution_prompt = f"""
        <system>
            <role>assistant AI</role>
            <task>recommandations de solutions pour des incidents environnementaux avec formatage markdown, **incluant des mesures spécifiques pour protéger les enfants et populations vulnérables**</task>
            <incident>
                <type>{prediction}</type>
                <zone>{zone}</zone>
                <sensitive_structures>{', '.join(sensitive_structures)}</sensitive_structures>
            </incident>
            <instructions>
                <instruction>**IMPÉRATIF : Vos recommandations DOIVENT inclure des mesures spécifiques pour protéger les enfants et les populations vulnérables des impacts de l'incident.**</instruction>
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
                <formatting_rule>**Structure Requise :** Incluez impérativement une section intitulée '**Mesures de Protection pour les Enfants et Populations Vulnérables**'.</formatting_rule>
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

** Mesures de Protection pour les Enfants et Populations Vulnérables **

- Création de ***zones tampons*** autour des écoles et centres de santé pour maintenir la couverture végétale
- Organisation de ***programmes éducatifs*** dans les écoles sur la protection de l'environnement
- Mise en place de ***systèmes d'alerte*** pour prévenir des risques sanitaires liés à la déforestation

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
    # Check if Earth Engine and analysis modules are available
    if not EARTH_ENGINE_AVAILABLE or not ANALYSIS_AVAILABLE:
        logging.warning("Cannot perform satellite analysis as required modules are not available")
        return {
            'error': 'Satellite analysis is not available in this environment',
            'missing_modules': {
                'earth_engine': not EARTH_ENGINE_AVAILABLE,
                'analysis': not ANALYSIS_AVAILABLE
            }
        }
    
    logging.info(f"Analyzing incident zone for {incident_type} at {incident_location}")
    
    try:
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
    except Exception as e:
        logging.error(f"Error during incident zone analysis: {str(e)}")
        return {
            'error': f"Analysis failed: {str(e)}",
            'incident_data': {
                'location': incident_location,
                'type': incident_type,
                'coordinates': [lat, lon],
                'dates': [start_date, end_date]
            }
        }
