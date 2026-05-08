# main_router.py
import os
import logging
import requests
import numpy as np
import time
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Dict, List, Optional
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
from ..services.supabase_storage import upload_plot_to_supabase  # Import the Supabase storage function

# Import pour le Moteur d'Impact
from ..services.ai_service import analyze_image_with_gemini, analyze_image_bytes_with_gemini, call_deepseek_chat
from ..services.spatial_calculator import (
    get_slope_data, 
    get_osm_data, 
    get_weather_data,
    filter_osm_by_radius,
    calculate_social_vulnerability,
    calculate_human_impact,
    get_satellite_analysis,
    get_geocoding_context
)
from ..impact_logic import calculate_dynamic_radius, calculate_global_impact
from ..schemas import AnalyzeRequest, AnalyzeResponse, SpatialData, SatelliteData, HumanImpact, ChatRequest
from ..config import settings

import numpy as np
from ..models import ImageModel
from ..database import database, execute_with_retry, fetch_with_retry, fetch_one_with_retry
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
            prediction, probabilities = prediction_task.get(timeout=600)  # Increased to 10 minutes
            logger.info(f"Prediction successful: {prediction} with probabilities: {probabilities}")
            if isinstance(probabilities, np.ndarray):
                probabilities = probabilities.tolist()
        except Exception as e:
            logger.error(f"Error during prediction task: {e}")
            raise HTTPException(status_code=500, detail=f"Error during prediction: {str(e)}")

        # Fetch contextual information asynchronously using Celery
        context_task = fetch_contextual_information.delay(prediction, data.sensitive_structures, data.zone)
        try:
            analysis, piste_solution = context_task.get(timeout=600)  # Increased to 10 minutes
            logger.info(f"Context fetching successful: {analysis}, {piste_solution}")
        except Exception as e:
            logger.error(f"Error during context fetching task: {e}")
            raise HTTPException(status_code=500, detail=f"Error during context fetching: {str(e)}")

        # Perform satellite data analysis
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
        end_date = datetime.now().strftime("%Y%m%d")
        satellite_analysis_task = analyze_incident_zone.delay(data.latitude, data.longitude, data.zone, prediction, start_date, end_date)
        try:
            satellite_analysis = satellite_analysis_task.get(timeout=600)  # Increased to 10 minutes
        except Exception as e:
            logger.error(f"Error during satellite analysis task: {e}")
            raise HTTPException(status_code=500, detail=f"Error during satellite analysis: {str(e)}")

        # Add satellite analysis to the existing analysis
        analysis += "\n\n" + satellite_analysis['textual_analysis']

        # Upload plots to Supabase
        ndvi_ndwi_plot_url = upload_plot_to_supabase(
            satellite_analysis['ndvi_ndwi_plot'], 
            'ndvi_ndwi', 
            data.incident_id
        )
        ndvi_heatmap_url = upload_plot_to_supabase(
            satellite_analysis['ndvi_heatmap'], 
            'ndvi_heatmap', 
            data.incident_id
        )
        landcover_plot_url = upload_plot_to_supabase(
            satellite_analysis['landcover_plot'], 
            'landcover', 
            data.incident_id
        )
        
        # Check if uploads were successful (returned a URL)
        if not all([ndvi_ndwi_plot_url, ndvi_heatmap_url, landcover_plot_url]):
            # Log the specific failures if needed (the upload function logs errors)
            logger.error("One or more plot uploads to Supabase failed.")
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
            await execute_with_retry(query=query, values=values)
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
                    await execute_with_retry(query=query, values=values)
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
                result = await fetch_one_with_retry(query=query, values=values)

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
                    history_results = await fetch_with_retry(query=history_query, values=history_values)
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
        await execute_with_retry(query=query, values=values)
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
        results = await fetch_with_retry(query=query, values=values)
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


# ============================================================
# MOTEUR D'IMPACT - Intégration
# ============================================================

