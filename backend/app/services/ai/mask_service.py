"""
Mask Detection Service.
Detects whether a cropped face is wearing a mask.
"""
import numpy as np
from typing import Optional
from app.core.logger import get_logger
from .models import MaskResult
from .gpu_manager import GPUManager

try:
    import torch
    import torch.nn as nn
    import torchvision.transforms as transforms
except ImportError:
    torch = None

logger = get_logger(__name__)

class MaskDetectionService:
    def __init__(self, model_path: str = "mask_detector.pth"):
        self.model_path = model_path
        self.model = None
        self.is_loaded = False
        self.gpu_manager = GPUManager()
        if torch:
            self.transform = transforms.Compose([
                transforms.ToPILImage(),
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                     std=[0.229, 0.224, 0.225])
            ])
            
    def load_model(self) -> None:
        if torch is None:
            logger.error("PyTorch is required for MaskDetectionService.")
            self.is_loaded = False
            return
            
        logger.info(f"Loading Mask Detector from {self.model_path}...")
        
        try:
            import torchvision.models as models
            self.model = models.mobilenet_v2(pretrained=False)
            self.model.classifier[1] = nn.Linear(self.model.last_channel, 2)
            
            try:
                self.model.load_state_dict(torch.load(self.model_path, map_location='cpu'))
                self.model.eval()
                if getattr(self.gpu_manager, 'is_cuda', False):
                    self.model.to('cuda')
                self.is_loaded = True
                logger.info("Mask Detector loaded successfully.")
            except FileNotFoundError:
                logger.warning(f"Mask model weights not found at {self.model_path}. Running in degraded mode (no mask detection).")
                self.model = None
                self.is_loaded = False
        except Exception as e:
            logger.error(f"Failed to load Mask Detector: {e}")
            self.model = None
            self.is_loaded = False
        
    def unload_model(self) -> None:
        if self.model is not None:
            del self.model
            self.model = None
            self.is_loaded = False
            logger.info("Mask Detector unloaded.")
            
    def detect_mask(self, face_crop: np.ndarray) -> MaskResult:
        if not getattr(self, 'is_loaded', False) or self.model is None:
            return MaskResult(has_mask=False, confidence=0.0)
            
        # Preprocess
        input_tensor = self.transform(face_crop).unsqueeze(0)
        
        if getattr(self.gpu_manager, 'is_cuda', False):
            input_tensor = input_tensor.to('cuda')
            
        with torch.no_grad():
            with self.gpu_manager.autocast():
                outputs = self.model(input_tensor)
                probs = torch.nn.functional.softmax(outputs, dim=1)
                
        probs_cpu = probs.cpu().numpy()[0]
        # Class 0: No Mask, Class 1: Mask
        has_mask = bool(probs_cpu[1] > probs_cpu[0])
        confidence = float(probs_cpu[1] if has_mask else probs_cpu[0])
        
        return MaskResult(has_mask=has_mask, confidence=confidence)
