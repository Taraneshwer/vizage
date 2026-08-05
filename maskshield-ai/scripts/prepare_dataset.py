import os
import cv2
import numpy as np
import shutil
import hashlib
from pathlib import Path
from tqdm import tqdm
import random
import json
import logging

try:
    import mediapipe as mp
except ImportError:
    mp = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatasetPreparer:
    def __init__(self, data_root: str, output_root: str, blur_threshold: float = 100.0, target_size: tuple = (112, 112)):
        self.data_root = Path(data_root)
        self.output_root = Path(output_root)
        self.blur_threshold = blur_threshold
        self.target_size = target_size
        
        self.yolo_dir = self.output_root / "yolo"
        self.arcface_dir = self.output_root / "arcface"
        
        # Initialize MediaPipe for alignment
        if mp:
            self.mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=True, max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5
            )
        else:
            self.face_mesh = None
            logger.warning("MediaPipe not installed, face alignment will be skipped.")

    def _hash_image(self, img_path: str) -> str:
        """Computes MD5 hash of the file."""
        hasher = hashlib.md5()
        with open(img_path, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()

    def _is_blurry(self, image: np.ndarray) -> bool:
        """Calculates variance of Laplacian to determine blurriness."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.Laplacian(gray, cv2.CV_64F).var() < self.blur_threshold

    def _align_face(self, image: np.ndarray) -> np.ndarray:
        """Align face using MediaPipe landmarks."""
        if not self.face_mesh:
            return cv2.resize(image, self.target_size)
            
        img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(img_rgb)
        
        if not results.multi_face_landmarks:
            return cv2.resize(image, self.target_size)
            
        face_landmarks = results.multi_face_landmarks[0]
        h, w = image.shape[:2]
        
        landmarks_abs = [(int(lm.x * w), int(lm.y * h)) for lm in face_landmarks.landmark]
        left_eye_idx, right_eye_idx = 468, 473
        
        if len(landmarks_abs) > 473:
            left_eye_center = np.array(landmarks_abs[left_eye_idx], dtype=np.float32)
            right_eye_center = np.array(landmarks_abs[right_eye_idx], dtype=np.float32)
            
            dy = right_eye_center[1] - left_eye_center[1]
            dx = right_eye_center[0] - left_eye_center[0]
            angle = np.degrees(np.arctan2(dy, dx))
            
            eyes_center = ((left_eye_center[0] + right_eye_center[0]) / 2, 
                           (left_eye_center[1] + right_eye_center[1]) / 2)
                           
            M = cv2.getRotationMatrix2D(eyes_center, angle, scale=1.0)
            M[0, 2] += (self.target_size[0] * 0.5) - eyes_center[0]
            M[1, 2] += (self.target_size[1] * 0.4) - eyes_center[1]
            
            aligned_face = cv2.warpAffine(image, M, self.target_size, flags=cv2.INTER_CUBIC)
            return aligned_face
        return cv2.resize(image, self.target_size)

    def process_and_split(self):
        """Processes images, removes duplicates/blurry, splits and saves in YOLO and ArcFace formats."""
        logger.info("Starting dataset preparation...")
        
        # Setup directories
        for split in ['train', 'val', 'test']:
            (self.yolo_dir / 'images' / split).mkdir(parents=True, exist_ok=True)
            (self.yolo_dir / 'labels' / split).mkdir(parents=True, exist_ok=True)
            (self.arcface_dir / split).mkdir(parents=True, exist_ok=True)
            
        seen_hashes = set()
        metadata = {'processed': 0, 'corrupt': 0, 'blurry': 0, 'duplicates': 0, 'valid': 0}
        
        # Class 0: Face, Class 1: Masked Face
        classes = {'lfw': 0, 'mask': 1, 'IMFD': 0, 'CMFD': 1}
        
        all_images = []
        for dataset_name, class_id in classes.items():
            ds_path = self.data_root / dataset_name
            if not ds_path.exists():
                logger.warning(f"Dataset path {ds_path} not found. Skipping.")
                continue
                
            for img_path in ds_path.rglob('*.*'):
                if img_path.suffix.lower() not in ['.jpg', '.jpeg', '.png']:
                    continue
                all_images.append((img_path, class_id))
                
        random.seed(42)
        random.shuffle(all_images)
        
        # Train/Val/Test split (70/20/10)
        n = len(all_images)
        train_end = int(0.7 * n)
        val_end = int(0.9 * n)
        
        for idx, (img_path, class_id) in enumerate(tqdm(all_images, desc="Processing Images")):
            metadata['processed'] += 1
            
            # 1. Duplicate check
            img_hash = self._hash_image(str(img_path))
            if img_hash in seen_hashes:
                metadata['duplicates'] += 1
                continue
            seen_hashes.add(img_hash)
            
            # 2. Corrupt check
            img = cv2.imread(str(img_path))
            if img is None or img.size == 0:
                metadata['corrupt'] += 1
                continue
                
            # 3. Blurry check
            if self._is_blurry(img):
                metadata['blurry'] += 1
                continue
                
            # 4. Align face (for ArcFace)
            aligned_img = self._align_face(img)
            
            # Assign split
            if idx < train_end:
                split = 'train'
            elif idx < val_end:
                split = 'val'
            else:
                split = 'test'
                
            out_name = f"{img_hash}.jpg"
            
            # Save YOLO format (just copy the original image or resized image, here we save aligned for face tasks)
            # For YOLO detection, we assume the whole image is the face if it's already cropped in the dataset
            yolo_img_path = self.yolo_dir / 'images' / split / out_name
            cv2.imwrite(str(yolo_img_path), img) # Save unaligned for YOLO
            
            yolo_lbl_path = self.yolo_dir / 'labels' / split / f"{img_hash}.txt"
            h, w = img.shape[:2]
            # Bounding box is the whole image since these are cropped datasets
            with open(yolo_lbl_path, 'w') as f:
                f.write(f"{class_id} 0.5 0.5 1.0 1.0\n")
                
            # Save ArcFace format (aligned) - group by identity if available (LFW has folders)
            # Mask dataset might not have identities, so we use dummy identity or use it just for robust training
            identity = img_path.parent.name
            arcface_id_dir = self.arcface_dir / split / identity
            arcface_id_dir.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(arcface_id_dir / out_name), aligned_img)
            
            metadata['valid'] += 1

        # Generate YAML for YOLO
        yolo_yaml = {
            'path': str(self.yolo_dir.absolute()).replace("\\", "/"),
            'train': 'images/train',
            'val': 'images/val',
            'test': 'images/test',
            'names': {0: 'face', 1: 'masked_face'}
        }
        
        with open(self.yolo_dir / 'data.yaml', 'w') as f:
            for k, v in yolo_yaml.items():
                if isinstance(v, dict):
                    f.write(f"{k}:\n")
                    for k2, v2 in v.items():
                        f.write(f"  {k2}: '{v2}'\n")
                else:
                    f.write(f"{k}: '{v}'\n")
                    
        # Save Metadata
        with open(self.output_root / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=4)
            
        logger.info(f"Preparation complete: {metadata}")

if __name__ == "__main__":
    preparer = DatasetPreparer(
        data_root="c:/Users/LParikshith/Downloads/vizage/maskshield-ai/datasets",
        output_root="c:/Users/LParikshith/Downloads/vizage/maskshield-ai/datasets/processed",
        blur_threshold=50.0
    )
    preparer.process_and_split()
