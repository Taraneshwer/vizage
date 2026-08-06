from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from typing import List
import numpy as np
import cv2
import io
import csv
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.schemas.api_schemas import (
    EnrollmentResponse, 
    BaseResponse, 
    IdentityModel,
    UpdateIdentityRequest
)
from app.api.v1.dependencies import get_enrollment_orchestrator
from app.services.orchestrators.enrollment_orchestrator import EnrollmentOrchestrator
from app.sources.frame import Frame
from app.api.v1.exceptions.handlers import EnrollmentException
from app.db.session import get_db_session
from app.db.repository.identity_repo import IdentityRepository
from app.db.models import Identity

router = APIRouter(prefix="/enrollment", tags=["Enrollment"])

@router.get("", response_model=List[IdentityModel], summary="List Enrolled Identities")
async def list_identities(session: AsyncSession = Depends(get_db_session)):
    """Retrieves all enrolled persons from SQLite."""
    repo = IdentityRepository(session)
    identities = await repo.get_all_identities()
    
    return [
        IdentityModel(
            identity_id=ident.identity_id,
            name=ident.name,
            department=ident.department,
            notes=ident.notes,
            is_active=ident.is_active,
            recognition_count=ident.recognition_count,
            last_seen=ident.last_seen.isoformat() if ident.last_seen else None,
            enrollment_date=ident.created_at.isoformat()
        )
        for ident in identities
    ]

                                                                            
                                                                      
@router.get("/export", summary="Export Identities to CSV")
async def export_identities(session: AsyncSession = Depends(get_db_session)):
    repo = IdentityRepository(session)
    identities = await repo.get_all_identities()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Identity ID", "Name", "Department", "Active", "Recognitions", "Last Seen", "Enrollment Date"])
    
    for ident in identities:
        writer.writerow([
            ident.identity_id,
            ident.name,
            ident.department or "",
            "Yes" if ident.is_active else "No",
            ident.recognition_count,
            ident.last_seen.isoformat() if ident.last_seen else "Never",
            ident.created_at.isoformat()
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=identities.csv"}
    )

@router.post("", response_model=EnrollmentResponse, summary="Enroll Person")
async def enroll_person(
    identity_id: str = Form(...),
    name: str = Form(...),
    department: str = Form(None),
    files: List[UploadFile] = File(...),
    orchestrator: EnrollmentOrchestrator = Depends(get_enrollment_orchestrator),
    session: AsyncSession = Depends(get_db_session)
):
    """Enrolls a person into the database and FAISS using provided images."""
    frames = []
    for i, file in enumerate(files):
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is not None:
            frames.append(Frame(source_id="api_enrollment", frame_id=str(i), image=image))
            
    if not frames:
        raise EnrollmentException("No valid images provided for enrollment.")
        
                                 
    repo = IdentityRepository(session)
    existing = await repo.get_by_identity_id(identity_id)
    if existing:
        raise EnrollmentException(f"Identity ID {identity_id} already exists.")
        
                   
    result = orchestrator.enroll_person(identity_id=identity_id, name=name, frames=frames)
    
    if not result.success:
        raise EnrollmentException(f"Enrollment failed: {result.error_msg}")
        
                    
    new_identity = Identity(
        identity_id=identity_id,
        name=name,
        department=department
    )
    session.add(new_identity)
                                                                                        
        
    return EnrollmentResponse(success=True, identity_id=identity_id, message="Enrollment successful.")

@router.get("/{person_id}", response_model=IdentityModel, summary="Get Enrolled Person")
async def get_enrolled_person(person_id: str, session: AsyncSession = Depends(get_db_session)):
    repo = IdentityRepository(session)
    ident = await repo.get_by_identity_id(person_id)
    if not ident:
        raise HTTPException(status_code=404, detail="Person not found")
        
    return IdentityModel(
        identity_id=ident.identity_id,
        name=ident.name,
        department=ident.department,
        notes=ident.notes,
        is_active=ident.is_active,
        recognition_count=ident.recognition_count,
        last_seen=ident.last_seen.isoformat() if ident.last_seen else None,
        enrollment_date=ident.created_at.isoformat()
    )

@router.put("/{person_id}", response_model=BaseResponse, summary="Update Enrolled Person")
async def update_enrolled_person(
    person_id: str, 
    update_data: UpdateIdentityRequest, 
    session: AsyncSession = Depends(get_db_session)
):
    repo = IdentityRepository(session)
    ident = await repo.get_by_identity_id(person_id)
    if not ident:
        raise HTTPException(status_code=404, detail="Person not found")
        
    if update_data.name is not None:
        ident.name = update_data.name
    if update_data.department is not None:
        ident.department = update_data.department
    if update_data.notes is not None:
        ident.notes = update_data.notes
        
    return BaseResponse(success=True, message=f"Person {person_id} updated.")

@router.delete("/{person_id}", response_model=BaseResponse, summary="Delete Enrolled Person")
async def delete_enrolled_person(
    person_id: str, 
    orchestrator: EnrollmentOrchestrator = Depends(get_enrollment_orchestrator),
    session: AsyncSession = Depends(get_db_session)
):
    """Deletes an enrolled person from FAISS and SQLite."""
                        
    repo = IdentityRepository(session)
    ident = await repo.get_by_identity_id(person_id)
    if not ident:
        raise HTTPException(status_code=404, detail="Person not found")
        
    await session.delete(ident)
    
                       
    orchestrator.faiss.delete_embedding(person_id)
    orchestrator.faiss.save_index()
    
    return BaseResponse(success=True, message=f"Person {person_id} deleted.")
