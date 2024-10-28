# API Routes Documentation

This document provides an overview of the API routes available in the Map Action project. These routes are defined in the `main_router.py` file and are responsible for handling various functionalities, including image predictions and WebSocket connections.

## Root Endpoint

-   **GET /**

    -   **Description**: Verifies that the API is running.
    -   **Response**: Returns a message indicating the API is operational.

## Image Prediction

-   **POST /image/predict**

    -   **Description**: Predicts the type of incident based on the provided image and other data.
    -   **Request Body**: Expects an `ImageModel` containing image name, sensitive structures, zone, and incident ID.
    -   **Response**: Returns prediction results, including incident type, probabilities, context, impact, and solution.

## WebSocket Chat

-   **WebSocket /ws/chat**

    -   **Description**: Handles chat interactions and chat history deletion.
    -   **Request**: Expects a WebSocket connection with actions such as "delete_chat".
    -   **Response**: Sends chat responses and manages chat history.

## Chat History

-   **GET /MapApi/history/{chat_key}**

    -   **Description**: Retrieves the chat history for a given chat key.
    -   **Response**: Returns a list of chat messages in chronological order.

## Additional Information

-   **Database Operations**: The API interacts with a database to store and retrieve predictions and chat history.
-   **Error Handling**: The API includes error handling for various operations, ensuring robust and reliable functionality.

For more detailed information on each route, refer to the `main_router.py` file in the `app/apis/` directory.
