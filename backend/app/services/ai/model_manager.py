"""
Model Manager for managing AI service lifecycles.
Provides lazy-loading, unloading, and status tracking to prevent VRAM overflow.
"""
import threading
from typing import Dict, Any, List
from app.core.logger import get_logger
from app.services.interfaces import IModelManager
from .models import ModelStatus
from .gpu_manager import GPUManager

logger = get_logger(__name__)

class ModelManager(IModelManager):
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ModelManager, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance
        
    def _initialize(self):
        self.gpu_manager = GPUManager()
        self.services: Dict[str, Any] = {}
        self.status: Dict[str, ModelStatus] = {}
        
    def register_service(self, name: str, service_instance: Any, backend: str = "PyTorch") -> None:
        """Registers an AI service for lifecycle management."""
        self.services[name] = service_instance
        self.status[name] = ModelStatus(
            name=name,
            status="Offline",
            device="CPU" if not getattr(self.gpu_manager, 'is_cuda', False) else "CUDA",
            backend=backend
        )
        logger.info(f"Registered AI Service: {name}")

    def load_models(self) -> None:
        """Iterates through registered services and invokes their internal load method."""
        for name, service in self.services.items():
            self.status[name].status = "Loading"
            try:
                if hasattr(service, "load_model"):
                    service.load_model()
                self.status[name].status = "Online"
                logger.info(f"Successfully loaded model: {name}")
            except Exception as e:
                self.status[name].status = "Error"
                self.status[name].error_message = str(e)
                logger.error(f"Failed to load model {name}: {e}")
                
    def unload_models(self) -> None:
        """Unloads all models to free up VRAM."""
        for name, service in self.services.items():
            try:
                if hasattr(service, "unload_model"):
                    service.unload_model()
                self.status[name].status = "Offline"
            except Exception as e:
                logger.error(f"Failed to unload model {name}: {e}")
        self.gpu_manager.empty_cache()
        logger.info("All AI models unloaded.")
        
    def get_service(self, name: str) -> Any:
        """Retrieves a registered service by name."""
        if name not in self.services:
            raise KeyError(f"AI Service '{name}' is not registered.")
        return self.services[name]
        
    def get_all_status(self) -> List[ModelStatus]:
        """Returns the status of all registered AI models."""
        return list(self.status.values())
        
    def update_model_metrics(self, name: str, inference_ms: float) -> None:
        """Updates real-time metrics for a specific model."""
        if name in self.status:
            current = self.status[name].avg_inference_ms
            if current is None:
                self.status[name].avg_inference_ms = inference_ms
            else:
                self.status[name].avg_inference_ms = (current * 0.9) + (inference_ms * 0.1)
