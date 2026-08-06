"""
Dataset source registry for MaskShield AI Dataset Builder.

Defines the static metadata for every supported dataset:
URL(s), expected checksums, archive type, post-extraction structure,
and the category (masked / unmasked / detection).

:class:`DatasetRegistry` is a read-only registry that maps dataset names
to :class:`DatasetSourceSpec` objects.  It is constructed once from the
:class:`~config.models.AppConfig` and injected into :class:`~services.downloader.DatasetDownloader`.

Design
------
* All spec objects are **frozen Pydantic models** — no mutation after construction.
* The registry merges static defaults with user overrides from ``config.json``.
* Datasets that require manual download (CelebA, CASIA-WebFace, VGGFace2,
  MAFA, etc.) are represented with ``downloadable=False`` and a ``manual_note``
  string that the CLI surfaces to the user.

Example::

    from config.loader import load_config
    from services.registry import DatasetRegistry

    cfg = load_config()
    registry = DatasetRegistry.from_config(cfg)
    spec = registry.get("lfw")
    print(spec.primary_url)
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field

from config.models import AppConfig


                                                                             
                      
                                                                             

ArchiveType = Literal["tar.gz", "tar.bz2", "tar.xz", "zip", "rar", "7z", "none"]
DatasetCategory = Literal["masked", "unmasked", "detection", "unknown"]


                                                                             
                              
                                                                             


class DatasetSourceSpec(BaseModel):
    """Complete metadata for a single downloadable dataset source.

    Attributes:
        name: Short identifier matching the key in ``config.json``.
        display_name: Human-readable full name.
        category: Semantic image category for this dataset.
        downloadable: ``True`` if a URL is available for automatic download.
        primary_url: Primary download URL (``None`` for manual-only datasets).
        extra_urls: Additional URLs required (e.g. annotations, splits).
        checksum_sha256: Expected SHA-256 hex digest of the downloaded archive,
            or ``None`` if not available / not checked.
        archive_type: Archive format for extraction.
        manual_note: Instructions for manually obtaining the dataset.
        manual_root_path: User-configured local path (for manual datasets).
        output_subdir: Subdirectory under ``datasets_root`` where the
            extracted files are placed.
        enabled: Whether the user has enabled this dataset in ``config.json``.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    display_name: str
    category: DatasetCategory
    downloadable: bool = True
    primary_url: str | None = None
    extra_urls: list[str] = Field(default_factory=list)
    checksum_sha256: str | None = None
    archive_type: ArchiveType = "zip"
    manual_note: str | None = None
    manual_root_path: Path | None = None
    output_subdir: str = ""
    enabled: bool = False

    @property
    def all_urls(self) -> list[str]:
        """All URLs that need to be downloaded (primary + extras).

        Returns:
            List of URL strings; may be empty for manual datasets.
        """
        urls: list[str] = []
        if self.primary_url:
            urls.append(self.primary_url)
        urls.extend(self.extra_urls)
        return urls


                                                                             
          
                                                                             


