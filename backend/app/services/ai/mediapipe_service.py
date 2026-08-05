"""
MediaPipe FaceMesh Service.
Responsible for face landmark extraction and face alignment.
"""
import numpy as np
import cv2
from typing import Optional, List
from app.core.logger import get_logger
from app.sources.frame import Frame
from .models import LandmarkResult

try:
    import mediapipe as mp
except ImportError:
    mp = None

logger = get_logger(__name__)

class MediaPipeService:
    def __init__(self, max_num_faces: int = 1, min_detection_confidence: float = 0.5):
        self.max_num_faces = max_num_faces
        self.min_detection_confidence = min_detection_confidence
        self.face_mesh = None
        
    def load_model(self) -> None:
        if mp is None:
            raise ImportError("mediapipe package is required for MediaPipeService.")
            
        logger.info("Loading MediaPipe FaceMesh...")
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True, # We crop images first, so static mode is better
            max_num_faces=self.max_num_faces,
            refine_landmarks=True,
            min_detection_confidence=self.min_detection_confidence
        )
        logger.info("MediaPipe FaceMesh loaded successfully.")
        
    def unload_model(self) -> None:
        if self.face_mesh is not None:
            self.face_mesh.close()
            self.face_mesh = None
            logger.info("MediaPipe FaceMesh unloaded.")
            
    def _align_face(self, image: np.ndarray, left_eye: tuple, right_eye: tuple, desired_size: tuple = (112, 112)) -> np.ndarray:
        """
        Aligns a face image using the eye centers.
        This is a standard affine transform commonly used for AdaFace / ArcFace.
        """
        left_eye_center = np.array(left_eye, dtype=np.float32)
        right_eye_center = np.array(right_eye, dtype=np.float32)
        
        # Calculate angle
        dy = right_eye_center[1] - left_eye_center[1]
        dx = right_eye_center[0] - left_eye_center[0]
        angle = np.degrees(np.arctan2(dy, dx))
        
        # Calculate center
        eyes_center = ((left_eye_center[0] + right_eye_center[0]) / 2, 
                       (left_eye_center[1] + right_eye_center[1]) / 2)
                       
        # Get rotation matrix
        M = cv2.getRotationMatrix2D(eyes_center, angle, scale=1.0)
        
        # Adjust matrix for translation to center of output
        M[0, 2] += (desired_size[0] * 0.5) - eyes_center[0]
        M[1, 2] += (desired_size[1] * 0.4) - eyes_center[1] # Eyes slightly above center
        
        # Perform affine warp
        aligned_face = cv2.warpAffine(image, M, desired_size, flags=cv2.INTER_CUBIC)
        return aligned_face

    def extract_landmarks(self, face_crop: np.ndarray) -> Optional[LandmarkResult]:
        """
        Extracts landmarks from a face crop and returns an aligned image.
        """
        if self.face_mesh is None:
            raise RuntimeError("MediaPipe FaceMesh is not loaded.")
            
        # MediaPipe requires RGB
        try:
            img_rgb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
        except Exception as e:
            logger.error(f"Failed to convert face_crop to RGB: {e}")
            return None
            
        results = self.face_mesh.process(img_rgb)
        
        if not results.multi_face_landmarks:
            return None
            
        # Get first face
        face_landmarks = results.multi_face_landmarks[0]
        h, w = face_crop.shape[:2]
        
        # Convert normalized coordinates to absolute pixels
        landmarks_abs = np.array([(int(lm.x * w), int(lm.y * h)) for lm in face_landmarks.landmark])
        
        # Standard eye indices in MediaPipe FaceMesh
        # Left eye center approx index 468
        # Right eye center approx index 473
        left_eye_idx = 468
        right_eye_idx = 473
        
        if len(landmarks_abs) > 473:
            left_eye = tuple(landmarks_abs[left_eye_idx])
            right_eye = tuple(landmarks_abs[right_eye_idx])
            aligned_face = self._align_face(face_crop, left_eye, right_eye)
            
            # Extract upper face (approx top 60%) for masked recognition
            h_aligned = aligned_face.shape[0]
            upper_face = aligned_face[0:int(h_aligned * 0.6), :].copy()
            # Resize back to standard embedding size
            upper_face = cv2.resize(upper_face, (112, 112))
        else:
            aligned_face = cv2.resize(face_crop, (112, 112))
            upper_face = aligned_face.copy()
            
        return LandmarkResult(
            landmarks=landmarks_abs,
            aligned_face_crop=aligned_face,
            upper_face_crop=upper_face
        )
