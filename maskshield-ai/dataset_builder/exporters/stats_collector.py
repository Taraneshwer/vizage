"""
Dataset statistics collector for MaskShield AI Dataset Builder.

:class:`StatsCollector` walks the canonical dataset directory structure
and computes a comprehensive :class:`DatasetStats` report covering:

* Identity counts and per-identity image counts
* Masked / unmasked / unknown image distribution
* Augmented image counts
* Image resolution distribution
* Validation rejection summary (integrated from a
  :class:`~validators.dataset_validator.DatasetValidationReport` if provided)
* Augmentation summary (integrated from a list of
  :class:`~augmentations.pipeline.AugmentationResult` if provided)

The :class:`DatasetStats` model is the single source of truth fed into
:mod:`exporters.csv_exporter`, :mod:`exporters.json_exporter`, and
:mod:`exporters.visualizer`.

Design
------
* ``StatsCollector`` is injected with :class:`~config.models.AppConfig`
  — no global state.
* Collection is done in a single filesystem walk; no images are loaded
  (counts only, not pixel-level stats).
* The resulting :class:`DatasetStats` is a **frozen Pydantic model** —
  safe to share, serialise, and pass between modules.

Example::

    from config.loader import load_config
    from exporters.stats_collector import StatsCollector

    cfg = load_config()
    collector = StatsCollector(cfg)
    stats = collector.collect()
    print(stats.summary())
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field

from config.models import AppConfig
from utils.file_ops import IMAGE_EXTENSIONS, count_files, iter_images, list_subdirs


# ---------------------------------------------------------------------------
# Per-identity stats
# ---------------------------------------------------------------------------


class IdentityStats(BaseModel):
    """Statistics for a single registered identity.

    Attributes:
        identity_id: The directory name (slug) for this identity.
        split: Which split this identity belongs to (``train``, ``val``, ``test``).
        total_images: Total image count including augmented copies.
        original_images: Non-augmented image count.
        augmented_images: Images whose filename contains ``_aug_``.
        resolutions: Mapping of ``"WxH"`` → count of images at that resolution.
    """

    model_config = ConfigDict(frozen=True)

    identity_id: str
    split: str
    total_images: int = 0
    original_images: int = 0
    augmented_images: int = 0
    resolutions: dict[str, int] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Resolution bucket
# ---------------------------------------------------------------------------


class ResolutionBucket(BaseModel):
    """Aggregated resolution statistics across the whole dataset.

    Attributes:
        resolution: ``"WxH"`` string.
        count: Number of images at this resolution.
    """

    model_config = ConfigDict(frozen=True)

    resolution: str
    count: int


# ---------------------------------------------------------------------------
# Top-level dataset stats
# ---------------------------------------------------------------------------


class DatasetStats(BaseModel):
    """Complete statistics snapshot of the organised dataset.

    Attributes:
        datasets_root: The root directory that was scanned.
        total_identities: Count of unique identity folders across all splits.
        train_identities: Identities in ``identities/`` (train set).
        val_identities: Identities in ``validation/``.
        test_identities: Identities in ``test/``.
        total_images: All images across all directories.
        masked_count: Images under ``masked/``.
        unmasked_count: Images under ``unmasked/``.
        unknown_count: Images under ``unknown/``.
        identity_images: Images under ``identities/``, ``validation/``, ``test/``.
        augmented_count: Images whose filename contains ``_aug_``.
        original_count: Images that are not augmented copies.
        duplicates_removed: Count from a validation report, if provided.
        corrupted_removed: Count from a validation report, if provided.
        rejection_breakdown: Per-reason rejection counts from validation.
        images_per_identity: Mapping of ``identity_id`` → total image count.
        per_identity_stats: Detailed :class:`IdentityStats` per identity.
        resolution_distribution: Resolution buckets sorted by count desc.
        min_images_per_identity: Minimum observed image count across identities.
        max_images_per_identity: Maximum observed image count across identities.
        mean_images_per_identity: Mean image count across identities.
    """

    model_config = ConfigDict(frozen=True)

    datasets_root: Path
    total_identities: int = 0
    train_identities: int = 0
    val_identities: int = 0
    test_identities: int = 0
    total_images: int = 0
    masked_count: int = 0
    unmasked_count: int = 0
    unknown_count: int = 0
    identity_images: int = 0
    augmented_count: int = 0
    original_count: int = 0
    duplicates_removed: int = 0
    corrupted_removed: int = 0
    rejection_breakdown: dict[str, int] = Field(default_factory=dict)
    images_per_identity: dict[str, int] = Field(default_factory=dict)
    per_identity_stats: list[IdentityStats] = Field(default_factory=list)
    resolution_distribution: list[ResolutionBucket] = Field(default_factory=list)
    min_images_per_identity: int = 0
    max_images_per_identity: int = 0
    mean_images_per_identity: float = 0.0

    def summary(self) -> str:
        """Return a formatted multi-line summary string.

        Returns:
            Human-readable stats summary.
        """
        lines = [
            f"Dataset Statistics — {self.datasets_root}",
            f"  Total identities  : {self.total_identities}",
            f"    Train           : {self.train_identities}",
            f"    Validation      : {self.val_identities}",
            f"    Test            : {self.test_identities}",
            f"  Total images      : {self.total_images}",
            f"    Identity images : {self.identity_images}",
            f"    Masked          : {self.masked_count}",
            f"    Unmasked        : {self.unmasked_count}",
            f"    Unknown         : {self.unknown_count}",
            f"    Augmented       : {self.augmented_count}",
            f"    Original        : {self.original_count}",
            f"  Duplicates removed: {self.duplicates_removed}",
            f"  Corrupted removed : {self.corrupted_removed}",
            f"  Images/identity   : min={self.min_images_per_identity} "
            f"max={self.max_images_per_identity} "
            f"mean={self.mean_images_per_identity:.1f}",
        ]
        return "\n".join(lines)

    def to_flat_dict(self) -> dict:
        """Return a flat dictionary suitable for a single CSV row.

        Returns:
            Dict with scalar fields only (no nested models).
        """
        return {
            "datasets_root": str(self.datasets_root),
            "total_identities": self.total_identities,
            "train_identities": self.train_identities,
            "val_identities": self.val_identities,
            "test_identities": self.test_identities,
            "total_images": self.total_images,
            "masked_count": self.masked_count,
            "unmasked_count": self.unmasked_count,
            "unknown_count": self.unknown_count,
            "identity_images": self.identity_images,
            "augmented_count": self.augmented_count,
            "original_count": self.original_count,
            "duplicates_removed": self.duplicates_removed,
            "corrupted_removed": self.corrupted_removed,
            "min_images_per_identity": self.min_images_per_identity,
            "max_images_per_identity": self.max_images_per_identity,
            "mean_images_per_identity": round(self.mean_images_per_identity, 2),
        }


# ---------------------------------------------------------------------------
# Collector service
# ---------------------------------------------------------------------------


class StatsCollector:
    """Walks the canonical dataset structure and computes :class:`DatasetStats`.

    Args:
        cfg: Validated :class:`~config.models.AppConfig`.

    Example::

        collector = StatsCollector(cfg)
        stats = collector.collect()
    """

    def __init__(self, cfg: AppConfig) -> None:
        self._cfg = cfg
        self._root = Path(cfg.paths.datasets_root)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def collect(
        self,
        *,
        validation_report: object | None = None,
        augmentation_results: list | None = None,
    ) -> DatasetStats:
        """Collect statistics from the canonical dataset directory.

        Args:
            validation_report: Optional
                :class:`~validators.dataset_validator.DatasetValidationReport`
                to integrate rejection/duplicate counts.
            augmentation_results: Optional list of
                :class:`~augmentations.pipeline.AugmentationResult` objects
                to integrate augmentation counts.

        Returns:
            Fully populated :class:`DatasetStats`.
        """
        logger.info("Collecting dataset statistics from: {root}", root=self._root)

        # ----------------------------------------------------------------
        # Per-category counts (flat dirs)
        # ----------------------------------------------------------------
        masked_count = self._count_images(self._root / "masked")
        unmasked_count = self._count_images(self._root / "unmasked")
        unknown_count = self._count_images(self._root / "unknown")

        # ----------------------------------------------------------------
        # Identity directories (train / val / test)
        # ----------------------------------------------------------------
        train_stats = self._collect_identity_dir(
            self._root / "identities", split="train"
        )
        val_stats = self._collect_identity_dir(
            self._root / "validation", split="val"
        )
        test_stats = self._collect_identity_dir(
            self._root / "test", split="test"
        )

        all_identity_stats = train_stats + val_stats + test_stats

        # ----------------------------------------------------------------
        # Aggregate identity image counts
        # ----------------------------------------------------------------
        images_per_identity: dict[str, int] = {
            s.identity_id: s.total_images for s in all_identity_stats
        }
        identity_images = sum(images_per_identity.values())

        augmented_count = sum(s.augmented_images for s in all_identity_stats)
        original_count = sum(s.original_images for s in all_identity_stats)

        # ----------------------------------------------------------------
        # Resolution distribution (across identity images only — fast count)
        # ----------------------------------------------------------------
        resolution_dist = self._build_resolution_distribution(all_identity_stats)

        # ----------------------------------------------------------------
        # Summary scalars
        # ----------------------------------------------------------------
        counts = list(images_per_identity.values())
        total_identities = len(counts)
        min_img = min(counts) if counts else 0
        max_img = max(counts) if counts else 0
        mean_img = sum(counts) / len(counts) if counts else 0.0

        total_images = masked_count + unmasked_count + unknown_count + identity_images

        # ----------------------------------------------------------------
        # Integrate validation report
        # ----------------------------------------------------------------
        duplicates_removed = 0
        corrupted_removed = 0
        rejection_breakdown: dict[str, int] = {}

        if validation_report is not None:
            duplicates_removed = getattr(validation_report, "duplicate_count", 0)
            corrupted_removed = getattr(
                validation_report, "rejection_breakdown", {}
            ).get("corrupted", 0)
            rejection_breakdown = dict(
                getattr(validation_report, "rejection_breakdown", {})
            )

        # ----------------------------------------------------------------
        # Integrate augmentation results
        # ----------------------------------------------------------------
        if augmentation_results is not None:
            aug_total = sum(
                getattr(r, "copies_created", 0) for r in augmentation_results
            )
            augmented_count = aug_total

        logger.success(
            "Stats collected: {ids} identities, {imgs} images.",
            ids=total_identities,
            imgs=total_images,
        )

        stats = DatasetStats(
            datasets_root=self._root,
            total_identities=total_identities,
            train_identities=len(train_stats),
            val_identities=len(val_stats),
            test_identities=len(test_stats),
            total_images=total_images,
            masked_count=masked_count,
            unmasked_count=unmasked_count,
            unknown_count=unknown_count,
            identity_images=identity_images,
            augmented_count=augmented_count,
            original_count=original_count,
            duplicates_removed=duplicates_removed,
            corrupted_removed=corrupted_removed,
            rejection_breakdown=rejection_breakdown,
            images_per_identity=images_per_identity,
            per_identity_stats=all_identity_stats,
            resolution_distribution=resolution_dist,
            min_images_per_identity=min_img,
            max_images_per_identity=max_img,
            mean_images_per_identity=mean_img,
        )

        logger.info("\n{summary}", summary=stats.summary())
        return stats

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _collect_identity_dir(
        self, identity_root: Path, split: str
    ) -> list[IdentityStats]:
        """Walk *identity_root* and build per-identity stats.

        Args:
            identity_root: Directory containing per-person subdirectories.
            split: Split label (``"train"``, ``"val"``, ``"test"``).

        Returns:
            List of :class:`IdentityStats` for each subdirectory found.
        """
        if not identity_root.is_dir():
            return []

        results: list[IdentityStats] = []
        for person_dir in sorted(identity_root.iterdir()):
            if not person_dir.is_dir():
                continue

            all_imgs = list(iter_images(person_dir, recursive=True))
            augmented = [p for p in all_imgs if "_aug_" in p.stem]
            original = [p for p in all_imgs if "_aug_" not in p.stem]

            res_counts: dict[str, int] = defaultdict(int)
            # Sample up to 200 images for resolution counting (performance).
            sample = all_imgs[:200]
            for img_path in sample:
                label = _fast_resolution_label(img_path)
                if label:
                    res_counts[label] += 1

            results.append(
                IdentityStats(
                    identity_id=person_dir.name,
                    split=split,
                    total_images=len(all_imgs),
                    original_images=len(original),
                    augmented_images=len(augmented),
                    resolutions=dict(res_counts),
                )
            )

        logger.debug(
            "Collected {n} identities from {split} split.", n=len(results), split=split
        )
        return results

    @staticmethod
    def _count_images(directory: Path) -> int:
        """Count all image files under *directory*.

        Args:
            directory: Directory to scan.

        Returns:
            Image file count, or 0 if directory does not exist.
        """
        if not directory.is_dir():
            return 0
        return sum(
            1
            for p in directory.rglob("*")
            if p.is_file() and p.suffix.lstrip(".").lower() in IMAGE_EXTENSIONS
        )

    @staticmethod
    def _build_resolution_distribution(
        identity_stats: list[IdentityStats],
    ) -> list[ResolutionBucket]:
        """Aggregate resolution counts across all identity stats.

        Args:
            identity_stats: Per-identity stats with resolution dicts.

        Returns:
            List of :class:`ResolutionBucket` sorted by count descending.
        """
        aggregated: dict[str, int] = defaultdict(int)
        for ist in identity_stats:
            for res, cnt in ist.resolutions.items():
                aggregated[res] += cnt

        return [
            ResolutionBucket(resolution=res, count=cnt)
            for res, cnt in sorted(aggregated.items(), key=lambda x: -x[1])
        ]


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _fast_resolution_label(img_path: Path) -> str | None:
    """Read image dimensions without full decode using Pillow's lazy loader.

    Args:
        img_path: Path to the image file.

    Returns:
        ``"WxH"`` label string, or ``None`` on failure.
    """
    try:
        from PIL import Image

        with Image.open(img_path) as img:
            w, h = img.size
        return f"{w}x{h}"
    except Exception:  # noqa: BLE001
        return None