class DatasetRegistry:
    """Read-only mapping of dataset name → :class:`DatasetSourceSpec`.

    Use :meth:`from_config` to construct an instance from the application
    configuration.

    Args:
        specs: Mapping from dataset name (lower-case) to spec.
    """

    def __init__(self, specs: dict[str, DatasetSourceSpec]) -> None:
        self._specs: dict[str, DatasetSourceSpec] = dict(specs)

                                                                        
             
                                                                        

    @classmethod
    def from_config(cls, cfg: AppConfig) -> DatasetRegistry:
        """Build a :class:`DatasetRegistry` from the application config.

        Merges hard-coded static defaults with user overrides from
        ``cfg.datasets``.

        Args:
            cfg: Validated :class:`~config.models.AppConfig`.

        Returns:
            A populated :class:`DatasetRegistry` instance.
        """
        raw = cfg.datasets
        specs: dict[str, DatasetSourceSpec] = {}

                                                                          
             
                                                                          
        lfw_raw = raw.lfw.model_extra or {}
        specs["lfw"] = DatasetSourceSpec(
            name="lfw",
            display_name="Labeled Faces in the Wild (LFW)",
            category="unmasked",
            downloadable=True,
            primary_url=lfw_raw.get(
                "url",
                "http://vis-www.cs.umass.edu/lfw/lfw.tgz",
            ),
            checksum_sha256=lfw_raw.get("checksum_sha256"),
            archive_type="tar.gz",
            output_subdir="raw/lfw",
            enabled=raw.lfw.enabled,
        )

                                                                          
                
                                                                          
        celeba_raw = raw.celeba.model_extra or {}
        specs["celeba"] = DatasetSourceSpec(
            name="celeba",
            display_name="CelebA — Large-scale Celebrity Attributes",
            category="unmasked",
            downloadable=False,
            manual_note=(
                "Download manually from https://mmlab.ie.cuhk.edu.hk/projects/CelebA.html\n"
                "Place the extracted folder and set 'manual_archive_path' in config.json."
            ),
            manual_root_path=_optional_path(celeba_raw.get("manual_archive_path")),
            output_subdir="raw/celeba",
            enabled=raw.celeba.enabled,
        )

                                                                          
                       
                                                                          
        casia_raw = raw.casia_webface.model_extra or {}
        specs["casia_webface"] = DatasetSourceSpec(
            name="casia_webface",
            display_name="CASIA-WebFace",
            category="unmasked",
            downloadable=False,
            manual_note=(
                "Requires academic licence.\n"
                "See: https://github.com/happynear/AMSoftmax\n"
                "Set 'manual_root_path' in config.json."
            ),
            manual_root_path=_optional_path(casia_raw.get("manual_root_path")),
            output_subdir="raw/casia_webface",
            enabled=raw.casia_webface.enabled,
        )

                                                                          
                  
                                                                          
        vgg_raw = raw.vggface2.model_extra or {}
        specs["vggface2"] = DatasetSourceSpec(
            name="vggface2",
            display_name="VGGFace2",
            category="unmasked",
            downloadable=False,
            manual_note=(
                "Requires registration at "
                "https://www.robots.ox.ac.uk/~vgg/data/vgg_face2/\n"
                "Set 'manual_root_path' in config.json."
            ),
            manual_root_path=_optional_path(vgg_raw.get("manual_root_path")),
            output_subdir="raw/vggface2",
            enabled=raw.vggface2.enabled,
        )

                                                                          
              
                                                                          
        rmfd_raw = raw.rmfd.model_extra or {}
        specs["rmfd"] = DatasetSourceSpec(
            name="rmfd",
            display_name="Real Masked Face Dataset (RMFD)",
            category="masked",
            downloadable=True,
            primary_url=rmfd_raw.get(
                "url",
                "https://github.com/X-zhangyang/Real-World-Masked-Face-Dataset/"
                "archive/refs/heads/master.zip",
            ),
            checksum_sha256=rmfd_raw.get("checksum_sha256"),
            archive_type="zip",
            output_subdir="raw/rmfd",
            enabled=raw.rmfd.enabled,
        )

                                                                          
              
                                                                          
        smfd_raw = raw.smfd.model_extra or {}
        specs["smfd"] = DatasetSourceSpec(
            name="smfd",
            display_name="Simulated Masked Face Dataset (SMFD)",
            category="masked",
            downloadable=False,
            manual_note="Provide the extracted folder path in config.json → 'manual_root_path'.",
            manual_root_path=_optional_path(smfd_raw.get("manual_root_path")),
            output_subdir="raw/smfd",
            enabled=raw.smfd.enabled,
        )

                                                                          
              
                                                                          
        mafa_raw = raw.mafa.model_extra or {}
        specs["mafa"] = DatasetSourceSpec(
            name="mafa",
            display_name="Mask-Wearing Faces in the Wild (MAFA)",
            category="masked",
            downloadable=False,
            manual_note=(
                "Requires academic request. "
                "See: http://www.escience.cn/people/geshiming/mafa.html\n"
                "Set 'manual_root_path' in config.json."
            ),
            manual_root_path=_optional_path(mafa_raw.get("manual_root_path")),
            output_subdir="raw/mafa",
            enabled=raw.mafa.enabled,
        )

                                                                          
                    
                                                                          
        wider_raw = raw.wider_face.model_extra or {}
        specs["wider_face"] = DatasetSourceSpec(
            name="wider_face",
            display_name="WIDER FACE",
            category="detection",
            downloadable=True,
            primary_url=wider_raw.get(
                "train_url",
                "https://huggingface.co/datasets/wider_face/resolve/main/data/WIDER_train.zip",
            ),
            extra_urls=[
                url
                for url in [
                    wider_raw.get(
                        "val_url",
                        "https://huggingface.co/datasets/wider_face/resolve/main/data/WIDER_val.zip",
                    ),
                    wider_raw.get(
                        "annotation_url",
                        "http://shuoyang1213.me/WIDERFACE/support/bbx_gt/wider_face_split.zip",
                    ),
                ]
                if url
            ],
            checksum_sha256=wider_raw.get("checksum_sha256"),
            archive_type="zip",
            output_subdir="raw/wider_face",
            enabled=raw.wider_face.enabled,
        )

                                                                          
                        
                                                                          
        mfn_raw = raw.maskedface_net.model_extra or {}
        specs["maskedface_net"] = DatasetSourceSpec(
            name="maskedface_net",
            display_name="MaskedFace-Net (CMFD + IMFD)",
            category="masked",
            downloadable=False,
            manual_note=(
                "Download CMFD and IMFD zip files from "
                "https://github.com/cabani/MaskedFace-Net\n"
                "Set 'cmfd_path' and 'imfd_path' in config.json."
            ),
            manual_root_path=_optional_path(mfn_raw.get("cmfd_path")),
            output_subdir="raw/maskedface_net",
            enabled=raw.maskedface_net.enabled,
        )

                                                                          
                
                                                                          
        custom_raw = raw.custom.model_extra or {}
        specs["custom"] = DatasetSourceSpec(
            name="custom",
            display_name="Custom Dataset",
            category=raw.custom.category,                          
            downloadable=False,
            manual_note="Set 'root_path' in config.json to your custom dataset folder.",
            manual_root_path=_optional_path(custom_raw.get("root_path")),
            output_subdir="raw/custom",
            enabled=raw.custom.enabled,
        )

        enabled_names = [name for name, spec in specs.items() if spec.enabled]
        logger.debug(
            "DatasetRegistry initialised: {total} datasets, {enabled} enabled: {names}",
            total=len(specs),
            enabled=len(enabled_names),
            names=enabled_names,
        )
        return cls(specs)

                                                                        
                
                                                                        

    def get(self, name: str) -> DatasetSourceSpec:
        """Return the spec for *name*, raising :class:`KeyError` if not found.

        Args:
            name: Dataset identifier (e.g. ``"lfw"``, ``"rmfd"``).

        Returns:
            The :class:`DatasetSourceSpec` for that dataset.

        Raises:
            KeyError: If *name* is not registered.
        """
        if name not in self._specs:
            raise KeyError(
                f"Unknown dataset '{name}'. "
                f"Available: {sorted(self._specs)}"
            )
        return self._specs[name]

    def all_specs(self) -> dict[str, DatasetSourceSpec]:
        """Return a shallow copy of all registered specs.

        Returns:
            Dict mapping dataset name to spec.
        """
        return dict(self._specs)

    def enabled_specs(self) -> dict[str, DatasetSourceSpec]:
        """Return only specs where ``enabled=True``.

        Returns:
            Filtered dict of enabled dataset specs.
        """
        return {name: spec for name, spec in self._specs.items() if spec.enabled}

    def downloadable_specs(self) -> dict[str, DatasetSourceSpec]:
        """Return only specs that are enabled AND have download URLs.

        Returns:
            Filtered dict of downloadable dataset specs.
        """
        return {
            name: spec
            for name, spec in self._specs.items()
            if spec.enabled and spec.downloadable
        }

    def manual_specs(self) -> dict[str, DatasetSourceSpec]:
        """Return only specs that are enabled but require manual download.

        Returns:
            Filtered dict of manual-download dataset specs.
        """
        return {
            name: spec
            for name, spec in self._specs.items()
            if spec.enabled and not spec.downloadable
        }

    def __contains__(self, name: str) -> bool:
        return name in self._specs

    def __len__(self) -> int:
        return len(self._specs)

    def __repr__(self) -> str:
        enabled = sum(1 for s in self._specs.values() if s.enabled)
        return f"DatasetRegistry(total={len(self._specs)}, enabled={enabled})"


                                                                             
                  
                                                                             


def _optional_path(value: str | None) -> Path | None:
    """Convert a config string to a :class:`Path`, or return ``None``.

    Args:
        value: String path or empty string from config.

    Returns:
        :class:`Path` if *value* is a non-empty string, else ``None``.
    """
    if value and value.strip():
        return Path(value.strip())
    return None
