# main_router.py
import os
import logging
import requests
import numpy as np
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse
from typing import Dict, List
import json
import asyncio
from datetime import datetime, timedelta
import ee

from ..services.websockets import ConnectionManager
from ..services import (
    chat_response,
    perform_prediction,
    fetch_contextual_information,
    celery_app,
    analyze_incident_zone,
)
from ..services.aws_s3_storage import upload_file_to_s3 # Import the AWS S3 storage function

import numpy as np
from ..models import ImageModel
from ..database import database
from dotenv import load_dotenv

load_dotenv()

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize ConnectionManager for handling WebSocket connections
manager = ConnectionManager()
router = APIRouter()

# Update the BASE_URL to match where the images are hosted
BASE_URL = os.getenv('SERVER_URL')

# Add this near the top of the file, with other global variables
impact_area_storage = {}

def construct_image_url(image_name: str) -> str:
    """
    Constructs the full URL for the image based on the image name.

    Args:
        image_name (str): The name or path of the image.

    Returns:
        str: The full URL to access the image.
    """
    return f"{BASE_URL}/{image_name.split('/')[-1]}"

async def fetch_image(image_url: str) -> bytes:
    """
    Fetches the image from the specified URL.

    Args:
        image_url (str): The URL of the image to fetch.

    Returns:
        bytes: The binary content of the fetched image.

    Raises:
        HTTPException: If the image cannot be fetched.
    """
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        logger.error(f"Failed to fetch image from {image_url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch image: {str(e)}")

def sanitize_error_message(message: str, sensitive_structures: List[str]) -> str:
    """
    Sanitizes the error message by masking sensitive structures.

    Args:
        message (str): The original error message.
        sensitive_structures (List[str]): A list of sensitive terms to mask.

    Returns:
        str: The sanitized error message.
    """
    sanitized_message = message
    for structure in sensitive_structures:
        # Simple string replacement to match exact test cases
        sanitized_message = sanitized_message.replace(structure, "[REDACTED]")
    return sanitized_message

@router.get("/")
def index():
    """
    Root endpoint to verify that the API is running.

    Returns:
        dict: A message indicating the API is operational.
    """
    return {"message": "Map Action classification model"}

