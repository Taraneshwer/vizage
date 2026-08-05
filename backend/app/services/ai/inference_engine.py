"""
Inference Engine.
The primary orchestrator of the AI pipeline. Takes a raw Frame, pushes it through
Detection -> MediaPipe -> Mask -> Embedding -> Search, and returns a RecognitionContext.
"""
from typing import List, Optional
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

logger = get_logger(__name__)

class InferenceEngine:
    def __init__(self, model_manager: ModelManager, perf_monitor: PerformanceMonitor):
        self.model_manager = model_manager
        self.perf_monitor = perf_monitor
        self.decision_engine = IdentityDecisionEngine()
        self._is_ready = False
        
        # We fetch the instantiated services from the ModelManager
        try:
            self.yolo: YOLODetectionService = self.model_manager.get_service("YOLO11")
            self.mediapipe: MediaPipeService = self.model_manager.get_service("MediaPipe")
            self.mask: MaskDetectionService = self.model_manager.get_service("MaskDetector")
            self.embedding: AdaFaceService = self.model_manager.get_service("AdaFace")
            self.faiss: FAISSService = self.model_manager.get_service("FAISS")
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
        
        # 1. Face Detection
        self.perf_monitor.start_timer(timers, "yolo_detection")
        try:
            detections = self.yolo.detect(frame)
        except Exception as e:
            logger.error(f"YOLO Inference failed: {e}")
            detections = []
        det_time = self.perf_monitor.stop_timer(timers, "yolo_detection")
        self.model_manager.update_model_metrics("YOLO11", det_time)
        
        # 2. Process each detected face
        for idx, det in enumerate(detections):
            # Give a pseudo tracking ID based on index for Temporal Memory to work
            # In a real system, a TrackingService (e.g., SORT/ByteTrack) would assign this.
            pseudo_tracking_id = f"track_{idx}"
            result = RecognitionResult(detection=det, is_unknown=True, tracking_id=pseudo_tracking_id)
            
            # 2.1 Landmark Alignment
            if det.face_crop is not None and det.face_crop.size > 0:
                self.perf_monitor.start_timer(timers, "mediapipe_landmarks")
                try:
                    lm_result = self.mediapipe.extract_landmarks(det.face_crop)
                    result.landmarks = lm_result
                except Exception as e:
                    logger.error(f"MediaPipe Inference failed: {e}")
                mp_time = self.perf_monitor.stop_timer(timers, "mediapipe_landmarks")
                self.model_manager.update_model_metrics("MediaPipe", mp_time)
                
                # 2.2 Mask Detection
                self.perf_monitor.start_timer(timers, "mask_detection")
                try:
                    mask_res = self.mask.detect_mask(det.face_crop)
                    result.mask = mask_res
                except Exception as e:
                    logger.error(f"Mask Detection failed: {e}")
                mask_time = self.perf_monitor.stop_timer(timers, "mask_detection")
                self.model_manager.update_model_metrics("MaskDetector", mask_time)
                
                # 2.3 AdaFace Embedding (Adaptive)
                if result.landmarks and result.landmarks.aligned_face_crop is not None:
                    # Adaptive Embedding Strategy
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
                    
                    # 2.4 FAISS Search & Decision Engine
                    if result.embedding:
                        self.perf_monitor.start_timer(timers, "faiss_search")
                        try:
                            # Fetch top 5 for Candidate Ranker
                            raw_candidates = self.faiss.search(result.embedding, k=5)
                            
                            # Push through Identity Decision Engine
                            result = self.decision_engine.process(result, raw_candidates)
                        except Exception as e:
                            logger.error(f"FAISS Search or Decision Engine failed: {e}")
                            result.is_unknown = True
                        faiss_time = self.perf_monitor.stop_timer(timers, "faiss_search")
                        self.model_manager.update_model_metrics("FAISS", faiss_time)
                        
            context.detections.append(result)
            
        self.perf_monitor.record_frame()
        return context
