"""
Custom API Exceptions for MaskShield AI.
"""
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from app.core.logger import get_logger

logger = get_logger(__name__)

class ApplicationException(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class RecognitionException(ApplicationException):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message, status_code)

class EnrollmentException(ApplicationException):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message, status_code)

class CameraException(ApplicationException):
    def __init__(self, message: str, status_code: int = 503):
        super().__init__(message, status_code)

class RuntimeException(ApplicationException):
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message, status_code)

def setup_exception_handlers(app):
    """Register global exception handlers for the FastAPI app."""
    
    @app.exception_handler(ApplicationException)
    async def application_exception_handler(request: Request, exc: ApplicationException):
        logger.error(f"ApplicationException: {exc.message} on {request.url.path}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.__class__.__name__, "message": exc.message},
        )
        
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled Exception: {str(exc)} on {request.url.path}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "InternalServerError", "message": "An unexpected error occurred."},
        )
