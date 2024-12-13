from transformers import AutoProcessor, AutoModelForZeroShotImageClassification
import torch
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

class EnvironmentClassifier:
    def __init__(self):
        # Load CLIP zero-shot classification model and processor
        self.processor = AutoProcessor.from_pretrained("openai/clip-vit-base-patch32")
        self.model = AutoModelForZeroShotImageClassification.from_pretrained("openai/clip-vit-base-patch32")

        # Candidate labels reflecting the known environmental tags plus a no-issue category
        self.candidate_labels = [
            "Caniveau obstrué",       # Blocked drain/gutter
            "Déchets",               # Waste
            "Déforestation",         # Deforestation
            "Feux de brousse",       # Bush fires
            "Pollution de l'eau",    # Water pollution
            "Pollution de l'air",    # Air pollution
            "Sécheresse",            # Drought
            "Sol dégradé",           # Degraded soil
            "Aucun problème environnemental"  # No environmental problem
        ]

    def is_environment_related(self, image_bytes):
        """
        Determines if an image is related to environmental issues using zero-shot classification.
        We classify against known environmental issue categories plus a "no environmental problem" category.
        
        Args:
            image_bytes (bytes): The image data in bytes format
            
        Returns:
            bool: True if the image likely shows an environmental problem, False otherwise
        """
        try:
            # Open the image
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            
            # Preprocess the image with your candidate labels
            inputs = self.processor(images=image, 
                                    text=self.candidate_labels, 
                                    return_tensors="pt", 
                                    padding=True)
            
            # Perform zero-shot classification
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits_per_image
                probs = logits.softmax(dim=1).cpu().tolist()[0]

            # Log the results for debugging
            for label, prob in zip(self.candidate_labels, probs):
                logger.info(f"Label: {label}, Probability: {prob:.4f}")

            # Identify the top predicted label
            max_label_idx = probs.index(max(probs))
            predicted_label = self.candidate_labels[max_label_idx]
            logger.info(f"Predicted label: {predicted_label}")

            # If the best prediction is not "no environmental problem", consider it environment-related
            # That is, if any environmental category is ranked higher than "Aucun problème environnemental".
            # Find the probability for "Aucun problème environnemental"
            no_problem_idx = self.candidate_labels.index("Aucun problème environnemental")
            no_problem_prob = probs[no_problem_idx]

            # If another label surpasses the no problem label, we consider it environment-related
            # Otherwise, it's not environment-related.
            is_environmental = no_problem_idx != max_label_idx
            return is_environmental

        except Exception as e:
            logger.error(f"Error in environment classification: {e}")
            # Default to True in case of errors to allow further processing
            return True
