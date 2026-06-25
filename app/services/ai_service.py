import json
import logging
import requests
import base64
import time
import re
from app.config import settings
from app.schemas import DeepSeekResponse

logger = logging.getLogger(__name__)


def _sanitize_error_text(text: str) -> str:
    """Masque les secrets potentiellement présents dans les messages d'erreur."""
    if not text:
        return ""
    sanitized = re.sub(r"([?&]key=)[^&\s]+", r"\1***", text)
    sanitized = re.sub(r"(AIza[0-9A-Za-z\-_]+)", "***", sanitized)
    return sanitized

def get_system_prompt() -> str:
    taxonomy_keys = {k: list(v.keys()) for k, v in settings.INCIDENT_TAXONOMY.items()}
    taxonomy_json = json.dumps(taxonomy_keys, ensure_ascii=False, indent=2)
    
    return f"""
Tu es un expert en analyse d'impact environnemental et en gestion de crises.
Analyse l'image fournie et détermine la nature de l'incident.
Tu DOIS répondre UNIQUEMENT avec un objet JSON valide, sans aucun texte avant ou après.

Voici la Taxonomie Officielle des incidents. Tu dois OBLIGATOIREMENT choisir une `macro_category` et une `sub_category` exactes parmi cette liste.

IMPORTANT : Si l'image ne montre aucun incident environnemental, ou s'il s'agit d'un objet hors contexte (chaussures, intérieur d'une maison, visage, écran, etc.), tu DOIS utiliser la catégorie "Hors Contexte / Image Invalide". Si l'environnement est naturel mais parfaitement sain, utilise "Statut Normal".

{taxonomy_json}

Le JSON doit contenir les clés suivantes :
- "macro_category": La macro-catégorie exacte tirée de la liste ci-dessus.
- "sub_category": La sous-catégorie exacte tirée de la liste ci-dessus.
- "source_size_meters": Un nombre (float) représentant LA TAILLE PHYSIQUE DIRECTE de la source de l'incident visible sur l'image en mètres (ex: le canal bouché fait 20m, le feu fait 50m). Ne calcule PAS la zone d'impact, juste la taille visible de la source.
- "spread_vectors": Un tableau listant les vecteurs de propagation actifs observés sur l'image (choisis parmi: "wind", "water_current", "slope", "human_contact", "vectors_insects_rodents").
- "description": Une description détaillée de ce que tu vois et de ton analyse.
"""


def _download_image_as_base64(image_url: str) -> str:
    """Télécharge une image depuis une URL et la convertit en base64."""
    headers = {"User-Agent": "MapActionImpactEngine/1.0"}
    response = requests.get(image_url, headers=headers, timeout=15)
    response.raise_for_status()
    return base64.b64encode(response.content).decode("utf-8")

def _detect_mime_type(image_url: str) -> str:
    """Détecte le type MIME basé sur l'extension de l'URL."""
    url_lower = image_url.lower()
    if url_lower.endswith(".png"):
        return "image/png"
    elif url_lower.endswith(".webp"):
        return "image/webp"
    elif url_lower.endswith(".gif"):
        return "image/gif"
    return "image/jpeg"

def _call_gemini_api(image_base64: str, mime_type: str) -> DeepSeekResponse:
    """
    Appel interne partagé vers l'API Gemini.
    Accepte une image en base64 et retourne un DeepSeekResponse validé.
    """
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": get_system_prompt() + "\n\nAnalyse cet incident et retourne le JSON demandé."},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_base64
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.2
        }
    }

    api_url = f"{settings.GEMINI_API_URL}?key={settings.GEMINI_API_KEY}"

    max_attempts = 3
    base_delay_seconds = 1

    try:
        last_http_error = None
        for attempt in range(1, max_attempts + 1):
            response = requests.post(
                api_url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=60
            )

            if response.status_code in (429, 503):
                last_http_error = requests.exceptions.HTTPError(
                    f"{response.status_code} Server Error: {response.reason}",
                    response=response,
                )
                if attempt < max_attempts:
                    delay = base_delay_seconds * (2 ** (attempt - 1))
                    logger.warning(
                        "Gemini indisponible (status=%s), retry %s/%s dans %ss",
                        response.status_code,
                        attempt,
                        max_attempts,
                        delay,
                    )
                    time.sleep(delay)
                    continue

            response.raise_for_status()
            result = response.json()

            content_str = result["candidates"][0]["content"]["parts"][0]["text"]
            parsed_data = json.loads(content_str)

            ai_response = DeepSeekResponse(**parsed_data)
            logger.info(f"Analyse Gemini réussie: {ai_response.macro_category} > {ai_response.sub_category}")
            return ai_response

        if last_http_error is not None:
            raise last_http_error

    except requests.exceptions.RequestException as e:
        error_detail = ""
        if hasattr(e, 'response') and e.response is not None:
            error_detail = f" - Body: {_sanitize_error_text(e.response.text)}"
        logger.error(f"Erreur lors de l'appel au Moteur Vision: {_sanitize_error_text(str(e))}{error_detail}")
        return _default_response("Le service d'analyse visuelle est temporairement indisponible.")
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.error(f"Erreur de parsing du Moteur Vision: {_sanitize_error_text(str(e))}")
        return _default_response("Le resultat du moteur visuel est invalide. Veuillez reessayer.")
    except Exception as e:
        logger.error(f"Erreur inattendue dans l'analyse Vision: {_sanitize_error_text(str(e))}")
        return _default_response("Une erreur technique est survenue pendant l'analyse visuelle.")


