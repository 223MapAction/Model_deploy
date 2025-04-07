import os
import json
from openai import OpenAI

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
        print(f"An error occurred: {e}")
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
    with context about the environmental incident.

    Args:
        prompt (str): The user's message to which the assistant should respond.
        context (str): A JSON string containing context about the incident.
        chat_history (list): The existing chat history for this session.
        impact_area (str): The area impacted by the incident.

    Returns:
        str: The assistant's response.

    Examples:
        >>> context = '{"type_incident": "Déforestation", "analysis": "La déforestation affecte la biodiversité locale.", "piste_solution": "Reforestation et éducation communautaire."}'
        >>> prompt = "Quels sont les impacts de la déforestation dans cette zone ?"
        >>> chat_response(prompt, context)
        'La déforestation affecte la biodiversité locale en réduisant les habitats naturels des espèces. Pour remédier à cela, la reforestation et l'éducation communautaire sont des pistes de solution envisageables.'

        >>> context = '{"type_incident": "Pollution de l'eau", "analysis": "Les rejets industriels ont contaminé la rivière.", "piste_solution": "Installation de stations de traitement des eaux."}'
        >>> prompt = "Comment pouvons-nous améliorer la qualité de l'eau ?"
        >>> chat_response(prompt, context)
        'Les rejets industriels ont contaminé la rivière. Pour améliorer la qualité de l'eau, l'installation de stations de traitement des eaux est recommandée.'
    """

    context_obj = json.loads(context)
    incident_type = context_obj.get('type_incident', 'Inconnu')
    analysis = context_obj.get('analysis', 'Non spécifié')
    piste_solution = context_obj.get('piste_solution', 'Non spécifié')
    impact_summary = context_obj.get('impact_summary', 'Non spécifié')

    # System prompt content remains the same
    system_prompt_content = f"""\n    <system>\n        <role>assistant AI</role>
        <task>analyse des incidents environnementaux</task>
        <location>Mali</location>\n        <incident>\n            <type>{incident_type}</type>\n            <analysis>{analysis}</analysis>\n            <solution_tracks>{piste_solution}</solution_tracks>\n            <impact_summary>{impact_summary}</impact_summary>\n        </incident>\n        <instructions>\n            <instruction>Adaptez vos réponses au contexte spécifique de l'incident.</instruction>\n            <instruction>Utilisez les informations de contexte pour enrichir vos explications.</instruction>\n            <instruction>Intégrez les données sur la zone d'impact dans vos analyses lorsque c'est pertinent.</instruction>\n            <instruction>Votre réponse doit clairement mentionner et se focaliser sur le type d'incident spécifique ({incident_type}) fourni dans le contexte.</instruction>\n            <instruction>Si la question dépasse le contexte fourni, mentionnez clairement que vous répondez de manière générale.</instruction>\n            <instruction>Priorisez les réponses concises et orientées sur la résolution du problème.</instruction>\n            <instruction>Ne déviez pas de la tâche principale et évitez les réponses non pertinentes.</instruction>\n            <response_formatting>\n                <formatting_rule>Répondez de manière concise, avec une longueur de réponse idéale de 2 à 3 phrases par section, sauf pour l'analyse d'impact détaillée.</formatting_rule>\n                <formatting_rule>Fournissez une réponse structurée : commencez par le problème principal, suivez avec la solution proposée.</formatting_rule>\n                <formatting_rule>Utilisez des mots simples et clairs, évitez le jargon technique inutile.</formatting_rule>\n                <formatting_rule>Donnez des informations essentielles en utilisant un langage direct et précis.</formatting_rule>\n                <formatting_rule>Si une recommandation est faite, assurez-vous qu'elle est faisable et contextualisée.</formatting_rule>\n            </response_formatting>\n        </instructions>\n        <examples>\n            <example>\n                <prompt>Quels sont les impacts de la déforestation dans cette zone ?</prompt>\n                <response>La déforestation affecte la biodiversité locale en réduisant les habitats naturels des espèces. Pour remédier à cela, la reforestation et l\'éducation communautaire sont des pistes de solution envisageables.</response>\n            </example>\n            <example>\n                <prompt>Quelle est l\'étendue de la zone touchée par cet incident ?</prompt>\n                <response>L\'analyse des données satellitaires montre que la zone impactée par cet incident couvre environ {impact_area} kilomètres carrés. Cette information nous aide à mieux comprendre l\'ampleur du problème et à planifier des interventions appropriées.</response>\n            </example>\n        </examples>\n    </system>\n    """

    # Build the input list for the Responses API, excluding the system message
    api_input = []
    # Add chat history
    for msg in chat_history:
        # Use 'output_text' for assistant, 'input_text' for user
        content_type = "output_text" if msg["role"] == "assistant" else "input_text"
        api_input.append({"role": msg["role"], "content": [{"type": content_type, "text": msg["content"]}]})
    # Add current user prompt
    api_input.append({"role": "user", "content": [{"type": "input_text", "text": prompt}]})

    try:
        # Prepare parameters
        response_params = {
            "model": "gpt-4o-mini",
            "input": api_input,
            "instructions": system_prompt_content, # Pass system prompt via instructions
            "temperature": 0.5,
            "max_output_tokens": 1080,
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
        print(f"An error occurred: {e}")
        return "Désolé, je ne peux pas traiter votre demande pour le moment."

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
