"""
GPU Manager for handling CUDA operations, memory, and mixed precision context.
Implemented as a Singleton to ensure unified resource management.
"""
import torch
import gc
from typing import Any, Dict, Optional
import threading
from app.core.logger import get_logger
from .models import GPUStatus

logger = get_logger(__name__)

class GPUManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(GPUManager, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance
        
    def _initialize(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.is_cuda = self.device.type == 'cuda'
        
        if self.is_cuda:
            logger.info(f"GPU Manager initialized. Device: {torch.cuda.get_device_name(0)}")
            # Optimize cudnn for fixed input sizes if possible
            torch.backends.cudnn.benchmark = True
        else:
            logger.warning("GPU Manager initialized on CPU. Performance will be degraded.")
            
    def get_device(self) -> torch.device:
        """Returns the primary compute device."""
        return self.device
        
    def empty_cache(self) -> None:
        """Forces Python garbage collection and CUDA cache clearing."""
        gc.collect()
        if self.is_cuda:
            torch.cuda.empty_cache()
            
    def get_status(self) -> GPUStatus:
        """Retrieves real-time GPU statistics."""
        if not self.is_cuda:
            return GPUStatus(
                is_available=False,
                device_name="CPU",
                total_memory_mb=0,
                allocated_memory_mb=0,
                free_memory_mb=0
            )
            
        try:
            device_id = torch.cuda.current_device()
            props = torch.cuda.get_device_properties(device_id)
            allocated = torch.cuda.memory_allocated(device_id)
            reserved = torch.cuda.memory_reserved(device_id)
            total = props.total_memory
            
            return GPUStatus(
                is_available=True,
                device_name=props.name,
                total_memory_mb=total // (1024 * 1024),
                allocated_memory_mb=allocated // (1024 * 1024),
                free_memory_mb=(total - reserved) // (1024 * 1024),
                utilization_percent=None, # Needs pynvml for accurate util, optional
                temperature=None
            )
        except Exception as e:
            logger.error(f"Failed to get GPU status: {e}")
            return GPUStatus(
                is_available=True,
                device_name="Unknown CUDA Device",
                total_memory_mb=0,
                allocated_memory_mb=0,
                free_memory_mb=0
            )

    def autocast(self):
        """
        Returns a context manager for mixed precision inference.
        Usage:
            with gpu_manager.autocast():
                model(input)
        """
        if self.is_cuda:
            return torch.amp.autocast('cuda')
        else:
            from contextlib import nullcontext
            return nullcontext()
