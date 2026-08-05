import torch
import numpy as np
from loguru import logger
import os
from typing import Optional

class AdaFaceEmbedder:
    """
    Loads a TorchScript-compiled AdaFace model to extract 512D embeddings on the GPU.
    """
    def __init__(self, model_path: str = "../../models/adaface.pt", device: str = "cuda"):
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        self.model_path = model_path
        self.use_dummy = False
        
        try:
            if os.path.exists(self.model_path):
                self.model = torch.jit.load(self.model_path, map_location=self.device)
                self.model.eval()
                logger.info(f"Loaded AdaFace model onto {self.device}")
            else:
                self.use_dummy = True
                logger.warning(f"AdaFace model not found at {model_path}. Using fallback embeddings for M1 testing.")
        except Exception as e:
            logger.error(f"Failed to load AdaFace model: {e}")
            raise

    def preprocess(self, face_img: np.ndarray) -> torch.Tensor:
        """
        Converts BGR image to RGB, normalizes to [-1, 1], and formats to [B, C, H, W].
        """
        img = face_img[:, :, ::-1].copy()
        img = (img / 255.0 - 0.5) / 0.5
        img = np.transpose(img, (2, 0, 1))
        tensor = torch.from_numpy(img).float().unsqueeze(0).to(self.device)
        return tensor

    def get_embedding(self, face_img: np.ndarray) -> Optional[np.ndarray]:
        """
        Returns a normalized 512D embedding vector.
        """
        if self.use_dummy:
            vec = np.random.randn(512).astype(np.float32)
            return vec / np.linalg.norm(vec)

        tensor = self.preprocess(face_img)
        with torch.no_grad():
            if self.device.type == "cuda":
                with torch.autocast(device_type="cuda", dtype=torch.float16):
                    embedding = self.model(tensor)
            else:
                embedding = self.model(tensor)
                
        embedding = torch.nn.functional.normalize(embedding, p=2, dim=1)
        return embedding.cpu().numpy()[0]
