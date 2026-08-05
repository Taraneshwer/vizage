import cv2
import time
import os
from loguru import logger
from capture import VideoCaptureThread
from detector import FaceDetectorTracker
from aligner import FaceAligner
from embedder import AdaFaceEmbedder

def main():
    logger.info("Initializing MaskShield AI Core Engine (Milestone 1)...")
    
    # Ensure models directory exists for future downloads
    os.makedirs("../../models", exist_ok=True)
    
    # Initialize Pipeline Components
    try:
        capture = VideoCaptureThread(source=0).start()
        # Fallback to standard yolov8n.pt if a dedicated face model isn't provided yet
        detector = FaceDetectorTracker(model_path="yolov8n.pt") 
        aligner = FaceAligner()
        embedder = AdaFaceEmbedder(model_path="../../models/adaface.pt")
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        return

    logger.info("Pipeline initialized. Press 'q' to quit.")
    
    try:
        while True:
            frame = capture.read()
            if frame is None:
                continue
                
            start_time = time.time()
            
            faces = detector.process_frame(frame)
            
            for face in faces:
                bbox = face["bbox"]
                track_id = face["track_id"]
                
                aligned_face = aligner.align(frame, bbox)
                if aligned_face is not None:
                    embedding = embedder.get_embedding(aligned_face)
                    
                    x1, y1, x2, y2 = bbox
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    label = f"ID: {track_id} (Emb: {embedding[0]:.2f})"
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            fps = 1.0 / (time.time() - start_time)
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            
            cv2.imshow("MaskShield AI - Core Engine", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
    finally:
        capture.stop()
        cv2.destroyAllWindows()
        logger.info("Shutdown complete.")

if __name__ == "__main__":
    main()
