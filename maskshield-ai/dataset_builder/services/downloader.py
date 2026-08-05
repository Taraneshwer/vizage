"""
Dataset downloader service for MaskShield AI Dataset Builder.

:class:`DatasetDownloader` handles the full acquisition lifecycle for a
single dataset URL:

1. **Check** — skip if a complete archive already exists on disk.
2. **Download** — stream from HTTP with tqdm progress bar.
3. **Resume** — use ``Range`` header if a ``.part`` file is present.
4. **Retry** — exponential backoff on transient HTTP / network errors.
5. **Verify** — SHA-256 checksum comparison (optional, per config).
6. **Extract** — tarball / zip / rar extraction to a temp dir, then move.
7. **Organise** — move extracted tree under the configured output subdir.

:class:`DownloadResult` captures the outcome of every attempt, including
error details, so the caller can aggregate results without exception handling.

Design
------
* No global state — all config is constructor-injected.
* HTTP session is created per :meth:`download_dataset` call (no shared state).
* Partial downloads are stored as ``<filename>.part`` and renamed atomically
  on completion.
* Thread safety: separate :class:`DatasetDownloader` instances are safe to
  run concurrently (each owns its session and temp files).

Example::

    from config.loader import load_config
    from services.registry import DatasetRegistry
    from services.downloader import DatasetDownloader

    cfg = load_config()
    registry = DatasetRegistry.from_config(cfg)
    downloader = DatasetDownloader(cfg)

    for name, spec in registry.downloadable_specs().items():
        for url in spec.all_urls:
            result = downloader.download_dataset(name, url, spec.archive_type)
            print(result)
"""

from __future__ import annotations

import shutil
import tarfile
import tempfile
import time
import zipfile
from enum import Enum
from pathlib import Path

import requests
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field
from tqdm import tqdm

from config.models import AppConfig
from utils.file_ops import ensure_dir, human_size
from utils.hashing import sha256_file


# ---------------------------------------------------------------------------
# Download status enum
# ---------------------------------------------------------------------------


class DownloadStatus(str, Enum):
    """Outcome of a single :meth:`~DatasetDownloader.download_dataset` call.

    Attributes:
        SUCCESS: Archive downloaded, checksum verified, extraction complete.
        SKIPPED: Archive already present — no work needed.
        CHECKSUM_MISMATCH: Download succeeded but SHA-256 did not match.
        HTTP_ERROR: Non-retryable HTTP status code received.
        NETWORK_ERROR: Connection / timeout error after all retries.
        EXTRACTION_ERROR: Archive could not be extracted.
        MANUAL_REQUIRED: Dataset requires manual download; no URL available.
        UNKNOWN_ERROR: Unclassified exception.
    """

    SUCCESS = "success"
    SKIPPED = "skipped"
    CHECKSUM_MISMATCH = "checksum_mismatch"
    HTTP_ERROR = "http_error"
    NETWORK_ERROR = "network_error"
    EXTRACTION_ERROR = "extraction_error"
    MANUAL_REQUIRED = "manual_required"
    UNKNOWN_ERROR = "unknown_error"


# ---------------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------------


class DownloadResult(BaseModel):
    """Outcome record for one download + extraction attempt.

    Attributes:
        dataset_name: Identifier of the dataset (e.g. ``"lfw"``).
        url: The URL that was (attempted to be) downloaded.
        status: Final :class:`DownloadStatus`.
        archive_path: Path to the downloaded archive, if saved.
        extract_path: Path where the archive was extracted.
        checksum_verified: ``True`` if SHA-256 was checked and matched.
        bytes_downloaded: Total bytes received in this call.
        elapsed_seconds: Wall-clock time for the whole operation.
        error_message: Human-readable error description on failure.
    """

    model_config = ConfigDict(frozen=True)

    dataset_name: str
    url: str
    status: DownloadStatus
    archive_path: Path | None = None
    extract_path: Path | None = None
    checksum_verified: bool = False
    bytes_downloaded: int = 0
    elapsed_seconds: float = 0.0
    error_message: str | None = None

    def __str__(self) -> str:
        parts = [
            f"DownloadResult({self.dataset_name}",
            f"status={self.status.value}",
            f"bytes={human_size(self.bytes_downloaded)}",
            f"elapsed={self.elapsed_seconds:.1f}s",
        ]
        if self.error_message:
            parts.append(f"error={self.error_message!r}")
        return ", ".join(parts) + ")"