async def _run_analysis(ai_data, latitude: float, longitude: float, incident_id: str = None) -> AnalyzeResponse:
    """Logique d'analyse partagée entre les endpoints URL et Upload."""
    
    # 1. Phase 1 : Collecte du contexte Macro (Rayon fixe 5km pour OSM)
    slope_result, osm_macro_result, sat_result, weather_result, geo_context = await asyncio.gather(
        asyncio.to_thread(get_slope_data, latitude, longitude),
        asyncio.to_thread(get_osm_data, latitude, longitude, 5000), # 5km macro scan
        asyncio.to_thread(get_satellite_analysis, latitude, longitude),
        asyncio.to_thread(get_weather_data, latitude, longitude),
        asyncio.to_thread(get_geocoding_context, latitude, longitude)
    )

    spatial_data = {
        "elevation": 0.0,
        "slope_percent": slope_result,
        "wind_speed": weather_result["wind_speed"],
        "precipitation": weather_result["precipitation"],
        "temperature_celsius": weather_result["temperature_celsius"]
    }

    # 2. Phase 2 : Calcul dynamique du rayon final (Analyse Croisée)
    radius_data = calculate_dynamic_radius(
        ai_data=ai_data,
        spatial_data=spatial_data,
        macro_osm_counts=osm_macro_result["counts"],
        sat_data=sat_result
    )
    final_radius = radius_data["final_radius"]
    radius_exp = radius_data.get("radius_explanation", "")

    # 3. Phase 3 : Calcul des scores sociaux et humains
    osm_micro_counts = filter_osm_by_radius(osm_macro_result, latitude, longitude, final_radius)
    social_data = calculate_social_vulnerability(osm_micro_counts, land_use=sat_result.get("land_use", "Inconnu"))
    social_score = social_data["score"]
    is_probabilistic = social_data["is_probabilistic"]
    estimated_buildings = social_data.get("estimated_buildings", 0)
    human_impact_data = calculate_human_impact(osm_micro_counts, estimated_buildings=estimated_buildings)

    # 4. Phase 4 : Calcul du risque potentiel (Si détecté)
    potential_risk_data = radius_data.get("potential_risk")
    if potential_risk_data:
        pot_radius = potential_risk_data["potential_radius"]
        osm_pot_counts = filter_osm_by_radius(osm_macro_result, latitude, longitude, pot_radius)
        social_pot = calculate_social_vulnerability(osm_pot_counts, land_use=sat_result.get("land_use", "Inconnu"))
        human_pot = calculate_human_impact(osm_pot_counts, estimated_buildings=social_pot.get("estimated_buildings"))
        
        potential_risk_data["stats"] = {
            "total_pop": human_pot["total_population_exposed"],
            "infrastructures": sum(v for k,v in osm_pot_counts.items() if k != "residential_buildings")
        }

    # 5. Phase 5 : Calcul du score d'impact global et réponse
    impact_data = calculate_global_impact(
        ai_data=ai_data,
        sat_data=sat_result,
        spatial_data=spatial_data,
        social_score=social_score
    )

    return AnalyzeResponse(
        incident_id=incident_id,
        latitude=latitude,
        longitude=longitude,
        ai_analysis=ai_data,
        topography=SpatialData(**spatial_data),
        satellite=SatelliteData(**sat_result),
        social_data=osm_micro_counts,
        social_vulnerability_score=social_score,
        is_social_probabilistic=is_probabilistic,
        human_impact=HumanImpact(**human_impact_data),
        impact_radius_meters=final_radius,
        radius_explanation=radius_exp,
        global_impact_score=impact_data["impact_score"],
        base_severity=settings.INCIDENT_TAXONOMY.get(ai_data.macro_category, {}).get(ai_data.sub_category, {}).get("base_severity", 5),
        impact_tags=settings.INCIDENT_TAXONOMY.get(ai_data.macro_category, {}).get(ai_data.sub_category, {}).get("impact_tags", []),
        geocoding=geo_context,
        potential_risk=potential_risk_data,
        recommendation=f"Intervention recommandée dans un rayon de {final_radius}m. Score de gravité: {impact_data['impact_score']}/10."
    )


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_incident(request: AnalyzeRequest):
    """Endpoint pour analyser un incident via URL d'image."""
    start_time = time.time()
    logger.info(f"Analyse via URL pour incident: {request.incident_id}")

    ai_data = await asyncio.to_thread(analyze_image_with_gemini, request.image_url)
    result = await _run_analysis(ai_data, request.latitude, request.longitude, request.incident_id)

    logger.info(f"Analyse terminée en {time.time() - start_time:.2f}s")
    return result


@router.post("/analyze/upload", response_model=AnalyzeResponse)
async def analyze_incident_upload(
    image: UploadFile = File(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    incident_id: Optional[str] = Form(None)
):
    """Endpoint pour analyser un incident via upload direct d'image."""
    start_time = time.time()
    logger.info(f"Analyse via Upload pour ({latitude}, {longitude})")

    image_bytes = await image.read()
    mime_type = image.content_type or "image/jpeg"

    ai_data = await asyncio.to_thread(analyze_image_bytes_with_gemini, image_bytes, mime_type)
    result = await _run_analysis(ai_data, latitude, longitude, incident_id)

    logger.info(f"Analyse terminée en {time.time() - start_time:.2f}s")
    return result


@router.post("/chat")
async def chat_with_assistant(request: ChatRequest):
    """Endpoint de chat contextuel avec DeepSeek."""
    try:
        # On prépare un résumé textuel clair au lieu du JSON brut
        ctx = request.context
        human = ctx.get('human_impact', {})
        topo = ctx.get('topography', {})
        sat = ctx.get('satellite', {})
        ai = ctx.get('ai_analysis', {})
        
        context_text = f"""RAPPORT D'INCIDENT MAP ACTION
- Position : Latitude {ctx.get('latitude')}, Longitude {ctx.get('longitude')}
- Localisation : {ctx.get('geocoding', {}).get('display_name', 'Inconnue')}
- Ville/Village : {ctx.get('geocoding', {}).get('city', 'Inconnu')} | Région : {ctx.get('geocoding', {}).get('region', 'Inconnue')} | Pays : {ctx.get('geocoding', {}).get('country', 'Inconnu')}
- Incident : {ai.get('macro_category')} - {ai.get('sub_category')}
- Tags d'impact : {', '.join(ctx.get('impact_tags', []))}
- Gravité Initiale: {ctx.get('base_severity')}/10 | Gravité Globale : {ctx.get('global_impact_score')}/10
- Rayon d'impact : {ctx.get('impact_radius_meters')} mètres
- Justification : {ctx.get('radius_explanation')}
- Population exposée : {human.get('total_population_exposed')} personnes
  (Hommes: {human.get('adult_men_exposed')}, Femmes: {human.get('adult_women_exposed')}, Enfants: {human.get('children_exposed')})
- Météo : {topo.get('temperature_celsius')}°C, Vent {topo.get('wind_speed')}km/h, Pluie {topo.get('precipitation')}mm
- Sol : Pente {topo.get('slope_percent')}%, Occupation: {sat.get('land_use')}
- Infrastructures : {ctx.get('social_data')}
- Risque potentiel : {ctx.get('potential_risk', {}).get('message') if ctx.get('potential_risk') else 'Aucun risque de propagation majeure détecté.'}
"""
        # On renvoie le générateur de texte encapsulé dans une StreamingResponse
        return StreamingResponse(call_deepseek_chat(request.messages, context_text), media_type="text/event-stream")
    except Exception as e:
        logger.error(f"Erreur API Chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))
