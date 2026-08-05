"""
Synthetic occlusion simulators for MaskShield AI Dataset Builder.

This module provides numpy-level image overlay operations that simulate
real-world face occlusions. These are applied **after** Albumentations
transforms in the augmentation pipeline.

Provided simulators
-------------------
* :class:`MaskSimulator` — overlays a rectangular surgical/cloth mask
  over the lower half of the face.
* :class:`SunglassesSimulator` — overlays a dark tinted rectangle over
  the eye region.
* :func:`apply_random_mask` / :func:`apply_random_sunglasses` —
  functional convenience wrappers used by the pipeline.

Design
------
* All simulators are **deterministic** given a :class:`random.Random`
  instance — no ``random.seed()`` global calls.
* They operate on BGR ``uint8`` numpy arrays (OpenCV convention) and
  return a new array (not in-place mutation).
* Config is injected via the relevant Pydantic sub-models; no global
  config access.

Example::

    import random
    from augmentations.mask_simulator import MaskSimulator

    rng = random.Random(42)
    sim = MaskSimulator(cfg.augmentation.transforms.random_mask_simulation)
    augmented = sim.apply(img_bgr, rng)
"""

from __future__ import annotations

import random

import numpy as np

from config.models import MaskSimulationConfig, SunglassesSimulationConfig


# ---------------------------------------------------------------------------
# Mask simulator
# ---------------------------------------------------------------------------


