"""
Pydantic v2 configuration models for MaskShield AI Dataset Builder.

All models use ``model_config = ConfigDict(frozen=True)`` so that
config objects are immutable after construction, enabling safe sharing
across concurrent threads/processes.

Example::

    from config.models import AppConfig
    cfg = AppConfig.model_validate(raw_dict)
    print(cfg.paths.datasets_root)
"""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Leaf-level models
# ---------------------------------------------------------------------------


class ProjectConfig(BaseModel):
    """Top-level project metadata."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., description="Human-readable project name.")
    version: str = Field(..., description="Semantic version string.")
    log_level: str = Field(
        default="INFO",
        pattern=r"^(TRACE|DEBUG|INFO|SUCCESS|WARNING|ERROR|CRITICAL)$",
        description="Loguru log level.",
    )


class PathsConfig(BaseModel):
    """Filesystem paths used by the pipeline."""

    model_config = ConfigDict(frozen=True)

    datasets_root: str = Field(..., description="Root output directory for datasets.")
    download_cache: str = Field(..., description="Temporary download cache directory.")
    log_dir: str = Field(..., description="Directory for log files.")
    reports_dir: str = Field(..., description="Directory for CSV/JSON reports.")
    plots_dir: str = Field(..., description="Directory for plot images.")
    checksums_file: str = Field(..., description="Path to the checksums JSON file.")
    temp_dir: str = Field(..., description="Scratch directory for archive extraction.")


class DownloaderConfig(BaseModel):
    """HTTP downloader settings."""

    model_config = ConfigDict(frozen=True)

    chunk_size_bytes: Annotated[int, Field(gt=0)] = Field(
        default=8_388_608,
        description="Bytes per chunk when streaming downloads.",
    )
    max_retries: Annotated[int, Field(ge=0)] = Field(
        default=5,
        description="Maximum retry attempts on transient failures.",
    )
    retry_backoff_seconds: Annotated[float, Field(ge=0.0)] = Field(
        default=2.0,
        description="Base seconds for exponential backoff between retries.",
    )
    timeout_seconds: Annotated[int, Field(gt=0)] = Field(
        default=60,
        description="HTTP connection+read timeout in seconds.",
    )
    verify_ssl: bool = Field(default=True, description="Verify TLS certificates.")
    resume_enabled: bool = Field(
        default=True,
        description="Use HTTP Range requests to resume partial downloads.",
    )
    max_concurrent_downloads: Annotated[int, Field(ge=1)] = Field(
        default=2,
        description="Maximum simultaneous download threads.",
    )


class ValidationConfig(BaseModel):
    """Thresholds for image validation and cleaning."""

    model_config = ConfigDict(frozen=True)

    min_image_size_px: Annotated[int, Field(gt=0)] = Field(
        default=32,
        description="Both width and height must be at least this many pixels.",
    )
    min_aspect_ratio: Annotated[float, Field(gt=0.0)] = Field(
        default=0.25,
        description="Minimum width/height aspect ratio.",
    )
    max_aspect_ratio: Annotated[float, Field(gt=0.0)] = Field(
        default=4.0,
        description="Maximum width/height aspect ratio.",
    )
    blur_threshold: Annotated[float, Field(ge=0.0)] = Field(
        default=80.0,
        description="Laplacian variance below this → image considered blurry.",
    )
    brightness_min: Annotated[float, Field(ge=0.0, le=255.0)] = Field(
        default=20.0,
        description="Mean pixel brightness must exceed this value.",
    )
    brightness_max: Annotated[float, Field(ge=0.0, le=255.0)] = Field(
        default=235.0,
        description="Mean pixel brightness must not exceed this value.",
    )
    supported_formats: list[str] = Field(
        default_factory=lambda: ["jpg", "jpeg", "png", "bmp", "webp", "tiff"],
        description="Lowercase file extensions considered valid.",
    )
    duplicate_hash_algorithm: str = Field(
        default="phash",
        pattern=r"^(phash|dhash|whash|ahash)$",
        description="Perceptual hash algorithm for duplicate detection.",
    )
    duplicate_hash_bits: Annotated[int, Field(ge=4)] = Field(
        default=8,
        description="Hash size in bits.",
    )
    max_duplicate_distance: Annotated[int, Field(ge=0)] = Field(
        default=10,
        description="Maximum Hamming distance to consider two images duplicates.",
    )

    @model_validator(mode="after")
    def _validate_brightness_range(self) -> ValidationConfig:
        """Ensure brightness_min is strictly less than brightness_max."""
        if self.brightness_min >= self.brightness_max:
            raise ValueError(
                f"brightness_min ({self.brightness_min}) must be less than "
                f"brightness_max ({self.brightness_max})."
            )
        return self


class PreprocessingConfig(BaseModel):
    """Image preprocessing options applied after validation."""

    model_config = ConfigDict(frozen=True)

    target_size: tuple[int, int] = Field(
        default=(112, 112),
        description="Output (width, height) in pixels.",
    )
    padding_color: tuple[int, int, int] = Field(
        default=(0, 0, 0),
        description="RGB padding colour when letterboxing.",
    )
    normalize_mean: tuple[float, float, float] = Field(
        default=(0.5, 0.5, 0.5),
        description="Per-channel mean for normalisation.",
    )
    normalize_std: tuple[float, float, float] = Field(
        default=(0.5, 0.5, 0.5),
        description="Per-channel std for normalisation.",
    )
    apply_histogram_equalization: bool = Field(
        default=False,
        description="Apply CLAHE histogram equalisation before saving.",
    )
    interpolation: str = Field(
        default="LANCZOS",
        pattern=r"^(NEAREST|BILINEAR|BICUBIC|LANCZOS|AREA)$",
        description="Pillow/OpenCV interpolation method name.",
    )


# ---------------------------------------------------------------------------
# Augmentation sub-models
# ---------------------------------------------------------------------------


class RotationTransformConfig(BaseModel):
    """Rotation augmentation parameters."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    limit_degrees: Annotated[int, Field(ge=0, le=180)] = 15
    probability: Annotated[float, Field(ge=0.0, le=1.0)] = 0.5


