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
    
                 
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Auth
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 1 week
    
              
    DATABASE_URL: str = DEFAULT_DB_URL
    
             
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    
               
    YOLO_MODEL_PATH: str = str(MODELS_DIR / "best_yolo.onnx")
    ADAFACE_MODEL_PATH: str = str(MODELS_DIR / "best_adaface.onnx")
    MASK_MODEL_PATH: str = str(MODELS_DIR / "mask_detector.pth")
    EXECUTION_PROVIDER: str = "CUDA"                      
    
              
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
