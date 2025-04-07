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

    Returns:
        str: The assistant's response as a string.

    Raises:
        Exception: Prints an error message if the API call fails and returns a default error response.
    """
    try:
        # Map messages to the 'input' format for the Responses API
        # Assuming the API accepts roles similar to chat completions within the input list
        api_input = []
        for m in messages:
             # Simple mapping, might need adjustment based on exact API requirements for roles within input
             # The example uses role: user -> content: [{type: input_text, text: ...}]
             # Let's adapt to a simpler text content structure if possible for general chat
             # Or structure more formally if needed. For now, map directly.
             api_input.append({
                 "role": m["role"],
                 "content": [{"type": "input_text", "text": m["content"]}] # Structure based on vision example
             })

        r = client.responses.create(
            model="gpt-4o-mini",
            input=api_input,
            temperature=1,
            max_output_tokens=1080, # Renamed from max_tokens
            top_p=1,
            # frequency_penalty and presence_penalty might not be direct params, check API docs if needed
            # Using standard params from the vision example
             text={
                "format": {
                    "type": "text"
                }
            },
            reasoning={},
            tools=[],
            store=True # Assuming we want to store responses like in the vision example
        )
        # Update response parsing for the Responses API structure
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

    # Parse the context JSON string to extract details about the incident
    context_obj = json.loads(context)
    incident_type = context_obj.get('type_incident', 'Inconnu')
    analysis = context_obj.get('analysis', 'Non spécifié')
    piste_solution = context_obj.get('piste_solution', 'Non spécifié')
    impact_summary = context_obj.get('impact_summary', 'Non spécifié')

    # Update the system message to include the impact summary
    system_prompt_content = f"""
    <system>
        <role>assistant AI</role>
        <task>analyse des incidents environnementaux</task>
        <location>Mali</location>
        <incident>
            <type>{incident_type}</type>
            <analysis>{analysis}</analysis>
            <solution_tracks>{piste_solution}</solution_tracks>
            <impact_summary>{impact_summary}</impact_summary>
        </incident>
        <instructions>
            <instruction>Adaptez vos réponses au contexte spécifique de l'incident.</instruction>
            <instruction>Utilisez les informations de contexte pour enrichir vos explications.</instruction>
            <instruction>Intégrez les données sur la zone d'impact dans vos analyses lorsque c'est pertinent.</instruction>
            <instruction>Analysez et mentionnez spécifiquement l'impact de l'incident sur les enfants et les populations vulnérables lorsque cela est pertinent.</instruction>
            <instruction>Votre réponse doit clairement mentionner et se focaliser sur le type d'incident spécifique ({incident_type}) fourni dans le contexte.</instruction>
            <instruction>Si la question dépasse le contexte fourni, mentionnez clairement que vous répondez de manière générale.</instruction>
            <instruction>Priorisez les réponses concises et orientées sur la résolution du problème.</instruction>
            <instruction>Ne déviez pas de la tâche principale et évitez les réponses non pertinentes.</instruction>
            <response_formatting>
                <formatting_rule>Répondez de manière concise, avec une longueur de réponse idéale de 2 à 3 phrases.</formatting_rule>
                <formatting_rule>Fournissez une réponse structurée : commencez par le problème principal, suivez avec la solution proposée.</formatting_rule>
                <formatting_rule>Utilisez des mots simples et clairs, évitez le jargon technique inutile.</formatting_rule>
                <formatting_rule>Donnez des informations essentielles en utilisant un langage direct et précis.</formatting_rule>
                <formatting_rule>Si une recommandation est faite, assurez-vous qu'elle est faisable et contextualisée.</formatting_rule>
            </response_formatting>
        </instructions>
        <examples>
            <example>
                <prompt>Quels sont les impacts de la déforestation dans cette zone ?</prompt>
                <response>La déforestation affecte la biodiversité locale en réduisant les habitats naturels des espèces. Pour remédier à cela, la reforestation et l'éducation communautaire sont des pistes de solution envisageables.</response>
            </example>
            <example>
                <prompt>Comment pouvons-nous améliorer la qualité de l'eau ?</prompt>
                <response>Les rejets industriels ont contaminé la rivière. Pour améliorer la qualité de l'eau, l'installation de stations de traitement des eaux est recommandée.</response>
            </example>
            <example>
                <prompt>Que peut-on faire pour limiter l'érosion des sols dans cette région ?</prompt>
                <response>L'érosion des sols est exacerbée par la déforestation et les pratiques agricoles non durables. Pour limiter l'érosion, il est recommandé de pratiquer l'agroforesterie, de planter des haies pour protéger les sols, et de promouvoir des techniques agricoles conservatrices.</response>
            </example>
            <example>
                <prompt>Quelles sont les conséquences de la pollution de l'air sur la santé publique ici ?</prompt>
                <response>La pollution de l'air, principalement due aux émissions industrielles et à la combustion de biomasse, a des effets négatifs sur la santé publique, notamment des problèmes respiratoires et cardiovasculaires. Pour atténuer ces impacts, il est essentiel de réduire les sources d'émissions et de promouvoir des énergies plus propres.</response>
            </example>
            <example>
                <prompt>Comment réduire l'impact de la pollution plastique sur l'environnement local ?</prompt>
                <response>La pollution plastique peut être réduite en mettant en place des systèmes de collecte et de recyclage des déchets, en sensibilisant la population à la réduction de l'utilisation du plastique, et en favorisant des alternatives biodégradables.</response>
            </example>
            <example>
                <prompt>Quelles mesures peuvent être prises pour protéger la faune menacée dans cette région ?</prompt>
                <response>Pour protéger la faune menacée, il est crucial de créer des zones protégées, de lutter contre le braconnage, et de promouvoir des pratiques agricoles respectueuses de l'environnement qui minimisent la destruction des habitats naturels.</response>
            </example>
            <example>
                <prompt>Parlons de musique !</prompt>
                <response>Je comprends que vous souhaitez parler de musique. Toutefois, ma tâche principale est d'analyser les incidents environnementaux. Si vous avez des questions sur un incident environnemental, je serais ravi de vous aider.</response>
            </example>
            <example>
                <prompt>Avez-vous vu le dernier film populaire ?</prompt>
                <response>Je ne suis pas programmé pour discuter des films récents. Mon rôle est de vous assister dans l'analyse des incidents environnementaux. Revenons à ce sujet, si vous le voulez bien.</response>
            </example>
            <example>
                <prompt>Quels sont les meilleurs restaurants ici ?</prompt>
                <response>Je me concentre actuellement sur l'analyse des incidents environnementaux. Pour toute question relative aux incidents ou à des pistes de solution, je suis prêt à vous aider.</response>
            </example>
            <example>
                <prompt>Quelle est l'étendue de la zone touchée par cet incident ?</prompt>
                <response>L'analyse des données satellitaires montre que la zone impactée par cet incident couvre environ {impact_area} kilomètres carrés. Cette information nous aide à mieux comprendre l'ampleur du problème et à planifier des interventions appropriées.</response>
            </example>
        </examples>
    </system>
    """

    # Build the input list for the Responses API
    api_input = [
        {"role": "system", "content": [{"type": "input_text", "text": system_prompt_content}]}
    ]
    # Add chat history
    for msg in chat_history:
        api_input.append({"role": msg["role"], "content": [{"type": "input_text", "text": msg["content"]}]})
    # Add current user prompt
    api_input.append({"role": "user", "content": [{"type": "input_text", "text": prompt}]})


    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            input=api_input,
            temperature=0.5,
            max_output_tokens=1080, # Renamed
            top_p=0.8,
            # frequency_penalty=0.3, # Check if supported or map to other params
            # presence_penalty=0.0,  # Check if supported
             text={
                "format": {
                    "type": "text"
                }
            },
            reasoning={},
            tools=[],
            store=True # Assuming default behavior
        )

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

    system_prompt_content = f"""
    <system>
        <role>assistant AI spécialisé en analyse environnementale</role>
        <task>analyse des données satellitaires pour incidents environnementaux avec formatage markdown</task>
        <incident>
            <type>{context['type_incident']}</type>
            <ndvi_data>
                <mean>{context['ndvi_mean']:.2f}</mean>
                <trend>{context['ndvi_trend']}</trend>
            </ndvi_data>
            <ndwi_data>
                <mean>{context['ndwi_mean']:.2f}</mean>
                <trend>{context['ndwi_trend']}</trend>
            </ndwi_data>
            <landcover>
                <dominant>{context['dominant_cover']}</dominant>
                <percentage>{context['dominant_cover_percentage']:.1f}%</percentage>
            </landcover>
        </incident>
        <instructions>
            <instruction>Analysez les données satellitaires fournies pour l'incident environnemental spécifié.</instruction>
            <instruction>Interprétez les tendances NDVI et NDWI en relation avec le type d'incident.</instruction>
            <instruction>Expliquez l'importance de la couverture terrestre dominante dans le contexte de l'incident.</instruction>
            <instruction>Fournissez des insights sur les implications potentielles pour l'environnement local.</instruction>
            <instruction>Suggérez des pistes de solution ou des recommandations basées sur l'analyse.</instruction>
            <instruction>Formatez la réponse en utilisant la syntaxe markdown appropriée.</instruction>
        </instructions>
        <response_formatting>
            <formatting_rule>Utilisez '**' pour les titres principaux. ex: **Titre**</formatting_rule>
            <formatting_rule>Utilisez '***texte***' pour mettre en gras et en italique les chiffres, pourcentages. ex: ***100***</formatting_rule>
            <formatting_rule>Utilisez '- ' au début d'une ligne pour les listes à puces. ex: - item</formatting_rule>
            <formatting_rule>Laissez une ligne vide entre chaque paragraphe pour bien espacer le contenu.</formatting_rule>
            <formatting_rule>Structurez la réponse en sections claires avec des titres appropriés.</formatting_rule>
            <formatting_rule>Utilisez des liens markdown si nécessaire : [texte du lien](URL)</formatting_rule>
        </response_formatting>
    </system>
    """

    user_prompt = f"Analysez les données satellitaires pour l'incident de type '{incident_type}' et fournissez un rapport détaillé formaté en markdown."

    api_input = [
        {"role": "system", "content": [{"type": "input_text", "text": system_prompt_content}]},
        {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]}
    ]

    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            input=api_input,
            temperature=0.7,
            max_output_tokens=2000, # Renamed
            top_p=0.9,
            # frequency_penalty=0.3, # Check if supported
            # presence_penalty=0.0, # Check if supported
             text={
                "format": {
                    "type": "text" # Expecting markdown, but API might just support 'text' or 'json'
                }
            },
            reasoning={},
            tools=[],
            store=True # Assuming default behavior
        )

        analysis = response.output[0].content[0].text
        return analysis

    except Exception as e:
        print(f"An error occurred while generating satellite data analysis: {e}")
        return "Désolé, une erreur s'est produite lors de l'analyse des données satellitaires."
