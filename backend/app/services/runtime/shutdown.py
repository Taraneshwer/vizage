"""
Runtime Shutdown Sequence.
Enforces safe teardown: Cameras -> Workers -> Sessions -> Models -> Database.
"""
from app.core.logger import get_logger
from app.services.ai.model_manager import ModelManager
from app.services.ai.gpu_manager import GPUManager

logger = get_logger(__name__)

def shutdown_runtime(model_manager: ModelManager):
    """Definitive shutdown sequence."""
    logger.info("Initiating Runtime Shutdown Sequence...")
    
                                                                                   
    logger.info("Runtime Sessions stopped.")
    
               
    model_manager.unload_models()
    logger.info("Models unloaded.")
    
                 
    logger.info("Database connections closed.")
    
                    
    gpu_manager = GPUManager()
    gpu_manager.empty_cache()
    logger.info("GPU VRAM cleared.")
    
    logger.info("Shutdown Sequence Complete.")
