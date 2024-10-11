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
    Sends the current chat history to the OpenAI API to generate a response from the assistant using GPT-4o-mini.

    Args:
        messages (list of dict): The current chat history as a list of message dictionaries.

    Returns:
        str: The assistant's response as a string.

    Raises:
        Exception: Prints an error message if the API call fails and returns a default error response.
    """
    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",  # The model version to use for generating responses
            messages=[{"role": m["role"], "content": m["content"]} for m in messages],
            temperature=1,  # Adjust the temperature if needed
            max_tokens=1080,  # Adjust as needed
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        response = r.choices[0].message.content
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


def chat_response(prompt: str, context: str = "", chat_history: list = []):
    """
    Processes a user's prompt to generate the assistant's response using GPT-4o-mini,
    with context about the environmental incident.

    Args:
        prompt (str): The user's message to which the assistant should respond.
        context (str): A JSON string containing context about the incident.
        chat_history (list): The existing chat history for this session.

    Returns:
        str: The assistant's response.
    """

    context_obj = json.loads(context)
    system_message = f"""
    Vous êtes un assistant AI spécialisé dans l'analyse des incidents environnementaux au Mali.
    Voici le contexte détaillé de l'incident actuel:
    Type d'incident: {context_obj['type_incident']}
    Contexte:
    {context_obj['analysis']}
    Pistes de solution:
    {context_obj['piste_solution']}

    Votre tâche est de fournir des informations précises et pertinentes en français, basées sur ce contexte détaillé.
    Adaptez vos réponses au contexte spécifique de l'incident et utilisez ces informations pour enrichir vos explications.
    Si on vous pose des questions sur des aspects non couverts par ce contexte, vous pouvez y répondre en vous basant sur vos connaissances générales,
    mais précisez que ces informations ne font pas partie du rapport spécifique de cet incident.
    """

    messages = [{"role": "system", "content": system_message}] + chat_history + [{"role": "user", "content": prompt}]

    try:
        # Get the assistant's response
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Make sure this model is available and correct
            messages=messages,
            temperature=1,
            max_tokens=1080,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        assistant_response = response.choices[0].message.content
        return assistant_response

    except Exception as e:
        print(f"An error occurred: {e}")
        return "Sorry, I can't process your request right now."
