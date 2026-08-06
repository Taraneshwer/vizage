"""
Dataset organizer service for MaskShield AI Dataset Builder.

:class:`DatasetOrganizer` converts any supported raw dataset (LFW, CelebA,
CASIA-WebFace, VGGFace2, RMFD, SMFD, MAFA, WIDER FACE, MaskedFace-Net,
Custom) into the **canonical folder layout** expected by all downstream
pipeline stages:

.. code-block:: text

    datasets/
    ├── identities/
    │   ├── person_001/
    │   │   ├── img_001.jpg
    │   │   └── img_002.jpg
    │   └── person_002/
    ├── masked/
    ├── unmasked/
    ├── validation/
    ├── test/
    └── unknown/

Architecture
------------
* **Strategy pattern** — each dataset has a dedicated private organiser
  method.  :class:`DatasetOrganizer` dispatches to the correct strategy
  via a ``_STRATEGY_MAP`` dict keyed on dataset name.
* **Copy vs Move** — the ``mode`` parameter controls whether files are
  copied (safe, non-destructive) or moved (fast, low-disk).
* **Train / Val / Test split** — after per-identity copy/move, identities
  are partitioned into ``identities/`` (train), ``validation/``, and
  ``test/`` directories using stratified sampling.
* **Skip-existing** — each destination file is skipped if it already
  exists, making the organiser idempotent.
* **Structured result** — :class:`OrganizeResult` captures counts of
  files organised, skipped, and any errors, per dataset.

Example::

    from config.loader import load_config
    from services.organizer import DatasetOrganizer

    cfg = load_config()
    organizer = DatasetOrganizer(cfg)
    result = organizer.organize("lfw", Path("datasets/raw/lfw"))
    print(result.summary())
"""

from __future__ import annotations

import random
import re
from enum import Enum
from pathlib import Path
from typing import Callable

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field

from config.models import AppConfig
from utils.file_ops import ensure_dir, extension_of, iter_images, safe_copy, safe_move


                                                                             
              
                                                                             


class OrganizeMode(str, Enum):
    """Whether to copy or move files during organisation.

    Attributes:
        COPY: Duplicate files into the canonical structure (non-destructive).
        MOVE: Move files (faster, lower disk usage).
    """

    COPY = "copy"
    MOVE = "move"


                                                                             
              
                                                                             


class OrganizeResult(BaseModel):
    """Outcome of organising a single dataset.

    Attributes:
        dataset_name: Short identifier of the dataset.
        source_root: Raw dataset root that was processed.
        output_root: Canonical output root (``datasets/``).
        files_processed: Files successfully placed in the canonical layout.
        files_skipped: Files skipped because the destination already existed.
        files_errored: Files that could not be processed.
        identities_found: Number of distinct identity folders created.
        masked_count: Images placed in ``masked/``.
        unmasked_count: Images placed in ``unmasked/``.
        unknown_count: Images placed in ``unknown/``.
        error_details: List of ``(path, reason)`` tuples for failed files.
    """

    model_config = ConfigDict(frozen=True)

    dataset_name: str
    source_root: Path
    output_root: Path
    files_processed: int = 0
    files_skipped: int = 0
    files_errored: int = 0
    identities_found: int = 0
    masked_count: int = 0
    unmasked_count: int = 0
    unknown_count: int = 0
    error_details: list[tuple[str, str]] = Field(default_factory=list)

    def summary(self) -> str:
        """Return a human-readable multi-line summary.

        Returns:
            Formatted summary string.
        """
        return (
            f"OrganizeResult — {self.dataset_name}\n"
            f"  Source        : {self.source_root}\n"
            f"  Output        : {self.output_root}\n"
            f"  Processed     : {self.files_processed}\n"
            f"  Skipped       : {self.files_skipped}\n"
            f"  Errored       : {self.files_errored}\n"
            f"  Identities    : {self.identities_found}\n"
            f"  Masked        : {self.masked_count}\n"
            f"  Unmasked      : {self.unmasked_count}\n"
            f"  Unknown       : {self.unknown_count}\n"
        )


                                                                             
                                                     
                                                                             


