"""
JSON report exporter for MaskShield AI Dataset Builder.

Writes a single, fully-structured ``report.json`` from a
:class:`~exporters.stats_collector.DatasetStats` object, along with a
machine-readable ``pipeline_manifest.json`` that records the pipeline run
metadata (timestamp, config snapshot, versions).

The JSON report is the canonical machine-readable output consumed by:

* CI/CD pipelines for dataset quality gates
* MLflow / W&B experiment tracking integrations
* Future training harness for dataset configuration

Design
------
* :class:`JsonExporter` is injected with config — no globals.
* All ``Path`` objects are serialised as strings.
* All ``datetime`` stamps are ISO-8601 UTC.
* Output is written atomically.

Example::

    from config.loader import load_config
    from exporters.stats_collector import StatsCollector
    from exporters.json_exporter import JsonExporter

    cfg = load_config()
    stats = StatsCollector(cfg).collect()
    exporter = JsonExporter(cfg)
    path = exporter.export(stats)
"""

from __future__ import annotations

import json
import os
import platform
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger
from pydantic import BaseModel, ConfigDict

from config.models import AppConfig
from exporters.stats_collector import DatasetStats


                                                                             
              
                                                                             


class JsonExportPaths(BaseModel):
    """Paths of JSON files written by :class:`JsonExporter`.

    Attributes:
        report_json: Full structured statistics report.
        manifest_json: Pipeline run manifest with metadata.
    """

    model_config = ConfigDict(frozen=True)

    report_json: Path
    manifest_json: Path


                                                                             
          
                                                                             


class JsonExporter:
    """Writes dataset statistics and pipeline manifest to JSON files.

    Args:
        cfg: Validated :class:`~config.models.AppConfig`.
    """

    def __init__(self, cfg: AppConfig) -> None:
        self._cfg = cfg
        self._reports_dir = Path(cfg.paths.reports_dir)

                                                                        
                
                                                                        

    def export(
        self,
        stats: DatasetStats,
        output_dir: Path | None = None,
    ) -> JsonExportPaths:
        """Write the full JSON report and pipeline manifest.

        Args:
            stats: Collected :class:`~exporters.stats_collector.DatasetStats`.
            output_dir: Override output directory.  Defaults to
                ``cfg.paths.reports_dir``.

        Returns:
            :class:`JsonExportPaths` with the written file paths.
        """
        dest = output_dir or self._reports_dir
        dest.mkdir(parents=True, exist_ok=True)

        report_path = self._write_report(stats, dest)
        manifest_path = self._write_manifest(stats, dest)

        logger.success(
            "JSON reports written:\n  {r}\n  {m}",
            r=report_path,
            m=manifest_path,
        )
        return JsonExportPaths(report_json=report_path, manifest_json=manifest_path)

                                                                        
                     
                                                                        

    def _write_report(self, stats: DatasetStats, dest: Path) -> Path:
        """Serialise the full :class:`DatasetStats` to JSON.

        Args:
            stats: Dataset statistics.
            dest: Output directory.

        Returns:
            Written file path.
        """
        out_path = dest / "report.json"

        doc = {
            "generated_at": _utc_now_iso(),
            "pipeline_version": self._cfg.project.version,
            "project_name": self._cfg.project.name,
            "datasets_root": str(stats.datasets_root),
            "summary": stats.to_flat_dict(),
            "rejection_breakdown": stats.rejection_breakdown,
            "resolution_distribution": [
                {"resolution": b.resolution, "count": b.count}
                for b in stats.resolution_distribution
            ],
            "splits": {
                "train": stats.train_identities,
                "val": stats.val_identities,
                "test": stats.test_identities,
            },
            "images_per_identity": dict(
                sorted(
                    stats.images_per_identity.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )
            ),
            "per_identity_detail": [
                {
                    "identity_id": ist.identity_id,
                    "split": ist.split,
                    "total_images": ist.total_images,
                    "original_images": ist.original_images,
                    "augmented_images": ist.augmented_images,
                }
                for ist in sorted(
                    stats.per_identity_stats,
                    key=lambda x: x.total_images,
                    reverse=True,
                )
            ],
        }

        _atomic_write_json(out_path, doc)
        logger.debug("Report JSON: {path}", path=out_path)
        return out_path

                                                                        
                       
                                                                        

    def _write_manifest(self, stats: DatasetStats, dest: Path) -> Path:
        """Write a pipeline run manifest capturing environment metadata.

        Args:
            stats: Dataset statistics (used for high-level counts).
            dest: Output directory.

        Returns:
            Written file path.
        """
        out_path = dest / "pipeline_manifest.json"

        manifest = {
            "generated_at": _utc_now_iso(),
            "project": {
                "name": self._cfg.project.name,
                "version": self._cfg.project.version,
            },
            "environment": {
                "python_version": sys.version,
                "platform": platform.platform(),
                "hostname": platform.node(),
            },
            "config_snapshot": {
                "datasets_root": self._cfg.paths.datasets_root,
                "log_level": self._cfg.project.log_level,
                "augmentation_enabled": self._cfg.augmentation.enabled,
                "copies_per_image": self._cfg.augmentation.copies_per_image,
                "augmentation_seed": self._cfg.augmentation.seed,
                "target_size": list(self._cfg.preprocessing.target_size),
                "validation": {
                    "min_image_size_px": self._cfg.validation.min_image_size_px,
                    "blur_threshold": self._cfg.validation.blur_threshold,
                    "duplicate_algorithm": self._cfg.validation.duplicate_hash_algorithm,
                    "max_duplicate_distance": self._cfg.validation.max_duplicate_distance,
                },
                "splits": {
                    "train_ratio": self._cfg.splits.train_ratio,
                    "val_ratio": self._cfg.splits.val_ratio,
                    "test_ratio": self._cfg.splits.test_ratio,
                    "random_seed": self._cfg.splits.random_seed,
                },
                "enabled_datasets": [
                    name
                    for name, entry in [
                        ("lfw", self._cfg.datasets.lfw),
                        ("celeba", self._cfg.datasets.celeba),
                        ("casia_webface", self._cfg.datasets.casia_webface),
                        ("vggface2", self._cfg.datasets.vggface2),
                        ("rmfd", self._cfg.datasets.rmfd),
                        ("smfd", self._cfg.datasets.smfd),
                        ("mafa", self._cfg.datasets.mafa),
                        ("wider_face", self._cfg.datasets.wider_face),
                        ("maskedface_net", self._cfg.datasets.maskedface_net),
                        ("custom", self._cfg.datasets.custom),
                    ]
                    if entry.enabled
                ],
            },
            "dataset_summary": stats.to_flat_dict(),
        }

        _atomic_write_json(out_path, manifest)
        logger.debug("Manifest JSON: {path}", path=out_path)
        return out_path


                                                                             
         
                                                                             


def _utc_now_iso() -> str:
    """Return the current UTC timestamp as an ISO-8601 string.

    Returns:
        e.g. ``"2026-08-05T16:32:00.123456+00:00"``
    """
    return datetime.now(tz=timezone.utc).isoformat()


def _atomic_write_json(path: Path, data: dict, indent: int = 2) -> None:
    """Write *data* as pretty-printed JSON to *path* atomically.

    Args:
        path: Destination file path.
        data: JSON-serialisable dictionary.
        indent: Indentation level.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp.json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=indent, default=str, ensure_ascii=False)
            fh.write("\n")                                    
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
