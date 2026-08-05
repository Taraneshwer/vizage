"""
Augmentation pipeline service for MaskShield AI Dataset Builder.

:class:`AugmentationPipeline` orchestrates the full augmentation workflow:

1. Load the source image.
2. Apply the Albumentations transform chain (rotation, flip, blur, noise…).
3. Apply synthetic mask simulation (optional, per-image probability).
4. Apply synthetic sunglasses simulation (optional, per-image probability).
5. Save each augmented copy with a deterministic filename suffix.
6. Return a structured :class:`AugmentationResult`.

This pipeline is designed to generate ``N`` augmented copies per image,
where ``N = cfg.augmentation.copies_per_image``.

Design
------
* A **per-image** :class:`random.Random` instance seeded from
  ``global_seed XOR image_index`` guarantees reproducible output for every
  image regardless of processing order.
* The Albumentations pipeline is built once and reused across all images.
* Custom simulators (:class:`~augmentations.mask_simulator.MaskSimulator`,
  :class:`~augmentations.mask_simulator.SunglassesSimulator`) run **after**
  Albumentations to maximise realism (noise on top of mask rather than mask
  on top of blurred image).
* ``dry_run=True`` runs all logic but does **not** write files — useful for
  profiling and testing.

Example::

    from config.loader import load_config
    from augmentations.pipeline import AugmentationPipeline

    cfg = load_config()
    pipeline = AugmentationPipeline(cfg)
    results = pipeline.augment_directory(
        src_dir=Path("datasets/identities"),
        dst_dir=Path("datasets/augmented"),
    )
    print(f"Generated {sum(r.copies_created for r in results)} augmented images.")
"""

from __future__ import annotations

import random
from collections.abc import Iterator
from pathlib import Path

import numpy as np
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field

from augmentations.mask_simulator import MaskSimulator, SunglassesSimulator
from augmentations.transforms import build_transform_pipeline
from config.models import AppConfig, AugmentationConfig
from utils.file_ops import ensure_dir, iter_images
from utils.image_utils import ImageLoadError, load_image_bgr, save_image


# ---------------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------------


class AugmentationResult(BaseModel):
    """Outcome of augmenting a single source image.

    Attributes:
        source_path: Original image that was augmented.
        copies_created: Number of augmented images successfully written.
        copies_failed: Number of copies that failed to generate.
        output_paths: Paths of the successfully written augmented images.
        error_message: Description of load / save errors, if any.
    """

    model_config = ConfigDict(frozen=True)

    source_path: Path
    copies_created: int = 0
    copies_failed: int = 0
    output_paths: list[Path] = Field(default_factory=list)
    error_message: str | None = None

    @property
    def succeeded(self) -> bool:
        """``True`` if at least one copy was created without error."""
        return self.copies_created > 0 and self.error_message is None


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


