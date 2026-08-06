"""
Dataset-level validation for MaskShield AI Dataset Builder.

:class:`DatasetValidator` orchestrates validation across an entire image
directory tree, adding two capabilities that require cross-image comparison:

* **Duplicate detection** — perceptual hashing with configurable Hamming
  distance threshold.  All images are hashed first, then pairwise distances
  are compared using a hash-bucket strategy for O(n) average complexity.
* **Batch validation summary** — aggregates per-image
  :class:`~validators.image_validator.ImageValidationResult` objects into
  a single :class:`DatasetValidationReport`.

Workflow
--------
1. Walk the dataset root with :func:`~utils.file_ops.iter_images`.
2. For each image: run :class:`~validators.image_validator.ImageValidator`.
3. After validation: run duplicate detection pass.
4. Produce a :class:`DatasetValidationReport`.
5. Optionally remove rejected/duplicate files in-place.

Design
------
* All state lives in local variables — no instance state mutated after
  ``__init__``.
* Progress is reported via Loguru (configurable level).
* The *dry_run* flag prevents any filesystem mutation, making the
  validator safe for CI/preview use.

Example::

    from config.loader import load_config
    from validators.dataset_validator import DatasetValidator

    cfg = load_config()
    validator = DatasetValidator(cfg.validation)
    report = validator.validate_directory(
        Path("datasets/lfw"),
        remove_invalid=True,
        dry_run=False,
    )
    print(report.summary())
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import imagehash
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field

from config.models import ValidationConfig
from utils.file_ops import iter_images
from utils.hashing import HashAlgorithm, hamming_distance, perceptual_hash
from validators.image_validator import (
    ImageValidationResult,
    ImageValidator,
    RejectionReason,
)


                                                                             
               
                                                                             


class DuplicateGroup(BaseModel):
    """A group of images that are perceptual near-duplicates of each other.

    Attributes:
        canonical: The image kept as the representative of the group.
        duplicates: All other images in the group (to be removed).
        max_distance: Largest Hamming distance within the group.
    """

    model_config = ConfigDict(frozen=True)

    canonical: Path
    duplicates: list[Path]
    max_distance: int


class DatasetValidationReport(BaseModel):
    """Summary of a full dataset validation run.

    Attributes:
        root: The directory that was validated.
        total_scanned: Number of image files examined.
        valid_count: Images that passed all checks.
        rejected_count: Images that failed at least one check.
        duplicate_count: Images identified as near-duplicates (excluding canonical).
        rejection_breakdown: Count per :class:`~validators.image_validator.RejectionReason`.
        duplicate_groups: Structured duplicate groups.
        invalid_paths: Paths of rejected images (for audit / removal).
        duplicate_paths: Paths of duplicate images to discard (for audit / removal).
    """

    model_config = ConfigDict(frozen=True)

    root: Path
    total_scanned: int = 0
    valid_count: int = 0
    rejected_count: int = 0
    duplicate_count: int = 0
    rejection_breakdown: dict[str, int] = Field(default_factory=dict)
    duplicate_groups: list[DuplicateGroup] = Field(default_factory=list)
    invalid_paths: list[Path] = Field(default_factory=list)
    duplicate_paths: list[Path] = Field(default_factory=list)

    def summary(self) -> str:
        """Return a human-readable multi-line summary string.

        Returns:
            Formatted summary suitable for console or log output.
        """
        lines = [
            f"Dataset Validation Report — {self.root}",
            f"  Total scanned : {self.total_scanned}",
            f"  Valid         : {self.valid_count}",
            f"  Rejected      : {self.rejected_count}",
            f"  Duplicates    : {self.duplicate_count}",
            "  Rejection breakdown:",
        ]
        for reason, count in sorted(self.rejection_breakdown.items()):
            lines.append(f"    {reason:<24} {count}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Serialise to a plain dict (JSON-compatible, paths as strings).

        Returns:
            Dict representation of the report.
        """
        data = self.model_dump()
                                                                 
        data["root"] = str(self.root)
        data["invalid_paths"] = [str(p) for p in self.invalid_paths]
        data["duplicate_paths"] = [str(p) for p in self.duplicate_paths]
        data["duplicate_groups"] = [
            {
                "canonical": str(g.canonical),
                "duplicates": [str(d) for d in g.duplicates],
                "max_distance": g.max_distance,
            }
            for g in self.duplicate_groups
        ]
        return data


                                                                             
                   
                                                                             