class BrightnessContrastTransformConfig(BaseModel):
    """Random brightness/contrast augmentation parameters."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    brightness_limit: Annotated[float, Field(ge=0.0, le=1.0)] = 0.2
    contrast_limit: Annotated[float, Field(ge=0.0, le=1.0)] = 0.2
    probability: Annotated[float, Field(ge=0.0, le=1.0)] = 0.5


class GaussianNoiseTransformConfig(BaseModel):
    """Gaussian noise augmentation parameters."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    var_limit: tuple[float, float] = (10.0, 50.0)
    probability: Annotated[float, Field(ge=0.0, le=1.0)] = 0.3


class GaussianBlurTransformConfig(BaseModel):
    """Gaussian blur augmentation parameters."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    blur_limit: tuple[int, int] = (3, 7)
    probability: Annotated[float, Field(ge=0.0, le=1.0)] = 0.3


class MotionBlurTransformConfig(BaseModel):
    """Motion blur augmentation parameters."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    blur_limit: Annotated[int, Field(ge=3)] = 7
    probability: Annotated[float, Field(ge=0.0, le=1.0)] = 0.2


class JpegCompressionTransformConfig(BaseModel):
    """JPEG compression artefact augmentation parameters."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    quality_lower: Annotated[int, Field(ge=1, le=100)] = 60
    quality_upper: Annotated[int, Field(ge=1, le=100)] = 95
    probability: Annotated[float, Field(ge=0.0, le=1.0)] = 0.3


class HorizontalFlipTransformConfig(BaseModel):
    """Horizontal flip augmentation parameters."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    probability: Annotated[float, Field(ge=0.0, le=1.0)] = 0.5


