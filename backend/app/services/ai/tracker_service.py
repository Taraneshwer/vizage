"""
ByteTrack Tracking Service.
Assigns persistent IDs to detected faces across frames.
"""
from typing import List, Dict, Any
import numpy as np
from app.core.logger import get_logger
from .models import DetectionResult

try:
    from ultralytics.trackers import BOTSORT, BYTETracker
except ImportError:
    BYTETracker = None

logger = get_logger(__name__)

class TrackerService:
    def __init__(self, track_thresh: float = 0.5, track_buffer: int = 30, match_thresh: float = 0.8, min_box_area: int = 100):
        self.track_thresh = track_thresh
        self.track_buffer = track_buffer
        self.match_thresh = match_thresh
        self.min_box_area = min_box_area
        self.tracker = None
        
    def load_model(self) -> None:
        if BYTETracker is None:
            logger.warning("ultralytics trackers not found. We will use a mock tracker.")
            return
            
                                                        
        class TrackerArgs:
            def __init__(self, track_thresh, track_buffer, match_thresh):
                self.track_high_thresh = track_thresh
                self.track_low_thresh = 0.1
                self.new_track_thresh = track_thresh
                self.track_buffer = track_buffer
                self.match_thresh = match_thresh
                self.gmc_method = 'sparseOptFlow'
                
        args = TrackerArgs(self.track_thresh, self.track_buffer, self.match_thresh)
        
        import inspect
        try:
            sig = inspect.signature(BYTETracker.__init__)
            if 'frame_rate' in sig.parameters:
                self.tracker = BYTETracker(args, frame_rate=30)
            else:
                self.tracker = BYTETracker(args)
        except Exception:
                                                
            self.tracker = BYTETracker(args)
            
        logger.info("ByteTrack loaded successfully.")
        
    def unload_model(self) -> None:
        self.tracker = None
        logger.info("ByteTrack unloaded.")
        
    def update(self, detections: List[DetectionResult], frame_img: np.ndarray) -> List[DetectionResult]:
        """
        Updates the tracker with new detections and assigns tracking_ids.
        """
        if not detections:
            return []
            
        if self.tracker is None:
                                                    
            for idx, det in enumerate(detections):
                det.tracking_id = f"mock_{idx}"
            return detections
            
                                                                        
        dets_array = []
        for det in detections:
            dets_array.append([
                det.bbox.x1, det.bbox.y1, det.bbox.x2, det.bbox.y2, 
                det.confidence, 0                   
            ])
            
        dets_tensor = np.array(dets_array)
        
                                                                                            
                                                                       
        import torch
        dets_tensor = torch.tensor(dets_tensor)
        
                        
        tracks = self.tracker.update(dets_tensor, frame_img)
        
        tracked_results = []
                                                                                                      
                                                                
        
        for track in tracks:
            x1, y1, x2, y2, track_id, conf, cls = track
            
                            
            area = (x2 - x1) * (y2 - y1)
            if area < self.min_box_area:
                continue
                
                                                             
            h, w = frame_img.shape[:2]
            cx1, cy1 = max(0, int(x1)), max(0, int(y1))
            cx2, cy2 = min(w, int(x2)), min(h, int(y2))
            
            face_crop = frame_img[cy1:cy2, cx1:cx2].copy()
            
            if face_crop.size == 0:
                continue
                
                                                                                                                       
                                                                         
            
            from .models import DetectionResult, BoundingBox
            tracked_results.append(DetectionResult(
                bbox=BoundingBox(x1=cx1, y1=cy1, x2=cx2, y2=cy2),
                confidence=float(conf),
                face_crop=face_crop,
                tracking_id=str(int(track_id))
            ))
            
        return tracked_results
