from transformers import AutoImageProcessor, AutoModelForImageClassification
import torch
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

class EnvironmentClassifier:
    def __init__(self):
        self.processor = AutoImageProcessor.from_pretrained("microsoft/resnet-50")
        self.model = AutoModelForImageClassification.from_pretrained("microsoft/resnet-50")
        
        # List of ImageNet classes that are related to environmental issues
        self.environment_related_classes = {
            'pollution', 'wasteland', 'forest', 'water', 'smoke', 
            'fire', 'landscape', 'soil', 'garbage', 'trash', 
            'desert', 'flood', 'drought'
        }

    def is_environment_related(self, image_bytes):
        """
        Determines if an image is related to environmental issues.
        
        Args:
            image_bytes (bytes): The image data in bytes format
            
        Returns:
            bool: True if the image is likely environment-related, False otherwise
        """
        try:
            # Open image
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            
            # Preprocess the image
            inputs = self.processor(images=image, return_tensors="pt")
            
            # Get prediction
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                predicted_label = logits.argmax(-1).item()
                
            # Get the predicted class name
            predicted_class = self.model.config.id2label[predicted_label].lower()
            
            # Check if any environment-related keywords are in the predicted class
            is_environmental = any(keyword in predicted_class 
                                 for keyword in self.environment_related_classes)
            
            logger.info(f"Image classified as: {predicted_class}")
            return is_environmental
            
        except Exception as e:
            logger.error(f"Error in environment classification: {e}")
            return True  # Default to True in case of errors to allow processing 