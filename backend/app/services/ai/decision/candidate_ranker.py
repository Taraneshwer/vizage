"""
Candidate Ranking Engine.
Re-ranks raw FAISS candidates using fused scores rather than raw cosine similarity.
"""
from typing import List, Tuple
from app.core.logger import get_logger
from app.services.ai.models import RecognitionCandidate, RecognitionResult
from .temporal_memory import TemporalMemory
from .confidence_fusion import ConfidenceFusionEngine

logger = get_logger(__name__)

class CandidateRankingEngine:
    def __init__(self, temporal_memory: TemporalMemory, fusion_engine: ConfidenceFusionEngine):
        self.temporal_memory = temporal_memory
        self.fusion_engine = fusion_engine
        
    def rank_candidates(
        self, 
        candidates: List[RecognitionCandidate], 
        result: RecognitionResult
    ) -> List[Tuple[RecognitionCandidate, float]]:
        """
        Takes raw FAISS candidates, calculates their fused verification score (which includes temporal),
        and returns them sorted by highest score.
        """
        if not candidates:
            return []
            
        tracking_id = result.tracking_id or "untracked"
        ranked = []
        
                                                                                    
        for candidate in candidates:
                                                                                    
            temp_result = result.copy(deep=False)
            temp_result.candidate = candidate
            
                                                                
            stability = self.temporal_memory.get_stability(tracking_id, candidate.identity_id)
            
                                  
            fused_score = self.fusion_engine.fuse_score(temp_result, stability)
            ranked.append((candidate, fused_score))
            
                                        
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked
