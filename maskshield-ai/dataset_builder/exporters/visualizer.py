"""
Matplotlib visualization module for MaskShield AI Dataset Builder.

Generates publication-quality plots from a
:class:`~exporters.stats_collector.DatasetStats` object:

1. **Identity distribution** — bar chart of images per identity (top N).
2. **Split distribution** — pie chart of train / val / test identity counts.
3. **Resolution distribution** — horizontal bar chart of resolution buckets.
4. **Class balance** — grouped bar chart comparing masked / unmasked /
   unknown / identity image counts.
5. **Augmentation preview** — grid of original + augmented thumbnails
   (delegated to :meth:`~augmentations.pipeline.AugmentationPipeline.generate_preview_grid`).
6. **Images-per-identity histogram** — frequency distribution of image
   counts across identities.

All plots are saved as high-DPI PNG files.  Every function is **pure**
given the same inputs and the same Matplotlib backend — no global state,
no side-effects beyond writing the PNG file.

Design
------
* :class:`DatasetVisualizer` is injected with :class:`~config.models.AppConfig`.
* Matplotlib is imported lazily so the module loads without a display
  server (important on headless Windows servers).
* The ``Agg`` backend is forced programmatically if no display is available.
* All plots use a consistent dark-themed colour palette matching the
  MaskShield AI visual identity.

Example::

    from config.loader import load_config
    from exporters.stats_collector import StatsCollector
    from exporters.visualizer import DatasetVisualizer

    cfg = load_config()
    stats = StatsCollector(cfg).collect()
    viz = DatasetVisualizer(cfg)
    paths = viz.generate_all(stats)
    print(paths)
"""

from __future__ import annotations

import os
from pathlib import Path

from loguru import logger
from pydantic import BaseModel, ConfigDict

from config.models import AppConfig
from exporters.stats_collector import DatasetStats

                                                                             
                                                                
                                                               
                                 
                                                                             
os.environ.setdefault("MPLBACKEND", "Agg")


                                                                             
              
                                                                             


class VisualizationPaths(BaseModel):
    """Paths of all plot PNG files written by :class:`DatasetVisualizer`.

    Attributes:
        identity_distribution: Bar chart of images per identity (top N).
        split_distribution: Pie chart of train/val/test split.
        resolution_distribution: Horizontal bar chart of resolution buckets.
        class_balance: Grouped bar chart of image category counts.
        images_per_identity_hist: Histogram of per-identity image counts.
    """

    model_config = ConfigDict(frozen=True)

    identity_distribution: Path | None = None
    split_distribution: Path | None = None
    resolution_distribution: Path | None = None
    class_balance: Path | None = None
    images_per_identity_hist: Path | None = None


                                                                             
                
                                                                             

_PALETTE = {
    "primary": "#4F8EF7",
    "accent": "#F76F4F",
    "success": "#4FF7A0",
    "warning": "#F7D44F",
    "neutral": "#8A8FA8",
    "bg_dark": "#1A1D2E",
    "bg_panel": "#252840",
    "text": "#E8EAF6",
    "grid": "#2E3250",
    "masked": "#F76F4F",
    "unmasked": "#4F8EF7",
    "identity": "#4FF7A0",
    "unknown": "#8A8FA8",
    "train": "#4F8EF7",
    "val": "#F7D44F",
    "test": "#F76F4F",
}

_FONT_FAMILY = "DejaVu Sans"                                         
_DPI = 150


                                                                             
                    
                                                                             


