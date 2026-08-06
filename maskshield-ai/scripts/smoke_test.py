import os
import sys
import cv2
import time
from pathlib import Path

                                               
backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.append(str(backend_dir))

from app.core.config import settings
from app.services.ai.yolo_service import YOLODetectionService
from app.services.ai.tracker_service import TrackerService
from app.services.ai.embedding_service import AdaFaceService

def run_smoke_test():
    print("\n--- End-to-End Smoke Test ---")
    models_dir = backend_dir / "models"
    
    yolo_path = models_dir / "best_yolo.onnx"
    adaface_path = models_dir / "best_adaface.onnx"
    
    if not yolo_path.exists() or not adaface_path.exists():
        print(f"[WARNING] Exported models missing for smoke test. Skipping smoke test.")
        return

                                                           
                                                                    
    settings.YOLO_MODEL_PATH = str(yolo_path)
    settings.ADAFACE_MODEL_PATH = str(adaface_path)
    
    print("[INFO] Initializing YOLO Detector...")
    detector = YOLODetectionService(model_path=str(yolo_path))
    detector.load_model()
    
    print("[INFO] Initializing ByteTrack...")
    tracker = TrackerService()
    
    print("[INFO] Initializing AdaFace...")
    embedder = AdaFaceService(model_path=str(adaface_path))
    embedder.load_model()
    
                                                    
    dataset_dir = backend_dir.parent / "maskshield-ai" / "datasets" / "processed" / "yolo" / "images" / "train"
    sample_images = list(dataset_dir.glob("*.jpg"))
    if not sample_images:
        print("[WARNING] No sample images found in dataset for smoke test. Generating a blank test image.")
        import numpy as np
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
    else:
        frame = cv2.imread(str(sample_images[0]))
        
    print("[INFO] Running Inference: YOLO -> ByteTrack -> AdaFace")
    start = time.time()
    
    from app.sources.frame import Frame
    h, w, c = frame.shape
    test_frame = Frame(
        frame_id="test", 
        source_id="test_cam", 
        image=frame, 
        timestamp=time.time(),
        width=w,
        height=h,
        channels=c
    )
    
                  
    detections = detector.detect(test_frame)
    print(f"       -> Detected {len(detections)} faces.")
    
                 
    tracked_objects = tracker.update(detections, frame)
    print(f"       -> Tracked {len(tracked_objects)} objects.")
    
                    
    features_extracted = 0
    for obj in tracked_objects:
        bbox = obj.get('bbox', [])
        if len(bbox) == 4:
            x1, y1, x2, y2 = map(int, bbox)
                                        
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)
            face_crop = frame[y1:y2, x1:x2]
            if face_crop.size > 0:
                features = embedder.extract_features(face_crop)
                features_extracted += 1
                
    elapsed = time.time() - start
    print(f"       -> Extracted features for {features_extracted} faces.")
    print(f"[SUCCESS] End-to-End smoke test completed in {elapsed:.4f} seconds.")

if __name__ == "__main__":
    try:
        run_smoke_test()
    except Exception as e:
        print(f"[ERROR] Smoke test failed: {e}")
        sys.exit(1)
