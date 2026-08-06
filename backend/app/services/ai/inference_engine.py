"""
Inference Engine.
The primary orchestrator of the AI pipeline. Takes a raw Frame, pushes it through
Detection -> MediaPipe -> Mask -> Embedding -> Search, and returns a RecognitionContext.
"""
from typing import List, Optional
import cv2
import numpy as np
from app.core.logger import get_logger
from app.sources.frame import Frame
from .models import RecognitionContext, RecognitionResult, RecognitionCandidate
from .performance_monitor import PerformanceMonitor
from .model_manager import ModelManager
from .yolo_service import YOLODetectionService
from .mediapipe_service import MediaPipeService
from .mask_service import MaskDetectionService
from .embedding_service import AdaFaceService
from .faiss_service import FAISSService
from .decision.decision_engine import IdentityDecisionEngine
from .tracker_service import TrackerService

logger = get_logger(__name__)

class InferenceEngine:
    def __init__(self, model_manager: ModelManager, perf_monitor: PerformanceMonitor):
        self.model_manager = model_manager
        self.perf_monitor = perf_monitor
        self.decision_engine = IdentityDecisionEngine()
        self._is_ready = False
        
                                                                  
        try:
            self.yolo: YOLODetectionService = self.model_manager.get_service("YOLO11")
            self.mediapipe: MediaPipeService = self.model_manager.get_service("MediaPipe")
            self.mask: MaskDetectionService = self.model_manager.get_service("MaskDetector")
            self.embedding: AdaFaceService = self.model_manager.get_service("AdaFace")
            self.faiss: FAISSService = self.model_manager.get_service("FAISS")
            self.tracker: TrackerService = self.model_manager.get_service("Tracker")
            self._is_ready = True
        except KeyError as e:
            logger.error(f"Failed to initialize InferenceEngine: {e}")
            
    def process_frame(self, frame: Frame) -> RecognitionContext:
        """
        Executes the full recognition pipeline on a single frame.
        """
        context = RecognitionContext(frame=frame)
        if not self._is_ready:
            logger.warning("InferenceEngine is not fully initialized. Skipping frame.")
            return context
            
        timers = context.timers
        
                           
        self.perf_monitor.start_timer(timers, "yolo_detection")
        try:
            detections = self.yolo.detect(frame)
        except Exception as e:
            logger.error(f"YOLO Inference failed: {e}")
            detections = []
        det_time = self.perf_monitor.stop_timer(timers, "yolo_detection")
        self.model_manager.update_model_metrics("YOLO11", det_time)
        
        # Fallback to MediaPipe FaceMesh for face detection if YOLO found 0 faces
        if not detections:
            try:
                if self.mediapipe and getattr(self.mediapipe, "is_loaded", False) and self.mediapipe.face_mesh:
                    img_h, img_w = frame.image.shape[:2]
                    img_rgb = cv2.cvtColor(frame.image, cv2.COLOR_BGR2RGB)
                    results = self.mediapipe.face_mesh.process(img_rgb)
                    
                    if results and results.multi_face_landmarks:
                        face_landmarks = results.multi_face_landmarks[0]
                        landmarks_abs = np.array([(int(lm.x * img_w), int(lm.y * img_h)) for lm in face_landmarks.landmark])
                        
                        xs = landmarks_abs[:, 0]
                        ys = landmarks_abs[:, 1]
                        xmin, xmax = int(np.min(xs)), int(np.max(xs))
                        ymin, ymax = int(np.min(ys)), int(np.max(ys))
                        
                        # Add a 15% margin to match standard face detector crop
                        w_box = xmax - xmin
                        h_box = ymax - ymin
                        x1 = max(0, int(xmin - 0.15 * w_box))
                        y1 = max(0, int(ymin - 0.15 * h_box))
                        x2 = min(img_w, int(xmax + 0.15 * w_box))
                        y2 = min(img_h, int(ymax + 0.15 * h_box))
                        
                        face_crop = frame.image[y1:y2, x1:x2].copy()
                        
                        from app.services.ai.models import DetectionResult, BoundingBox
                        synthetic_det = DetectionResult(
                            bbox=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2),
                            confidence=0.95,
                            face_crop=face_crop
                        )
                        detections = [synthetic_det]
                        logger.info("YOLO detected 0 faces; successfully fell back to MediaPipe FaceMesh to detect face.")
            except Exception as e:
                logger.error(f"MediaPipe Face Detection fallback failed: {e}")
        
                                
        self.perf_monitor.start_timer(timers, "bytetrack")
        try:
            if frame.source_id and frame.source_id.startswith("api_"):
                tracked_detections = detections
                for idx, det in enumerate(tracked_detections):
                    det.tracking_id = f"static_{idx}"
            else:
                tracked_detections = self.tracker.update(detections, frame.image)
        except Exception as e:
            logger.error(f"Tracker failed: {e}")
            tracked_detections = detections
        track_time = self.perf_monitor.stop_timer(timers, "bytetrack")
        self.model_manager.update_model_metrics("Tracker", track_time)
        
                                       
        for idx, det in enumerate(tracked_detections):
            tracking_id = getattr(det, 'tracking_id', f"track_{idx}")
            result = RecognitionResult(detection=det, is_unknown=True, tracking_id=tracking_id)
            
                                    
            if det.face_crop is not None and det.face_crop.size > 0:
                self.perf_monitor.start_timer(timers, "mediapipe_landmarks")
                try:
                    lm_result = self.mediapipe.extract_landmarks(det.face_crop)
                    result.landmarks = lm_result
                except Exception as e:
                    logger.error(f"MediaPipe Inference failed: {e}")
                mp_time = self.perf_monitor.stop_timer(timers, "mediapipe_landmarks")
                self.model_manager.update_model_metrics("MediaPipe", mp_time)
                
                                    
                self.perf_monitor.start_timer(timers, "mask_detection")
                try:
                    mask_res = self.mask.detect_mask(det.face_crop)
                    result.mask = mask_res
                except Exception as e:
                    logger.error(f"Mask Detection failed: {e}")
                mask_time = self.perf_monitor.stop_timer(timers, "mask_detection")
                self.model_manager.update_model_metrics("MaskDetector", mask_time)
                
                                                  
                if result.landmarks and result.landmarks.aligned_face_crop is not None:
                                                 
                    is_masked = result.mask.has_mask if result.mask else False
                    if is_masked and result.landmarks.upper_face_crop is not None:
                        face_for_embedding = result.landmarks.upper_face_crop
                        is_upper = True
                    else:
                        face_for_embedding = result.landmarks.aligned_face_crop
                        is_upper = False
                        
                    self.perf_monitor.start_timer(timers, "adaface_embedding")
                    try:
                        emb = self.embedding.generate_embedding(face_for_embedding)
                        emb.is_upper_face = is_upper
                        result.embedding = emb
                    except Exception as e:
                        logger.error(f"AdaFace Inference failed: {e}")
                    ada_time = self.perf_monitor.stop_timer(timers, "adaface_embedding")
                    self.model_manager.update_model_metrics("AdaFace", ada_time)
                    
                                                        
                    if result.embedding:
                        self.perf_monitor.start_timer(timers, "faiss_search")
                        try:
                                                              
                            raw_candidates = self.faiss.search(result.embedding, k=5)
                            
                                                                   
                            result = self.decision_engine.process(result, raw_candidates)
                        except Exception as e:
                            logger.error(f"FAISS Search or Decision Engine failed: {e}")
                            result.is_unknown = True
                        faiss_time = self.perf_monitor.stop_timer(timers, "faiss_search")
                        self.model_manager.update_model_metrics("FAISS", faiss_time)
                        
            context.detections.append(result)
            
        self.perf_monitor.record_frame()
        return context
