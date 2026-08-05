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
    # Add candidate A 4 times, candidate B 1 time
    for _ in range(4):
        mem.update_track("track_1", "ID_A", 0.9)
    mem.update_track("track_1", "ID_B", 0.8)
    
    assert mem.tracks["track_1"].dominant_identity == "ID_A"
    assert mem.get_stability("track_1", "ID_A") == 0.8 # 4 out of 5
    assert mem.get_stability("track_1", "ID_B") == 0.2 # 1 out of 5
    
def test_confidence_fusion(base_result):
    fusion = ConfidenceFusionEngine()
    
    candidate = RecognitionCandidate(identity_id="ID_A", similarity_score=0.8)
    base_result.candidate = candidate
    
    # Weights: embedding=0.60, temporal=0.25, detection=0.15
    # score = (0.8 * 0.60) + (1.0 * 0.25) + (0.9 * 0.15) = 0.48 + 0.25 + 0.135 = 0.865
    score = fusion.fuse_score(base_result, temporal_stability=1.0)
    assert abs(score - 0.865) < 0.001
    
    # Mask penalty test
    base_result.mask = MaskResult(has_mask=True, confidence=0.9)
    candidate.similarity_score = 0.4 # below 0.5 triggers mask penalty of 0.10
    # score = (0.4 * 0.60) + (1.0 * 0.25) + (0.9 * 0.15) - 0.10 = 0.24 + 0.25 + 0.135 - 0.10 = 0.525
    score = fusion.fuse_score(base_result, temporal_stability=1.0)
    assert abs(score - 0.525) < 0.001

def test_unknown_detector(base_result):
    thresholds = ThresholdManager()
    detector = UnknownDetectionEngine(thresholds)
    
    candidate = RecognitionCandidate(identity_id="ID_A", similarity_score=0.9)
    base_result.candidate = candidate
    
    # Test Known
    explanation = detector.evaluate(base_result, fused_score=0.8)
    assert explanation.is_accepted is True
    assert explanation.decision_type == "Known"
    
    # Test Possible Match
    explanation = detector.evaluate(base_result, fused_score=0.55)
    assert explanation.is_accepted is False
    assert explanation.decision_type == "Possible Match"
    
    # Test Unknown
    explanation = detector.evaluate(base_result, fused_score=0.3)
    assert explanation.is_accepted is False
    assert explanation.decision_type == "Unknown"
