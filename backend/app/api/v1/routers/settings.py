from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.api.v1.dependencies import get_settings
from app.core.runtime_config import RuntimeConfig
from app.api.v1.schemas.api_schemas import BaseResponse

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("", response_model=Dict[str, Any], summary="Get Runtime Settings")
async def get_current_settings(config: RuntimeConfig = Depends(get_settings)):
    return config.model_dump()

@router.put("", response_model=BaseResponse, summary="Update Runtime Settings")
async def update_settings(updates: Dict[str, Any], config: RuntimeConfig = Depends(get_settings)):
    """Update settings (requires application restart for some to take effect)."""
    # Just update the pydantic model in memory for now
    for k, v in updates.items():
        if hasattr(config, k):
            setattr(config, k, v)
    return BaseResponse(success=True, message="Settings updated in memory.")
