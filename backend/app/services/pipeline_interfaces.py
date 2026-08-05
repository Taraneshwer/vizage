"""
Abstract interfaces for the future Processing Pipeline.
Ensures the Source Framework remains completely isolated from AI concepts.
"""
from abc import ABC, abstractmethod
from typing import Any, List, Dict
from app.sources.frame import Frame

class IProcessingStage(ABC):
    """
    A single stage in the AI processing pipeline.
    """
    @abstractmethod
    async def process(self, frame: Frame, context: Dict[str, Any]) -> Frame:
        """Executes the stage logic and updates the frame/context."""
        pass

class IPipelineOrchestrator(ABC):
    """
    Coordinates the execution of multiple IProcessingStages on a stream of Frames.
    """
    @abstractmethod
    def add_stage(self, stage: IProcessingStage) -> None:
        """Registers a processing stage (e.g. Detection, Alignment)."""
        pass
        
    @abstractmethod
    async def run_pipeline(self, frame: Frame) -> Dict[str, Any]:
        """Passes a frame through all registered stages sequentially."""
        pass
