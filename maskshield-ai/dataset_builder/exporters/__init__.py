"""
Exporters package for MaskShield AI Dataset Builder.

Sub-modules
-----------
* :mod:`exporters.stats_collector` — Walks the canonical dataset and builds
  a :class:`~exporters.stats_collector.DatasetStats` model.
* :mod:`exporters.csv_exporter`    — Writes summary, per-identity, and
  resolution CSV reports.
* :mod:`exporters.json_exporter`   — Writes full JSON report and pipeline
  manifest.
* :mod:`exporters.visualizer`      — Matplotlib distribution plots.

Typical usage::

    from config.loader import load_config
    from exporters import CsvExporter, JsonExporter, StatsCollector

    cfg = load_config()
    stats = StatsCollector(cfg).collect()
    CsvExporter(cfg).export(stats)
    JsonExporter(cfg).export(stats)
"""

from exporters.csv_exporter import CsvExportPaths, CsvExporter
from exporters.json_exporter import JsonExportPaths, JsonExporter
from exporters.stats_collector import (
    DatasetStats,
    IdentityStats,
    ResolutionBucket,
    StatsCollector,
)
from exporters.visualizer import DatasetVisualizer, VisualizationPaths

__all__ = [
    # stats_collector
    "StatsCollector",
    "DatasetStats",
    "IdentityStats",
    "ResolutionBucket",
    # csv_exporter
    "CsvExporter",
    "CsvExportPaths",
    # json_exporter
    "JsonExporter",
    "JsonExportPaths",
    # visualizer
    "DatasetVisualizer",
    "VisualizationPaths",
]