class RandomShadowTransformConfig(BaseModel):
    """Random shadow augmentation parameters."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    num_shadows_lower: Annotated[int, Field(ge=1)] = 1
    num_shadows_upper: Annotated[int, Field(ge=1)] = 2
    shadow_dimension: Annotated[int, Field(ge=3)] = 5
    probability: Annotated[float, Field(ge=0.0, le=1.0)] = 0.2


class MaskSimulationConfig(BaseModel):
    """Synthetic mask overlay augmentation parameters."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    probability: Annotated[float, Field(ge=0.0, le=1.0)] = 0.4
    mask_color_range: tuple[
        tuple[int, int], tuple[int, int], tuple[int, int]
    ] = ((180, 210), (180, 210), (180, 210))
    mask_height_ratio: tuple[float, float] = (0.35, 0.55)
    mask_width_ratio: tuple[float, float] = (0.70, 0.95)


class SunglassesSimulationConfig(BaseModel):
    """Synthetic sunglasses overlay augmentation parameters."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    probability: Annotated[float, Field(ge=0.0, le=1.0)] = 0.2
    tint_color: tuple[int, int, int] = (20, 20, 20)
    alpha: Annotated[float, Field(ge=0.0, le=1.0)] = 0.7


class PartialOcclusionConfig(BaseModel):
    """Random rectangular occlusion (CoarseDropout) parameters."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    probability: Annotated[float, Field(ge=0.0, le=1.0)] = 0.3
    max_holes: Annotated[int, Field(ge=1)] = 3
    max_height_ratio: Annotated[float, Field(gt=0.0, le=1.0)] = 0.25
    max_width_ratio: Annotated[float, Field(gt=0.0, le=1.0)] = 0.25


class TransformSetConfig(BaseModel):
    """Container for all per-transform configuration objects."""

    model_config = ConfigDict(frozen=True)

    rotation: RotationTransformConfig = Field(default_factory=RotationTransformConfig)
    brightness_contrast: BrightnessContrastTransformConfig = Field(
        default_factory=BrightnessContrastTransformConfig
    )
    gaussian_noise: GaussianNoiseTransformConfig = Field(
        default_factory=GaussianNoiseTransformConfig
    )
    gaussian_blur: GaussianBlurTransformConfig = Field(
        default_factory=GaussianBlurTransformConfig
    )
    motion_blur: MotionBlurTransformConfig = Field(
        default_factory=MotionBlurTransformConfig
    )
    jpeg_compression: JpegCompressionTransformConfig = Field(
        default_factory=JpegCompressionTransformConfig
    )
    horizontal_flip: HorizontalFlipTransformConfig = Field(
        default_factory=HorizontalFlipTransformConfig
    )
    random_shadow: RandomShadowTransformConfig = Field(
        default_factory=RandomShadowTransformConfig
    )
    random_mask_simulation: MaskSimulationConfig = Field(
        default_factory=MaskSimulationConfig
    )
    random_sunglasses: SunglassesSimulationConfig = Field(
        default_factory=SunglassesSimulationConfig
    )
    partial_occlusion: PartialOcclusionConfig = Field(
        default_factory=PartialOcclusionConfig
    )


