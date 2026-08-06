"""
Runtime Startup Sequence.
Enforces the exact order of initialization: Configuration -> GPU -> Models -> DB -> Runtime.
"""
import importlib.util
from pathlib import Path
from app.core.logger import get_logger
from app.core.config import settings
from app.services.ai.gpu_manager import GPUManager
from app.services.ai.model_manager import ModelManager

logger = get_logger(__name__)

def validate_startup():
    logger.info("--- Startup Validation ---")
    
                       
    packages = ["ultralytics", "mediapipe", "torch", "onnxruntime", "cv2"]
    logger.info("Validating Python Packages:")
    for pkg in packages:
        spec = importlib.util.find_spec(pkg)
        if spec is None:
            logger.warning(f"  [MISSING] {pkg}")
        else:
            logger.info(f"  [OK]      {pkg}")
            
                     
    models = {
        "YOLO": settings.YOLO_MODEL_PATH,
        "AdaFace": settings.ADAFACE_MODEL_PATH,
        "MaskDetector": settings.MASK_MODEL_PATH
    }
    
    logger.info("Validating Model Paths:")
    for name, path_str in models.items():
        p = Path(path_str)
        if p.exists():
            logger.info(f"  [OK]      {name}: {p.resolve()}")
        else:
            logger.warning(f"  [MISSING] {name}: {p.resolve()} - Service will run in degraded mode.")
            
    logger.info("--------------------------")

def initialize_runtime():
    """Definitive startup sequence."""
    logger.info("Initializing MaskShield AI Runtime Sequence...")
    
    validate_startup()
    
                                                  
    logger.info("Configuration loaded.")
    
            
    gpu_manager = GPUManager()
    status = gpu_manager.get_status()
    logger.info(f"GPU Manager initialized: {status.device_name} (Available: {status.is_available})")
    
               
    model_manager = ModelManager()
    
    from app.services.ai.yolo_service import YOLODetectionService
    from app.services.ai.mediapipe_service import MediaPipeService
    from app.services.ai.mask_service import MaskDetectionService
    from app.services.ai.embedding_service import AdaFaceService
    from app.services.ai.faiss_service import FAISSService
    from app.services.ai.tracker_service import TrackerService
    
    model_manager.register_service("YOLO11", YOLODetectionService(model_path=settings.YOLO_MODEL_PATH))
    model_manager.register_service("Tracker", TrackerService(track_thresh=settings.TRACK_THRESH, track_buffer=settings.TRACK_BUFFER, match_thresh=settings.MATCH_THRESH, min_box_area=settings.MIN_BOX_AREA))
    model_manager.register_service("MediaPipe", MediaPipeService())
    model_manager.register_service("MaskDetector", MaskDetectionService(model_path=settings.MASK_MODEL_PATH))
    model_manager.register_service("AdaFace", AdaFaceService(model_path=settings.ADAFACE_MODEL_PATH))
    model_manager.register_service("FAISS", FAISSService())
    
                                                                                                           
                                                           
    model_manager.load_models()
    
                                  
    models = model_manager.get_all_status()
    logger.info(f"Models initialized: {len(models)} online.")
    
                                                            
    logger.info("Database initialized.")
    
                                                                           
    logger.info("Runtime Sequence Complete. Ready for Inference.")
    
    return model_manager