class _OrganizeAccumulator:
    """Mutable stats accumulator used during a single organize run."""

    def __init__(self, dataset_name: str, source_root: Path, output_root: Path) -> None:
        self.dataset_name = dataset_name
        self.source_root = source_root
        self.output_root = output_root
        self.files_processed: int = 0
        self.files_skipped: int = 0
        self.files_errored: int = 0
        self.identities: set[str] = set()
        self.masked_count: int = 0
        self.unmasked_count: int = 0
        self.unknown_count: int = 0
        self.error_details: list[tuple[str, str]] = []

    def to_result(self) -> OrganizeResult:
        """Convert accumulator state to an immutable :class:`OrganizeResult`."""
        return OrganizeResult(
            dataset_name=self.dataset_name,
            source_root=self.source_root,
            output_root=self.output_root,
            files_processed=self.files_processed,
            files_skipped=self.files_skipped,
            files_errored=self.files_errored,
            identities_found=len(self.identities),
            masked_count=self.masked_count,
            unmasked_count=self.unmasked_count,
            unknown_count=self.unknown_count,
            error_details=self.error_details,
        )


                                                                             
                   
                                                                             


class DatasetOrganizer:
    """Converts raw dataset trees into the canonical MaskShield AI layout.

    Args:
        cfg: Validated :class:`~config.models.AppConfig`.

    Example::

        organizer = DatasetOrganizer(cfg)
        result = organizer.organize("lfw", Path("datasets/raw/lfw"), mode=OrganizeMode.COPY)
    """

                                                        
    _STRATEGY_MAP: dict[str, str] = {
        "lfw": "_organize_lfw",
        "celeba": "_organize_celeba",
        "casia_webface": "_organize_casia",
        "vggface2": "_organize_vggface2",
        "rmfd": "_organize_rmfd",
        "smfd": "_organize_smfd",
        "mafa": "_organize_mafa",
        "wider_face": "_organize_wider",
        "maskedface_net": "_organize_maskedface_net",
        "custom": "_organize_custom",
    }

    def __init__(self, cfg: AppConfig) -> None:
        self._cfg = cfg
        self._datasets_root = Path(cfg.paths.datasets_root)
        self._splits_cfg = cfg.splits

                                                  
        self._identities_dir = self._datasets_root / "identities"
        self._masked_dir = self._datasets_root / "masked"
        self._unmasked_dir = self._datasets_root / "unmasked"
        self._validation_dir = self._datasets_root / "validation"
        self._test_dir = self._datasets_root / "test"
        self._unknown_dir = self._datasets_root / "unknown"

        for d in (
            self._identities_dir,
            self._masked_dir,
            self._unmasked_dir,
            self._validation_dir,
            self._test_dir,
            self._unknown_dir,
        ):
            ensure_dir(d)

                                                                        
                
                                                                        

    def organize(
        self,
        dataset_name: str,
        source_root: Path,
        mode: OrganizeMode = OrganizeMode.COPY,
    ) -> OrganizeResult:
        """Organise a raw dataset into the canonical folder layout.

        Args:
            dataset_name: One of the known dataset identifiers (e.g. ``"lfw"``).
            source_root: Root directory of the extracted raw dataset.
            mode: :class:`OrganizeMode` — ``COPY`` or ``MOVE``.

        Returns:
            :class:`OrganizeResult` describing what was done.

        Raises:
            NotADirectoryError: If *source_root* is not a directory.
            ValueError: If *dataset_name* is not supported.
        """
        if not source_root.is_dir():
            raise NotADirectoryError(f"Source root is not a directory: {source_root}")

        strategy_name = self._STRATEGY_MAP.get(dataset_name)
        if not strategy_name:
            raise ValueError(
                f"No organizer strategy for dataset '{dataset_name}'. "
                f"Supported: {sorted(self._STRATEGY_MAP)}"
            )

        logger.info(
            "Organising [{name}]: {src} → {dst} (mode={mode})",
            name=dataset_name,
            src=source_root,
            dst=self._datasets_root,
            mode=mode.value,
        )

        acc = _OrganizeAccumulator(
            dataset_name=dataset_name,
            source_root=source_root,
            output_root=self._datasets_root,
        )

        strategy: Callable[[Path, OrganizeMode, _OrganizeAccumulator], None] = getattr(
            self, strategy_name
        )
        strategy(source_root, mode, acc)

                                                   
        self._apply_splits(acc)

        result = acc.to_result()
        logger.success(
            "Organisation complete [{name}]: {n} files, {i} identities.",
            name=dataset_name,
            n=result.files_processed,
            i=result.identities_found,
        )
        logger.info("\n{summary}", summary=result.summary())
        return result

    def organize_manual(
        self,
        dataset_name: str,
        source_root: Path,
        mode: OrganizeMode = OrganizeMode.COPY,
    ) -> OrganizeResult:
        """Alias for :meth:`organize`, used when the source came from a
        manual download path configured in ``config.json``.

        Args:
            dataset_name: Dataset identifier.
            source_root: User-provided root path.
            mode: Copy or move.

        Returns:
            :class:`OrganizeResult`.
        """
        return self.organize(dataset_name, source_root, mode)

                                                                        
                                     
                                                                        

    def _organize_lfw(
        self,
        source_root: Path,
        mode: OrganizeMode,
        acc: _OrganizeAccumulator,
    ) -> None:
        """Organise LFW.

        LFW layout: ``lfw/<person_name>/<image_file.jpg>``

        Args:
            source_root: Extracted LFW root (contains the ``lfw/`` subdir).
            mode: Copy or move.
            acc: Mutable accumulator.
        """
                                                                           
        lfw_inner = source_root / "lfw"
        scan_root = lfw_inner if lfw_inner.is_dir() else source_root

        for person_dir in sorted(scan_root.iterdir()):
            if not person_dir.is_dir():
                continue
            person_id = _sanitise_identity(person_dir.name)
            dest_dir = self._identities_dir / person_id
            ensure_dir(dest_dir)
            acc.identities.add(person_id)

            for img_path in iter_images(person_dir, recursive=False):
                new_name = f"{person_id}_{img_path.name}"
                dest_file = dest_dir / new_name
                self._transfer(img_path, dest_file, mode, acc)
                acc.unmasked_count += 1

    def _organize_celeba(
        self,
        source_root: Path,
        mode: OrganizeMode,
        acc: _OrganizeAccumulator,
    ) -> None:
        """Organise CelebA.

        CelebA layout: flat ``img_align_celeba/<image_id>.jpg`` with
        identity labels in ``identity_CelebA.txt``.

        Args:
            source_root: Extracted CelebA root.
            mode: Copy or move.
            acc: Mutable accumulator.
        """
        img_dir = source_root / "img_align_celeba"
        identity_file = source_root / "identity_CelebA.txt"

        if not img_dir.is_dir():
                              
            img_dir = source_root

                                         
        id_map: dict[str, str] = {}
        if identity_file.exists():
            for line in identity_file.read_text(encoding="utf-8").splitlines():
                parts = line.strip().split()
                if len(parts) == 2:
                    img_name, person_id = parts
                    id_map[img_name] = f"celeba_{person_id.zfill(6)}"
        else:
            logger.warning(
                "CelebA identity file not found at {path}. "
                "Images will be placed in 'unknown/'.",
                path=identity_file,
            )

        for img_path in iter_images(img_dir, recursive=False):
            person_id = id_map.get(img_path.name)
            if person_id:
                dest_dir = self._identities_dir / person_id
                ensure_dir(dest_dir)
                acc.identities.add(person_id)
                dest_file = dest_dir / img_path.name
                self._transfer(img_path, dest_file, mode, acc)
                acc.unmasked_count += 1
            else:
                dest_file = self._unknown_dir / img_path.name
                self._transfer(img_path, dest_file, mode, acc)
                acc.unknown_count += 1

    def _organize_casia(
        self,
        source_root: Path,
        mode: OrganizeMode,
        acc: _OrganizeAccumulator,
    ) -> None:
        """Organise CASIA-WebFace.

        CASIA layout: ``<person_id>/<image_file.jpg>``

        Args:
            source_root: Extracted CASIA-WebFace root.
            mode: Copy or move.
            acc: Mutable accumulator.
        """
        for person_dir in sorted(source_root.iterdir()):
            if not person_dir.is_dir():
                continue
            person_id = f"casia_{_sanitise_identity(person_dir.name)}"
            dest_dir = self._identities_dir / person_id
            ensure_dir(dest_dir)
            acc.identities.add(person_id)

            for img_path in iter_images(person_dir, recursive=False):
                dest_file = dest_dir / img_path.name
                self._transfer(img_path, dest_file, mode, acc)
                acc.unmasked_count += 1

    def _organize_vggface2(
        self,
        source_root: Path,
        mode: OrganizeMode,
        acc: _OrganizeAccumulator,
    ) -> None:
        """Organise VGGFace2.

        VGGFace2 layout: ``data/<n_id>/<m_id>/<image_file.jpg>``
        or flat ``<n_id>/<image_file.jpg>``.

        Args:
            source_root: Extracted VGGFace2 root.
            mode: Copy or move.
            acc: Mutable accumulator.
        """
        data_dir = source_root / "data"
        scan_root = data_dir if data_dir.is_dir() else source_root

        for person_dir in sorted(scan_root.iterdir()):
            if not person_dir.is_dir():
                continue
            person_id = f"vgg_{_sanitise_identity(person_dir.name)}"
            dest_dir = self._identities_dir / person_id
            ensure_dir(dest_dir)
            acc.identities.add(person_id)

                                                      
            for img_path in iter_images(person_dir, recursive=True):
                dest_file = dest_dir / img_path.name
                self._transfer(img_path, dest_file, mode, acc)
                acc.unmasked_count += 1

    def _organize_rmfd(
        self,
        source_root: Path,
        mode: OrganizeMode,
        acc: _OrganizeAccumulator,
    ) -> None:
        """Organise RMFD (Real Masked Face Dataset).

        RMFD layout (two sub-directories):
        - ``RMFD/self-built-masked-face-recognition-dataset/`` — masked faces
          organised by identity.
        - ``RMFD/real-world-masked-face-dataset/`` — real-world masked faces.

        Args:
            source_root: Extracted RMFD root.
            mode: Copy or move.
            acc: Mutable accumulator.
        """
                                                                
        inner = _find_inner_root(source_root, "Real-World-Masked-Face-Dataset")

        masked_identity_dir = _find_subdir(inner, [
            "self-built-masked-face-recognition-dataset",
            "masked-face-recognition-dataset",
        ])
        masked_real_dir = _find_subdir(inner, [
            "real-world-masked-face-dataset",
            "RMFRD",
        ])

                                                       
        if masked_identity_dir and masked_identity_dir.is_dir():
            for person_dir in sorted(masked_identity_dir.iterdir()):
                if not person_dir.is_dir():
                    continue
                person_id = f"rmfd_{_sanitise_identity(person_dir.name)}"
                dest_dir = self._identities_dir / person_id
                ensure_dir(dest_dir)
                acc.identities.add(person_id)

                for img_path in iter_images(person_dir, recursive=True):
                    dest_file = dest_dir / img_path.name
                    self._transfer(img_path, dest_file, mode, acc)

                masked_dest = self._masked_dir / person_id
                ensure_dir(masked_dest)
                for img_path in iter_images(person_dir, recursive=True):
                    dest_file = masked_dest / img_path.name
                    self._transfer(img_path, dest_file, mode, acc)
                    acc.masked_count += 1

                                                       
        if masked_real_dir and masked_real_dir.is_dir():
            for img_path in iter_images(masked_real_dir, recursive=True):
                dest_file = self._masked_dir / img_path.name
                self._transfer(img_path, dest_file, mode, acc)
                acc.masked_count += 1

    def _organize_smfd(
        self,
        source_root: Path,
        mode: OrganizeMode,
        acc: _OrganizeAccumulator,
    ) -> None:
        """Organise SMFD (Simulated Masked Face Dataset).

        Flat structure: all images → ``masked/``.

        Args:
            source_root: SMFD root directory.
            mode: Copy or move.
            acc: Mutable accumulator.
        """
        for img_path in iter_images(source_root, recursive=True):
            dest_file = self._masked_dir / f"smfd_{img_path.name}"
            self._transfer(img_path, dest_file, mode, acc)
            acc.masked_count += 1

    def _organize_mafa(
        self,
        source_root: Path,
        mode: OrganizeMode,
        acc: _OrganizeAccumulator,
    ) -> None:
        """Organise MAFA (Mask-Wearing Faces in the Wild).

        All images → ``masked/``.

        Args:
            source_root: MAFA root directory.
            mode: Copy or move.
            acc: Mutable accumulator.
        """
        for img_path in iter_images(source_root, recursive=True):
            dest_file = self._masked_dir / f"mafa_{img_path.name}"
            self._transfer(img_path, dest_file, mode, acc)
            acc.masked_count += 1

    def _organize_wider(
        self,
        source_root: Path,
        mode: OrganizeMode,
        acc: _OrganizeAccumulator,
    ) -> None:
        """Organise WIDER FACE.

        WIDER FACE is a detection dataset with no per-person identity.
        All images → ``unknown/``.

        Args:
            source_root: Extracted WIDER FACE root.
            mode: Copy or move.
            acc: Mutable accumulator.
        """
        for img_path in iter_images(source_root, recursive=True):
            dest_file = self._unknown_dir / f"wider_{img_path.name}"
            self._transfer(img_path, dest_file, mode, acc)
            acc.unknown_count += 1

    def _organize_maskedface_net(
        self,
        source_root: Path,
        mode: OrganizeMode,
        acc: _OrganizeAccumulator,
    ) -> None:
        """Organise MaskedFace-Net (CMFD + IMFD).

        Both splits are flat directories of masked face images.
        All images → ``masked/``.

        Args:
            source_root: Root containing CMFD and/or IMFD subdirectories.
            mode: Copy or move.
            acc: Mutable accumulator.
        """
        cmfd_dir = _find_subdir(source_root, ["CMFD", "cmfd"])
        imfd_dir = _find_subdir(source_root, ["IMFD", "imfd"])

        for split_dir, prefix in [(cmfd_dir, "cmfd"), (imfd_dir, "imfd")]:
            scan = split_dir if split_dir and split_dir.is_dir() else source_root
            for img_path in iter_images(scan, recursive=True):
                dest_file = self._masked_dir / f"{prefix}_{img_path.name}"
                self._transfer(img_path, dest_file, mode, acc)
                acc.masked_count += 1

    def _organize_custom(
        self,
        source_root: Path,
        mode: OrganizeMode,
        acc: _OrganizeAccumulator,
    ) -> None:
        """Organise a custom user dataset.

        Expected layout: ``<source_root>/<person_name>/<images>``
        If images are flat (no subfolders), they go to ``unknown/``.

        Args:
            source_root: Custom dataset root.
            mode: Copy or move.
            acc: Mutable accumulator.
        """
        subdirs = [p for p in source_root.iterdir() if p.is_dir()]

        if subdirs:
                                      
            for person_dir in sorted(subdirs):
                person_id = f"custom_{_sanitise_identity(person_dir.name)}"
                dest_dir = self._identities_dir / person_id
                ensure_dir(dest_dir)
                acc.identities.add(person_id)

                for img_path in iter_images(person_dir, recursive=True):
                    dest_file = dest_dir / img_path.name
                    self._transfer(img_path, dest_file, mode, acc)
                    acc.unmasked_count += 1
        else:
                                                    
            for img_path in iter_images(source_root, recursive=False):
                dest_file = self._unknown_dir / f"custom_{img_path.name}"
                self._transfer(img_path, dest_file, mode, acc)
                acc.unknown_count += 1

                                                                        
                            
                                                                        

    def _transfer(
        self,
        src: Path,
        dst: Path,
        mode: OrganizeMode,
        acc: _OrganizeAccumulator,
    ) -> None:
        """Copy or move *src* to *dst*, updating the accumulator.

        Skips the transfer if *dst* already exists (idempotent).

        Args:
            src: Source file path.
            dst: Destination file path.
            mode: :class:`OrganizeMode` — COPY or MOVE.
            acc: Mutable accumulator to update.
        """
        if dst.exists():
            acc.files_skipped += 1
            return

        try:
            if mode == OrganizeMode.COPY:
                safe_copy(src, dst, overwrite=False)
            else:
                safe_move(src, dst)
            acc.files_processed += 1
        except OSError as exc:
            acc.files_errored += 1
            acc.error_details.append((str(src), str(exc)))
            logger.error(
                "Transfer error: {src} → {dst}: {exc}",
                src=src,
                dst=dst,
                exc=exc,
            )

                                                                        
                                       
                                                                        

    def _apply_splits(self, acc: _OrganizeAccumulator) -> None:
        """Partition identity directories into train / val / test.

        Identities that already exist in ``validation/`` or ``test/``
        are not moved again (idempotent).

        After this call:
        - ``identities/<person>/`` → train set (remains in place).
        - ``validation/<person>/`` → val set.
        - ``test/<person>/`` → test set.

        Args:
            acc: Accumulator with the set of identities found.
        """
        if not acc.identities:
            return

        split_cfg = self._splits_cfg
        rng = random.Random(split_cfg.random_seed)

        all_ids = sorted(acc.identities)
        if split_cfg.stratify:
            rng.shuffle(all_ids)

        n_total = len(all_ids)
        n_val = max(1, int(n_total * split_cfg.val_ratio))
        n_test = max(1, int(n_total * split_cfg.test_ratio))

        val_ids = set(all_ids[:n_val])
        test_ids = set(all_ids[n_val : n_val + n_test])

        logger.info(
            "Splits: {train} train / {val} val / {test} test identities.",
            train=n_total - n_val - n_test,
            val=n_val,
            test=n_test,
        )

        for person_id in all_ids:
            src_dir = self._identities_dir / person_id

            if person_id in val_ids:
                dst_dir = self._validation_dir / person_id
            elif person_id in test_ids:
                dst_dir = self._test_dir / person_id
            else:
                continue                                 

            if dst_dir.exists():
                continue                               

            try:
                ensure_dir(dst_dir.parent)
                src_dir.rename(dst_dir)
                logger.debug(
                    "Split [{id}] → {dir}", id=person_id, dir=dst_dir.parent.name
                )
            except OSError as exc:
                logger.warning(
                    "Could not move identity {id} to split dir: {exc}",
                    id=person_id,
                    exc=exc,
                )


                                                                             
                      
                                                                             


