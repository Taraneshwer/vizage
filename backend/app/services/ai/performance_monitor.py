"""
Performance Monitor for tracking inference latencies.
"""
import time
from typing import Dict, Any, List
from app.core.logger import get_logger

logger = get_logger(__name__)

class PerformanceMonitor:
    def __init__(self):
        self._metrics: Dict[str, List[float]] = {}
        self._frame_times: List[float] = []
        self._last_frame_time = None
        self._max_history = 100
        
    def start_timer(self, context_timers: Dict[str, float], operation: str) -> None:
        """Starts a timer for a specific operation in the context."""
        context_timers[f"{operation}_start"] = time.perf_counter()
        
    def stop_timer(self, context_timers: Dict[str, float], operation: str) -> float:
        """Stops the timer and records the duration."""
        start_key = f"{operation}_start"
        if start_key not in context_timers:
            return 0.0
            
        duration = (time.perf_counter() - context_timers[start_key]) * 1000 # to ms
        context_timers[f"{operation}_duration"] = duration
        
        self._record_metric(operation, duration)
        return duration
        
    def _record_metric(self, name: str, value: float) -> None:
        if name not in self._metrics:
            self._metrics[name] = []
        self._metrics[name].append(value)
        if len(self._metrics[name]) > self._max_history:
            self._metrics[name].pop(0)
            
    def record_frame(self) -> None:
        """Records frame completion to calculate FPS."""
        now = time.perf_counter()
        if self._last_frame_time is not None:
            self._frame_times.append(now - self._last_frame_time)
            if len(self._frame_times) > self._max_history:
                self._frame_times.pop(0)
        self._last_frame_time = now
        
    def get_fps(self) -> float:
        """Calculates moving average FPS."""
        if not self._frame_times:
            return 0.0
        avg_time = sum(self._frame_times) / len(self._frame_times)
        return 1.0 / avg_time if avg_time > 0 else 0.0
        
    def get_average_metric(self, operation: str) -> float:
        if operation not in self._metrics or not self._metrics[operation]:
            return 0.0
        return sum(self._metrics[operation]) / len(self._metrics[operation])
