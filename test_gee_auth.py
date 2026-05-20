import ee
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("--- Tentative de reconnexion forcée à Google Earth Engine ---")
try:
    # On force l'ouverture du lien d'authentification
    ee.Authenticate(force=True)
    
    # On tente d'initialiser pour vérifier si ça marche vraiment
    # Remplacez le projet par le vôtre si nécessaire
    ee.Initialize(project="gen-lang-client-0736065387")
    print("\n✅ SUCCÈS : Google Earth Engine est maintenant activé et initialisé !")
    
except Exception as e:
    print(f"\n❌ ERREUR : {e}")
    print("\nSi le navigateur ne s'ouvre pas, copiez le lien qui s'affiche ci-dessus manuellement.")
