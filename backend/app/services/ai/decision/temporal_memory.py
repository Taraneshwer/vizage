"""
Temporal Memory.
Maintains short-term identity history across sequential frames to prevent flickering.
"""
from typing import Dict, List, Tuple
from collections import deque
from app.core.logger import get_logger
from app.services.ai.models import RecognitionCandidate

logger = get_logger(__name__)

class TrackHistory:
    def __init__(self, max_len: int = 10):
        self.max_len = max_len
        self.candidates: deque = deque(maxlen=max_len)
        self.scores: deque = deque(maxlen=max_len)
        
    def add(self, candidate_id: str, score: float):
        self.candidates.append(candidate_id)
        self.scores.append(score)
        
    @property
    def dominant_identity(self) -> str:
        if not self.candidates:
            return "UNKNOWN"
                                                   
        counts = {}
        for c in self.candidates:
            counts[c] = counts.get(c, 0) + 1
        return max(counts, key=counts.get)
        
    @property
    def stability(self) -> float:
        """Returns the ratio of frames that agree on the dominant identity."""
        if not self.candidates:
            return 0.0
        dom = self.dominant_identity
        count = sum(1 for c in self.candidates if c == dom)
        return count / len(self.candidates)

class TemporalMemory:
    def __init__(self, max_history_frames: int = 15):
        self.max_history_frames = max_history_frames
        self.tracks: Dict[str, TrackHistory] = {}
        
    def update_track(self, tracking_id: str, candidate_id: str, score: float) -> None:
        """Records a candidate for a specific track."""
        if tracking_id not in self.tracks:
            self.tracks[tracking_id] = TrackHistory(max_len=self.max_history_frames)
            
        self.tracks[tracking_id].add(candidate_id, score)
        
    def get_stability(self, tracking_id: str, candidate_id: str) -> float:
        """
        Returns the temporal stability of a SPECIFIC candidate in the current track.
        If the candidate is the dominant one, it gets the full stability score.
        If not, it gets a heavily penalized score.
        """
        if tracking_id not in self.tracks:
            return 0.0
            
        track = self.tracks[tracking_id]
        if not track.candidates:
            return 0.0
            
        count = sum(1 for c in track.candidates if c == candidate_id)
        return count / len(track.candidates)
        
    def remove_track(self, tracking_id: str) -> None:
        if tracking_id in self.tracks:
            del self.tracks[tracking_id]
