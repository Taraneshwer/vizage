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

if torch:
    class FaceModel(nn.Module):
        def __init__(self, embedding_size=512):
            super(FaceModel, self).__init__()
            import torchvision.models as models
            self.backbone = models.resnet50(pretrained=False)
            self.backbone.fc = nn.Linear(self.backbone.fc.in_features, embedding_size)
            self.bn = nn.BatchNorm1d(embedding_size)

        def forward(self, x):
            x = self.backbone(x)
            x = self.bn(x)
            return x
else:
    class FaceModel:
        pass


class AdaFaceService:
    def __init__(self, model_path: str = "adaface_ir100.pth"):
        self.model_path = model_path
        self.model = None
        self.is_loaded = False
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
        
        try:
            if self.model_path.endswith('.onnx'):
                if ort is None:
                    logger.error("onnxruntime is required for ONNX model inference.")
                    self.is_loaded = False
                    return
                if getattr(self.gpu_manager, 'is_cuda', False):
                    providers = [
                        ('CUDAExecutionProvider', {
                            'device_id': 0,
                            'arena_extend_strategy': 'kNextPowerOfTwo',
                            'cudnn_conv_algo_search': 'EXHAUSTIVE',
                            'do_copy_in_default_stream': True,
                        }),
                        'CPUExecutionProvider'
                    ]
                else:
                    providers = ['CPUExecutionProvider']
                self.model = ort.InferenceSession(self.model_path, providers=providers)
                self.is_onnx = True
                self.is_loaded = True
                logger.info("AdaFace ONNX model loaded successfully.")
                return

            if torch is None:
                logger.error("PyTorch is required for AdaFaceService.")
                self.is_loaded = False
                return
                
                              
            self.model = FaceModel(512)
            
            try:
                state_dict = torch.load(self.model_path, map_location='cpu')
                # Handle both bare keys (original AdaFace) and backbone-prefixed keys
                sample_key = next(iter(state_dict))
                if not sample_key.startswith('backbone.'):
                    # Remap: add 'backbone.' prefix to all conv/bn keys except the head
                    new_sd = {}
                    for k, v in state_dict.items():
                        if k.startswith('fc.') or k.startswith('bn.'):
                            new_sd[k] = v
                        else:
                            new_sd['backbone.' + k] = v
                    state_dict = new_sd
                missing, unexpected = self.model.load_state_dict(state_dict, strict=False)
                if missing:
                    logger.warning(f"AdaFace load_state_dict: {len(missing)} missing keys (e.g. {missing[:3]})")
                if unexpected:
                    logger.warning(f"AdaFace load_state_dict: {len(unexpected)} unexpected keys")
                logger.info("AdaFace weights loaded successfully.")
            except FileNotFoundError:
                logger.warning(f"AdaFace weights not found at {self.model_path}. Using random weights — recognition will be inaccurate!")
                
            self.model.eval()
            if getattr(self.gpu_manager, 'is_cuda', False):
                self.model.to('cuda')
            self.is_onnx = False
            self.is_loaded = True
            logger.info("AdaFace PyTorch model loaded successfully.")

        except Exception as e:
            logger.error(f"Failed to load AdaFace model: {e}")
            self.is_loaded = False
            return

        # Perform GPU Warmup
        try:
            dummy_crop = np.zeros((112, 112, 3), dtype=np.uint8)
            _ = self.generate_embedding(dummy_crop)
            logger.info("AdaFace model warmed up on GPU/CPU.")
        except Exception as w_err:
            logger.warning(f"AdaFace warmup warning: {w_err}")
        
    def unload_model(self) -> None:
        if self.model is not None:
            del self.model
            self.model = None
            self.is_loaded = False
            logger.info("AdaFace model unloaded.")
            
    def generate_embedding(self, aligned_face: np.ndarray) -> Optional[Embedding]:
        if not getattr(self, 'is_loaded', False) or self.model is None:
            return None
            
                                  
        if getattr(self, 'is_onnx', False):
                                
            img = cv2.cvtColor(aligned_face, cv2.COLOR_BGR2RGB)
            img = cv2.resize(img, (112, 112))
            img = (img.astype(np.float32) / 255.0 - 0.5) / 0.5
            img = np.transpose(img, (2, 0, 1))
            input_tensor = np.expand_dims(img, axis=0)
            
            input_name = self.model.get_inputs()[0].name
            features = self.model.run(None, {input_name: input_tensor})[0]
                                 
            emb_array = features[0] / np.linalg.norm(features[0])
        else:
            # Convert BGR (OpenCV) -> RGB before passing to the transform
            aligned_face_rgb = cv2.cvtColor(aligned_face, cv2.COLOR_BGR2RGB)
            input_tensor = self.transform(aligned_face_rgb).unsqueeze(0)
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
