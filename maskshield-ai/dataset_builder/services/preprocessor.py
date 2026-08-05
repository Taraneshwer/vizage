"""
Image preprocessor service for MaskShield AI Dataset Builder.

:class:`ImagePreprocessor` applies a deterministic, configurable preprocessing
pipeline to individual images and optionally to entire directory trees.

Pipeline steps (applied in order)
----------------------------------
1. **Load** — OpenCV BGR read.
2. **Face-crop hook** (optional) — caller-provided :class:`FaceCropHook`
   implementation.  Skip if ``None``.
3. **Letterbox resize** — resize to ``target_size`` with padding, preserving
   aspect ratio.
4. **CLAHE** (optional) — contrast-limited adaptive histogram equalisation.
5. **Save** — write to destination with format / quality from config.
6. **Metadata** — persist an accompanying ``.json`` sidecar containing
   the original resolution, file size, and processing parameters.

Design
------
* ``ImagePreprocessor`` accepts a :class:`~config.models.PreprocessingConfig`
  plus an optional :class:`FaceCropHook` — no global state, fully injectable.
* The ``FaceCropHook`` is a :class:`~typing.Protocol` so any callable
  object with the right signature can be used (MediaPipe, YOLO, fixed crop…).
* Batch processing (:meth:`process_directory`) yields
  :class:`PreprocessingResult` objects one at a time, making it trivial
  to wrap in a thread pool for parallel execution.
* **Idempotent** — if the destination file already exists and
  ``overwrite=False``, the file is skipped and the result reflects that.

Example::

    from config.loader import load_config
    from services.preprocessor import ImagePreprocessor

    cfg = load_config()
    preprocessor = ImagePreprocessor(cfg.preprocessing)
    result = preprocessor.process(
        src=Path("datasets/identities/person_001/img.jpg"),
        dst=Path("datasets/processed/person_001/img.jpg"),
    )
    print(result.status)
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from enum import Enum
from pathlib import Path
from typing import Protocol, runtime_checkable

import cv2
import numpy as np
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field

from config.models import PreprocessingConfig
from utils.file_ops import ensure_dir, iter_images
from utils.image_utils import (
    ImageLoadError,
    apply_clahe,
    image_dimensions,
    letterbox_resize,
    load_image_bgr,
    save_image,
)


# ---------------------------------------------------------------------------
# Face crop hook protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class FaceCropHook(Protocol):
    """Protocol for face detection / crop callbacks.

    Implementors receive a BGR image array and must return either a
    cropped face region array or the original array unchanged (if no
    face is detected).

    This design allows the preprocessor to be future-proofed for
    YOLO-based or MediaPipe-based cropping without any change to the
    preprocessor itself.

    Example implementation::

        class FixedCenterCrop:
            def __call__(self, img: np.ndarray) -> np.ndarray:
                h, w = img.shape[:2]
                crop_size = min(h, w)
                y0 = (h - crop_size) // 2
                x0 = (w - crop_size) // 2
                return img[y0:y0+crop_size, x0:x0+crop_size]
    """

    def __call__(self, image: np.ndarray) -> np.ndarray:
        """Detect and crop a face from *image*.

        Args:
            image: BGR ``uint8`` numpy array.

        Returns:
            Cropped face region as a BGR ``uint8`` array.
            If no face is detected, return *image* unchanged.
        """
        ...


# ---------------------------------------------------------------------------
# Processing status
# ---------------------------------------------------------------------------


class ProcessingStatus(str, Enum):
    """Outcome of a single image preprocessing call.

    Attributes:
        SUCCESS: All steps completed and output file written.
        SKIPPED: Destination file already exists and overwrite is disabled.
        LOAD_ERROR: Source image could not be decoded.
        SAVE_ERROR: Output file could not be written.
        CROP_ERROR: Face crop hook raised an exception.
        UNKNOWN_ERROR: Unclassified exception during processing.
    """

    SUCCESS = "success"
    SKIPPED = "skipped"
    LOAD_ERROR = "load_error"
    SAVE_ERROR = "save_error"
    CROP_ERROR = "crop_error"
    UNKNOWN_ERROR = "unknown_error"


# ---------------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------------


class PreprocessingResult(BaseModel):
    """Outcome of preprocessing a single image.

    Attributes:
        src: Original source path.
        dst: Destination output path.
        status: :class:`ProcessingStatus`.
        original_width: Source image width before processing.
        original_height: Source image height before processing.
        output_width: Width of the saved output.
        output_height: Height of the saved output.
        was_cropped: Whether a face crop hook modified the image.
        was_equalised: Whether CLAHE was applied.
        error_message: Reason for failure if status is not SUCCESS/SKIPPED.
    """

    model_config = ConfigDict(frozen=True)

    src: Path
    dst: Path
    status: ProcessingStatus
    original_width: int | None = None
    original_height: int | None = None
    output_width: int | None = None
    output_height: int | None = None
    was_cropped: bool = False
    was_equalised: bool = False
    error_message: str | None = None

    @property
    def succeeded(self) -> bool:
        """``True`` if the image was processed and saved successfully."""
        return self.status == ProcessingStatus.SUCCESS


# ---------------------------------------------------------------------------
# Image metadata sidecar model
# ---------------------------------------------------------------------------


class ImageMetadata(BaseModel):
    """JSON sidecar written alongside each processed image.

    Attributes:
        original_path: Absolute string path to the source image.
        original_width: Source width in pixels.
        original_height: Source height in pixels.
        output_width: Processed width in pixels.
        output_height: Processed height in pixels.
        original_file_size_bytes: Source file size.
        target_size: ``(width, height)`` configured for resizing.
        interpolation: Interpolation method used.
        clahe_applied: Whether CLAHE was applied.
        face_crop_applied: Whether a face crop hook was invoked.
        padding_color: BGR padding colour used.
    """

    model_config = ConfigDict(frozen=True)

    original_path: str
    original_width: int
    original_height: int
    output_width: int
    output_height: int
    original_file_size_bytes: int
    target_size: tuple[int, int]
    interpolation: str
    clahe_applied: bool
    face_crop_applied: bool
    padding_color: tuple[int, int, int]


# ---------------------------------------------------------------------------
# Interpolation map
# ---------------------------------------------------------------------------

_INTERPOLATION_MAP: dict[str, int] = {
    "NEAREST": cv2.INTER_NEAREST,
    "BILINEAR": cv2.INTER_LINEAR,
    "BICUBIC": cv2.INTER_CUBIC,
    "LANCZOS": cv2.INTER_LANCZOS4,
    "AREA": cv2.INTER_AREA,
}


# ---------------------------------------------------------------------------
# Preprocessor service
# ---------------------------------------------------------------------------


class ImagePreprocessor:
    """Applies the configured preprocessing pipeline to individual images.

    Args:
        config: Validated :class:`~config.models.PreprocessingConfig`.
        face_crop_hook: Optional callable conforming to :class:`FaceCropHook`.
            When provided, it is called after loading and before resizing.

    Example::

        preprocessor = ImagePreprocessor(cfg.preprocessing)
        result = preprocessor.process(src=Path("in.jpg"), dst=Path("out.jpg"))
    """

    def __init__(
        self,
        config: PreprocessingConfig,
        face_crop_hook: FaceCropHook | None = None,
    ) -> None:
        self._cfg = config
        self._hook = face_crop_hook

        self._target_w, self._target_h = config.target_size
        self._interpolation = _INTERPOLATION_MAP.get(
            config.interpolation.upper(), cv2.INTER_LANCZOS4
        )
        self._pad_color: tuple[int, int, int] = (
            config.padding_color[2],  # BGR: R→B
            config.padding_color[1],
            config.padding_color[0],  # BGR: B→R
        )

    # ------------------------------------------------------------------
    # Public API — single image
    # ------------------------------------------------------------------

    def process(
        self,
        src: Path,
        dst: Path,
        *,
        overwrite: bool = False,
        write_sidecar: bool = True,
        jpeg_quality: int = 95,
    ) -> PreprocessingResult:
        """Preprocess *src* and write result to *dst*.

        Args:
            src: Source image path.
            dst: Destination image path.
            overwrite: If ``True``, overwrite *dst* when it already exists.
            write_sidecar: If ``True``, write a ``<dst>.json`` metadata file.
            jpeg_quality: JPEG / WebP output quality (1–100).

        Returns:
            :class:`PreprocessingResult` describing the outcome.
        """
        # ----------------------------------------------------------------
        # Skip check
        # ----------------------------------------------------------------
        if dst.exists() and not overwrite:
            logger.debug("Skipping existing: {path}", path=dst)
            return PreprocessingResult(
                src=src,
                dst=dst,
                status=ProcessingStatus.SKIPPED,
            )

        # ----------------------------------------------------------------
        # Load
        # ----------------------------------------------------------------
        try:
            img = load_image_bgr(src)
        except (ImageLoadError, FileNotFoundError, OSError) as exc:
            logger.error("Load error [{path}]: {exc}", path=src, exc=exc)
            return PreprocessingResult(
                src=src,
                dst=dst,
                status=ProcessingStatus.LOAD_ERROR,
                error_message=str(exc),
            )

        orig_dims = image_dimensions(img)
        file_size = src.stat().st_size if src.exists() else 0

        # ----------------------------------------------------------------
        # Step 1 — Face crop hook
        # ----------------------------------------------------------------
        was_cropped = False
        if self._hook is not None:
            try:
                cropped = self._hook(img)
                if cropped is not img and cropped.size > 0:
                    img = cropped
                    was_cropped = True
                    logger.debug("Face crop applied: {path}", path=src)
            except Exception as exc:  # noqa: BLE001
                logger.error("Face crop error [{path}]: {exc}", path=src, exc=exc)
                return PreprocessingResult(
                    src=src,
                    dst=dst,
                    status=ProcessingStatus.CROP_ERROR,
                    original_width=orig_dims.width,
                    original_height=orig_dims.height,
                    error_message=str(exc),
                )

        # ----------------------------------------------------------------
        # Step 2 — Letterbox resize
        # ----------------------------------------------------------------
        img = letterbox_resize(
            img,
            target_w=self._target_w,
            target_h=self._target_h,
            pad_color=self._pad_color,
            interpolation=self._interpolation,
        )

        # ----------------------------------------------------------------
        # Step 3 — CLAHE (optional)
        # ----------------------------------------------------------------
        was_equalised = False
        if self._cfg.apply_histogram_equalization:
            img = apply_clahe(img)
            was_equalised = True

        # ----------------------------------------------------------------
        # Step 4 — Save
        # ----------------------------------------------------------------
        ensure_dir(dst.parent)
        try:
            save_image(img, dst, quality=jpeg_quality)
        except (ValueError, OSError) as exc:
            logger.error("Save error [{path}]: {exc}", path=dst, exc=exc)
            return PreprocessingResult(
                src=src,
                dst=dst,
                status=ProcessingStatus.SAVE_ERROR,
                original_width=orig_dims.width,
                original_height=orig_dims.height,
                error_message=str(exc),
            )

        out_dims = image_dimensions(img)

        # ----------------------------------------------------------------
        # Step 5 — Sidecar metadata
        # ----------------------------------------------------------------
        if write_sidecar:
            self._write_sidecar(
                dst=dst,
                src=src,
                orig_dims=orig_dims,
                out_dims=out_dims,
                file_size=file_size,
                was_cropped=was_cropped,
                was_equalised=was_equalised,
            )

        logger.debug(
            "Processed: {src} → {dst} ({ow}x{oh} → {nw}x{nh})",
            src=src.name,
            dst=dst.name,
            ow=orig_dims.width,
            oh=orig_dims.height,
            nw=out_dims.width,
            nh=out_dims.height,
        )

        return PreprocessingResult(
            src=src,
            dst=dst,
            status=ProcessingStatus.SUCCESS,
            original_width=orig_dims.width,
            original_height=orig_dims.height,
            output_width=out_dims.width,
            output_height=out_dims.height,
            was_cropped=was_cropped,
            was_equalised=was_equalised,
        )

    # ------------------------------------------------------------------
    # Public API — batch processing
    # ------------------------------------------------------------------

    def process_directory(
        self,
        src_dir: Path,
        dst_dir: Path,
        *,
        overwrite: bool = False,
        write_sidecar: bool = True,
        jpeg_quality: int = 95,
    ) -> Iterator[PreprocessingResult]:
        """Preprocess all images under *src_dir* and write to *dst_dir*.

        Mirrors the relative path structure of *src_dir* under *dst_dir*.
        Yields one :class:`PreprocessingResult` per image file encountered.

        Args:
            src_dir: Source directory to scan recursively.
            dst_dir: Output root directory.
            overwrite: Forward to :meth:`process`.
            write_sidecar: Forward to :meth:`process`.
            jpeg_quality: Forward to :meth:`process`.

        Yields:
            :class:`PreprocessingResult` for each image encountered.

        Raises:
            NotADirectoryError: If *src_dir* is not a directory.
        """
        if not src_dir.is_dir():
            raise NotADirectoryError(f"Not a directory: {src_dir}")

        processed = skipped = errored = 0

        for img_path in iter_images(src_dir, recursive=True):
            rel = img_path.relative_to(src_dir)
            dst_path = dst_dir / rel

            result = self.process(
                src=img_path,
                dst=dst_path,
                overwrite=overwrite,
                write_sidecar=write_sidecar,
                jpeg_quality=jpeg_quality,
            )

            if result.status == ProcessingStatus.SUCCESS:
                processed += 1
            elif result.status == ProcessingStatus.SKIPPED:
                skipped += 1
            else:
                errored += 1

            if (processed + skipped + errored) % 1000 == 0:
                logger.info(
                    "Preprocessing progress: {ok} ok / {skip} skipped / {err} errors",
                    ok=processed,
                    skip=skipped,
                    err=errored,
                )

            yield result

        logger.success(
            "Preprocessing complete: {ok} processed, {skip} skipped, {err} errors.",
            ok=processed,
            skip=skipped,
            err=errored,
        )

    def process_directory_eager(
        self,
        src_dir: Path,
        dst_dir: Path,
        *,
        overwrite: bool = False,
        write_sidecar: bool = True,
        jpeg_quality: int = 95,
    ) -> list[PreprocessingResult]:
        """Eagerly process all images and return the full result list.

        Convenience wrapper around :meth:`process_directory` for callers
        that do not want a lazy iterator.

        Args:
            src_dir: Source directory.
            dst_dir: Output directory.
            overwrite: Overwrite existing output files.
            write_sidecar: Write metadata sidecar JSON files.
            jpeg_quality: Output quality.

        Returns:
            List of :class:`PreprocessingResult` objects.
        """
        return list(
            self.process_directory(
                src_dir=src_dir,
                dst_dir=dst_dir,
                overwrite=overwrite,
                write_sidecar=write_sidecar,
                jpeg_quality=jpeg_quality,
            )
        )

    # ------------------------------------------------------------------
    # Public API — normalisation (for training pipelines)
    # ------------------------------------------------------------------

    def normalise_array(self, img: np.ndarray) -> np.ndarray:
        """Apply configured mean/std normalisation to a ``float32`` image array.

        This is **not** applied during :meth:`process` (which saves ``uint8``
        JPEG/PNG).  It is provided as a utility for training data loaders
        that need normalised tensors.

        Args:
            img: ``uint8`` BGR image array in range [0, 255].

        Returns:
            ``float32`` array in approximately [-1, 1] after
            ``(img / 255 - mean) / std`` per channel.
        """
        cfg = self._cfg
        arr = img.astype(np.float32) / 255.0
        mean = np.array(cfg.normalize_mean[::-1], dtype=np.float32)  # BGR order
        std = np.array(cfg.normalize_std[::-1], dtype=np.float32)
        return (arr - mean) / std

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _write_sidecar(
        self,
        dst: Path,
        src: Path,
        orig_dims: object,  # ImageDimensions
        out_dims: object,   # ImageDimensions
        file_size: int,
        was_cropped: bool,
        was_equalised: bool,
    ) -> None:
        """Write a JSON sidecar file alongside the processed image.

        The sidecar is placed at ``<dst_path>.json``.

        Args:
            dst: Processed image destination path.
            src: Original source path.
            orig_dims: Original image dimensions.
            out_dims: Output image dimensions.
            file_size: Original file size in bytes.
            was_cropped: Whether face crop was applied.
            was_equalised: Whether CLAHE was applied.
        """
        metadata = ImageMetadata(
            original_path=str(src.resolve()),
            original_width=orig_dims.width,  # type: ignore[attr-defined]
            original_height=orig_dims.height,  # type: ignore[attr-defined]
            output_width=out_dims.width,  # type: ignore[attr-defined]
            output_height=out_dims.height,  # type: ignore[attr-defined]
            original_file_size_bytes=file_size,
            target_size=self._cfg.target_size,
            interpolation=self._cfg.interpolation,
            clahe_applied=was_equalised,
            face_crop_applied=was_cropped,
            padding_color=self._cfg.padding_color,
        )
        sidecar_path = dst.with_suffix(dst.suffix + ".json")
        try:
            sidecar_path.write_text(
                json.dumps(metadata.model_dump(), indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.warning(
                "Could not write sidecar for {path}: {exc}", path=dst, exc=exc
            )
