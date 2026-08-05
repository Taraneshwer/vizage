"""
Albumentations transform builders for MaskShield AI Dataset Builder.

This module converts the typed config models from
:mod:`config.models` into concrete ``albumentations`` transform objects.
Every function is **pure** — given the same config it always returns the
same transform; no state, no randomness at construction time.

The :func:`build_transform_pipeline` function is the primary entry-point:
it assembles all enabled transforms into a single
``albumentations.Compose`` object that the :class:`~augmentations.pipeline.AugmentationPipeline`
applies to images.

Custom transforms (:class:`~augmentations.mask_simulator`) are **not**
built here; they are integrated at the pipeline level.

Example::

    from config.loader import load_config
    from augmentations.transforms import build_transform_pipeline

    cfg = load_config()
    transform = build_transform_pipeline(cfg.augmentation, seed=42)
    augmented = transform(image=img_array)["image"]
"""

from __future__ import annotations

import albumentations as A
from albumentations.core.transforms_interface import ImageOnlyTransform

from config.models import AugmentationConfig


# ---------------------------------------------------------------------------
# Individual transform builders
# ---------------------------------------------------------------------------


def _build_rotation(cfg: AugmentationConfig) -> A.BasicTransform | None:
    """Build a ``SafeRotate`` transform if rotation is enabled.

    Args:
        cfg: Augmentation configuration.

    Returns:
        Albumentations transform or ``None`` if disabled.
    """
    rc = cfg.transforms.rotation
    if not rc.enabled:
        return None
    return A.SafeRotate(
        limit=rc.limit_degrees,
        p=rc.probability,
        border_mode=0,  # cv2.BORDER_CONSTANT
    )


def _build_brightness_contrast(cfg: AugmentationConfig) -> A.BasicTransform | None:
    """Build a ``RandomBrightnessContrast`` transform.

    Args:
        cfg: Augmentation configuration.

    Returns:
        Albumentations transform or ``None`` if disabled.
    """
    bc = cfg.transforms.brightness_contrast
    if not bc.enabled:
        return None
    return A.RandomBrightnessContrast(
        brightness_limit=bc.brightness_limit,
        contrast_limit=bc.contrast_limit,
        p=bc.probability,
    )


def _build_gaussian_noise(cfg: AugmentationConfig) -> A.BasicTransform | None:
    """Build a ``GaussNoise`` transform.

    Args:
        cfg: Augmentation configuration.

    Returns:
        Albumentations transform or ``None`` if disabled.
    """
    gn = cfg.transforms.gaussian_noise
    if not gn.enabled:
        return None
    return A.GaussNoise(
        var_limit=gn.var_limit,
        p=gn.probability,
    )


def _build_gaussian_blur(cfg: AugmentationConfig) -> A.BasicTransform | None:
    """Build a ``GaussianBlur`` transform.

    Args:
        cfg: Augmentation configuration.

    Returns:
        Albumentations transform or ``None`` if disabled.
    """
    gb = cfg.transforms.gaussian_blur
    if not gb.enabled:
        return None
    # blur_limit must be a list/tuple of odd integers; albumentations handles this.
    return A.GaussianBlur(
        blur_limit=list(gb.blur_limit),
        p=gb.probability,
    )


def _build_motion_blur(cfg: AugmentationConfig) -> A.BasicTransform | None:
    """Build a ``MotionBlur`` transform.

    Args:
        cfg: Augmentation configuration.

    Returns:
        Albumentations transform or ``None`` if disabled.
    """
    mb = cfg.transforms.motion_blur
    if not mb.enabled:
        return None
    return A.MotionBlur(
        blur_limit=mb.blur_limit,
        p=mb.probability,
    )


def _build_jpeg_compression(cfg: AugmentationConfig) -> A.BasicTransform | None:
    """Build an ``ImageCompression`` (JPEG artefacts) transform.

    Args:
        cfg: Augmentation configuration.

    Returns:
        Albumentations transform or ``None`` if disabled.
    """
    jc = cfg.transforms.jpeg_compression
    if not jc.enabled:
        return None
    return A.ImageCompression(
        quality_lower=jc.quality_lower,
        quality_upper=jc.quality_upper,
        compression_type=A.ImageCompression.ImageCompressionType.JPEG,
        p=jc.probability,
    )


