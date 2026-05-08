# Initialisation du module app (vide pour le sandbox afin d'éviter les conflits avec l'ancien code)
from .services import predict, perform_prediction, fetch_contextual_information, celery_app, analyze_incident_zone
from .models import ImageModel