import pytest
from app.services.ai.decision.threshold_manager import ThresholdManager
from app.services.ai.decision.state_machine import RecognitionStateManager
from app.services.ai.decision.temporal_memory import TemporalMemory
from app.services.ai.decision.confidence_fusion import ConfidenceFusionEngine
from app.services.ai.decision.unknown_detector import UnknownDetectionEngine
from app.services.ai.decision.candidate_ranker import CandidateRankingEngine
from app.services.ai.models import (
    RecognitionState, RecognitionResult, RecognitionCandidate, 
    DetectionResult, BoundingBox, MaskResult
)

@pytest.fixture
def base_result():
    return RecognitionResult(
        detection=DetectionResult(
            bbox=BoundingBox(x1=0, y1=0, x2=100, y2=100),
            confidence=0.9
        ),
        is_unknown=True,
        tracking_id="track_0"
    )

def test_threshold_manager():
    manager = ThresholdManager()
    assert manager.get("quality_min") == 0.50
    manager.update("quality_min", 0.60)
    assert manager.get("quality_min") == 0.60
    
def test_state_machine():
    machine = RecognitionStateManager()
    assert machine.get_state("track_1") == RecognitionState.SEARCHING
    machine.transition("track_1", RecognitionState.VERIFYING)
    assert machine.get_state("track_1") == RecognitionState.VERIFYING
    
def test_temporal_memory():
    mem = TemporalMemory(max_history_frames=5)
                                                 
    for _ in range(4):
        mem.update_track("track_1", "ID_A", 0.9)
    mem.update_track("track_1", "ID_B", 0.8)
    
    assert mem.tracks["track_1"].dominant_identity == "ID_A"
    assert mem.get_stability("track_1", "ID_A") == 0.8             
    assert mem.get_stability("track_1", "ID_B") == 0.2             
    
def test_confidence_fusion(base_result):
    fusion = ConfidenceFusionEngine()
    
    candidate = RecognitionCandidate(identity_id="ID_A", similarity_score=0.8)
    base_result.candidate = candidate
    
                                                            
                                                                                      
    score = fusion.fuse_score(base_result, temporal_stability=1.0)
    assert abs(score - 0.865) < 0.001
    
                       
    base_result.mask = MaskResult(has_mask=True, confidence=0.9)
    candidate.similarity_score = 0.4                                          
                                                                                                    
    score = fusion.fuse_score(base_result, temporal_stability=1.0)
    assert abs(score - 0.525) < 0.001

def test_unknown_detector(base_result):
    thresholds = ThresholdManager()
    detector = UnknownDetectionEngine(thresholds)
    
    candidate = RecognitionCandidate(identity_id="ID_A", similarity_score=0.9)
    base_result.candidate = candidate
    
                
    explanation = detector.evaluate(base_result, fused_score=0.8)
    assert explanation.is_accepted is True
    assert explanation.decision_type == "Known"
    
                         
    explanation = detector.evaluate(base_result, fused_score=0.55)
    assert explanation.is_accepted is False
    assert explanation.decision_type == "Possible Match"
    
                  
    explanation = detector.evaluate(base_result, fused_score=0.3)
    assert explanation.is_accepted is False
    assert explanation.decision_type == "Unknown"
