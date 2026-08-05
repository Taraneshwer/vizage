"""
Augmentations package for MaskShield AI Dataset Builder.

Sub-modules
-----------
* :mod:`augmentations.transforms`     — Albumentations transform builders
* :mod:`augmentations.mask_simulator` — Synthetic mask & sunglasses overlays
* :mod:`augmentations.pipeline`       — Orchestrating pipeline service

Example::

    from config.loader import load_config
    from augmentations import AugmentationPipeline, MaskSimulator

    cfg = load_config()
    pipeline = AugmentationPipeline(cfg)
    results = pipeline.augment_directory_eager(
        src_dir=Path("datasets/identities"),
        dst_dir=Path("datasets/augmented"),
    )
"""

from augmentations.mask_simulator import (
    MaskSimulator,
    SunglassesSimulator,
    apply_random_mask,
    apply_random_sunglasses,
)
from augmentations.pipeline import AugmentationPipeline, AugmentationResult
from augmentations.transforms import build_preview_transform, build_transform_pipeline

__all__ = [
    # mask_simulator
    "MaskSimulator",
    "SunglassesSimulator",
    "apply_random_mask",
    "apply_random_sunglasses",
    # pipeline
    "AugmentationPipeline",
    "AugmentationResult",
    # transforms
    "build_transform_pipeline",
    "build_preview_transform",
]
