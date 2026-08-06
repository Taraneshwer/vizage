"""
Confidence Fusion Engine.
Fuses multiple AI signals into a single Verification Score.
"""
from app.core.logger import get_logger
from app.services.ai.models import RecognitionResult

logger = get_logger(__name__)

class ConfidenceFusionEngine:
    def __init__(self):
                                                          
        self.weights = {
            "embedding": 0.60,
            "temporal": 0.25,
            "detection": 0.15
        }
        
    def fuse_score(self, result: RecognitionResult, temporal_stability: float) -> float:
        """
        Calculates a final weighted verification score between 0.0 and 1.0.
        """
        if result.candidate is None:
            return 0.0
            
                            
        embedding_score = result.candidate.similarity_score
        detection_score = result.detection.confidence
        
                                                                                          
        mask_penalty = 0.0
        if result.mask and result.mask.has_mask:
                                                                                         
            if embedding_score < 0.5:
                mask_penalty = 0.10
                
                                
        final_score = (
            (embedding_score * self.weights["embedding"]) +
            (temporal_stability * self.weights["temporal"]) +
            (detection_score * self.weights["detection"])
        ) - mask_penalty
        
        return max(0.0, min(1.0, final_score))