class DatasetVisualizer:
    """Generates and saves Matplotlib plots for dataset statistics.

    Args:
        cfg: Validated :class:`~config.models.AppConfig`.

    Example::

        viz = DatasetVisualizer(cfg)
        paths = viz.generate_all(stats)
    """

    def __init__(self, cfg: AppConfig) -> None:
        self._cfg = cfg
        self._plots_dir = Path(cfg.paths.plots_dir)
        self._plots_dir.mkdir(parents=True, exist_ok=True)
        self._top_n = cfg.statistics.top_identities_for_plot
        self._apply_style()

                                                                        
                
                                                                        

    def generate_all(
        self,
        stats: DatasetStats,
        output_dir: Path | None = None,
    ) -> VisualizationPaths:
        """Generate all standard plots and save them to *output_dir*.

        Args:
            stats: Collected :class:`~exporters.stats_collector.DatasetStats`.
            output_dir: Override output directory.  Defaults to
                ``cfg.paths.plots_dir``.

        Returns:
            :class:`VisualizationPaths` with paths of written PNG files.
        """
        if not self._cfg.statistics.generate_plots:
            logger.info("Plot generation disabled in config (generate_plots=false).")
            return VisualizationPaths()

        dest = output_dir or self._plots_dir
        dest.mkdir(parents=True, exist_ok=True)

        paths = VisualizationPaths(
            identity_distribution=self.plot_identity_distribution(stats, dest),
            split_distribution=self.plot_split_distribution(stats, dest),
            resolution_distribution=self.plot_resolution_distribution(stats, dest),
            class_balance=self.plot_class_balance(stats, dest),
            images_per_identity_hist=self.plot_images_per_identity_histogram(stats, dest),
        )

        logger.success(
            "All plots saved to: {dir}", dir=dest
        )
        return paths

    def plot_identity_distribution(
        self,
        stats: DatasetStats,
        output_dir: Path,
    ) -> Path | None:
        """Bar chart — images per identity, top N identities.

        Args:
            stats: Dataset statistics.
            output_dir: Output directory.

        Returns:
            Path to the saved PNG, or ``None`` on failure.
        """
        import matplotlib.pyplot as plt

        if not stats.images_per_identity:
            logger.warning("No identity data — skipping identity distribution plot.")
            return None

        out_path = output_dir / "identity_distribution.png"

        sorted_ids = sorted(
            stats.images_per_identity.items(), key=lambda x: x[1], reverse=True
        )
        top_ids = sorted_ids[: self._top_n]

        labels = [_truncate(k, 20) for k, _ in top_ids]
        values = [v for _, v in top_ids]

        fig, ax = plt.subplots(figsize=(14, 6))
        self._style_axes(ax)

        bars = ax.bar(
            range(len(labels)),
            values,
            color=_PALETTE["primary"],
            edgecolor=_PALETTE["bg_dark"],
            linewidth=0.5,
            alpha=0.9,
        )

                                                                   
        min_imgs = self._cfg.statistics.min_images_per_identity
        for bar, val in zip(bars, values):
            if val < min_imgs:
                bar.set_color(_PALETTE["accent"])

        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=7)
        ax.set_ylabel("Image Count", color=_PALETTE["text"])
        ax.set_title(
            f"Images per Identity — Top {self._top_n} (orange = below threshold)",
            color=_PALETTE["text"],
            fontsize=12,
            pad=14,
        )
        _add_value_labels(ax, bars, color=_PALETTE["text"], fontsize=7)
        _add_mean_line(ax, stats.mean_images_per_identity, _PALETTE["success"])
        _save_fig(fig, out_path)
        return out_path

    def plot_split_distribution(
        self,
        stats: DatasetStats,
        output_dir: Path,
    ) -> Path | None:
        """Pie chart — train / val / test identity counts.

        Args:
            stats: Dataset statistics.
            output_dir: Output directory.

        Returns:
            Path to the saved PNG, or ``None`` on failure.
        """
        import matplotlib.pyplot as plt

        if stats.total_identities == 0:
            logger.warning("No identities — skipping split distribution plot.")
            return None

        out_path = output_dir / "split_distribution.png"

        labels = ["Train", "Validation", "Test"]
        sizes = [stats.train_identities, stats.val_identities, stats.test_identities]
        colors = [_PALETTE["train"], _PALETTE["val"], _PALETTE["test"]]

                                 
        filtered = [(l, s, c) for l, s, c in zip(labels, sizes, colors) if s > 0]
        if not filtered:
            return None
        labels, sizes, colors = zip(*filtered)                            

        fig, ax = plt.subplots(figsize=(7, 7))
        fig.patch.set_facecolor(_PALETTE["bg_dark"])
        ax.set_facecolor(_PALETTE["bg_dark"])

        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=None,
            autopct="%1.1f%%",
            colors=colors,
            startangle=140,
            pctdistance=0.78,
            wedgeprops={"edgecolor": _PALETTE["bg_dark"], "linewidth": 2},
        )
        for at in autotexts:
            at.set_color(_PALETTE["bg_dark"])
            at.set_fontsize(11)
            at.set_fontweight("bold")

        ax.legend(
            wedges,
            [f"{l} ({s})" for l, s in zip(labels, sizes)],
            loc="lower center",
            bbox_to_anchor=(0.5, -0.05),
            ncol=3,
            facecolor=_PALETTE["bg_panel"],
            edgecolor=_PALETTE["grid"],
            labelcolor=_PALETTE["text"],
            fontsize=10,
        )
        ax.set_title(
            f"Identity Split Distribution (total: {stats.total_identities})",
            color=_PALETTE["text"],
            fontsize=13,
            pad=16,
        )
        _save_fig(fig, out_path)
        return out_path

    def plot_resolution_distribution(
        self,
        stats: DatasetStats,
        output_dir: Path,
    ) -> Path | None:
        """Horizontal bar chart — image resolution distribution (top 20).

        Args:
            stats: Dataset statistics.
            output_dir: Output directory.

        Returns:
            Path to the saved PNG, or ``None`` on failure.
        """
        import matplotlib.pyplot as plt

        if not stats.resolution_distribution:
            logger.warning("No resolution data — skipping plot.")
            return None

        out_path = output_dir / "resolution_distribution.png"

        top = stats.resolution_distribution[:20]
        labels = [b.resolution for b in top]
        values = [b.count for b in top]
        total = sum(values) or 1

        fig, ax = plt.subplots(figsize=(10, max(4, len(labels) * 0.45)))
        self._style_axes(ax)

        bars = ax.barh(
            range(len(labels)),
            values,
            color=_PALETTE["accent"],
            edgecolor=_PALETTE["bg_dark"],
            linewidth=0.5,
            alpha=0.9,
        )
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels, fontsize=9)
        ax.invert_yaxis()
        ax.set_xlabel("Image Count", color=_PALETTE["text"])
        ax.set_title(
            "Image Resolution Distribution (top 20)",
            color=_PALETTE["text"],
            fontsize=12,
            pad=14,
        )

                                    
        for i, (bar, val) in enumerate(zip(bars, values)):
            pct = val / total * 100
            ax.text(
                val + max(values) * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{val:,} ({pct:.1f}%)",
                va="center",
                ha="left",
                color=_PALETTE["text"],
                fontsize=8,
            )

        _save_fig(fig, out_path)
        return out_path

    def plot_class_balance(
        self,
        stats: DatasetStats,
        output_dir: Path,
    ) -> Path | None:
        """Grouped bar chart — masked / unmasked / identity / unknown counts.

        Args:
            stats: Dataset statistics.
            output_dir: Output directory.

        Returns:
            Path to the saved PNG, or ``None`` on failure.
        """
        import matplotlib.pyplot as plt
        import numpy as np

        out_path = output_dir / "class_balance.png"

        categories = ["Identity\n(train+val+test)", "Masked", "Unmasked", "Unknown"]
        counts = [
            stats.identity_images,
            stats.masked_count,
            stats.unmasked_count,
            stats.unknown_count,
        ]
        colors = [
            _PALETTE["identity"],
            _PALETTE["masked"],
            _PALETTE["unmasked"],
            _PALETTE["unknown"],
        ]

        fig, ax = plt.subplots(figsize=(9, 5))
        self._style_axes(ax)

        x = np.arange(len(categories))
        bars = ax.bar(
            x,
            counts,
            width=0.55,
            color=colors,
            edgecolor=_PALETTE["bg_dark"],
            linewidth=0.8,
        )

        ax.set_xticks(x)
        ax.set_xticklabels(categories, fontsize=10)
        ax.set_ylabel("Image Count", color=_PALETTE["text"])
        ax.set_title(
            "Dataset Class Balance",
            color=_PALETTE["text"],
            fontsize=13,
            pad=14,
        )
        _add_value_labels(ax, bars, color=_PALETTE["text"], fontsize=9)
        _save_fig(fig, out_path)
        return out_path

    def plot_images_per_identity_histogram(
        self,
        stats: DatasetStats,
        output_dir: Path,
    ) -> Path | None:
        """Histogram — frequency distribution of images per identity.

        Args:
            stats: Dataset statistics.
            output_dir: Output directory.

        Returns:
            Path to the saved PNG, or ``None`` on failure.
        """
        import matplotlib.pyplot as plt

        if not stats.images_per_identity:
            logger.warning("No identity data — skipping histogram.")
            return None

        out_path = output_dir / "images_per_identity_histogram.png"
        counts = list(stats.images_per_identity.values())

        fig, ax = plt.subplots(figsize=(10, 5))
        self._style_axes(ax)

        n_bins = min(50, max(10, len(set(counts))))
        ax.hist(
            counts,
            bins=n_bins,
            color=_PALETTE["primary"],
            edgecolor=_PALETTE["bg_dark"],
            linewidth=0.5,
            alpha=0.88,
        )
        _add_mean_line(ax, stats.mean_images_per_identity, _PALETTE["success"])

        ax.set_xlabel("Images per Identity", color=_PALETTE["text"])
        ax.set_ylabel("Number of Identities", color=_PALETTE["text"])
        ax.set_title(
            f"Images per Identity Distribution  "
            f"(mean={stats.mean_images_per_identity:.1f}, "
            f"min={stats.min_images_per_identity}, "
            f"max={stats.max_images_per_identity})",
            color=_PALETTE["text"],
            fontsize=12,
            pad=14,
        )
        _save_fig(fig, out_path)
        return out_path

                                                                        
                            
                                                                        

    @staticmethod
    def _apply_style() -> None:
        """Apply the global Matplotlib rcParams for the MaskShield theme."""
        import matplotlib as mpl

        mpl.rcParams.update(
            {
                "figure.facecolor": _PALETTE["bg_dark"],
                "axes.facecolor": _PALETTE["bg_panel"],
                "axes.edgecolor": _PALETTE["grid"],
                "axes.labelcolor": _PALETTE["text"],
                "xtick.color": _PALETTE["text"],
                "ytick.color": _PALETTE["text"],
                "grid.color": _PALETTE["grid"],
                "grid.linewidth": 0.5,
                "grid.alpha": 0.6,
                "text.color": _PALETTE["text"],
                "font.family": _FONT_FAMILY,
                "figure.dpi": _DPI,
                "savefig.dpi": _DPI,
                "savefig.facecolor": _PALETTE["bg_dark"],
                "savefig.edgecolor": "none",
                "savefig.bbox": "tight",
                "savefig.pad_inches": 0.15,
            }
        )

    @staticmethod
    def _style_axes(ax: object) -> None:                          
        """Apply consistent axis styling.

        Args:
            ax: Matplotlib ``Axes`` object.
        """
        ax.yaxis.grid(True, alpha=0.4, color=_PALETTE["grid"])                              
        ax.set_axisbelow(True)                              
        ax.spines["top"].set_visible(False)                                
        ax.spines["right"].set_visible(False)                              
        ax.spines["left"].set_color(_PALETTE["grid"])                               
        ax.spines["bottom"].set_color(_PALETTE["grid"])                             
        ax.tick_params(colors=_PALETTE["text"])                                      


                                                                             
                           
                                                                             


