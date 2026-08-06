"""
Image-level utility functions for MaskShield AI Dataset Builder.

Provides stateless helpers used by validators, preprocessors, and
augmentation pipelines:

- :func:`load_image_bgr`  — OpenCV BGR load with error handling
- :func:`load_image_rgb`  — OpenCV BGR → RGB conversion
- :func:`load_pil`        — Pillow load with conversion to RGB
- :func:`image_dimensions` — fast (width, height, channels) without full decode
- :func:`laplacian_variance` — blur score via Laplacian variance
- :func:`mean_brightness`   — mean luminance of a BGR/RGB image
- :func:`is_grayscale`      — detect single-channel or near-greyscale images
- :func:`letterbox_resize`  — resize-with-padding to target dimensions
- :func:`apply_clahe`       — contrast-limited adaptive histogram equalisation
- :func:`bgr_to_rgb`        — in-place channel swap
- :func:`save_image`        — save a numpy array as JPEG/PNG with quality control
- :class:`ImageLoadError`   — domain exception for unreadable images

All functions operate on numpy arrays (OpenCV convention) unless explicitly
documented otherwise.  No global state; no side-effects on import.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError


                                                                             
                  
                                                                             


class ImageLoadError(OSError):
    """Raised when an image file cannot be decoded into a numpy array.

    Attributes:
        path: The path that failed to load.
    """

    def __init__(self, path: Path, reason: str) -> None:
        self.path = path
        super().__init__(f"Cannot load image '{path}': {reason}")


                                                                             
                                
                                                                             


class ImageDimensions(NamedTuple):
    """Width, height, and channel count of an image.

    Attributes:
        width: Pixel width.
        height: Pixel height.
        channels: Number of colour channels (1 = greyscale, 3 = RGB/BGR).
    """

    width: int
    height: int
    channels: int


                                                                             
              
                                                                             


def load_image_bgr(path: Path) -> np.ndarray:
    """Load an image file as a BGR numpy array using OpenCV.

    Args:
        path: Path to the image file.

    Returns:
        ``uint8`` numpy array of shape ``(H, W, 3)`` in BGR colour order.

    Raises:
        ImageLoadError: If OpenCV cannot decode the file.
        FileNotFoundError: If *path* does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {path}")

    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise ImageLoadError(path, "cv2.imread returned None — possibly corrupted or unsupported format.")
    return img


def load_image_rgb(path: Path) -> np.ndarray:
    """Load an image file as an RGB numpy array.

    Wraps :func:`load_image_bgr` and converts the channel order.

    Args:
        path: Path to the image file.

    Returns:
        ``uint8`` numpy array of shape ``(H, W, 3)`` in RGB colour order.

    Raises:
        ImageLoadError: If the file cannot be decoded.
        FileNotFoundError: If *path* does not exist.
    """
    return cv2.cvtColor(load_image_bgr(path), cv2.COLOR_BGR2RGB)