def analyze_image_with_gemini(image_url: str) -> DeepSeekResponse:
    """Analyse une image à partir d'une URL."""
    try:
        image_base64 = _download_image_as_base64(image_url)
        mime_type = _detect_mime_type(image_url)
    except Exception as e:
        logger.error(f"Impossible de telecharger l'image {image_url}: {_sanitize_error_text(str(e))}")
        return _default_response("Impossible de recuperer l'image fournie.")
    return _call_gemini_api(image_base64, mime_type)


def analyze_image_bytes_with_gemini(image_bytes: bytes, mime_type: str = "image/jpeg") -> DeepSeekResponse:
    """Analyse une image à partir de bytes bruts (upload direct)."""
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    return _call_gemini_api(image_base64, mime_type)


def _default_response(error_msg: str) -> DeepSeekResponse:
    """Retourne une réponse par défaut en cas d'erreur pour ne pas bloquer le moteur."""
    return DeepSeekResponse(
        macro_category="Autre",
        sub_category="Incident non répertorié",
        source_size_meters=50.0,
        spread_vectors=["unknown"],
        description=f"L'analyse visuelle a échoué. Détails: {error_msg}"
    )

def call_deepseek_chat(messages: list, context_summary: str) -> str:
    """
    Appelle l'API DeepSeek pour une discussion contextuelle.
    Si la clé DeepSeek est manquante, utilise Gemini en fallback automatique.
    """
    system_prompt = f"""Tu es l'Expert Stratégique Map Action, un conseiller de haut niveau pour les décideurs civils et militaires. 
Ta mission est de fournir des analyses claires, aérées et immédiatement exploitables.

CONTEXTE DE L'INCIDENT :
{context_summary}

DIRECTIVES DE RÉPONSE (CRITIQUES) :
1. LISIBILITÉ : Interdiction d'utiliser le gras (**texte**) ou les triples astérisques (***).
2. STRUCTURE : Utilise uniquement des tirets simples (-) pour les listes. Saute une ligne entre chaque point.
3. TON : Administratif, direct, et institutionnel (Style INSTAT / Ministère).
4. CONTEXTE : Tu connais parfaitement la localisation (GPS) et les chiffres du rapport. Utilise-les sans les répéter inutilement.
5. CONCISION : Pas de blabla, pas d'introductions répétitives. Va droit au but.

Réponds toujours en Français."""

    # Vérification de la clé API
    if not settings.DEEPSEEK_API_KEY or "votre_cle" in settings.DEEPSEEK_API_KEY or "your_deepseek" in settings.DEEPSEEK_API_KEY:
        yield "Erreur : Le moteur de discussion n'est pas configuré."
        return

    payload = {
        "model": settings.DEEPSEEK_MODEL,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
        "temperature": 0.7,
        "max_tokens": 1000,
        "stream": True  # Activation du mode streaming
    }

    try:
        # Construction de l'URL complète à partir de la base URL
        base_url = settings.DEEPSEEK_API_URL.rstrip('/')
        full_url = f"{base_url}/chat/completions"
        if "/v1" not in full_url and "deepseek.com" in full_url:
             full_url = f"{base_url}/v1/chat/completions"

        response = requests.post(
            full_url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"
            },
            json=payload,
            stream=True,
            timeout=90
        )
        response.raise_for_status()

        # Lecture du flux SSE (Server-Sent Events)
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith("data: "):
                    data_str = decoded_line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        import json
                        chunk = json.loads(data_str)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content")
                        if content: # Vérifie que le contenu n'est pas None ou vide
                            yield content
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        logger.error(f"Erreur DeepSeek Chat: {e}")
        yield f"Désolé, je rencontre une difficulté technique pour répondre : {e}"

