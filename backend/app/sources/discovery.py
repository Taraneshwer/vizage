"""
Interfaces for discovering network and local video sources dynamically.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pydantic import BaseModel

class DiscoveredDevice(BaseModel):
    """Represents a dynamically discovered hardware or network camera."""
    device_id: str
    name: str
    source_type: str
    connection_uri: str
    metadata: Dict[str, Any] = {}

class ISourceDiscoveryService(ABC):
    """
    Interface for scanning and returning available camera devices.
    Future implementations will handle ONVIF, UPnP, and OS-level USB enumeration.
    """
    @abstractmethod
    async def scan_usb_cameras(self) -> List[DiscoveredDevice]:
        """Scans local USB/PCIe video capture devices."""
        pass
        
    @abstractmethod
    async def scan_network_cameras(self) -> List[DiscoveredDevice]:
        """Scans local network for RTSP, ONVIF, or ESP32 devices."""
        pass
