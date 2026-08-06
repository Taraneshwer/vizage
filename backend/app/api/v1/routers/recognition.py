from fastapi import APIRouter, Depends, UploadFile, File
from typing import List
import numpy as np
import cv2
from app.api.v1.schemas.api_schemas import RecognitionResultModel, BatchRecognitionResultModel
from app.api.v1.dependencies import get_inference_engine
from app.services.ai.inference_engine import InferenceEngine
from app.sources.frame import Frame
from app.api.v1.exceptions.handlers import RecognitionException

router = APIRouter(prefix="/recognition", tags=["Recognition"])

async def process_image_upload(file: UploadFile, engine: InferenceEngine) -> RecognitionResultModel:
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if image is None:
        raise RecognitionException(f"Invalid image file: {file.filename}")
        
    frame = Frame(source_id="api_upload", frame_id="0", image=image)
    context = engine.process_frame(frame)
    
    if not context.detections:
        raise RecognitionException("No faces detected in image.")
        
                                                                                   
                                                                     
    det = context.detections[0]                                      
    
    candidate_model = None
    if det.candidate:
        candidate_model = {
            "identity_id": det.candidate.identity_id,
            "similarity_score": det.candidate.similarity_score,
            "name": det.candidate.name
        }
        
    bbox = None
    if det.detection:
        bbox = {
            "x1": det.detection.bbox.x1,
            "y1": det.detection.bbox.y1,
            "x2": det.detection.bbox.x2,
            "y2": det.detection.bbox.y2
        }
        
    return RecognitionResultModel(
        is_unknown=det.is_unknown,
        state=det.state.name,
        verification_score=det.verification_score,
        candidate=candidate_model,
        bbox=bbox,
        tracking_id=det.tracking_id,
        has_mask=det.mask.has_mask if det.mask else False,
        processing_time_ms=sum([v for k,v in context.timers.items() if k.endswith("_duration")])
    )

@router.post("", response_model=RecognitionResultModel, summary="Recognize Single Image")
async def recognize_single(
    file: UploadFile = File(...),
    engine: InferenceEngine = Depends(get_inference_engine)
):
    """Processes a single uploaded image and returns recognition results."""
    return await process_image_upload(file, engine)

@router.post("/batch", response_model=BatchRecognitionResultModel, summary="Recognize Batch of Images")
async def recognize_batch(
    files: List[UploadFile] = File(...),
    engine: InferenceEngine = Depends(get_inference_engine)
):
    """Processes multiple uploaded images and returns a batch of results."""
    results = []
    for file in files:
        try:
            res = await process_image_upload(file, engine)
            results.append(res)
        except Exception as e:
                                                        
            pass
            
    return BatchRecognitionResultModel(success=True, results=results)
