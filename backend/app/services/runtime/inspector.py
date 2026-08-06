"""
Runtime Inspector.
Generates comprehensive point-in-time diagnostics of the entire backend.
"""
from typing import Dict, Any
from app.core.logger import get_logger
from app.services.ai.model_manager import ModelManager
from app.services.ai.gpu_manager import GPUManager

logger = get_logger(__name__)

class RuntimeInspector:
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        self.gpu_manager = GPUManager()
        
    def generate_report(self) -> Dict[str, Any]:
        logger.info("Generating Runtime Diagnostics Report...")
        
        report = {
            "health": "OK",
            "gpu": self.gpu_manager.get_status().model_dump(),
            "models": [m.model_dump() for m in self.model_manager.get_all_status()],
            "system": {
                "active_sessions": 0,                                                         
            }
        }
        
                                              
        for m in report["models"]:
            if m["status"] == "Error":
                report["health"] = "DEGRADED"
                
                          
        if report["gpu"]["is_available"]:
            if report["gpu"]["free_memory_mb"] < 500:
                report["health"] = "CRITICAL_MEMORY"
                
        return report
