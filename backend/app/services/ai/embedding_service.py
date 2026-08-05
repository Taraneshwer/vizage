"""
AdaFace Embedding Service.
Generates facial embeddings from aligned face crops.
"""
import numpy as np
from typing import Optional
import cv2
from app.core.logger import get_logger
from .models import Embedding
from .gpu_manager import GPUManager

try:
    import torch
    import torch.nn as nn
    import torchvision.transforms as transforms
except ImportError:
    torch = None

try:
    import onnxruntime as ort
except ImportError:
    ort = None

logger = get_logger(__name__)

class AdaFaceService:
    def __init__(self, model_path: str = "adaface_ir100.pth"):
        self.model_path = model_path
        self.model = None
        self.gpu_manager = GPUManager()
        if torch:
            self.transform = transforms.Compose([
                transforms.ToPILImage(),
                transforms.Resize((112, 112)),
                transforms.ToTensor(),
                transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])
            ])
            
    def load_model(self) -> None:
        logger.info(f"Loading AdaFace from {self.model_path}...")
        
        if self.model_path.endswith('.onnx'):
            if ort is None:
                raise ImportError("onnxruntime is required for ONNX model inference.")
            providers = ['CUDAExecutionProvider'] if getattr(self.gpu_manager, 'is_cuda', False) else ['CPUExecutionProvider']
            self.model = ort.InferenceSession(self.model_path, providers=providers)
            self.is_onnx = True
            logger.info("AdaFace ONNX model loaded successfully.")
            return

        if torch is None:
            raise ImportError("PyTorch is required for AdaFaceService.")
            
        # PyTorch fallback
        import torchvision.models as models
        self.model = models.resnet50(pretrained=False)
        self.model.fc = nn.Linear(self.model.fc.in_features, 512)
        
        try:
            self.model.load_state_dict(torch.load(self.model_path, map_location='cpu'))
        except FileNotFoundError:
            logger.warning(f"AdaFace weights not found at {self.model_path}. Using uninitialized ResNet50.")
            
        self.model.eval()
        if getattr(self.gpu_manager, 'is_cuda', False):
            self.model.to('cuda')
        self.is_onnx = False
        logger.info("AdaFace PyTorch model loaded successfully.")
        
    def unload_model(self) -> None:
        if self.model is not None:
            del self.model
            self.model = None
            logger.info("AdaFace model unloaded.")
            
    def generate_embedding(self, aligned_face: np.ndarray) -> Embedding:
        if self.model is None:
            raise RuntimeError("AdaFace model is not loaded.")
            
        # Apply transform directly
        if getattr(self, 'is_onnx', False):
            # ONNX preprocessing
            img = cv2.cvtColor(aligned_face, cv2.COLOR_BGR2RGB)
            img = cv2.resize(img, (112, 112))
            img = (img.astype(np.float32) / 255.0 - 0.5) / 0.5
            img = np.transpose(img, (2, 0, 1))
            input_tensor = np.expand_dims(img, axis=0)
            
            input_name = self.model.get_inputs()[0].name
            features = self.model.run(None, {input_name: input_tensor})[0]
            # Normalize embedding
            emb_array = features[0] / np.linalg.norm(features[0])
        else:
            input_tensor = self.transform(aligned_face).unsqueeze(0)
            if getattr(self.gpu_manager, 'is_cuda', False):
                input_tensor = input_tensor.to('cuda')
                
            with torch.no_grad():
                with self.gpu_manager.autocast():
                    features = self.model(input_tensor)
                    features = torch.nn.functional.normalize(features, p=2, dim=1)
            emb_array = features.cpu().numpy()[0]
        
        return Embedding(
            vector=emb_array,
            model_version="adaface_ir100"
        )