def load_pil(path: Path) -> Image.Image:
    """Load an image file as a Pillow :class:`~PIL.Image.Image` (RGB mode).

    Args:
        path: Path to the image file.

    Returns:
        A Pillow ``Image`` in ``"RGB"`` mode.

    Raises:
        ImageLoadError: If Pillow cannot decode the file.
        FileNotFoundError: If *path* does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {path}")
    try:
        img = Image.open(path)
        return img.convert("RGB")
    except UnidentifiedImageError as exc:
        raise ImageLoadError(path, f"Pillow cannot identify image: {exc}") from exc
    except Exception as exc:
        raise ImageLoadError(path, str(exc)) from exc


                                                                             
                  
                                                                             


def image_dimensions(img: np.ndarray) -> ImageDimensions:
    """Extract width, height, and channel count from a numpy array.

    Args:
        img: Image array of shape ``(H, W)`` or ``(H, W, C)``.

    Returns:
        :class:`ImageDimensions` named tuple.

    Raises:
        ValueError: If *img* has an unexpected number of dimensions.
    """
    if img.ndim == 2:
        h, w = img.shape
        return ImageDimensions(width=w, height=h, channels=1)
    elif img.ndim == 3:
        h, w, c = img.shape
        return ImageDimensions(width=w, height=h, channels=c)
    else:
        raise ValueError(f"Unexpected array shape: {img.shape}")


                                                                             
                 
                                                                             


def laplacian_variance(img: np.ndarray) -> float:
    """Compute the Laplacian variance as a focus / sharpness measure.

    A lower value indicates a blurrier image.  Values below ~80 are
    typically considered too blurry for face recognition training.

    Args:
        img: BGR or RGB ``uint8`` image array.

    Returns:
        Non-negative float representing the Laplacian variance.

    Example::

        score = laplacian_variance(load_image_bgr(path))
        if score < 80.0:
            print("Image is too blurry")
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def mean_brightness(img: np.ndarray) -> float:
    """Compute the mean pixel brightness of an image.

    Converts to greyscale first to get a single luminance channel.

    Args:
        img: BGR or RGB ``uint8`` image array.

    Returns:
        Float in [0, 255] representing mean luminance.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    return float(np.mean(gray))


def is_grayscale(img: np.ndarray, *, tolerance: int = 5) -> bool:
    """Detect whether an image is effectively greyscale.

    Checks if all three colour channels are within *tolerance* of each other
    for every pixel, indicating no colour variation.

    Args:
        img: BGR ``uint8`` image array of shape ``(H, W, 3)``.
        tolerance: Maximum channel difference to still consider greyscale.

    Returns:
        ``True`` if the image is greyscale or near-greyscale.
    """
    if img.ndim == 2:
        return True
    b, g, r = img[:, :, 0], img[:, :, 1], img[:, :, 2]
    return bool(
        np.all(np.abs(b.astype(int) - g.astype(int)) <= tolerance)
        and np.all(np.abs(b.astype(int) - r.astype(int)) <= tolerance)
    )


                                                                             
            
                                                                             


def letterbox_resize(
    img: np.ndarray,
    target_w: int,
    target_h: int,
    pad_color: tuple[int, int, int] = (0, 0, 0),
    interpolation: int = cv2.INTER_LANCZOS4,
) -> np.ndarray:
    """Resize *img* to fit within (*target_w*, *target_h*) with letterbox padding.

    Maintains the original aspect ratio.  Padding is added symmetrically
    on the shorter axis using *pad_color*.

    Args:
        img: Source image array (BGR or RGB).
        target_w: Target canvas width in pixels.
        target_h: Target canvas height in pixels.
        pad_color: BGR/RGB tuple used to fill padding regions.
        interpolation: OpenCV interpolation flag.

    Returns:
        New ``uint8`` array of exactly shape ``(target_h, target_w, C)``.
    """
    src_h, src_w = img.shape[:2]
    scale = min(target_w / src_w, target_h / src_h)
    new_w = int(round(src_w * scale))
    new_h = int(round(src_h * scale))

    resized = cv2.resize(img, (new_w, new_h), interpolation=interpolation)

                           
    canvas = np.full(
        (target_h, target_w, img.shape[2]) if img.ndim == 3 else (target_h, target_w),
        pad_color[0] if img.ndim == 2 else 0,
        dtype=np.uint8,
    )
    if img.ndim == 3:
        canvas[:, :] = pad_color

    offset_y = (target_h - new_h) // 2
    offset_x = (target_w - new_w) // 2
    canvas[offset_y : offset_y + new_h, offset_x : offset_x + new_w] = resized
    return canvas


def apply_clahe(
    img: np.ndarray,
    clip_limit: float = 2.0,
    tile_grid_size: tuple[int, int] = (8, 8),
) -> np.ndarray:
    """Apply Contrast-Limited Adaptive Histogram Equalization (CLAHE).

    Operates in the L-channel of LAB colour space so that hue is
    preserved while local contrast is enhanced.

    Args:
        img: BGR ``uint8`` image array.
        clip_limit: Threshold for contrast limiting.
        tile_grid_size: Size of the grid for histogram equalization.

    Returns:
        CLAHE-enhanced BGR ``uint8`` array of the same shape as *img*.
    """
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l_channel, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    l_channel = clahe.apply(l_channel)
    lab = cv2.merge([l_channel, a, b])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def bgr_to_rgb(img: np.ndarray) -> np.ndarray:
    """Convert a BGR array to RGB by reversing the channel axis.

    Args:
        img: BGR ``uint8`` array of shape ``(H, W, 3)``.

    Returns:
        RGB ``uint8`` array (a view or copy depending on memory layout).
    """
    return img[:, :, ::-1]


                                                                             
              
                                                                             


                                                           
_ENCODE_PARAMS: dict[str, list[int]] = {
    "jpg": [cv2.IMWRITE_JPEG_QUALITY, 95],
    "jpeg": [cv2.IMWRITE_JPEG_QUALITY, 95],
    "png": [cv2.IMWRITE_PNG_COMPRESSION, 6],
    "webp": [cv2.IMWRITE_WEBP_QUALITY, 95],
    "bmp": [],
    "tiff": [],
    "tif": [],
}


def save_image(
    img: np.ndarray,
    dest: Path,
    quality: int = 95,
) -> None:
    """Save a numpy image array to *dest* with format-appropriate compression.

    The output format is inferred from *dest*'s extension.

    Args:
        img: BGR ``uint8`` image array.
        dest: Destination file path.  Parent directory must exist.
        quality: JPEG / WebP quality (1–100).  Ignored for PNG/BMP/TIFF.

    Raises:
        ValueError: If the file extension is not supported.
        OSError: If OpenCV fails to write the file.
    """
    ext = dest.suffix.lstrip(".").lower()
    if ext not in _ENCODE_PARAMS:
        raise ValueError(
            f"Unsupported output extension '{ext}'. "
            f"Supported: {sorted(_ENCODE_PARAMS)}"
        )

    params = list(_ENCODE_PARAMS[ext])
                                         
    if ext in {"jpg", "jpeg"}:
        params = [cv2.IMWRITE_JPEG_QUALITY, max(1, min(100, quality))]
    elif ext == "webp":
        params = [cv2.IMWRITE_WEBP_QUALITY, max(1, min(100, quality))]

    success = cv2.imwrite(str(dest), img, params)
    if not success:
        raise OSError(f"cv2.imwrite failed for path: {dest}")
