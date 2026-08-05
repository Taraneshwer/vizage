"""
Configuration package for MaskShield AI Dataset Builder.

Exposes the top-level :class:`AppConfig` model and the
:func:`load_config` factory so consumers only need a single import.
"""

from config.loader import load_config
from config.models import (
    AppConfig,
    AugmentationConfig,
    DatasetEntryConfig,
    DatasetsConfig,
    DownloaderConfig,
    PathsConfig,
    PreprocessingConfig,
    ProjectConfig,
    SplitsConfig,
    StatisticsConfig,
    ValidationConfig,
)

__all__ = [
    "load_config",
    "AppConfig",
    "AugmentationConfig",
    "DatasetEntryConfig",
    "DatasetsConfig",
    "DownloaderConfig",
    "PathsConfig",
    "PreprocessingConfig",
    "ProjectConfig",
    "SplitsConfig",
    "StatisticsConfig",
    "ValidationConfig",
]
