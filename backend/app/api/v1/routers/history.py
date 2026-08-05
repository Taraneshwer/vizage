from fastapi import APIRouter, Query, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional
import io
import csv
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.schemas.api_schemas import BaseResponse
from app.db.session import get_db_session
from app.db.repository.history_repo import HistoryRepository

router = APIRouter(prefix="/history", tags=["History"])

@router.get("", response_model=Dict[str, Any], summary="Get Recognition History")
async def get_history(
    limit: int = Query(50, description="Max records to return"),
    offset: int = Query(0, description="Pagination offset"),
    search: Optional[str] = Query(None, description="Search term"),
    session: AsyncSession = Depends(get_db_session)
):
    """Retrieves recognition history from SQLite."""
    repo = HistoryRepository(session)
    records, total = await repo.get_history(limit=limit, offset=offset, search=search)
    
    results = []
    for r in records:
        results.append({
            "history_id": r.id,
            "timestamp": r.timestamp.isoformat(),
            "identity_id": r.identity_id,
            "name": r.name,
            "department": r.department,
            "verification_score": r.verification_score,
            "mode": r.mode,
            "camera_id": r.camera_id,
            "tracking_id": r.tracking_id,
            "processing_time_ms": r.processing_time_ms,
            "state": r.state,
            "has_mask": r.has_mask
        })
        
    return {
        "success": True,
        "total": total,
        "limit": limit,
        "offset": offset,
        "records": results
    }

@router.delete("", response_model=BaseResponse, summary="Clear History")
async def clear_history(session: AsyncSession = Depends(get_db_session)):
    """Clears all recognition history."""
    repo = HistoryRepository(session)
    await repo.clear_all()
    return BaseResponse(success=True, message="History cleared.")

@router.delete("/{history_id}", response_model=BaseResponse, summary="Delete History Event")
async def delete_history_event(history_id: str, session: AsyncSession = Depends(get_db_session)):
    repo = HistoryRepository(session)
    # wait, HistoryRepository uses BaseModel which has `id` string (uuid)
    # let's write a quick method or use generic get
    event = await repo.get(history_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    await repo.delete(event)
    return BaseResponse(success=True, message=f"Event {history_id} deleted.")

@router.get("/export", summary="Export History to CSV")
async def export_history(session: AsyncSession = Depends(get_db_session)):
    """Exports history to CSV."""
    repo = HistoryRepository(session)
    # get all history for export (limit high)
    records, _ = await repo.get_history(limit=100000, offset=0, search=None)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(["Timestamp", "Identity ID", "Name", "Department", "Verification Score", "Mode", "Camera ID", "Tracking ID", "Processing Time (ms)", "State", "Has Mask"])
    
    for r in records:
        writer.writerow([
            r.timestamp.isoformat(),
            r.identity_id or "UNKNOWN",
            r.name or "Unknown Person",
            r.department or "",
            r.verification_score,
            r.mode,
            r.camera_id,
            r.tracking_id,
            r.processing_time_ms,
            r.state,
            "Yes" if r.has_mask else "No"
        ])
        
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=recognition_history.csv"}
    )
