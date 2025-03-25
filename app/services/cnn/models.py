from typing import List, Optional, Tuple
from pydantic import BaseModel, Field

class PredictionTag(BaseModel):
    """Represents a single environmental issue tag with its probability."""
    tag: str = Field(description="The environmental issue tag")
    probability: float = Field(description="Confidence score between 0 and 1")

class PredictionResult(BaseModel):
    """Represents the complete prediction result from either the CNN or OpenAI model."""
    top_predictions: List[PredictionTag] = Field(
        description="List of top predictions, sorted by probability in descending order"
    )
    all_probabilities: List[float] = Field(
        description="Raw probability scores for all possible tags in the predefined order"
    )
    
    @classmethod
    def from_prediction_tuple(cls, prediction_tuple: Tuple[List[Tuple[str, float]], List[float]]) -> "PredictionResult":
        """
        Creates a PredictionResult from the tuple format returned by prediction functions.
        
        Args:
            prediction_tuple: A tuple containing (list of (tag, probability) tuples, list of all probabilities)
            
        Returns:
            PredictionResult: A structured prediction result
        """
        top_predictions_tuple, all_probabilities = prediction_tuple
        top_predictions = [
            PredictionTag(tag=tag, probability=prob) 
            for tag, prob in top_predictions_tuple
        ]
        
        return cls(
            top_predictions=top_predictions,
            all_probabilities=all_probabilities
        ) 