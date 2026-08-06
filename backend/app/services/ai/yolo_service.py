"""
YOLO11 Face Detection Service.
Responsible for detecting faces and extracting tight face crops.
"""
import numpy as np
import time
from typing import List, Optional
from app.core.logger import get_logger
from app.sources.frame import Frame
from .models import DetectionResult, BoundingBox
from .gpu_manager import GPUManager

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

logger = get_logger(__name__)

class YOLODetectionService:
    def __init__(self, model_path: str = "yolov8n-face.pt", conf_threshold: float = 0.5):
        # using v8n-face as placeholder for face model
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.model = None
        self.is_loaded = False
        self.gpu_manager = GPUManager()
        
    def load_model(self) -> None:
        """Loads the YOLO model into the allocated GPU/CPU."""
        if YOLO is None:
            logger.error("ultralytics package is required for YOLO Detection.")
            self.is_loaded = False
            return
            
        logger.info(f"Loading YOLO model from {self.model_path}...")
        
        try:
            # YOLO auto-detects .pt, .onnx, and .engine. We specify task to ensure correct inference mode.
            self.model = YOLO(self.model_path, task='detect')
            
            # Only call .to() for PyTorch weights (.pt)
            if self.model_path.endswith('.pt') and getattr(self.gpu_manager, 'is_cuda', False):
                self.model.to('cuda')
                
            self.is_loaded = True
            logger.info("YOLO model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            self.is_loaded = False
        
    def unload_model(self) -> None:
        """Unloads the YOLO model."""
        if self.model is not None:
            del self.model
            self.model = None
            self.is_loaded = False
            logger.info("YOLO model unloaded.")
            
    def detect(self, frame: Frame) -> List[DetectionResult]:
        """
        Runs inference on the frame and returns bounding boxes and face crops.
        """
        if not getattr(self, 'is_loaded', False) or self.model is None:
            return []
            
        img_array = frame.image
        results = []
        
        with self.gpu_manager.autocast():
            # YOLO inference
            preds = self.model(img_array, conf=self.conf_threshold, verbose=False)
            
        for pred in preds:
            boxes = pred.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = float(box.conf[0].item())
                
                # Ensure bounds are within the image
                h, w = img_array.shape[:2]
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                
                # Extract crop
                face_crop = img_array[y1:y2, x1:x2].copy()
                
                if face_crop.size == 0:
                    continue
                    
                results.append(DetectionResult(
                    bbox=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2),
                    confidence=conf,
                    face_crop=face_crop
                ))
                
        return results