def _build_horizontal_flip(cfg: AugmentationConfig) -> A.BasicTransform | None:
    """Build a ``HorizontalFlip`` transform.

    Args:
        cfg: Augmentation configuration.

    Returns:
        Albumentations transform or ``None`` if disabled.
    """
    hf = cfg.transforms.horizontal_flip
    if not hf.enabled:
        return None
    return A.HorizontalFlip(p=hf.probability)


def _build_random_shadow(cfg: AugmentationConfig) -> A.BasicTransform | None:
    """Build a ``RandomShadow`` transform.

    Args:
        cfg: Augmentation configuration.

    Returns:
        Albumentations transform or ``None`` if disabled.
    """
    rs = cfg.transforms.random_shadow
    if not rs.enabled:
        return None
    return A.RandomShadow(
        num_shadows_lower=rs.num_shadows_lower,
        num_shadows_upper=rs.num_shadows_upper,
        shadow_dimension=rs.shadow_dimension,
        p=rs.probability,
    )


# ---------------------------------------------------------------------------
# Coarse-dropout (partial occlusion) — uses albumentations built-in
# ---------------------------------------------------------------------------


def _build_coarse_dropout(cfg: AugmentationConfig) -> A.BasicTransform | None:
    """Build a ``CoarseDropout`` transform for partial face occlusion.

    The hole dimensions are computed from the target image size using
    the configured ratio limits.  Since image size is not known at
    build time, a representative 112×112 canvas is assumed; the actual
    effect scales proportionally.

    Args:
        cfg: Augmentation configuration.

    Returns:
        Albumentations transform or ``None`` if disabled.
    """
    po = cfg.transforms.partial_occlusion
    if not po.enabled:
        return None

    # Reference canvas size for ratio calculation.
    ref_w, ref_h = 112, 112
    max_h = max(1, int(ref_h * po.max_height_ratio))
    max_w = max(1, int(ref_w * po.max_width_ratio))

    return A.CoarseDropout(
        max_holes=po.max_holes,
        max_height=max_h,
        max_width=max_w,
        fill_value=0,
        p=po.probability,
    )


# ---------------------------------------------------------------------------
# Pipeline builder
# ---------------------------------------------------------------------------

# Ordered list of (builder_function) — applied left-to-right.
_BUILDERS = [
    _build_horizontal_flip,
    _build_rotation,
    _build_brightness_contrast,
    _build_gaussian_noise,
    _build_gaussian_blur,
    _build_motion_blur,
    _build_jpeg_compression,
    _build_random_shadow,
    _build_coarse_dropout,
]


def build_transform_pipeline(
    cfg: AugmentationConfig,
    seed: int | None = None,
) -> A.Compose:
    """Assemble all enabled transforms into a single ``albumentations.Compose``.

    Only transforms whose ``enabled`` flag is ``True`` in *cfg* are
    included.  The order follows :data:`_BUILDERS`.

    Note: Synthetic mask simulation and sunglasses overlays are **not**
    included here — they are custom numpy-level operations applied by
    :class:`~augmentations.mask_simulator.MaskSimulator` at the pipeline level.

    Args:
        cfg: Augmentation configuration section of the app config.
        seed: Optional integer seed for Albumentations RNG.  Defaults to
            ``cfg.seed`` when ``None``.

    Returns:
        An ``albumentations.Compose`` object ready to call with
        ``transform(image=arr)["image"]``.

    Example::

        transform = build_transform_pipeline(cfg.augmentation, seed=42)
        result = transform(image=bgr_array)
        augmented_img = result["image"]
    """
    active_seed = seed if seed is not None else cfg.seed
    transforms: list[A.BasicTransform] = []

    for builder in _BUILDERS:
        t = builder(cfg)
        if t is not None:
            transforms.append(t)

    return A.Compose(
        transforms=transforms,
        seed=active_seed,
    )


def build_preview_transform(cfg: AugmentationConfig) -> A.Compose:
    """Build a deterministic transform for augmentation preview grids.

    Sets ``p=1.0`` on all enabled transforms so the preview shows every
    augmentation applied simultaneously.

    Args:
        cfg: Augmentation configuration.

    Returns:
        ``albumentations.Compose`` with all transforms forced active.
    """
    # Re-use standard builders but patch probability to 1.0.
    transforms: list[A.BasicTransform] = []
    for builder in _BUILDERS:
        t = builder(cfg)
        if t is not None:
            # Albumentations transforms support deepcopy + p override.
            import copy
            t_copy = copy.deepcopy(t)
            t_copy.p = 1.0
            transforms.append(t_copy)

    return A.Compose(transforms=transforms, seed=cfg.seed)
