"""
Stress Test Utility.
Benchmarks the Recognition Orchestrator and Inference Pipeline.
"""
import sys
import os
import asyncio
import time
import numpy as np

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.logger import get_logger
from app.sources.frame import Frame
from app.services.runtime.startup import initialize_runtime
from app.services.ai.inference_engine import InferenceEngine
from app.services.ai.performance_monitor import PerformanceMonitor

logger = get_logger(__name__)

async def run_benchmark():
    logger.info("Starting Stress Test...")
    model_manager = initialize_runtime()
    
    # Initialize components
    monitor = PerformanceMonitor()
    # Need to check if InferenceEngine takes perf_monitor in __init__ or if we inject it
    try:
        engine = InferenceEngine(model_manager=model_manager)
    except TypeError:
        # If the signature requires it
        engine = InferenceEngine(model_manager=model_manager, perf_monitor=monitor)
        
    logger.info("Warming up models...")
    dummy_frame = Frame(source_id="test", frame_id=0, image=np.zeros((640, 480, 3), dtype=np.uint8))
    engine.process_frame(dummy_frame)
    
    logger.info("Running 50 synthetic frames...")
    start_time = time.time()
    
    for i in range(1, 51):
        frame = Frame(source_id="test", frame_id=i, image=np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8))
        engine.process_frame(frame)
        
    end_time = time.time()
    elapsed = end_time - start_time
    fps = 50 / elapsed
    
    logger.info(f"Stress Test Complete. Elapsed: {elapsed:.2f}s, FPS: {fps:.2f}")
    
    # Output metrics
    for model_stat in model_manager.get_all_status():
        logger.info(f"Model: {model_stat.name} - Avg Latency: {model_stat.avg_inference_ms if model_stat.avg_inference_ms else 0:.2f}ms")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