@router.post("/image/predict")
async def predict_incident_type(data: ImageModel):
    """
    Predicts the type of incident based on the provided image and other data.

    Args:
        data (ImageModel): The input data containing image name, sensitive structures, zone, and incident ID.

    Returns:
        JSONResponse: The prediction results including incident type, probabilities, context, impact, and solution.

    Raises:
        HTTPException: If any step in the prediction process fails.
    """
    try:
        logger.info(
            f"Received request for image: {data.image_name} with sensitive structures: {data.sensitive_structures}, incident_id: {data.incident_id} in zone: {data.zone}"
        )

        # Handle Supabase URLs directly, otherwise use the old construct_image_url logic
        if data.image_name.startswith('https://') and 'supabase.co' in data.image_name:
            image_url = data.image_name  # Use Supabase URL as-is
            logger.info(f"Using Supabase URL directly: {image_url}")
        else:
            image_url = construct_image_url(data.image_name)  # Legacy server-based images
            logger.info(f"Constructed legacy server URL: {image_url}")
        
        image = await fetch_image(image_url)

        # Perform prediction asynchronously using Celery
        prediction_task = perform_prediction.delay(image)
        try:
            prediction, probabilities = prediction_task.get(timeout=120)
            logger.info(f"Prediction successful: {prediction} with probabilities: {probabilities}")
            if isinstance(probabilities, np.ndarray):
                probabilities = probabilities.tolist()
        except Exception as e:
            logger.error(f"Error during prediction task: {e}")
            raise HTTPException(status_code=500, detail=f"Error during prediction: {str(e)}")

        # Fetch contextual information asynchronously using Celery
        context_task = fetch_contextual_information.delay(prediction, data.sensitive_structures, data.zone)
        try:
            analysis, piste_solution = context_task.get(timeout=120)
            logger.info(f"Context fetching successful: {analysis}, {piste_solution}")
        except Exception as e:
            logger.error(f"Error during context fetching task: {e}")
            raise HTTPException(status_code=500, detail=f"Error during context fetching: {str(e)}")

        # Perform satellite data analysis
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
        end_date = datetime.now().strftime("%Y%m%d")
        satellite_analysis_task = analyze_incident_zone.delay(data.latitude, data.longitude, data.zone, prediction, start_date, end_date)
        try:
            satellite_analysis = satellite_analysis_task.get(timeout=120)
        except Exception as e:
            logger.error(f"Error during satellite analysis task: {e}")
            raise HTTPException(status_code=500, detail=f"Error during satellite analysis: {str(e)}")

        # Add satellite analysis to the existing analysis
        analysis += "\n\n" + satellite_analysis['textual_analysis']

        # Upload plots to AWS S3
        # container_name = os.environ['BLOB_CONTAINER_NAME']  # Replace with your actual container name
        bucket_name = os.environ.get('S3_BUCKET_NAME')
        region_name = os.environ.get('AWS_REGION')

        if not bucket_name:
             logger.error("S3_BUCKET_NAME environment variable is not set.")
             # Handle the error appropriately, maybe raise HTTPException or return an error response
             raise HTTPException(status_code=500, detail="S3 bucket name not configured.")


        # ndvi_ndwi_plot_url = upload_file_to_blob(container_name, satellite_analysis['ndvi_ndwi_plot'])
        # ndvi_heatmap_url = upload_file_to_blob(container_name, satellite_analysis['ndvi_heatmap'])
        # landcover_plot_url = upload_file_to_blob(container_name, satellite_analysis['landcover_plot'])
        
        ndvi_ndwi_plot_url = upload_file_to_s3(bucket_name, satellite_analysis['ndvi_ndwi_plot'], region_name)
        ndvi_heatmap_url = upload_file_to_s3(bucket_name, satellite_analysis['ndvi_heatmap'], region_name)
        landcover_plot_url = upload_file_to_s3(bucket_name, satellite_analysis['landcover_plot'], region_name)
        
        # Check if uploads were successful (returned a URL)
        if not all([ndvi_ndwi_plot_url, ndvi_heatmap_url, landcover_plot_url]):
            # Log the specific failures if needed (the upload function logs errors)
            logger.error("One or more plot uploads to S3 failed.")
            # Decide how to handle partial failure - raise error or continue with missing URLs?
            # For now, raising an error might be safer.
            raise HTTPException(status_code=500, detail="Failed to upload analysis plots.")


        # Prepare the response
        response = {
            "prediction": prediction,
            "probabilities": probabilities,
            "analysis": analysis,
            "piste_solution": piste_solution,
            "ndvi_ndwi_plot": ndvi_ndwi_plot_url,
            "ndvi_heatmap": ndvi_heatmap_url,
            "landcover_plot": landcover_plot_url,
        }

        # Validate all required fields are present
        if not all([data.incident_id, prediction, piste_solution, analysis]):
            raise HTTPException(status_code=400, detail="Missing required fields for database insertion.")

        # Convert prediction list to a string format for database insertion
        prediction_texts = [pred[0] for pred in prediction]
        prediction_texts = [text.replace("Pollution de leau", "Pollution de l'eau").replace("Pollution de lair", "Pollution de l'air") for text in prediction_texts]
        if len(prediction_texts) == 1:
            prediction_str = prediction_texts[0].encode('utf-8').decode('utf-8')
        else:
            prediction_str = ", ".join(prediction_texts).encode('utf-8').decode('utf-8')

        # Insert the prediction and context into the database
        query = """
        INSERT INTO "Mapapi_prediction" (incident_id, incident_type, piste_solution, analysis, ndvi_ndwi_plot, ndvi_heatmap, landcover_plot)
        VALUES (:incident_id, :incident_type, :piste_solution, :analysis, :ndvi_ndwi_plot, :ndvi_heatmap, :landcover_plot);
        """
        values = {
            "incident_id": data.incident_id,
            "incident_type": prediction_str,
            "piste_solution": piste_solution,
            "analysis": analysis,
            "ndvi_ndwi_plot": ndvi_ndwi_plot_url,
            "ndvi_heatmap": ndvi_heatmap_url,
            "landcover_plot": landcover_plot_url,
        }

        try:
            await database.execute(query=query, values=values)
            logger.info(f"Database insertion successful for incident_id {data.incident_id}")
        except Exception as e:
            # Log the specific database error and traceback
            logger.error(f"Database insertion failed for incident_id {data.incident_id}.")
            logger.exception(e)
            # Re-raise HTTPException with a generic message, hiding internal details from the client
            # but ensuring the detailed error is logged internally.
            raise HTTPException(status_code=500, detail="An internal error occurred while saving the prediction results.")

        return JSONResponse(content=response)

    except HTTPException as http_exc:
        # Re-raise HTTPExceptions to be handled by the global exception handler
        raise http_exc
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# This will store chat histories for each session in-memory
# Note: For scalability and persistence, consider removing this and relying solely on the database
chat_histories: Dict[str, List[Dict[str, str]]] = {}


