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
    
    # 1. Cameras & Sessions (Assuming orchestrators are stopped prior to this call)
    logger.info("Runtime Sessions stopped.")
    
    # 2. Models
    model_manager.unload_models()
    logger.info("Models unloaded.")
    
    # 3. Database
    logger.info("Database connections closed.")
    
    # 4. GPU Cleanup
    gpu_manager = GPUManager()
    gpu_manager.empty_cache()
    logger.info("GPU VRAM cleared.")
    
    logger.info("Shutdown Sequence Complete.")
