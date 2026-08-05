import os
import sys
import cv2
import time
from pathlib import Path
import numpy as np

# Add backend to path so we can import services
backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.append(str(backend_dir))

from app.core.config import settings
from app.services.ai.yolo_service import YOLODetectionService
from app.services.ai.tracker_service import TrackerService
from app.services.ai.embedding_service import AdaFaceService
from app.sources.frame import Frame

def run_pre_train_verification():
    print("\n--- Pre-Training Inference Verification ---")
    models_dir = backend_dir / "models"
    yolo_path = models_dir / "yolo11n.pt"
    adaface_path = models_dir / "best_adaface.onnx"
    
    # Use official yolo11n.pt which will automatically download and detect 'person'
    if not adaface_path.exists():
        print(f"[ERROR] Required models not found in {models_dir}.")
        return

    # Initialize Services
    settings.YOLO_MODEL_PATH = str(yolo_path)
    settings.ADAFACE_MODEL_PATH = str(adaface_path)
    
    print("[INFO] Initializing Services...")
    detector = YOLODetectionService(model_path=str(yolo_path))
    detector.load_model()
    
    tracker = TrackerService()
    
    embedder = AdaFaceService(model_path=str(adaface_path))
    embedder.load_model()
    
    # Grab 10 sample images from LFW dataset
    dataset_dir = backend_dir.parent / "maskshield-ai" / "datasets" / "lfw"
    if not dataset_dir.exists():
        print(f"[ERROR] LFW dataset not found at {dataset_dir}")
        return
        
    sample_images = list(dataset_dir.rglob("*.jpg"))[:10]
    if not sample_images:
        print("[ERROR] No sample images found in LFW dataset.")
        return
        
    print(f"[INFO] Found {len(sample_images)} sample images. Running Inference...")
    
    success_count = 0
    
    for i, img_path in enumerate(sample_images):
        frame_bgr = cv2.imread(str(img_path))
        if frame_bgr is None:
            continue
            
        h, w, c = frame_bgr.shape
        test_frame = Frame(
            frame_id=f"test_{i}", 
            source_id="test_cam", 
            image=frame_bgr, 
            timestamp=time.time(),
            width=w,
            height=h,
            channels=c
        )
        
        print(f"\n[Image {i+1}] {img_path.name}")
        
        # 1. Detection
        detections = detector.detect(test_frame)
        print(f"  -> YOLO: Detected {len(detections)} faces.")
        
        if not detections:
            continue
            
        # 2. Tracking
        tracked_objects = tracker.update(detections, test_frame.image)
        print(f"  -> ByteTrack: Assigned {len(tracked_objects)} track IDs.")
        
        # 3. Recognition
        features_extracted = 0
        for obj in tracked_objects:
            if hasattr(obj, 'bbox'):
                x1, y1 = obj.bbox.x1, obj.bbox.y1
                x2, y2 = obj.bbox.x2, obj.bbox.y2
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                face_crop = frame_bgr[y1:y2, x1:x2]
                
                if face_crop.size > 0:
                    embedding_result = embedder.generate_embedding(face_crop)
                    if embedding_result is not None and len(embedding_result.vector) == 512:
                        features_extracted += 1
                        
        print(f"  -> AdaFace: Extracted {features_extracted} valid 512-d embeddings.")
        if features_extracted > 0:
            success_count += 1
            
    print(f"\n[RESULT] Verification successful on {success_count}/{len(sample_images)} images.")

if __name__ == "__main__":
    try:
        run_pre_train_verification()
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