@router.websocket("/ws/chat")
async def chat_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for handling chat interactions and chat history deletion.

    Args:
        websocket (WebSocket): The WebSocket connection.

    Raises:
        WebSocketDisconnect: If the connection is closed.
    """
    logger.info(f"WebSocket connection attempt from {websocket.client.host}")
    origin = websocket.headers.get("origin")
    logger.info(f"Received Origin: {origin}")

    allowed_origins = [
        "http://197.155.176.134",
        "http://localhost:3000",
        "http://127.0.0.1",
        "http://57.153.185.160",
        "https://app.map-action.com",  
        "http://app.map-action.com",
        None,
    ]
    if origin not in allowed_origins:
        logger.warning(f"Connection rejected from origin: {origin}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    logger.info(f"Connection accepted from origin: {origin}")
    await manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_json()

            action = data.get("action")
            incident_id = data.get("incident_id")
            session_id = data.get("session_id")

            if not incident_id or not session_id:
                logger.error("Missing incident_id or session_id in message")
                await websocket.send_json({"error": "Missing incident_id or session_id"})
                continue

            if action == "delete_chat":
                # Handle chat history deletion
                chat_key = f"{session_id}{incident_id}"
                query = """
                DELETE FROM "Mapapi_chathistory"
                WHERE session_id = :session_id;
                """
                values = {"session_id": chat_key}
                try:
                    await database.execute(query=query, values=values)
                    logger.info(f"Chat history deleted for session {chat_key}")

                    # Clear in-memory chat history
                    if chat_key in chat_histories:
                        del chat_histories[chat_key]

                    # Send a confirmation to the client
                    await websocket.send_json({"message": "Chat history deleted successfully."})
                except Exception as e:
                    logger.error(f"Error deleting chat history: {e}")
                    await websocket.send_json({"error": "Error deleting chat history."})
            else:
                # Fetch context from the database based on incident_id
                query = """
                SELECT incident_type, analysis, piste_solution
                FROM "Mapapi_prediction"
                WHERE incident_id = :incident_id;
                """
                values = {"incident_id": incident_id}
                result = await database.fetch_one(query=query, values=values)

                if result:
                    context_obj = {
                        "type_incident": result["incident_type"],
                        "analysis": result["analysis"],
                        "piste_solution": result["piste_solution"],
                    }
                    context = json.dumps(context_obj)
                    
                    # Retrieve impact_area from in-memory storage
                    impact_area = impact_area_storage.get(incident_id, None)
                else:
                    logger.error(f"No context found for incident_id: {incident_id}")
                    await websocket.send_json({"error": "No context found for the given incident_id"})
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                    return

                chat_key = f"{session_id}{incident_id}"

                # Initialize chat history if not present
                if chat_key not in chat_histories:
                    history_query = """
                    SELECT question, answer FROM "Mapapi_chathistory"
                    WHERE session_id = :session_id
                    ORDER BY id ASC;
                    """
                    history_values = {"session_id": chat_key}
                    history_results = await database.fetch_all(query=history_query, values=history_values)
                    chat_histories[chat_key] = [
                        {"role": "user", "content": record["question"]}
                        for record in history_results
                    ] + [
                        {"role": "assistant", "content": record["answer"]}
                        for record in history_results
                    ]

                # Add the user's question to the chat history
                question = data.get("question")
                chat_histories[chat_key].append({"role": "user", "content": question})

                # Get response from chat bot
                chatbot_response = chat_response(question, context, chat_histories[chat_key], impact_area)

                # Append assistant's response to history
                chat_histories[chat_key].append({"role": "assistant", "content": chatbot_response})

                # Send the response back through the WebSocket
                response_message = {
                    "incident_id": incident_id,
                    "session_id": session_id,
                    "question": question,
                    "answer": chatbot_response,
                }

                await websocket.send_json(response_message)

                # Save the chat history to the database
                await save_chat_history(chat_key, question, chatbot_response)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"WebSocket disconnected from {websocket.client.host}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)


async def save_chat_history(chat_key: str, question: str, answer: str):
    """
    Saves a single chat interaction to the database.

    Args:
        chat_key (str): The unique identifier for the chat session.
        question (str): The user's question.
        answer (str): The assistant's answer.

    Raises:
        HTTPException: If there is an error saving to the database.
    """
    query = """
    INSERT INTO "Mapapi_chathistory" (session_id, question, answer)
    VALUES (:session_id, :question, :answer);
    """
    values = {
        "session_id": chat_key,
        "question": question,
        "answer": answer,
    }
    try:
        await database.execute(query=query, values=values)
        logger.info(f"Chat history saved for session {chat_key}")
    except Exception as e:
        logger.error(f"Error saving chat history: {e}")


@router.get("/MapApi/history/{chat_key}")
async def get_chat_history(chat_key: str):
    """
    Retrieves the chat history for a given chat_key.

    Args:
        chat_key (str): The unique identifier for the chat session.

    Returns:
        list: A list of chat messages in chronological order.

    Raises:
        HTTPException: If there is an error fetching the chat history.
    """
    query = """
    SELECT question, answer FROM "Mapapi_chathistory"
    WHERE session_id = :session_id
    ORDER BY id ASC;
    """
    values = {"session_id": chat_key}
    try:
        results = await database.fetch_all(query=query, values=values)
        # Format the results to interleave user and assistant messages
        formatted_history = []
        for record in results:
            formatted_history.append({"role": "user", "content": record["question"]})
            formatted_history.append({"role": "assistant", "content": record["answer"]})
        return formatted_history
    except Exception as e:
        logger.error(f"Error fetching chat history: {e}")
        raise HTTPException(status_code=500, detail="Error fetching chat history")


async def expire_impact_area(incident_id: str, delay: int):
    await asyncio.sleep(delay)
    impact_area_storage.pop(incident_id, None)


