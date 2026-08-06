"""
Identity Decision Engine.
Orchestrates the entire decision phase after FAISS search.
"""
from typing import List
from app.core.logger import get_logger
from app.services.ai.models import RecognitionResult, RecognitionCandidate, RecognitionState
from .threshold_manager import ThresholdManager
from .state_machine import RecognitionStateManager
from .session_manager import RecognitionSessionManager
from .confidence_fusion import ConfidenceFusionEngine
from .temporal_memory import TemporalMemory
from .candidate_ranker import CandidateRankingEngine
from .unknown_detector import UnknownDetectionEngine

logger = get_logger(__name__)

class IdentityDecisionEngine:
    def __init__(self):
        self.thresholds = ThresholdManager()
        self.state_manager = RecognitionStateManager()
        self.session_manager = RecognitionSessionManager()
        
        self.fusion = ConfidenceFusionEngine()
        self.temporal = TemporalMemory()
        
        self.ranker = CandidateRankingEngine(self.temporal, self.fusion)
        self.unknown_detector = UnknownDetectionEngine(self.thresholds)
        
    def process(self, result: RecognitionResult, raw_candidates: List[RecognitionCandidate]) -> RecognitionResult:
        """
        Takes raw candidates from FAISS and produces a final, explained recognition result.
        """
        tracking_id = result.tracking_id or "untracked"
        
                                                     
        quality_min = self.thresholds.get("quality_min")
        if result.detection.confidence < quality_min:
            result.is_unknown = True
            result.state = RecognitionState.SEARCHING
            return result
            
                                                                                      
        ranked = self.ranker.rank_candidates(raw_candidates, result)
        
        if not ranked:
            result.is_unknown = True
            result.state = RecognitionState.SEARCHING
            return result
            
                                                              
        top_candidate, top_score = ranked[0]
        self.temporal.update_track(tracking_id, top_candidate.identity_id, top_score)
        
                                                                                  
        stability = self.temporal.get_stability(tracking_id, top_candidate.identity_id)
        
                                    
                                                        
        result.candidate = top_candidate
        explanation = self.unknown_detector.evaluate(result, top_score)
        
                                       
        result.decision_explanation = explanation
        result.verification_score = top_score
        
                                 
        if explanation.is_accepted:
                                                                                    
            if stability >= self.thresholds.get("temporal_stability_min"):
                self.state_manager.transition(tracking_id, RecognitionState.RECOGNIZED)
            else:
                self.state_manager.transition(tracking_id, RecognitionState.VERIFYING)
                
            result.is_unknown = False
        else:
            self.state_manager.transition(tracking_id, RecognitionState.SEARCHING)
            result.is_unknown = True
            
        result.state = self.state_manager.get_state(tracking_id)
        
                              
        self.session_manager.log_recognition(is_unknown=result.is_unknown, confidence=top_score)
        
        return result