class AugmentationPipeline:
    """Applies the full augmentation pipeline to a dataset directory.

    Args:
        cfg: Validated :class:`~config.models.AppConfig`.

    Example::

        pipeline = AugmentationPipeline(cfg)
        for result in pipeline.augment_directory(src_dir, dst_dir):
            print(result.copies_created)
    """

    def __init__(self, cfg: AppConfig) -> None:
        self._cfg = cfg
        self._aug_cfg: AugmentationConfig = cfg.augmentation

        if not self._aug_cfg.enabled:
            logger.warning("Augmentation is disabled in config (enabled=false).")

        # Build the Albumentations Compose pipeline once.
        self._transform = build_transform_pipeline(
            self._aug_cfg, seed=self._aug_cfg.seed
        )

        # Build custom simulators.
        self._mask_sim = MaskSimulator(
            self._aug_cfg.transforms.random_mask_simulation
        )
        self._glasses_sim = SunglassesSimulator(
            self._aug_cfg.transforms.random_sunglasses
        )

        self._n_copies = self._aug_cfg.copies_per_image
        self._global_seed = self._aug_cfg.seed
        self._output_fmt = f".{self._aug_cfg.output_format.lstrip('.')}"
        self._jpeg_quality = self._aug_cfg.jpeg_quality

    # ------------------------------------------------------------------
    # Public API — batch
    # ------------------------------------------------------------------

    def augment_directory(
        self,
        src_dir: Path,
        dst_dir: Path,
        *,
        dry_run: bool = False,
        overwrite: bool = False,
    ) -> Iterator[AugmentationResult]:
        """Augment every image under *src_dir* and write copies to *dst_dir*.

        Mirrors the relative path structure of *src_dir* under *dst_dir*,
        appending ``_aug_<n>`` before the extension for each copy.

        Args:
            src_dir: Source directory to scan recursively.
            dst_dir: Output root directory for augmented images.
            dry_run: If ``True``, run the pipeline but do not write files.
            overwrite: If ``True``, overwrite existing augmented files.

        Yields:
            :class:`AugmentationResult` for each source image processed.

        Raises:
            NotADirectoryError: If *src_dir* is not a directory.
        """
        if not src_dir.is_dir():
            raise NotADirectoryError(f"Not a directory: {src_dir}")

        if not self._aug_cfg.enabled:
            logger.warning("Augmentation skipped — disabled in config.")
            return

        total_created = 0
        total_failed = 0

        for idx, img_path in enumerate(iter_images(src_dir, recursive=True)):
            rel = img_path.relative_to(src_dir)
            dst_base = dst_dir / rel.parent

            result = self.augment_image(
                src=img_path,
                dst_dir=dst_base,
                image_index=idx,
                dry_run=dry_run,
                overwrite=overwrite,
            )
            total_created += result.copies_created
            total_failed += result.copies_failed

            if (idx + 1) % 500 == 0:
                logger.info(
                    "Augmentation progress: {n} images | {c} copies | {f} failed",
                    n=idx + 1,
                    c=total_created,
                    f=total_failed,
                )

            yield result

        logger.success(
            "Augmentation complete: {c} copies created, {f} failed.",
            c=total_created,
            f=total_failed,
        )

    def augment_directory_eager(
        self,
        src_dir: Path,
        dst_dir: Path,
        *,
        dry_run: bool = False,
        overwrite: bool = False,
    ) -> list[AugmentationResult]:
        """Eagerly augment all images and return the full result list.

        Args:
            src_dir: Source directory.
            dst_dir: Output directory.
            dry_run: Skip writing files.
            overwrite: Overwrite existing augmented files.

        Returns:
            List of :class:`AugmentationResult` objects.
        """
        return list(
            self.augment_directory(
                src_dir=src_dir,
                dst_dir=dst_dir,
                dry_run=dry_run,
                overwrite=overwrite,
            )
        )

    # ------------------------------------------------------------------
    # Public API — single image
    # ------------------------------------------------------------------

    def augment_image(
        self,
        src: Path,
        dst_dir: Path,
        *,
        image_index: int = 0,
        dry_run: bool = False,
        overwrite: bool = False,
    ) -> AugmentationResult:
        """Generate ``copies_per_image`` augmented variants of *src*.

        Each copy uses a deterministic per-copy RNG seeded from
        ``global_seed XOR (image_index * 1000 + copy_index)``.

        Args:
            src: Source image file.
            dst_dir: Directory to write augmented copies into.
            image_index: Unique integer index of this image (used for seeding).
            dry_run: Run pipeline but skip writing output.
            overwrite: Overwrite existing copies.

        Returns:
            :class:`AugmentationResult`.
        """
        # Load source image.
        try:
            original = load_image_bgr(src)
        except (ImageLoadError, FileNotFoundError, OSError) as exc:
            logger.error("Cannot load [{path}]: {exc}", path=src, exc=exc)
            return AugmentationResult(
                source_path=src,
                copies_created=0,
                copies_failed=self._n_copies,
                error_message=str(exc),
            )

        if not dry_run:
            ensure_dir(dst_dir)

        stem = src.stem
        output_paths: list[Path] = []
        failed = 0

        for copy_idx in range(self._n_copies):
            # Deterministic per-copy seed.
            copy_seed = self._global_seed ^ (image_index * 1_000 + copy_idx)
            rng = random.Random(copy_seed)

            out_name = f"{stem}_aug_{copy_idx}{self._output_fmt}"
            out_path = dst_dir / out_name

            if out_path.exists() and not overwrite:
                output_paths.append(out_path)
                continue

            try:
                augmented = self._apply_pipeline(original.copy(), rng, copy_seed)
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "Augmentation failed [{src}] copy {n}: {exc}",
                    src=src.name,
                    n=copy_idx,
                    exc=exc,
                )
                failed += 1
                continue

            if not dry_run:
                try:
                    save_image(augmented, out_path, quality=self._jpeg_quality)
                    output_paths.append(out_path)
                except (ValueError, OSError) as exc:
                    logger.error(
                        "Save failed [{path}]: {exc}", path=out_path, exc=exc
                    )
                    failed += 1
            else:
                # Dry run: count as created without writing.
                output_paths.append(out_path)

        logger.debug(
            "Augmented [{src}]: {ok}/{total} copies.",
            src=src.name,
            ok=len(output_paths),
            total=self._n_copies,
        )

        return AugmentationResult(
            source_path=src,
            copies_created=len(output_paths),
            copies_failed=failed,
            output_paths=output_paths,
        )

    # ------------------------------------------------------------------
    # Private: apply full pipeline to one image
    # ------------------------------------------------------------------

    def _apply_pipeline(
        self, img: np.ndarray, rng: random.Random, seed: int
    ) -> np.ndarray:
        """Apply the complete augmentation pipeline to a single image array.

        Order:
        1. Albumentations transforms (rotation, flip, noise, blur, etc.)
        2. Synthetic mask overlay
        3. Synthetic sunglasses overlay

        Args:
            img: BGR ``uint8`` source image array.
            rng: Per-copy seeded :class:`random.Random`.
            seed: Integer seed forwarded to Albumentations.

        Returns:
            Augmented BGR ``uint8`` array.
        """
        # Step 1 — Albumentations (operates on RGB internally).
        img_rgb = img[:, :, ::-1]  # BGR → RGB
        result = self._transform(image=img_rgb)
        img_rgb = result["image"]
        img = img_rgb[:, :, ::-1]  # RGB → BGR

        # Step 2 — Synthetic mask
        mask_cfg = self._aug_cfg.transforms.random_mask_simulation
        if mask_cfg.enabled:
            img = self._mask_sim.apply(img, rng)

        # Step 3 — Synthetic sunglasses
        glasses_cfg = self._aug_cfg.transforms.random_sunglasses
        if glasses_cfg.enabled:
            img = self._glasses_sim.apply(img, rng)

        return img

    # ------------------------------------------------------------------
    # Public: preview
    # ------------------------------------------------------------------

    def generate_preview_grid(
        self,
        src: Path,
        output_path: Path,
        n_samples: int = 8,
    ) -> None:
        """Generate a grid image showing *n_samples* augmented variants.

        Writes a single PNG grid image to *output_path* for visual inspection.

        Args:
            src: Source image to augment for preview.
            output_path: Destination PNG file path.
            n_samples: Number of augmented samples to include in the grid.
        """
        import cv2

        try:
            original = load_image_bgr(src)
        except (ImageLoadError, FileNotFoundError, OSError) as exc:
            logger.error("Cannot load preview source [{path}]: {exc}", path=src, exc=exc)
            return

        samples: list[np.ndarray] = [original]

        for i in range(n_samples - 1):
            rng = random.Random(self._global_seed + i + 1)
            try:
                aug = self._apply_pipeline(original.copy(), rng, self._global_seed + i + 1)
                samples.append(aug)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Preview sample {i} failed: {exc}", i=i, exc=exc)

        # Resize all samples to a common size for the grid.
        thumb_size = (128, 128)
        thumbnails = [
            cv2.resize(s, thumb_size, interpolation=cv2.INTER_LANCZOS4)
            for s in samples
        ]

        # Arrange into a row grid (up to 8 per row).
        cols = min(8, len(thumbnails))
        rows = (len(thumbnails) + cols - 1) // cols
        row_imgs = []
        for r in range(rows):
            row_slice = thumbnails[r * cols : (r + 1) * cols]
            while len(row_slice) < cols:
                row_slice.append(np.zeros((thumb_size[1], thumb_size[0], 3), dtype=np.uint8))
            row_imgs.append(np.hstack(row_slice))

        grid = np.vstack(row_imgs)
        ensure_dir(output_path.parent)
        cv2.imwrite(str(output_path), grid)
        logger.success("Preview grid saved: {path}", path=output_path)
