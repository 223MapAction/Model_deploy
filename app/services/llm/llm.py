import os
import json
from openai import OpenAI
import logging

# Initialize logging
logger = logging.getLogger(__name__)

# Initialize the OpenAI client with an API key from environment variables
client = OpenAI(
    api_key=os.getenv("OPENAI_KEY"),  # Retrieves the API key from the "OPENAI_KEY" environment variable
)

# Initial message from the assistant in the chat history
messages = [{"role": "assistant", "content": "How can I help?"}]

def display_chat_history(messages):
    """
    Prints the chat history to the console. Each message is displayed with the sender's role and content.

    Args:
        messages (list of dict): A list of dictionaries where each dictionary represents a message in the chat history.
                                 Each message has a 'role' key indicating who sent the message and a 'content' key with the message text.
    """
    for message in messages:
        print(f"{message['role'].capitalize()}: {message['content']}")

def get_assistant_response(messages):
    """
    Sends the current chat history to the OpenAI API to generate a response from the assistant using GPT-4o-mini via the Responses API.

    Args:
        messages (list of dict): The current chat history as a list of message dictionaries.
                                 Assumes the first message might be a system prompt.

    Returns:
        str: The assistant's response as a string.

    Raises:
        Exception: Prints an error message if the API call fails and returns a default error response.
    """
    system_prompt = None
    api_input = []

    # Separate system prompt and build input list
    for m in messages:
        if m["role"] == "system":
            system_prompt = m["content"]
        else:
            # Use 'output_text' for assistant, 'input_text' for user, based on error message
            content_type = "output_text" if m["role"] == "assistant" else "input_text"
            api_input.append({
                "role": m["role"],
                "content": [{"type": content_type, "text": m["content"]}]
            })

    try:
        # Prepare parameters for the API call
        response_params = {
            "model": "gpt-4o-mini",
            "input": api_input,
            "temperature": 0.5,
            "max_output_tokens": 1080,
            "top_p": 0.8,
            "text": {"format": {"type": "text"}},
            "reasoning": {},
            "tools": [],
            "store": True
        }
        # Add instructions parameter if a system prompt exists
        if system_prompt:
            response_params["instructions"] = system_prompt

        # Call the Responses API
        r = client.responses.create(**response_params)
        
        # Parse the response
        response = r.output[0].content[0].text
        return response
        
    except Exception as e:
        # Log the specific error type and message
        logger.error(f"OpenAI API call failed in get_assistant_response.")
        logger.exception(e)
        return "Sorry, I can't process your request right now."

def get_response(prompt: str):
    """
    Processes a user's prompt to generate and display the assistant's response using GPT-4o-mini.

    Args:
        prompt (str): The user's message to which the assistant should respond.

    Returns:
        str: The assistant's response, which is also added to the chat history and displayed along with the rest of the conversation.
    """
    # Add the user's message to the chat history
    messages.append({"role": "user", "content": prompt})

    # Get the assistant's response and add it to the chat history
    response = get_assistant_response(messages)
    messages.append({"role": "assistant", "content": response})

    # Display the updated chat history
    display_chat_history(messages)

    return response


import json

