"""
Health Monitor for unified AI subsystem diagnostics.
"""
import time
from typing import Dict, Any
from app.core.logger import get_logger
from .models import SystemHealth
from .gpu_manager import GPUManager
from .model_manager import ModelManager
from .performance_monitor import PerformanceMonitor

logger = get_logger(__name__)

class HealthMonitor:
    def __init__(self, 
                 gpu_manager: GPUManager, 
                 model_manager: ModelManager,
                 perf_monitor: PerformanceMonitor):
        self.gpu_manager = gpu_manager
        self.model_manager = model_manager
        self.perf_monitor = perf_monitor
        self.start_time = time.time()
        
    def get_system_health(self) -> SystemHealth:
        """Collects metrics from all managers and returns a structured health object."""
        return SystemHealth(
            gpu=self.gpu_manager.get_status(),
            models=self.model_manager.get_all_status(),
            uptime_seconds=time.time() - self.start_time,
            fps=self.perf_monitor.get_fps()
        )
