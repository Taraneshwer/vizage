"""
Strict Service Interfaces (Dependency Inversion).
Implementations for AI components will be built in future milestones.
"""
from abc import ABC, abstractmethod
from typing import Any, List, Dict

class IModelManager(ABC):
    @abstractmethod
    def load_models(self) -> None:
        pass

class ICameraService(ABC):
    @abstractmethod
    def start_stream(self, source: str) -> None:
        pass
        
    @abstractmethod
    def read_frame(self) -> Any:
        pass

class IRecognitionService(ABC):
    @abstractmethod
    def recognize_face(self, frame: Any) -> Dict[str, Any]:
        pass

class IEnrollmentService(ABC):
    @abstractmethod
    def enroll_identity(self, name: str, images: List[Any]) -> bool:
        pass

class ITrackingService(ABC):
    @abstractmethod
    def update_tracks(self, detections: List[Any]) -> List[Any]:
        pass

class IVectorStoreService(ABC):
    @abstractmethod
    def add_embedding(self, identity_id: str, embedding: Any) -> None:
        pass
        
    @abstractmethod
    def search(self, embedding: Any, k: int = 1) -> List[Dict[str, Any]]:
        pass
