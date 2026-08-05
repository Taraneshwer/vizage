"""
Unknown Detection Engine.
Classifies the final fused result against configurable thresholds.
"""
from typing import Tuple
from app.core.logger import get_logger
from app.services.ai.models import RecognitionResult, DecisionExplanation
from .threshold_manager import ThresholdManager

logger = get_logger(__name__)

class UnknownDetectionEngine:
    def __init__(self, threshold_manager: ThresholdManager):
        self.thresholds = threshold_manager
        
    def evaluate(self, result: RecognitionResult, fused_score: float) -> DecisionExplanation:
        """
        Determines whether the candidate should be accepted, marked as possible match, or unknown.
        """
        if not result.candidate:
            return DecisionExplanation(
                reason="No candidate provided by FAISS",
                is_accepted=False,
                decision_type="Unknown"
            )
            
        # Determine applicable threshold
        is_masked = result.mask.has_mask if result.mask else False
        threshold = self.thresholds.get("masked_verification_min" if is_masked else "unmasked_verification_min")
        unknown_max = self.thresholds.get("unknown_max")
        
        explanation = DecisionExplanation(
            embedding_score=result.candidate.similarity_score,
            temporal_stability=fused_score, # For simplicity here
            tracking_score=result.detection.confidence,
            is_accepted=False,
            decision_type="Unknown",
            reason=""
        )
        
        # Logic branches
        if fused_score >= threshold:
            explanation.is_accepted = True
            explanation.decision_type = "Known"
            explanation.reason = f"Fused score ({fused_score:.2f}) exceeded threshold ({threshold:.2f})"
        elif fused_score >= unknown_max:
            explanation.is_accepted = False
            explanation.decision_type = "Possible Match"
            explanation.reason = f"Fused score ({fused_score:.2f}) in ambiguous range ({unknown_max:.2f} - {threshold:.2f})"
        else:
            explanation.is_accepted = False
            explanation.decision_type = "Unknown"
            explanation.reason = f"Fused score ({fused_score:.2f}) below unknown threshold ({unknown_max:.2f})"
            
        return explanation
