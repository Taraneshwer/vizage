import cv2
import numpy as np
import mediapipe as mp
from loguru import logger
from typing import Optional, Tuple

class FaceAligner:
    """
    Uses MediaPipe FaceMesh to detect facial landmarks and align the face crop.
    """
    def __init__(self, output_size: Tuple[int, int] = (112, 112)):
        self.output_size = output_size
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )
        logger.info("Initialized MediaPipe Face Aligner")

    def align(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
        """
        Extracts and aligns the face from the frame using the bounding box.
        """
        x1, y1, x2, y2 = bbox
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        
        face_crop = frame[y1:y2, x1:x2]
        if face_crop.size == 0 or face_crop.shape[0] == 0 or face_crop.shape[1] == 0:
            return None

        rgb_crop = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_crop)
        
        # In a full production setup with full landmarks, we calculate an affine transform.
        # For Milestone 1, verifying the pipeline, standard resizing of the accurate crop suffices
        # if landmarks validate the presence of a face.
        if results.multi_face_landmarks:
            aligned_face = cv2.resize(face_crop, self.output_size)
            return aligned_face
            
        return None