def _sanitise_identity(name: str) -> str:
    """Sanitise a raw identity name into a safe directory name.

    Replaces spaces and special characters with underscores, lowercases,
    and truncates to 128 characters.

    Args:
        name: Raw identity name (e.g. ``"George_W_Bush"``).

    Returns:
        Safe directory-friendly string.
    """
    safe = re.sub(r"[^\w\-]", "_", name).lower()
    return safe[:128]


def _find_inner_root(root: Path, partial_name: str) -> Path:
    """Search for a subdirectory whose name contains *partial_name* (case-insensitive).

    Args:
        root: Directory to search.
        partial_name: Substring to look for.

    Returns:
        Matching subdirectory, or *root* if not found.
    """
    lower = partial_name.lower()
    for child in root.iterdir():
        if child.is_dir() and lower in child.name.lower():
            return child
    return root


def _find_subdir(root: Path, candidates: list[str]) -> Path | None:
    """Return the first candidate subdirectory that exists under *root*.

    Args:
        root: Parent directory.
        candidates: List of subdirectory names to try in order.

    Returns:
        :class:`Path` of the first matching subdirectory, or ``None``.
    """
    for name in candidates:
        candidate = root / name
        if candidate.is_dir():
            return candidate
                                
    lower_candidates = {c.lower() for c in candidates}
    for child in root.iterdir():
        if child.is_dir() and child.name.lower() in lower_candidates:
            return child
    return None
