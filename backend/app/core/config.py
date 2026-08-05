"""
Configuration management using Pydantic Settings.
Environment variables override these default values.
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.core.constants import PROJECT_NAME, API_V1_STR, DEFAULT_DB_URL

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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
