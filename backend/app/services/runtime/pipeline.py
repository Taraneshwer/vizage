"""
Runtime Pipeline Middleware.
Enables adding arbitrary steps (metrics, logging, custom filters) to the frame processing path.
"""
from abc import ABC, abstractmethod
from typing import Any, List, Dict
from app.sources.frame import Frame
from app.services.ai.models import RecognitionContext
from app.core.logger import get_logger

logger = get_logger(__name__)

class IMiddleware(ABC):
    @abstractmethod
    def process_before(self, frame: Frame) -> Frame:
        """Called before the InferenceEngine processes the frame."""
        pass
        
    @abstractmethod
    def process_after(self, context: RecognitionContext) -> RecognitionContext:
        """Called after the InferenceEngine has populated the context."""
        pass

class LoggingMiddleware(IMiddleware):
    def process_before(self, frame: Frame) -> Frame:
                                                                  
        return frame
        
    def process_after(self, context: RecognitionContext) -> RecognitionContext:
        if context.detections:
            num_faces = len(context.detections)
            logger.debug(f"Detected {num_faces} faces in frame.")
        return context

class MemoryOptimizationMiddleware(IMiddleware):
    def process_before(self, frame: Frame) -> Frame:
        return frame
        
    def process_after(self, context: RecognitionContext) -> RecognitionContext:
        """Drops bulky image arrays from the context to free memory."""
                               
        if getattr(context.frame, 'image', None) is not None:
            context.frame.image = None
            
        for det in context.detections:
            if det.detection:
                det.detection.face_crop = None
            if det.landmarks:
                det.landmarks.aligned_face_crop = None
                det.landmarks.upper_face_crop = None
                
        return context

class RuntimePipeline:
    def __init__(self):
        self.middlewares: List[IMiddleware] = []
        
    def add_middleware(self, middleware: IMiddleware):
        self.middlewares.append(middleware)
        
    def run_before(self, frame: Frame) -> Frame:
        for mw in self.middlewares:
            try:
                frame = mw.process_before(frame)
            except Exception as e:
                logger.error(f"Middleware {mw.__class__.__name__} failed in process_before: {e}")
        return frame
        
    def run_after(self, context: RecognitionContext) -> RecognitionContext:
        for mw in self.middlewares:
            try:
                context = mw.process_after(context)
            except Exception as e:
                logger.error(f"Middleware {mw.__class__.__name__} failed in process_after: {e}")
        return context