# ---------------------------------------------------------------------------
# Downloader service
# ---------------------------------------------------------------------------


class DatasetDownloader:
    """Downloads, verifies, and extracts dataset archives.

    Args:
        cfg: Validated :class:`~config.models.AppConfig`.

    Example::

        downloader = DatasetDownloader(cfg)
        result = downloader.download_dataset("lfw", spec.primary_url, "tar.gz")
        assert result.status == DownloadStatus.SUCCESS
    """

    def __init__(self, cfg: AppConfig) -> None:
        self._cfg = cfg
        self._dl_cfg = cfg.downloader

        self._cache_dir: Path = Path(cfg.paths.download_cache)
        self._temp_dir: Path = Path(cfg.paths.temp_dir)
        self._datasets_root: Path = Path(cfg.paths.datasets_root)

        ensure_dir(self._cache_dir)
        ensure_dir(self._temp_dir)
        ensure_dir(self._datasets_root)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def download_dataset(
        self,
        dataset_name: str,
        url: str,
        archive_type: str,
        *,
        expected_checksum: str | None = None,
        output_subdir: str = "",
    ) -> DownloadResult:
        """Download a single dataset archive from *url*, extract it, and
        place it under the configured datasets root.

        Args:
            dataset_name: Short identifier (used for logging and file naming).
            url: Full HTTP/HTTPS URL to the archive.
            archive_type: One of ``"tar.gz"``, ``"tar.bz2"``, ``"tar.xz"``,
                ``"zip"``, or ``"none"`` (raw file, no extraction).
            expected_checksum: SHA-256 hex digest to verify after download.
                Pass ``None`` to skip verification.
            output_subdir: Subdirectory under ``datasets_root`` for extraction.

        Returns:
            A :class:`DownloadResult` describing the outcome.
        """
        t_start = time.monotonic()
        archive_name = _url_filename(url)
        archive_path = self._cache_dir / archive_name
        extract_root = self._datasets_root / output_subdir if output_subdir else self._datasets_root

        logger.info(
            "Downloading [{name}]: {url}", name=dataset_name, url=url
        )

        # ----------------------------------------------------------------
        # Skip if already downloaded and extracted
        # ----------------------------------------------------------------
        if archive_path.exists() and self._archive_intact(archive_path, archive_type):
            logger.info(
                "[{name}] Archive already present: {path}. Checking extraction ...",
                name=dataset_name,
                path=archive_path,
            )
            if extract_root.exists() and any(extract_root.iterdir()):
                logger.success("[{name}] Already extracted. Skipping.", name=dataset_name)
                return DownloadResult(
                    dataset_name=dataset_name,
                    url=url,
                    status=DownloadStatus.SKIPPED,
                    archive_path=archive_path,
                    extract_path=extract_root,
                    elapsed_seconds=time.monotonic() - t_start,
                )

        # ----------------------------------------------------------------
        # Download (with resume + retry)
        # ----------------------------------------------------------------
        try:
            bytes_downloaded = self._download_with_retry(url, archive_path)
        except requests.HTTPError as exc:
            elapsed = time.monotonic() - t_start
            logger.error("[{name}] HTTP error: {exc}", name=dataset_name, exc=exc)
            return DownloadResult(
                dataset_name=dataset_name,
                url=url,
                status=DownloadStatus.HTTP_ERROR,
                bytes_downloaded=0,
                elapsed_seconds=elapsed,
                error_message=str(exc),
            )
        except (requests.ConnectionError, requests.Timeout) as exc:
            elapsed = time.monotonic() - t_start
            logger.error("[{name}] Network error after retries: {exc}", name=dataset_name, exc=exc)
            return DownloadResult(
                dataset_name=dataset_name,
                url=url,
                status=DownloadStatus.NETWORK_ERROR,
                bytes_downloaded=0,
                elapsed_seconds=elapsed,
                error_message=str(exc),
            )

        # ----------------------------------------------------------------
        # Checksum verification
        # ----------------------------------------------------------------
        checksum_verified = False
        if expected_checksum:
            checksum_verified = self._verify_checksum(
                archive_path, expected_checksum, dataset_name
            )
            if not checksum_verified:
                elapsed = time.monotonic() - t_start
                return DownloadResult(
                    dataset_name=dataset_name,
                    url=url,
                    status=DownloadStatus.CHECKSUM_MISMATCH,
                    archive_path=archive_path,
                    bytes_downloaded=bytes_downloaded,
                    elapsed_seconds=elapsed,
                    error_message="SHA-256 checksum mismatch.",
                )

        # ----------------------------------------------------------------
        # Extraction
        # ----------------------------------------------------------------
        if archive_type == "none":
            ensure_dir(extract_root)
            dest = extract_root / archive_name
            shutil.copy2(archive_path, dest)
            extract_path: Path = extract_root
        else:
            try:
                extract_path = self._extract_archive(
                    archive_path, archive_type, extract_root
                )
            except Exception as exc:
                elapsed = time.monotonic() - t_start
                logger.error("[{name}] Extraction failed: {exc}", name=dataset_name, exc=exc)
                return DownloadResult(
                    dataset_name=dataset_name,
                    url=url,
                    status=DownloadStatus.EXTRACTION_ERROR,
                    archive_path=archive_path,
                    bytes_downloaded=bytes_downloaded,
                    elapsed_seconds=elapsed,
                    error_message=str(exc),
                )

        elapsed = time.monotonic() - t_start
        logger.success(
            "[{name}] Done — {size} in {t:.1f}s → {path}",
            name=dataset_name,
            size=human_size(bytes_downloaded),
            t=elapsed,
            path=extract_path,
        )
        return DownloadResult(
            dataset_name=dataset_name,
            url=url,
            status=DownloadStatus.SUCCESS,
            archive_path=archive_path,
            extract_path=extract_path,
            checksum_verified=checksum_verified,
            bytes_downloaded=bytes_downloaded,
            elapsed_seconds=elapsed,
        )

    def download_all(
        self,
        specs: dict,  # dict[str, DatasetSourceSpec]
    ) -> list[DownloadResult]:
        """Download all datasets described by *specs*.

        Iterates sequentially (respecting ``max_concurrent_downloads=1``
        semantics). For parallel downloads, call :meth:`download_dataset`
        from a thread pool in the caller.

        Args:
            specs: Mapping of name → :class:`~services.registry.DatasetSourceSpec`.

        Returns:
            List of :class:`DownloadResult` objects, one per URL attempted.
        """
        results: list[DownloadResult] = []
        for name, spec in specs.items():
            if not spec.downloadable:
                logger.warning(
                    "[{name}] Requires manual download. {note}",
                    name=name,
                    note=spec.manual_note or "",
                )
                for url in (spec.all_urls or [""]):
                    results.append(
                        DownloadResult(
                            dataset_name=name,
                            url=url or "",
                            status=DownloadStatus.MANUAL_REQUIRED,
                            error_message=spec.manual_note,
                        )
                    )
                continue

            for url in spec.all_urls:
                result = self.download_dataset(
                    dataset_name=name,
                    url=url,
                    archive_type=spec.archive_type,
                    expected_checksum=spec.checksum_sha256,
                    output_subdir=spec.output_subdir,
                )
                results.append(result)
        return results

    # ------------------------------------------------------------------
    # Private: download logic
    # ------------------------------------------------------------------

    def _download_with_retry(self, url: str, dest: Path) -> int:
        """Download *url* to *dest*, resuming if a ``.part`` file exists.

        Retries up to ``max_retries`` times with exponential backoff.

        Args:
            url: HTTP/HTTPS URL to download.
            dest: Final destination path for the completed archive.

        Returns:
            Total bytes downloaded in this call.

        Raises:
            requests.HTTPError: On non-retryable HTTP status (4xx).
            requests.ConnectionError: After all retries exhausted.
            requests.Timeout: After all retries exhausted.
        """
        part_path = dest.with_suffix(dest.suffix + ".part")
        max_retries = self._dl_cfg.max_retries
        backoff = self._dl_cfg.retry_backoff_seconds

        for attempt in range(1, max_retries + 2):
            try:
                return self._attempt_download(url, dest, part_path)
            except requests.HTTPError as exc:
                # 4xx are not retryable.
                if exc.response is not None and exc.response.status_code < 500:
                    raise
                if attempt > max_retries:
                    raise
                wait = backoff * (2 ** (attempt - 1))
                logger.warning(
                    "Attempt {attempt}/{max} failed: {exc}. Retrying in {wait:.1f}s ...",
                    attempt=attempt,
                    max=max_retries + 1,
                    exc=exc,
                    wait=wait,
                )
                time.sleep(wait)
            except (requests.ConnectionError, requests.Timeout) as exc:
                if attempt > max_retries:
                    raise
                wait = backoff * (2 ** (attempt - 1))
                logger.warning(
                    "Attempt {attempt}/{max} network error: {exc}. Retrying in {wait:.1f}s ...",
                    attempt=attempt,
                    max=max_retries + 1,
                    exc=exc,
                    wait=wait,
                )
                time.sleep(wait)

        # This line is unreachable but satisfies mypy.
        raise requests.ConnectionError("Exhausted retries.")  # pragma: no cover

    def _attempt_download(self, url: str, dest: Path, part_path: Path) -> int:
        """Single HTTP download attempt, supporting resume via Range header.

        Args:
            url: Full download URL.
            dest: Final file path after successful completion.
            part_path: Partial-file path used during download.

        Returns:
            Number of bytes downloaded in this attempt.

        Raises:
            requests.HTTPError: On HTTP error status.
        """
        headers: dict[str, str] = {}
        resume_pos = 0

        if self._dl_cfg.resume_enabled and part_path.exists():
            resume_pos = part_path.stat().st_size
            headers["Range"] = f"bytes={resume_pos}-"
            logger.debug(
                "Resuming from byte {pos} for {url}", pos=resume_pos, url=url
            )

        with requests.Session() as session:
            response = session.get(
                url,
                headers=headers,
                stream=True,
                timeout=self._dl_cfg.timeout_seconds,
                verify=self._dl_cfg.verify_ssl,
            )
            response.raise_for_status()

            total_size = int(response.headers.get("Content-Length", 0)) + resume_pos
            mode = "ab" if resume_pos > 0 else "wb"

            bytes_this_attempt = 0
            chunk_size = self._dl_cfg.chunk_size_bytes

            with (
                part_path.open(mode) as fh,
                tqdm(
                    total=total_size or None,
                    initial=resume_pos,
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                    desc=dest.name,
                    dynamic_ncols=True,
                ) as bar,
            ):
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        fh.write(chunk)
                        bytes_this_attempt += len(chunk)
                        bar.update(len(chunk))

        # Rename .part → final destination atomically.
        part_path.rename(dest)
        logger.debug(
            "Download complete: {path} ({size})",
            path=dest,
            size=human_size(resume_pos + bytes_this_attempt),
        )
        return bytes_this_attempt

    # ------------------------------------------------------------------
    # Private: verification
    # ------------------------------------------------------------------

    def _verify_checksum(
        self,
        archive_path: Path,
        expected: str,
        dataset_name: str,
    ) -> bool:
        """Verify SHA-256 digest of *archive_path* against *expected*.

        Args:
            archive_path: Downloaded archive file.
            expected: Expected lowercase hex digest.
            dataset_name: Used for log messages only.

        Returns:
            ``True`` if the digest matches.
        """
        logger.info("[{name}] Verifying SHA-256 ...", name=dataset_name)
        actual = sha256_file(archive_path)
        if actual.lower() == expected.lower():
            logger.success("[{name}] Checksum OK: {digest}", name=dataset_name, digest=actual)
            return True
        logger.error(
            "[{name}] Checksum MISMATCH!\n  expected: {exp}\n  actual  : {act}",
            name=dataset_name,
            exp=expected,
            act=actual,
        )
        return False

    # ------------------------------------------------------------------
    # Private: extraction
    # ------------------------------------------------------------------

    def _extract_archive(
        self,
        archive_path: Path,
        archive_type: str,
        extract_root: Path,
    ) -> Path:
        """Extract *archive_path* to *extract_root*.

        Extraction is performed into a temporary directory first, then
        moved into place to prevent partial extractions being left behind
        on failure.

        Args:
            archive_path: Local archive file.
            archive_type: Format string (``"tar.gz"``, ``"zip"``, etc.).
            extract_root: Final destination directory.

        Returns:
            *extract_root* after successful extraction.

        Raises:
            ValueError: If *archive_type* is not supported.
            tarfile.TarError: On corrupted tar archives.
            zipfile.BadZipFile: On corrupted zip archives.
            OSError: On filesystem errors during extraction.
        """
        ensure_dir(extract_root)

        logger.info(
            "Extracting {archive} → {dest}",
            archive=archive_path.name,
            dest=extract_root,
        )

        with tempfile.TemporaryDirectory(dir=self._temp_dir) as tmp_str:
            tmp = Path(tmp_str)

            if archive_type in {"tar.gz", "tar.bz2", "tar.xz", "tar"}:
                self._extract_tar(archive_path, tmp)
            elif archive_type == "zip":
                self._extract_zip(archive_path, tmp)
            elif archive_type in {"rar", "7z"}:
                self._extract_patool(archive_path, tmp)
            else:
                raise ValueError(
                    f"Unsupported archive type: '{archive_type}'. "
                    "Supported: tar.gz, tar.bz2, tar.xz, zip, rar, 7z, none."
                )

            # Move extracted contents to final destination.
            self._move_extracted(tmp, extract_root)

        logger.success("Extraction complete → {path}", path=extract_root)
        return extract_root

    @staticmethod
    def _extract_tar(archive_path: Path, dest: Path) -> None:
        """Extract a tar archive (any compression) to *dest*.

        Args:
            archive_path: Path to the ``.tar.*`` file.
            dest: Destination directory.
        """
        with tarfile.open(archive_path, "r:*") as tf:
            # Safety filter: reject absolute paths and ``..`` traversal.
            members = [
                m for m in tf.getmembers()
                if not (
                    Path(m.name).is_absolute()
                    or ".." in Path(m.name).parts
                )
            ]
            tf.extractall(path=str(dest), members=members)  # type: ignore[call-arg]

    @staticmethod
    def _extract_zip(archive_path: Path, dest: Path) -> None:
        """Extract a ZIP archive to *dest*.

        Args:
            archive_path: Path to the ``.zip`` file.
            dest: Destination directory.
        """
        with zipfile.ZipFile(archive_path, "r") as zf:
            # Safety filter: reject absolute paths and ``..`` traversal.
            safe_members = [
                name for name in zf.namelist()
                if not (
                    Path(name).is_absolute()
                    or ".." in Path(name).parts
                )
            ]
            for member in safe_members:
                zf.extract(member, path=str(dest))

    @staticmethod
    def _extract_patool(archive_path: Path, dest: Path) -> None:
        """Extract RAR / 7z archives using ``patool``.

        Args:
            archive_path: Path to the archive file.
            dest: Destination directory.

        Raises:
            ImportError: If ``patool`` is not installed.
        """
        try:
            import patoollib  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "patool is required for RAR/7z extraction. "
                "Install with: pip install patool"
            ) from exc
        patoollib.extract_archive(str(archive_path), outdir=str(dest))

    @staticmethod
    def _move_extracted(src_dir: Path, dst_dir: Path) -> None:
        """Move all top-level items from *src_dir* into *dst_dir*.

        If *src_dir* contains a single subdirectory (common in tarballs),
        that subdirectory's contents are moved instead of the directory itself,
        flattening one level.

        Args:
            src_dir: Temporary extraction directory.
            dst_dir: Final destination directory.
        """
        ensure_dir(dst_dir)
        children = list(src_dir.iterdir())

        # Unwrap single-directory tarballs (e.g. ``lfw/`` inside ``lfw.tgz``).
        if len(children) == 1 and children[0].is_dir():
            src_dir = children[0]
            children = list(src_dir.iterdir())

        for item in children:
            target = dst_dir / item.name
            if target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            shutil.move(str(item), str(dst_dir))

    # ------------------------------------------------------------------
    # Private: helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _archive_intact(path: Path, archive_type: str) -> bool:
        """Quick sanity check that the archive file is non-zero and readable.

        Args:
            path: Archive file path.
            archive_type: Archive format string.

        Returns:
            ``True`` if the file exists and appears intact.
        """
        if not path.is_file() or path.stat().st_size == 0:
            return False
        try:
            if archive_type == "zip":
                with zipfile.ZipFile(path):
                    pass
            elif "tar" in archive_type:
                with tarfile.open(path, "r:*"):
                    pass
        except Exception:
            return False
        return True


# ---------------------------------------------------------------------------
# Module-level helper
# ---------------------------------------------------------------------------


def _url_filename(url: str) -> str:
    """Extract the filename component from a URL.

    Args:
        url: Full URL string.

    Returns:
        Filename portion (everything after the last ``/``),
        or ``"download"`` if the URL ends with a slash.
    """
    part = url.rstrip("/").split("/")[-1]
    # Strip query strings.
    return part.split("?")[0] or "download"
