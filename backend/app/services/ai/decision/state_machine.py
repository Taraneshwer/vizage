"""
Recognition State Machine.
Tracks state transitions for an active track.
"""
from typing import Dict, Optional
from app.core.logger import get_logger
from app.services.ai.models import RecognitionState

logger = get_logger(__name__)

class RecognitionStateManager:
    def __init__(self):
        # Maps tracking_id to its current state
        self._states: Dict[str, RecognitionState] = {}
        
    def get_state(self, tracking_id: str) -> RecognitionState:
        """Retrieves the current state of a track, defaulting to SEARCHING."""
        return self._states.get(tracking_id, RecognitionState.SEARCHING)
        
    def transition(self, tracking_id: str, new_state: RecognitionState) -> None:
        """Transitions a track to a new state if valid."""
        current = self.get_state(tracking_id)
        if current != new_state:
            # logger.debug(f"Track {tracking_id} State Transition: {current.value} -> {new_state.value}")
            self._states[tracking_id] = new_state
            
    def remove_track(self, tracking_id: str) -> None:
        """Cleans up memory when a track is lost."""
        if tracking_id in self._states:
            del self._states[tracking_id]
