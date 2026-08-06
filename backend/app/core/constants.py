"""
Application-wide constants.
No magic numbers should exist outside this file.
"""

         
PROJECT_NAME = "Vizage"
API_V1_STR = "/api/v1"

          
DEFAULT_DB_URL = "sqlite+aiosqlite:///vizage.db"

         
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)
LOG_ROTATION = "10 MB"
LOG_RETENTION = "14 days"