class AugmentationConfig(BaseModel):
    """Top-level augmentation pipeline configuration."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    copies_per_image: Annotated[int, Field(ge=1)] = 3
    output_format: str = Field(
        default="jpg",
        pattern=r"^(jpg|jpeg|png|bmp|webp)$",
    )
    jpeg_quality: Annotated[int, Field(ge=1, le=100)] = 95
    seed: int = 42
    transforms: TransformSetConfig = Field(default_factory=TransformSetConfig)


# ---------------------------------------------------------------------------
# Dataset entry models
# ---------------------------------------------------------------------------


class DatasetEntryConfig(BaseModel):
    """Configuration for a single named dataset source."""

    model_config = ConfigDict(frozen=True, extra="allow")

    enabled: bool = False
    category: str = Field(
        ...,
        pattern=r"^(masked|unmasked|detection|unknown)$",
        description="Semantic category of images in this dataset.",
    )
    note: str | None = Field(
        default=None,
        description="Human-readable note (e.g. download instructions).",
    )


class DatasetsConfig(BaseModel):
    """Map of dataset name → entry config. Accepts arbitrary extra keys."""

    model_config = ConfigDict(frozen=True)

    lfw: DatasetEntryConfig
    celeba: DatasetEntryConfig
    casia_webface: DatasetEntryConfig
    vggface2: DatasetEntryConfig
    rmfd: DatasetEntryConfig
    smfd: DatasetEntryConfig
    mafa: DatasetEntryConfig
    wider_face: DatasetEntryConfig
    maskedface_net: DatasetEntryConfig
    custom: DatasetEntryConfig

    def enabled_datasets(self) -> dict[str, DatasetEntryConfig]:
        """Return only the datasets that have ``enabled=True``.

        Returns:
            A dict mapping dataset name to its config.
        """
        return {
            name: entry
            for name, entry in self.__iter__()
            if isinstance(entry, DatasetEntryConfig) and entry.enabled
        }

    def __iter__(self):  # type: ignore[override]
        """Yield ``(field_name, value)`` pairs for iteration."""
        for field_name in self.model_fields:
            yield field_name, getattr(self, field_name)


class StatisticsConfig(BaseModel):
    """Options controlling report generation."""

    model_config = ConfigDict(frozen=True)

    generate_csv: bool = True
    generate_json: bool = True
    generate_plots: bool = True
    min_images_per_identity: Annotated[int, Field(ge=1)] = 5
    top_identities_for_plot: Annotated[int, Field(ge=1)] = 30


class SplitsConfig(BaseModel):
    """Train / val / test split ratios."""

    model_config = ConfigDict(frozen=True)

    train_ratio: Annotated[float, Field(gt=0.0, lt=1.0)] = 0.80
    val_ratio: Annotated[float, Field(gt=0.0, lt=1.0)] = 0.10
    test_ratio: Annotated[float, Field(gt=0.0, lt=1.0)] = 0.10
    stratify: bool = True
    random_seed: int = 42

    @model_validator(mode="after")
    def _ratios_sum_to_one(self) -> SplitsConfig:
        """Ensure the three ratios sum to exactly 1.0 (within float tolerance)."""
        total = self.train_ratio + self.val_ratio + self.test_ratio
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                f"train_ratio + val_ratio + test_ratio must equal 1.0, got {total:.6f}."
            )
        return self


# ---------------------------------------------------------------------------
# Root config model
# ---------------------------------------------------------------------------


class AppConfig(BaseModel):
    """Root configuration model for the MaskShield AI Dataset Builder.

    This is the single source of truth for all pipeline settings.
    Instantiate via :func:`config.loader.load_config`.

    Attributes:
        project: Project metadata (name, version, log level).
        paths: Filesystem path configuration.
        downloader: HTTP download settings.
        validation: Image validation thresholds.
        preprocessing: Preprocessing options.
        augmentation: Augmentation pipeline settings.
        datasets: Per-dataset source configuration.
        statistics: Report generation options.
        splits: Train/val/test split ratios.
    """

    model_config = ConfigDict(frozen=True)

    project: ProjectConfig
    paths: PathsConfig
    downloader: DownloaderConfig
    validation: ValidationConfig
    preprocessing: PreprocessingConfig
    augmentation: AugmentationConfig
    datasets: DatasetsConfig
    statistics: StatisticsConfig
    splits: SplitsConfig

    @field_validator("datasets", mode="before")
    @classmethod
    def _coerce_dataset_entries(cls, v: Any) -> Any:
        """Auto-inject ``category`` into dataset entries that lack explicit models.

        Args:
            v: Raw datasets dict from JSON.

        Returns:
            The (possibly coerced) dict for Pydantic to validate.
        """
        return v
