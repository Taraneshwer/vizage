"""
Dependency Injection Layer.
Extracts singletons from the FastAPI app state to inject into routers.
"""
from fastapi import Request
from app.services.ai.model_manager import ModelManager
from app.services.ai.inference_engine import InferenceEngine
from app.services.runtime.camera_runtime import CameraRuntime
from app.services.orchestrators.recognition_orchestrator import RecognitionOrchestrator
from app.services.orchestrators.enrollment_orchestrator import EnrollmentOrchestrator
from app.services.runtime.inspector import RuntimeInspector
from app.core.runtime_config import app_runtime_config, RuntimeConfig

def get_settings() -> RuntimeConfig:
    return app_runtime_config

def get_model_manager(request: Request) -> ModelManager:
    return request.app.state.model_manager

def get_inference_engine(request: Request) -> InferenceEngine:
    return request.app.state.inference_engine

def get_camera_runtime(request: Request) -> CameraRuntime:
    return request.app.state.camera_runtime
    
def get_recognition_orchestrator(request: Request) -> RecognitionOrchestrator:
    return request.app.state.recognition_orchestrator

def get_enrollment_orchestrator(request: Request) -> EnrollmentOrchestrator:
    return request.app.state.enrollment_orchestrator
    
def get_runtime_inspector(request: Request) -> RuntimeInspector:
    return request.app.state.runtime_inspector
