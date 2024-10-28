# Language Model (LLM) Component

This document provides an overview of the LLM component used in the Map Action project. The LLM is responsible for generating responses to user prompts and analyzing satellite data for environmental incidents.

## Key Functions

-   **get_response**: Processes a user's prompt to generate and display the assistant's response using the GPT-4o-mini model.

    -   **Args**: `prompt` (str) - The user's message to which the assistant should respond.
    -   **Returns**: The assistant's response, which is also added to the chat history.

-   **chat_response**: Generates the assistant's response using GPT-4o-mini, with context about the environmental incident.

    -   **Args**: `prompt` (str), `context` (str), `chat_history` (list), `impact_area` (str).
    -   **Returns**: The assistant's response.

-   **generate_satellite_analysis**: Generates a detailed analysis of satellite data for environmental incidents using LLM, with proper markdown formatting.
    -   **Args**: `ndvi_data` (pd.DataFrame), `ndwi_data` (pd.DataFrame), `landcover_data` (dict), `incident_type` (str).
    -   **Returns**: Detailed analysis of the satellite data, formatted in markdown.

## Integration with OpenAI

The LLM component uses the OpenAI API to generate responses. It initializes the OpenAI client with an API key from environment variables and interacts with the API to process chat history and generate responses.

For more detailed information on each function, refer to the `llm.py` file in the `app/services/llm/` directory.