def chat_response(prompt: str, context: str = "", chat_history: list = [], impact_area: str = "Non spécifié"):
    """
    Processes a user's prompt to generate the assistant's response using GPT-4o-mini,
    strictly focusing on the provided environmental incident context.
    """
    context_obj = json.loads(context)
    incident_type = context_obj.get('type_incident', 'Inconnu')
    analysis = context_obj.get('analysis', 'Non spécifié')
    piste_solution = context_obj.get('piste_solution', 'Non spécifié')
    # impact_summary = context_obj.get('impact_summary', 'Non spécifié') # Removed as it's not fetched/passed

    # --- Modified System Prompt ---
    system_prompt_content = f"""
    <system>
        <role>Spécialiste IA d'analyse d'incidents environnementaux pour Map Action</role>
        <objective>Votre unique objectif est d'analyser et de discuter de l'incident environnemental spécifique fourni dans le contexte. Ne déviez PAS de ce sujet.</objective>

        <context_incident>
            <type_incident>{incident_type}</type_incident>
            <analyse_initiale>{analysis}</analyse_initiale>
            <pistes_solution_initiales>{piste_solution}</pistes_solution_initiales>
            <zone_impact>{impact_area}</zone_impact>
        </context_incident>

        <instructions>
            <instruction>**MISSION PRINCIPALE** : Répondez aux questions de l'utilisateur EN VOUS BASANT STRICTEMENT sur le <context_incident> fourni. Utilisez les détails (type, analyse, solutions, zone) pour formuler vos réponses.</instruction>
            <instruction>**FOCALISATION** : Concentrez-vous UNIQUEMENT sur l'incident '{incident_type}'. Ne discutez pas d'autres sujets.</instruction>
            <instruction>**GESTION DES QUESTIONS GÉNÉRIQUES** : Si l'utilisateur pose des questions sur votre identité ("Qui es-tu?", "Que peux-tu faire?") ou des questions hors sujet, répondez très brièvement que vous êtes un assistant focalisé sur l'incident actuel et réorientez immédiatement la conversation vers l'incident '{incident_type}'. Par exemple: "Je suis une IA dédiée à l'analyse de l'incident actuel ({incident_type}). Comment puis-je vous aider concernant cet incident spécifique ?"</instruction>
            <instruction>**TON ET STYLE** : Soyez factuel, concis et orienté solution. Évitez les salutations génériques répétitives.</instruction>
            <instruction>Si la question dépasse le contexte fourni, mentionnez que l'information n'est pas disponible dans le contexte actuel de l'incident '{incident_type}'.</instruction>
            <instruction>Ne spéculez pas au-delà des informations fournies.</instruction>
            <response_formatting>
                <formatting_rule>Répondez de manière concise (2-3 phrases idéalement).</formatting_rule>
                <formatting_rule>Utilisez des mots simples et clairs.</formatting_rule>
                <formatting_rule>Donnez des informations essentielles en langage direct.</formatting_rule>
            </response_formatting>
        </instructions>

        <example_handling_generic_query>
            <user_prompt>Que peux-tu faire ?</user_prompt>
            <assistant_response>Je suis une IA spécialisée dans l'analyse de l'incident '{incident_type}'. Avez-vous des questions spécifiques sur l'analyse, les solutions proposées ou l'impact dans la zone de '{impact_area}' ?</assistant_response>
        </example_handling_generic_query>

    </system>
    """
    # --- End of Modified System Prompt ---


    # ... (Build api_input list - remains the same) ...
    api_input = []
    # Add chat history
    for msg in chat_history:
        content_type = "output_text" if msg["role"] == "assistant" else "input_text"
        api_input.append({"role": msg["role"], "content": [{"type": content_type, "text": msg["content"]}]})
    # Add current user prompt
    api_input.append({"role": "user", "content": [{"type": "input_text", "text": prompt}]})

    try:
        # ... (Prepare response_params - remains the same) ...
        response_params = {
            "model": "gpt-4o-mini",
            "input": api_input,
            "instructions": system_prompt_content, # Pass system prompt via instructions
            "temperature": 0.5, # Lower temperature might help stay on topic
            "max_output_tokens": 500, # Reduced max tokens slightly, chat doesn't need huge responses
            "top_p": 0.8,
             "text":{
                "format": {
                    "type": "text"
                }
            },
            "reasoning":{},
            "tools":[],
            "store":True
        }

        # Call the API
        response = client.responses.create(**response_params)

        # Parse response
        assistant_response = response.output[0].content[0].text
        return assistant_response

    except Exception as e:
        # Use logger instead of print for consistency
        logger.error(f"OpenAI API call failed in chat_response.")
        logger.exception(e)
        return "Désolé, je ne peux pas traiter votre demande pour le moment." # Keep French error message