class MaskSimulator:
    """Overlays a synthetic surgical/cloth mask rectangle on the lower face.

    The mask covers approximately the nose and mouth region using a
    randomly-coloured solid rectangle with optional slight opacity blending
    for realism.

    Args:
        config: :class:`~config.models.MaskSimulationConfig` with probability
            and geometry parameters.

    Example::

        sim = MaskSimulator(cfg.augmentation.transforms.random_mask_simulation)
        img_with_mask = sim.apply(bgr_img, rng)
    """

    def __init__(self, config: MaskSimulationConfig) -> None:
        self._cfg = config

    def apply(self, img: np.ndarray, rng: random.Random) -> np.ndarray:
        """Conditionally overlay a synthetic mask on *img*.

        Args:
            img: BGR ``uint8`` image array of shape ``(H, W, 3)``.
            rng: Seeded :class:`random.Random` instance for reproducibility.

        Returns:
            New BGR ``uint8`` array with mask applied, or *img* unchanged
            if the probability check failed.
        """
        if rng.random() > self._cfg.probability:
            return img

        h, w = img.shape[:2]
        result = img.copy()

        # Geometry: mask covers lower portion of the image.
        mask_h_ratio = rng.uniform(*self._cfg.mask_height_ratio)
        mask_w_ratio = rng.uniform(*self._cfg.mask_width_ratio)

        mask_h = int(h * mask_h_ratio)
        mask_w = int(w * mask_w_ratio)

        # Vertical position: lower-middle of face (below nose).
        y_start = int(h * 0.45)
        y_end = min(h, y_start + mask_h)

        # Horizontal position: centred with some jitter.
        x_center = w // 2
        x_start = max(0, x_center - mask_w // 2)
        x_end = min(w, x_start + mask_w)

        # Colour: sample from config ranges (per channel).
        r_range, g_range, b_range = self._cfg.mask_color_range
        # Config is RGB order; OpenCV is BGR.
        color_bgr = (
            rng.randint(*b_range),
            rng.randint(*g_range),
            rng.randint(*r_range),
        )

        # Blend mask rectangle over image with slight transparency.
        alpha = rng.uniform(0.82, 0.97)
        overlay = result.copy()
        overlay[y_start:y_end, x_start:x_end] = color_bgr

        result = _blend(result, overlay, alpha)

        # Add subtle edge softening (box blur on mask boundary).
        result = _soften_edges(result, y_start, y_end, x_start, x_end, blur_px=3)

        return result

    def should_apply(self, rng: random.Random) -> bool:
        """Check (without side effects) whether this simulator would fire.

        Args:
            rng: Seeded :class:`random.Random`.

        Returns:
            ``True`` if the probability threshold would be met.
        """
        return rng.random() <= self._cfg.probability


# ---------------------------------------------------------------------------
# Sunglasses simulator
# ---------------------------------------------------------------------------


class SunglassesSimulator:
    """Overlays a dark tinted rectangle over the eye region.

    Simulates sunglasses / protective eyewear occlusion, which is a
    common real-world scenario for face recognition under partial occlusion.

    Args:
        config: :class:`~config.models.SunglassesSimulationConfig`.

    Example::

        sim = SunglassesSimulator(cfg.augmentation.transforms.random_sunglasses)
        img_with_glasses = sim.apply(bgr_img, rng)
    """

    def __init__(self, config: SunglassesSimulationConfig) -> None:
        self._cfg = config

    def apply(self, img: np.ndarray, rng: random.Random) -> np.ndarray:
        """Conditionally overlay synthetic sunglasses on *img*.

        Args:
            img: BGR ``uint8`` image array of shape ``(H, W, 3)``.
            rng: Seeded :class:`random.Random`.

        Returns:
            New BGR ``uint8`` array, or *img* unchanged if probability missed.
        """
        if rng.random() > self._cfg.probability:
            return img

        h, w = img.shape[:2]
        result = img.copy()

        # Eye-band geometry: approximately top 25–45 % of face height.
        y_start = int(h * 0.25)
        y_end = int(h * 0.47)
        # Slightly narrower than full width.
        x_margin = int(w * rng.uniform(0.05, 0.12))
        x_start = x_margin
        x_end = w - x_margin

        # Tint colour in BGR (config provides RGB).
        r, g, b = self._cfg.tint_color
        tint_bgr = (b, g, r)

        overlay = result.copy()
        overlay[y_start:y_end, x_start:x_end] = tint_bgr

        result = _blend(result, overlay, self._cfg.alpha)
        result = _soften_edges(result, y_start, y_end, x_start, x_end, blur_px=5)

        return result


# ---------------------------------------------------------------------------
# Functional convenience wrappers
# ---------------------------------------------------------------------------


def apply_random_mask(
    img: np.ndarray,
    config: MaskSimulationConfig,
    rng: random.Random,
) -> np.ndarray:
    """Apply a :class:`MaskSimulator` in a single function call.

    Args:
        img: Source BGR image.
        config: Mask simulation config.
        rng: Seeded RNG.

    Returns:
        Augmented BGR image.
    """
    return MaskSimulator(config).apply(img, rng)


def apply_random_sunglasses(
    img: np.ndarray,
    config: SunglassesSimulationConfig,
    rng: random.Random,
) -> np.ndarray:
    """Apply a :class:`SunglassesSimulator` in a single function call.

    Args:
        img: Source BGR image.
        config: Sunglasses simulation config.
        rng: Seeded RNG.

    Returns:
        Augmented BGR image.
    """
    return SunglassesSimulator(config).apply(img, rng)


# ---------------------------------------------------------------------------
# Private numpy helpers
# ---------------------------------------------------------------------------


def _blend(base: np.ndarray, overlay: np.ndarray, alpha: float) -> np.ndarray:
    """Alpha-blend *overlay* onto *base* with weight *alpha*.

    Args:
        base: Original image array.
        overlay: Image with the new region drawn.
        alpha: Weight of *overlay* in range [0, 1].  1.0 = fully overlay.

    Returns:
        Blended ``uint8`` array.
    """
    blended = (alpha * overlay + (1.0 - alpha) * base).astype(np.uint8)
    return blended


def _soften_edges(
    img: np.ndarray,
    y0: int,
    y1: int,
    x0: int,
    x1: int,
    blur_px: int = 3,
) -> np.ndarray:
    """Apply a mild Gaussian blur along the boundary of a rectangular region.

    Blends a 1-pixel border strip between the occluder rectangle and the
    surrounding image pixels to reduce hard edges.

    Args:
        img: Full image array (modified in-place copy).
        y0: Top boundary of the rectangle.
        y1: Bottom boundary of the rectangle.
        x0: Left boundary.
        x1: Right boundary.
        blur_px: Blur kernel half-size (must be odd after ``2*n+1``).

    Returns:
        Modified ``uint8`` image array.
    """
    import cv2  # lazy import to keep module importable without cv2 at parse-time

    ksize = max(1, blur_px * 2 + 1)  # ensure odd kernel size
    # Blur a 1-pixel border around the rectangle.
    border = max(1, blur_px)
    y0b = max(0, y0 - border)
    y1b = min(img.shape[0], y1 + border)
    x0b = max(0, x0 - border)
    x1b = min(img.shape[1], x1 + border)

    region = img[y0b:y1b, x0b:x1b].copy()
    blurred = cv2.GaussianBlur(region, (ksize, ksize), 0)

    # Only replace the border rows/cols, not the core rectangle.
    mask = np.zeros(region.shape[:2], dtype=bool)
    inner_y0 = y0 - y0b
    inner_y1 = y1 - y0b
    inner_x0 = x0 - x0b
    inner_x1 = x1 - x0b
    mask[:inner_y0, :] = True
    mask[inner_y1:, :] = True
    mask[:, :inner_x0] = True
    mask[:, inner_x1:] = True

    result = img.copy()
    combined = region.copy()
    combined[mask] = blurred[mask]
    result[y0b:y1b, x0b:x1b] = combined
    return result