class DatasetValidator:
    """Orchestrates image-level validation and duplicate detection across a
    directory tree, producing a structured :class:`DatasetValidationReport`.

    Args:
        config: Validated :class:`~config.models.ValidationConfig`.

    Example::

        validator = DatasetValidator(cfg.validation)
        report = validator.validate_directory(Path("datasets/lfw"))
    """

    def __init__(self, config: ValidationConfig) -> None:
        self._cfg = config
        self._image_validator = ImageValidator(config)

                                                                        
                
                                                                        

    def validate_directory(
        self,
        root: Path,
        *,
        remove_invalid: bool = False,
        remove_duplicates: bool = False,
        dry_run: bool = True,
    ) -> DatasetValidationReport:
        """Validate all images under *root* and optionally remove bad files.

        Args:
            root: Root directory to scan recursively.
            remove_invalid: If ``True`` and ``dry_run=False``, physically
                delete images that fail validation checks.
            remove_duplicates: If ``True`` and ``dry_run=False``, physically
                delete duplicate images, keeping one canonical per group.
            dry_run: When ``True`` (default), no files are removed regardless
                of the other flags.  Use ``False`` with care.

        Returns:
            A fully populated :class:`DatasetValidationReport`.

        Raises:
            NotADirectoryError: If *root* is not a directory.
        """
        if not root.is_dir():
            raise NotADirectoryError(f"Not a directory: {root}")

        logger.info(
            "Starting dataset validation: root={root} | dry_run={dry_run}",
            root=root,
            dry_run=dry_run,
        )

                                                                          
                                        
                                                                          
        results: list[ImageValidationResult] = self._run_image_validation(root)

                                                                          
                                                                            
                                                                          
        valid_results = [r for r in results if r.is_valid]
        duplicate_groups = self._detect_duplicates(valid_results)

                                                                          
                                  
                                                                          
        report = self._compile_report(root, results, duplicate_groups)
        logger.info("Validation complete.\n{summary}", summary=report.summary())

                                                                          
                                    
                                                                          
        if not dry_run:
            if remove_invalid:
                self._remove_files(report.invalid_paths, label="invalid")
            if remove_duplicates:
                self._remove_files(report.duplicate_paths, label="duplicate")
        else:
            if remove_invalid or remove_duplicates:
                logger.warning(
                    "dry_run=True — no files removed (would remove "
                    "{n} invalid + {d} duplicate).",
                    n=len(report.invalid_paths),
                    d=len(report.duplicate_paths),
                )

        return report

    def validate_single(self, image_path: Path) -> ImageValidationResult:
        """Validate a single image without duplicate detection.

        Convenience wrapper around :class:`~validators.image_validator.ImageValidator`.

        Args:
            image_path: Path to the image file.

        Returns:
            :class:`~validators.image_validator.ImageValidationResult`.
        """
        return self._image_validator.validate(image_path)

    def save_report(self, report: DatasetValidationReport, output_path: Path) -> None:
        """Persist the report as a JSON file.

        Args:
            report: The report to serialise.
            output_path: Destination ``.json`` file path.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        data = report.to_dict()
        output_path.write_text(
            json.dumps(data, indent=2, default=str), encoding="utf-8"
        )
        logger.info("Validation report saved: {path}", path=output_path)

                                                                        
                     
                                                                        

    def _run_image_validation(self, root: Path) -> list[ImageValidationResult]:
        """Walk *root* and validate each image.

        Args:
            root: Directory to scan.

        Returns:
            List of :class:`ImageValidationResult` objects.
        """
        results: list[ImageValidationResult] = []
        total = 0
        for img_path in iter_images(root):
            total += 1
            result = self._image_validator.validate(img_path)
            results.append(result)
            if total % 500 == 0:
                logger.info("Validated {n} images so far ...", n=total)
        logger.info("Phase 1 complete: scanned {n} images.", n=total)
        return results

    def _detect_duplicates(
        self,
        valid_results: list[ImageValidationResult],
    ) -> list[DuplicateGroup]:
        """Run perceptual hash-based duplicate detection.

        Uses a hash-bucket approach: images whose hash strings are identical
        are placed in the same bucket immediately; for near-duplicates,
        pairwise Hamming distances are compared within a candidate window.

        Args:
            valid_results: Images that passed per-image validation.

        Returns:
            List of :class:`DuplicateGroup` objects (may be empty).
        """
        if not valid_results:
            return []

        algo = HashAlgorithm(self._cfg.duplicate_hash_algorithm)
        hash_size = self._cfg.duplicate_hash_bits
        max_dist = self._cfg.max_duplicate_distance

        logger.info(
            "Duplicate detection: algorithm={algo}, hash_size={size}, max_distance={dist}",
            algo=algo.value,
            size=hash_size,
            dist=max_dist,
        )

                                 
        path_to_hash: dict[Path, imagehash.ImageHash] = {}
        for result in valid_results:
            try:
                h = perceptual_hash(result.path, algorithm=algo, hash_size=hash_size)
                path_to_hash[result.path] = h
            except Exception as exc:
                logger.warning(
                    "Cannot hash {path}: {exc}", path=result.path, exc=exc
                )

                                                                          
        buckets: dict[str, list[Path]] = defaultdict(list)
        for path, h in path_to_hash.items():
            buckets[str(h)].append(path)

                                                          
                                                                     
                                                                               
                                                                              
                                
        duplicate_groups: list[DuplicateGroup] = []
        assigned: set[Path] = set()

        sorted_paths = sorted(path_to_hash.keys(), key=lambda p: str(path_to_hash[p]))

        for i, path_a in enumerate(sorted_paths):
            if path_a in assigned:
                continue
            group_dups: list[Path] = []
            group_max_dist: int = 0

            for path_b in sorted_paths[i + 1 :]:
                if path_b in assigned:
                    continue
                dist = hamming_distance(path_to_hash[path_a], path_to_hash[path_b])
                if dist <= max_dist:
                    group_dups.append(path_b)
                    assigned.add(path_b)
                    group_max_dist = max(group_max_dist, dist)

            if group_dups:
                assigned.add(path_a)
                duplicate_groups.append(
                    DuplicateGroup(
                        canonical=path_a,
                        duplicates=group_dups,
                        max_distance=group_max_dist,
                    )
                )
                logger.debug(
                    "Duplicate group: canonical={canon} | {n} duplicates",
                    canon=path_a.name,
                    n=len(group_dups),
                )

        total_dups = sum(len(g.duplicates) for g in duplicate_groups)
        logger.info(
            "Duplicate detection complete: {groups} groups, {dups} duplicates.",
            groups=len(duplicate_groups),
            dups=total_dups,
        )
        return duplicate_groups

    def _compile_report(
        self,
        root: Path,
        results: list[ImageValidationResult],
        duplicate_groups: list[DuplicateGroup],
    ) -> DatasetValidationReport:
        """Aggregate per-image results and duplicate groups into a report.

        Args:
            root: Validated directory root.
            results: All per-image validation results.
            duplicate_groups: Duplicate groups from phase 2.

        Returns:
            Fully populated :class:`DatasetValidationReport`.
        """
        invalid_paths: list[Path] = []
        duplicate_paths: list[Path] = []
        breakdown: dict[str, int] = defaultdict(int)

        for result in results:
            if not result.is_valid:
                invalid_paths.append(result.path)
                for reason in result.rejection_reasons:
                    breakdown[reason.value] += 1

        for group in duplicate_groups:
            for dup in group.duplicates:
                duplicate_paths.append(dup)

        total_scanned = len(results)
        rejected_count = len(invalid_paths)
        duplicate_count = len(duplicate_paths)
        valid_count = total_scanned - rejected_count

        return DatasetValidationReport(
            root=root,
            total_scanned=total_scanned,
            valid_count=valid_count,
            rejected_count=rejected_count,
            duplicate_count=duplicate_count,
            rejection_breakdown=dict(breakdown),
            duplicate_groups=duplicate_groups,
            invalid_paths=invalid_paths,
            duplicate_paths=duplicate_paths,
        )

    @staticmethod
    def _remove_files(paths: list[Path], label: str) -> None:
        """Delete a list of files from disk.

        Args:
            paths: File paths to delete.
            label: Human-readable label for log messages.
        """
        removed = 0
        for path in paths:
            try:
                path.unlink(missing_ok=True)
                removed += 1
            except OSError as exc:
                logger.error(
                    "Failed to remove {label} file {path}: {exc}",
                    label=label,
                    path=path,
                    exc=exc,
                )
        logger.info("Removed {n} {label} file(s).", n=removed, label=label)
