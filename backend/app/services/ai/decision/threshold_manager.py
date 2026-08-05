"""
Threshold Manager for Identity Decision Engine.
Stores and validates configuration thresholds for recognition.
"""
from typing import Dict
from app.core.logger import get_logger

logger = get_logger(__name__)

class ThresholdManager:
    def __init__(self):
        # Default thresholds
        self._thresholds: Dict[str, float] = {
            "masked_verification_min": 0.55, # Stricter for upper-face only
            "unmasked_verification_min": 0.60,
            "unknown_max": 0.45,             # Below this is strictly unknown
            "quality_min": 0.50,
            "temporal_stability_min": 0.70
        }
        
    def get(self, key: str) -> float:
        """Retrieves a specific threshold."""
        if key not in self._thresholds:
            raise KeyError(f"Threshold '{key}' not found.")
        return self._thresholds[key]
        
    def update(self, key: str, value: float) -> None:
        """Updates a threshold dynamically."""
        if key not in self._thresholds:
            logger.warning(f"Attempted to update unknown threshold: {key}")
            return
        if not (0.0 <= value <= 1.0):
            raise ValueError("Thresholds must be between 0.0 and 1.0")
            
        logger.info(f"Updated threshold {key}: {self._thresholds[key]} -> {value}")
        self._thresholds[key] = value

    def get_all(self) -> Dict[str, float]:
        return self._thresholds.copy()