def generate_satellite_analysis(ndvi_data, ndwi_data, landcover_data, incident_type):
    """
    Generate a detailed analysis of satellite data for environmental incidents using LLM,
    with proper markdown formatting.

    Args:
        ndvi_data (pd.DataFrame): DataFrame containing NDVI data
        ndwi_data (pd.DataFrame): DataFrame containing NDWI data
        landcover_data (dict): Dictionary containing land cover data
        incident_type (str): Type of environmental incident

    Returns:
        str: Detailed analysis of the satellite data, formatted in markdown
    """
    # Prepare the context
    context = {
        "type_incident": incident_type,
        "ndvi_mean": ndvi_data['NDVI'].mean(),
        "ndvi_trend": 'augmentation' if ndvi_data['NDVI'].iloc[-1] > ndvi_data['NDVI'].iloc[0] else 'diminution',
        "ndwi_mean": ndwi_data['NDWI'].mean(),
        "ndwi_trend": 'augmentation' if ndwi_data['NDWI'].iloc[-1] > ndwi_data['NDWI'].iloc[0] else 'diminution',
        "dominant_cover": max(landcover_data, key=landcover_data.get),
        "dominant_cover_percentage": landcover_data[max(landcover_data, key=landcover_data.get)] / sum(landcover_data.values()) * 100
    }

    # System prompt content remains the same
    system_prompt_content = f"""\n    <system>\n        <role>assistant AI spécialisé en analyse environnementale</role>\n        <task>analyse des données satellitaires pour incidents environnementaux avec formatage markdown</task>\n        <incident>\n            <type>{context['type_incident']}</type>\n            <ndvi_data>\n                <mean>{context['ndvi_mean']:.2f}</mean>\n                <trend>{context['ndvi_trend']}</trend>\n            </ndvi_data>\n            <ndwi_data>\n                <mean>{context['ndwi_mean']:.2f}</mean>\n                <trend>{context['ndwi_trend']}</trend>\n            </ndwi_data>\n            <landcover>\n                <dominant>{context['dominant_cover']}</dominant>\n                <percentage>{context['dominant_cover_percentage']:.1f}%</percentage>\n            </landcover>\n        </incident>\n        <instructions>\n            <instruction>Analysez les données satellitaires fournies pour l'incident environnemental spécifié.</instruction>\n            <instruction>Interprétez les tendances NDVI et NDWI en relation avec le type d'incident.</instruction>\n            <instruction>Expliquez l'importance de la couverture terrestre dominante dans le contexte de l'incident.</instruction>\n            <instruction>Fournissez des insights sur les implications potentielles pour l'environnement local.</instruction>\n            <instruction>Suggérez des pistes de solution ou des recommandations basées sur l'analyse.</instruction>\n            <instruction>Formatez la réponse en utilisant la syntaxe markdown appropriée.</instruction>\n        </instructions>\n        <response_formatting>\n            <formatting_rule>Utilisez '**' pour les titres principaux. ex: **Titre**</formatting_rule>\n            <formatting_rule>Utilisez '***texte***' pour mettre en gras et en italique les chiffres, pourcentages. ex: ***100***</formatting_rule>\n            <formatting_rule>Utilisez '- ' au début d'une ligne pour les listes à puces. ex: - item</formatting_rule>\n            <formatting_rule>Laissez une ligne vide entre chaque paragraphe pour bien espacer le contenu.</formatting_rule>\n            <formatting_rule>Structurez la réponse en sections claires avec des titres appropriés.</formatting_rule>\n            <formatting_rule>Utilisez des liens markdown si nécessaire : [texte du lien](URL)</formatting_rule>\n        </response_formatting>\n    </system>\n    """

    user_prompt = f"Analysez les données satellitaires pour l'incident de type '{incident_type}' et fournissez un rapport détaillé formaté en markdown."

    # Build the input list for the Responses API, only user message needed here
    api_input = [
        {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]}
    ]

    try:
        # Prepare parameters
        response_params = {
            "model": "gpt-4o-mini",
            "input": api_input,
            "instructions": system_prompt_content, # Pass system prompt via instructions
            "temperature": 0.7,
            "max_output_tokens": 2000,
            "top_p": 0.9,
            "text": {"format": {"type": "text"}},
            "reasoning": {},
            "tools": [],
            "store": True
        }
        
        # Call the API
        response = client.responses.create(**response_params)

        # Parse response
        analysis = response.output[0].content[0].text
        return analysis

    except Exception as e:
        print(f"An error occurred while generating satellite data analysis: {e}")
        return "Désolé, une erreur s'est produite lors de l'analyse des données satellitaires."
