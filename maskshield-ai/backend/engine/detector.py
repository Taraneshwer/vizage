from typing import List, Dict, Any, Tuple
from ultralytics import YOLO
from loguru import logger
import numpy as np

class FaceDetectorTracker:
    """
    Wraps YOLO11 and ByteTrack for simultaneous face detection and multi-object tracking.
    """
    def __init__(self, model_path: str = "models/yolov8n.pt", conf_thresh: float = 0.5):
        self.model_path = model_path
        self.conf_thresh = conf_thresh
        try:
            self.model = YOLO(self.model_path)
            logger.info(f"Loaded YOLO model from {model_path}")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise

    def process_frame(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Runs detection and tracking on a single frame.
        Returns a list of tracked faces with bounding boxes and IDs.
        """
        # YOLO's track method includes ByteTrack if tracker is specified.
        results = self.model.track(frame, tracker="bytetrack.yaml", persist=True, conf=self.conf_thresh, verbose=False)
        tracked_faces = []
        
        if results and len(results) > 0:
            result = results[0]
            if result.boxes is not None:
                boxes = result.boxes.xyxy.cpu().numpy()
                confs = result.boxes.conf.cpu().numpy()
                
                if result.boxes.id is not None:
                    ids = result.boxes.id.int().cpu().numpy()
                else:
                    ids = [-1] * len(boxes)
                    
                for box, conf, track_id in zip(boxes, confs, ids):
                    x1, y1, x2, y2 = map(int, box)
                    tracked_faces.append({
                        "track_id": track_id,
                        "bbox": (x1, y1, x2, y2),
                        "confidence": float(conf)
                    })
        return tracked_faces
