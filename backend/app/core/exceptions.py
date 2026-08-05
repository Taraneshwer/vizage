"""
Global exception handlers for FastAPI.
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from loguru import logger

class VizageException(Exception):
    """Base exception for all custom Vizage errors."""
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class ResourceNotFoundException(VizageException):
    def __init__(self, message: str):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)

async def vizage_exception_handler(request: Request, exc: VizageException):
    logger.error(f"VizageException: {exc.message} at {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "error_type": exc.__class__.__name__},
    )

async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled Exception at {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal Server Error"},
    )
