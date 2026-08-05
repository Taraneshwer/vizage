"""
Services package for MaskShield AI Dataset Builder.

Provides the core business-logic services:

* :mod:`services.registry`   — :class:`DatasetRegistry` and :class:`DatasetSourceSpec`
* :mod:`services.downloader` — :class:`DatasetDownloader` and :class:`DownloadResult`

Example::

    from config.loader import load_config
    from services import DatasetDownloader, DatasetRegistry

    cfg = load_config()
    registry = DatasetRegistry.from_config(cfg)
    downloader = DatasetDownloader(cfg)
    results = downloader.download_all(registry.downloadable_specs())
"""

from services.downloader import DatasetDownloader, DownloadResult, DownloadStatus
from services.organizer import DatasetOrganizer, OrganizeMode, OrganizeResult
from services.preprocessor import (
    FaceCropHook,
    ImageMetadata,
    ImagePreprocessor,
    PreprocessingResult,
    ProcessingStatus,
)
from services.registry import DatasetRegistry, DatasetSourceSpec

__all__ = [
    "DatasetDownloader",
    "DownloadResult",
    "DownloadStatus",
    "DatasetOrganizer",
    "OrganizeMode",
    "OrganizeResult",
    "FaceCropHook",
    "ImageMetadata",
    "ImagePreprocessor",
    "PreprocessingResult",
    "ProcessingStatus",
    "DatasetRegistry",
    "DatasetSourceSpec",
]
