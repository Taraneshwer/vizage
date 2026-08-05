"""
CSV report exporter for MaskShield AI Dataset Builder.

Writes three complementary CSV files from a :class:`~exporters.stats_collector.DatasetStats`
object:

1. **summary.csv** — one row with all scalar dataset-level metrics.
2. **per_identity.csv** — one row per identity with image counts and split.
3. **resolution_distribution.csv** — resolution buckets sorted by count.

All files are written atomically via a temp-file-then-rename pattern so
a partial write never leaves a corrupt CSV on disk.

Design
------
* :class:`CsvExporter` is injected with config; no global state.
* Output paths are derived from ``cfg.paths.reports_dir`` by default but
  can be overridden per call.
* Encoding is always UTF-8 with BOM for maximum Excel compatibility.

Example::

    from config.loader import load_config
    from exporters.stats_collector import StatsCollector
    from exporters.csv_exporter import CsvExporter

    cfg = load_config()
    stats = StatsCollector(cfg).collect()
    exporter = CsvExporter(cfg)
    paths = exporter.export(stats)
    print(paths)
"""

from __future__ import annotations

import csv
import os
import tempfile
from pathlib import Path

from loguru import logger
from pydantic import BaseModel, ConfigDict

from config.models import AppConfig
from exporters.stats_collector import DatasetStats


# ---------------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------------


class CsvExportPaths(BaseModel):
    """Paths of all CSV files written by :class:`CsvExporter`.

    Attributes:
        summary_csv: Path to the dataset-level summary CSV.
        per_identity_csv: Path to the per-identity breakdown CSV.
        resolution_csv: Path to the resolution distribution CSV.
    """

    model_config = ConfigDict(frozen=True)

    summary_csv: Path
    per_identity_csv: Path
    resolution_csv: Path


# ---------------------------------------------------------------------------
# Exporter
# ---------------------------------------------------------------------------


class CsvExporter:
    """Writes dataset statistics to CSV reports.

    Args:
        cfg: Validated :class:`~config.models.AppConfig`.
    """

    def __init__(self, cfg: AppConfig) -> None:
        self._cfg = cfg
        self._reports_dir = Path(cfg.paths.reports_dir)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def export(
        self,
        stats: DatasetStats,
        output_dir: Path | None = None,
    ) -> CsvExportPaths:
        """Write all three CSV reports for *stats*.

        Args:
            stats: Fully collected :class:`~exporters.stats_collector.DatasetStats`.
            output_dir: Override output directory.  Defaults to
                ``cfg.paths.reports_dir``.

        Returns:
            :class:`CsvExportPaths` with the written file paths.
        """
        dest = output_dir or self._reports_dir
        dest.mkdir(parents=True, exist_ok=True)

        summary_path = self._write_summary(stats, dest)
        identity_path = self._write_per_identity(stats, dest)
        resolution_path = self._write_resolution(stats, dest)

        logger.success(
            "CSV reports written:\n  {s}\n  {i}\n  {r}",
            s=summary_path,
            i=identity_path,
            r=resolution_path,
        )

        return CsvExportPaths(
            summary_csv=summary_path,
            per_identity_csv=identity_path,
            resolution_csv=resolution_path,
        )

    # ------------------------------------------------------------------
    # Private: individual report writers
    # ------------------------------------------------------------------

    def _write_summary(self, stats: DatasetStats, dest: Path) -> Path:
        """Write dataset-level summary as a single-row CSV.

        Args:
            stats: :class:`~exporters.stats_collector.DatasetStats`.
            dest: Output directory.

        Returns:
            Path of the written file.
        """
        out_path = dest / "summary.csv"
        flat = stats.to_flat_dict()
        rows = [flat]
        _atomic_write_csv(
            path=out_path,
            fieldnames=list(flat.keys()),
            rows=rows,
        )
        logger.debug("Summary CSV: {path}", path=out_path)
        return out_path

    def _write_per_identity(self, stats: DatasetStats, dest: Path) -> Path:
        """Write per-identity image counts as a multi-row CSV.

        Args:
            stats: Dataset stats.
            dest: Output directory.

        Returns:
            Path of the written file.
        """
        out_path = dest / "per_identity.csv"
        fieldnames = [
            "identity_id",
            "split",
            "total_images",
            "original_images",
            "augmented_images",
        ]
        rows = [
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
        ]
        _atomic_write_csv(path=out_path, fieldnames=fieldnames, rows=rows)
        logger.debug("Per-identity CSV: {path} ({n} rows)", path=out_path, n=len(rows))
        return out_path

    def _write_resolution(self, stats: DatasetStats, dest: Path) -> Path:
        """Write resolution distribution as a multi-row CSV.

        Args:
            stats: Dataset stats.
            dest: Output directory.

        Returns:
            Path of the written file.
        """
        out_path = dest / "resolution_distribution.csv"
        fieldnames = ["resolution", "count", "percentage"]
        total = sum(b.count for b in stats.resolution_distribution) or 1
        rows = [
            {
                "resolution": b.resolution,
                "count": b.count,
                "percentage": round(b.count / total * 100, 2),
            }
            for b in stats.resolution_distribution
        ]
        _atomic_write_csv(path=out_path, fieldnames=fieldnames, rows=rows)
        logger.debug("Resolution CSV: {path}", path=out_path)
        return out_path


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _atomic_write_csv(
    path: Path,
    fieldnames: list[str],
    rows: list[dict],
    encoding: str = "utf-8-sig",
) -> None:
    """Write *rows* to *path* atomically (temp file → rename).

    UTF-8 with BOM (``utf-8-sig``) so Excel opens the file correctly
    without a manual encoding step.

    Args:
        path: Destination CSV file path.
        fieldnames: Ordered list of column names.
        rows: List of dicts mapping fieldname → value.
        encoding: File encoding (default ``utf-8-sig`` for Excel compat).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp.csv")
    try:
        with os.fdopen(fd, "w", encoding=encoding, newline="") as fh:
            writer = csv.DictWriter(
                fh,
                fieldnames=fieldnames,
                extrasaction="ignore",
                lineterminator="\r\n",
            )
            writer.writeheader()
            writer.writerows(rows)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
