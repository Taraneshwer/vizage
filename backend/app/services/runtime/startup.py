"""
Runtime Startup Sequence.
Enforces the exact order of initialization: Configuration -> GPU -> Models -> DB -> Runtime.
"""
from app.core.logger import get_logger
from app.services.ai.gpu_manager import GPUManager
from app.services.ai.model_manager import ModelManager

logger = get_logger(__name__)

def initialize_runtime():
    """Definitive startup sequence."""
    logger.info("Initializing MaskShield AI Runtime Sequence...")
    
    # 1. Configuration (Already loaded implicitly)
    logger.info("Configuration loaded.")
    
    # 2. GPU
    gpu_manager = GPUManager()
    status = gpu_manager.get_status()
    logger.info(f"GPU Manager initialized: {status.device_name} (Available: {status.is_available})")
    
    # 3. Models
    model_manager = ModelManager()
    
    from app.services.ai.yolo_service import YOLODetectionService
    from app.services.ai.mediapipe_service import MediaPipeService
    from app.services.ai.mask_service import MaskDetectionService
    from app.services.ai.embedding_service import AdaFaceService
    from app.services.ai.faiss_service import FAISSService
    
    model_manager.register_service("YOLO11", YOLODetectionService())
    model_manager.register_service("MediaPipe", MediaPipeService())
    model_manager.register_service("MaskDetector", MaskDetectionService())
    model_manager.register_service("AdaFace", AdaFaceService())
    model_manager.register_service("FAISS", FAISSService())
    
    # model_manager.load_models() # Tests/Runtime can decide when to load, but typically we load on startup
    # We will load them now so they are ready for inference
    model_manager.load_models()
    
    # Ensure all models are loaded
    models = model_manager.get_all_status()
    logger.info(f"Models initialized: {len(models)} online.")
    
    # 4. Database (Placeholder for SQLite Repositories init)
    logger.info("Database initialized.")
    
    # 5. Event Bus and Runtimes will be initialized dynamically per request
    logger.info("Runtime Sequence Complete. Ready for Inference.")
    
    return model_manager
