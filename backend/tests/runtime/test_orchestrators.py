import pytest
import asyncio
import numpy as np
from app.core.events import EventBus, FrameCapturedEvent
from app.sources.frame import Frame
from app.services.runtime.pipeline import RuntimePipeline, LoggingMiddleware, MemoryOptimizationMiddleware
from app.services.runtime.recovery import ErrorRecoveryManager
from app.services.ai.models import RecognitionContext
from app.services.runtime.inspector import RuntimeInspector

@pytest.fixture
def mock_frame():
    return Frame(source_id="test_cam", frame_id=1, image=np.zeros((480, 640, 3), dtype=np.uint8))

@pytest.fixture
def mock_context(mock_frame):
    ctx = RecognitionContext(frame=mock_frame)
    return ctx

def test_event_bus_publish():
    bus = EventBus()
    events_received = []
    
    async def handler(event):
        events_received.append(event)
        
    bus.subscribe(FrameCapturedEvent, handler)
    
    async def run():
        await bus.publish(FrameCapturedEvent(camera_id="cam_1", frame_id=100))
        
    asyncio.run(run())
    
    assert len(events_received) == 1
    assert events_received[0].frame_id == 100

def test_pipeline_middleware(mock_frame, mock_context):
    pipeline = RuntimePipeline()
    pipeline.add_middleware(LoggingMiddleware())
    pipeline.add_middleware(MemoryOptimizationMiddleware())
    
    result_frame = pipeline.run_before(mock_frame)
    assert result_frame.frame_id == mock_frame.frame_id
    
                               
    assert mock_context.frame.image is not None
    result_context = pipeline.run_after(mock_context)
    assert result_context.frame.image is None

def test_error_recovery():
    recovery = ErrorRecoveryManager()
                                                 
    try:
        raise Exception("CUDA out of memory in test")
    except Exception as e:
        recovery.handle_exception(e, source="test")
        
                        
    try:
        raise Exception("Camera disconnected unexpectedly")
    except Exception as e:
        recovery.handle_exception(e, source="test")
        
def test_runtime_inspector():
                                      
    class MockModelManager:
        def get_all_status(self):
            return []
            
    inspector = RuntimeInspector(MockModelManager())
    report = inspector.generate_report()
    
    assert "health" in report
    assert "gpu" in report
    assert "models" in report
    assert report["health"] in ["OK", "DEGRADED", "CRITICAL_MEMORY"]
