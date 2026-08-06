"""
Configuration management using Pydantic Settings.
Environment variables override these default values.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.core.constants import PROJECT_NAME, API_V1_STR, DEFAULT_DB_URL

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = BACKEND_DIR / "models"

class Settings(BaseSettings):
    """
    Application settings and configuration.
    """
    PROJECT_NAME: str = PROJECT_NAME
    API_V1_STR: str = API_V1_STR
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = DEFAULT_DB_URL
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    
    # AI Models
    YOLO_MODEL_PATH: str = str(MODELS_DIR / "best_yolo.onnx")
    ADAFACE_MODEL_PATH: str = str(MODELS_DIR / "best_adaface.onnx")
    MASK_MODEL_PATH: str = str(MODELS_DIR / "mask_detector.pth")
    EXECUTION_PROVIDER: str = "CUDA" # CPU, CUDA, TensorRT
    
    # Tracking
    TRACK_THRESH: float = 0.5
    MATCH_THRESH: float = 0.8
    TRACK_BUFFER: int = 30
    MIN_BOX_AREA: int = 100

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
