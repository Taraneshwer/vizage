"""
Single-image validation for MaskShield AI Dataset Builder.

This module provides :class:`ImageValidator`, a stateless service that
applies a configurable battery of checks to individual image files and
returns a structured :class:`ImageValidationResult`.

Checks performed (in order)
----------------------------
1. **Format** — file extension is in the allowed set.
2. **Decodability** — file can be opened by both OpenCV and Pillow.
3. **Minimum size** — width and height are at least *min_image_size_px*.
4. **Aspect ratio** — width/height ratio within [min, max].
5. **Blur** — Laplacian variance above *blur_threshold*.
6. **Brightness** — mean luminance within [brightness_min, brightness_max].

Duplicate detection is handled at the dataset level (see
:mod:`validators.dataset_validator`) because it requires comparing
images against each other.

Design
------
* ``ImageValidator`` is injected with a :class:`~config.models.ValidationConfig`
  — no global config access.
* All results are immutable Pydantic models.
* Every failure reason is a typed :class:`RejectionReason` enum value,
  enabling programmatic filtering downstream.

Example::

    from config.loader import load_config
    from validators.image_validator import ImageValidator

    cfg = load_config()
    validator = ImageValidator(cfg.validation)
    result = validator.validate(Path("datasets/lfw/person_001/img_001.jpg"))
    if not result.is_valid:
        print(result.rejection_reasons)
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field

from config.models import ValidationConfig
from utils.image_utils import (
    ImageLoadError,
    image_dimensions,
    laplacian_variance,
    load_image_bgr,
    mean_brightness,
)


                                                                             
                         
                                                                             


class RejectionReason(str, Enum):
    """Enumeration of all possible image rejection causes.

    Attributes:
        UNSUPPORTED_FORMAT: File extension not in allowed set.
        CORRUPTED: Image cannot be decoded by OpenCV or Pillow.
        TOO_SMALL: Width or height below the minimum pixel threshold.
        BAD_ASPECT_RATIO: Width/height ratio outside the allowed range.
        TOO_BLURRY: Laplacian variance below the blur threshold.
        TOO_DARK: Mean brightness below the minimum threshold.
        TOO_BRIGHT: Mean brightness above the maximum threshold.
    """

    UNSUPPORTED_FORMAT = "unsupported_format"
    CORRUPTED = "corrupted"
    TOO_SMALL = "too_small"
    BAD_ASPECT_RATIO = "bad_aspect_ratio"
    TOO_BLURRY = "too_blurry"
    TOO_DARK = "too_dark"
    TOO_BRIGHT = "too_bright"


                                                                             
              
                                                                             


class ImageValidationResult(BaseModel):
    """Immutable result of validating a single image file.

    Attributes:
        path: Absolute path to the validated image.
        is_valid: ``True`` if all checks passed.
        rejection_reasons: List of :class:`RejectionReason` values that
            caused the image to be rejected.  Empty when ``is_valid`` is
            ``True``.
        width: Decoded image width in pixels, or ``None`` if decoding failed.
        height: Decoded image height in pixels, or ``None`` if decoding failed.
        blur_score: Laplacian variance, or ``None`` if decoding failed.
        brightness_score: Mean luminance [0–255], or ``None`` if decoding failed.
        file_size_bytes: Size of the file on disk in bytes.
    """

    model_config = ConfigDict(frozen=True)

    path: Path
    is_valid: bool
    rejection_reasons: list[RejectionReason] = Field(default_factory=list)
    width: int | None = None
    height: int | None = None
    blur_score: float | None = None
    brightness_score: float | None = None
    file_size_bytes: int = 0

    @property
    def aspect_ratio(self) -> float | None:
        """Compute width / height aspect ratio, or ``None`` if dimensions unknown."""
        if self.width is not None and self.height is not None and self.height > 0:
            return self.width / self.height
        return None

    @property
    def resolution_label(self) -> str:
        """Human-readable resolution string, e.g. ``'112x112'``."""
        if self.width is not None and self.height is not None:
            return f"{self.width}x{self.height}"
        return "unknown"


                                                                             
                   
                                                                             


class ImageValidator:
    """Applies a configurable battery of checks to a single image file.

    This class is **stateless after construction** — the same instance
    can safely validate images concurrently across threads.

    Args:
        config: Validated :class:`~config.models.ValidationConfig` instance.

    Example::

        validator = ImageValidator(cfg.validation)
        result = validator.validate(Path("img.jpg"))
        assert result.is_valid
    """

    def __init__(self, config: ValidationConfig) -> None:
        self._cfg = config
        self._allowed_extensions: frozenset[str] = frozenset(
            ext.lower().lstrip(".") for ext in config.supported_formats
        )

                                                                        
                
                                                                        

    def validate(self, image_path: Path) -> ImageValidationResult:
        """Validate a single image file against all configured checks.

        Checks run in order; if the image cannot be decoded, pixel-level
        checks are skipped (they would fail unconditionally anyway).

        Args:
            image_path: Path to the image file to validate.

        Returns:
            An :class:`ImageValidationResult` describing every check result.
        """
        logger.debug("Validating image: {path}", path=image_path)

        reasons: list[RejectionReason] = []
        file_size = image_path.stat().st_size if image_path.exists() else 0

                                                                          
                          
                                                                          
        if not self._check_format(image_path):
            reasons.append(RejectionReason.UNSUPPORTED_FORMAT)
            logger.debug(
                "Rejected (format): {path} | ext={ext}",
                path=image_path,
                ext=image_path.suffix,
            )
                                                     
            return ImageValidationResult(
                path=image_path,
                is_valid=False,
                rejection_reasons=reasons,
                file_size_bytes=file_size,
            )

                                                                          
                                
                                                                          
        try:
            img = load_image_bgr(image_path)
        except (ImageLoadError, FileNotFoundError, OSError) as exc:
            reasons.append(RejectionReason.CORRUPTED)
            logger.debug(
                "Rejected (corrupted): {path} | reason={reason}",
                path=image_path,
                reason=str(exc),
            )
            return ImageValidationResult(
                path=image_path,
                is_valid=False,
                rejection_reasons=reasons,
                file_size_bytes=file_size,
            )

        dims = image_dimensions(img)
        blur = laplacian_variance(img)
        brightness = mean_brightness(img)

                                                                          
                                
                                                                          
        if not self._check_size(dims.width, dims.height):
            reasons.append(RejectionReason.TOO_SMALL)
            logger.debug(
                "Rejected (too_small): {path} | {w}x{h}",
                path=image_path,
                w=dims.width,
                h=dims.height,
            )

                                                                          
                                
                                                                          
        if not self._check_aspect_ratio(dims.width, dims.height):
            reasons.append(RejectionReason.BAD_ASPECT_RATIO)
            ratio = dims.width / dims.height if dims.height else 0
            logger.debug(
                "Rejected (aspect_ratio): {path} | ratio={ratio:.3f}",
                path=image_path,
                ratio=ratio,
            )

                                                                          
                        
                                                                          
        if not self._check_blur(blur):
            reasons.append(RejectionReason.TOO_BLURRY)
            logger.debug(
                "Rejected (blurry): {path} | blur_score={score:.2f}",
                path=image_path,
                score=blur,
            )

                                                                          
                              
                                                                          
        brightness_reason = self._check_brightness(brightness)
        if brightness_reason is not None:
            reasons.append(brightness_reason)
            logger.debug(
                "Rejected ({reason}): {path} | brightness={b:.2f}",
                reason=brightness_reason.value,
                path=image_path,
                b=brightness,
            )

                                                                          
                         
                                                                          
        is_valid = len(reasons) == 0
        if is_valid:
            logger.debug("Accepted: {path}", path=image_path)

        return ImageValidationResult(
            path=image_path,
            is_valid=is_valid,
            rejection_reasons=reasons,
            width=dims.width,
            height=dims.height,
            blur_score=blur,
            brightness_score=brightness,
            file_size_bytes=file_size,
        )

    def is_valid_format(self, image_path: Path) -> bool:
        """Quick format-only check without loading the image.

        Args:
            image_path: File to check.

        Returns:
            ``True`` if the extension is in the allowed set.
        """
        return self._check_format(image_path)

                                                                        
                           
                                                                        

    def _check_format(self, path: Path) -> bool:
        """Return ``True`` if the file extension is allowed."""
        ext = path.suffix.lstrip(".").lower()
        return ext in self._allowed_extensions

    def _check_size(self, width: int, height: int) -> bool:
        """Return ``True`` if both dimensions meet the minimum."""
        minimum = self._cfg.min_image_size_px
        return width >= minimum and height >= minimum

    def _check_aspect_ratio(self, width: int, height: int) -> bool:
        """Return ``True`` if width/height ratio is within bounds."""
        if height == 0:
            return False
        ratio = width / height
        return self._cfg.min_aspect_ratio <= ratio <= self._cfg.max_aspect_ratio

    def _check_blur(self, score: float) -> bool:
        """Return ``True`` if the image is sharp enough."""
        return score >= self._cfg.blur_threshold

    def _check_brightness(self, brightness: float) -> RejectionReason | None:
        """Return a rejection reason if brightness is out of range, else ``None``."""
        if brightness < self._cfg.brightness_min:
            return RejectionReason.TOO_DARK
        if brightness > self._cfg.brightness_max:
            return RejectionReason.TOO_BRIGHT
        return None
