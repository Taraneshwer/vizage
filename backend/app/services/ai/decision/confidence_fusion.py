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
        When there is no temporal history (stability == 0), the temporal weight is
        redistributed to the embedding score so single-frame results aren't penalised.
        """
        if result.candidate is None:
            return 0.0
            
                            
        embedding_score = result.candidate.similarity_score
        detection_score = result.detection.confidence
        
        # If no temporal history yet, boost embedding weight to compensate
        if temporal_stability == 0.0:
            emb_w   = self.weights["embedding"] + self.weights["temporal"]
            temp_w  = 0.0
            det_w   = self.weights["detection"]
        else:
            emb_w   = self.weights["embedding"]
            temp_w  = self.weights["temporal"]
            det_w   = self.weights["detection"]
                                                                                          
        mask_penalty = 0.0
        if result.mask and result.mask.has_mask:
                                                                                         
            if embedding_score < 0.5:
                mask_penalty = 0.10
                
                                
        final_score = (
            (embedding_score * emb_w) +
            (temporal_stability * temp_w) +
            (detection_score * det_w)
        ) - mask_penalty
        
        return max(0.0, min(1.0, final_score))