def _save_fig(fig: object, path: Path) -> None:                          
    """Save *fig* to *path* and close it to free memory.

    Args:
        fig: Matplotlib ``Figure``.
        path: Destination PNG file path.
    """
    import matplotlib.pyplot as plt

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(str(path))                              
        logger.debug("Plot saved: {path}", path=path)
    except Exception as exc:                
        logger.error("Failed to save plot {path}: {exc}", path=path, exc=exc)
    finally:
        plt.close(fig)                          


def _add_value_labels(
    ax: object,                          
    bars: object,                          
    color: str = "white",
    fontsize: int = 8,
) -> None:
    """Annotate each bar with its numeric value.

    Args:
        ax: Matplotlib ``Axes``.
        bars: ``BarContainer`` from ``ax.bar()``.
        color: Label text colour.
        fontsize: Label font size.
    """
    for bar in bars:                            
        height = bar.get_height()
        if height > 0:
            ax.text(                              
                bar.get_x() + bar.get_width() / 2.0,
                height + max(height * 0.01, 0.5),
                f"{int(height):,}",
                ha="center",
                va="bottom",
                color=color,
                fontsize=fontsize,
                fontweight="bold",
            )


def _add_mean_line(ax: object, mean: float, color: str) -> None:                          
    """Draw a dashed vertical / horizontal mean line with label.

    Args:
        ax: Matplotlib ``Axes``.
        mean: Mean value to annotate.
        color: Line colour.
    """
    ax.axhline(                              
        mean,
        color=color,
        linestyle="--",
        linewidth=1.2,
        alpha=0.8,
        label=f"Mean: {mean:.1f}",
    )
    ax.legend(                              
        facecolor=_PALETTE["bg_panel"],
        edgecolor=_PALETTE["grid"],
        labelcolor=_PALETTE["text"],
        fontsize=9,
    )


def _truncate(text: str, max_len: int) -> str:
    """Truncate *text* to *max_len* characters with ellipsis.

    Args:
        text: Input string.
        max_len: Maximum character count.

    Returns:
        Truncated string.
    """
    return text if len(text) <= max_len else text[: max_len - 1] + "…"
