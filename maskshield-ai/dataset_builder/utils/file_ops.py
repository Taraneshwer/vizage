"""
Filesystem utility helpers for MaskShield AI Dataset Builder.

Provides:
- :func:`ensure_dir` — create directory tree idempotently
- :func:`safe_move` — atomic file move with parent creation
- :func:`safe_copy` — copy a file ensuring the destination parent exists
- :func:`iter_images` — recursively yield image paths filtered by extension
- :func:`count_files` — count files matching a glob pattern
- :func:`human_size` — human-readable byte string (KB / MB / GB)
- :func:`atomic_write_text` — write text via a temp file then rename
- :func:`remove_empty_dirs` — prune empty directories under a root
- :func:`list_subdirs` — list immediate subdirectories
- :func:`extension_of` — normalised lowercase extension without the dot

All functions are pure / stateless unless stated otherwise.
No global state; no side-effects on import.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path

# ---------------------------------------------------------------------------
# Supported image extensions (lowercase, without leading dot)
# ---------------------------------------------------------------------------

IMAGE_EXTENSIONS: frozenset[str] = frozenset(
    {"jpg", "jpeg", "png", "bmp", "webp", "tiff", "tif"}
)


# ---------------------------------------------------------------------------
# Directory helpers
# ---------------------------------------------------------------------------


def ensure_dir(path: Path) -> Path:
    """Create *path* and all missing parent directories.

    Idempotent — if *path* already exists as a directory the call is a
    no-op.  If *path* exists as a file a :class:`NotADirectoryError` is
    raised by the underlying OS.

    Args:
        path: Directory path to create.

    Returns:
        The same *path* object (for chaining).

    Raises:
        NotADirectoryError: If *path* is an existing regular file.
        OSError: On any other OS-level failure.

    Example::

        log_dir = ensure_dir(Path("logs/run_01"))
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_subdirs(root: Path) -> list[Path]:
    """Return a sorted list of immediate subdirectories of *root*.

    Args:
        root: Parent directory to scan.

    Returns:
        Sorted list of :class:`Path` objects for each child directory.

    Raises:
        NotADirectoryError: If *root* is not a directory.
    """
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")
    return sorted(p for p in root.iterdir() if p.is_dir())


def remove_empty_dirs(root: Path) -> int:
    """Recursively remove empty directories under *root* (bottom-up).

    The *root* itself is **not** removed even if it becomes empty.

    Args:
        root: Directory tree to prune.

    Returns:
        Number of directories that were removed.
    """
    removed = 0
    for dirpath, dirnames, filenames in os.walk(str(root), topdown=False):
        current = Path(dirpath)
        if current == root:
            continue
        if not filenames and not list(current.iterdir()):
            current.rmdir()
            removed += 1
    return removed


# ---------------------------------------------------------------------------
# File operations
# ---------------------------------------------------------------------------


def safe_move(src: Path, dst: Path) -> Path:
    """Move *src* to *dst*, creating *dst*'s parent directories as needed.

    Args:
        src: Source file path.
        dst: Destination file path.

    Returns:
        The resolved destination path after the move.

    Raises:
        FileNotFoundError: If *src* does not exist.
        OSError: On any OS-level failure.
    """
    ensure_dir(dst.parent)
    shutil.move(str(src), str(dst))
    return dst


def safe_copy(src: Path, dst: Path, *, overwrite: bool = False) -> Path:
    """Copy *src* to *dst*, creating *dst*'s parent directories as needed.

    Args:
        src: Source file path.
        dst: Destination file path.
        overwrite: When ``False`` (default) and *dst* exists, the call is a
            no-op and the existing *dst* is returned.  When ``True`` the
            file is always overwritten.

    Returns:
        The destination path.

    Raises:
        FileNotFoundError: If *src* does not exist.
        OSError: On any OS-level failure.
    """
    ensure_dir(dst.parent)
    if dst.exists() and not overwrite:
        return dst
    shutil.copy2(str(src), str(dst))
    return dst


def atomic_write_text(path: Path, content: str, encoding: str = "utf-8") -> None:
    """Write *content* to *path* atomically using a sibling temp file + rename.

    On POSIX the rename is atomic; on Windows it is ``os.replace`` which
    is as close to atomic as Windows allows.

    Args:
        path: Target file path.  Parent must exist.
        content: Text to write.
        encoding: Text encoding.  Defaults to ``utf-8``.

    Raises:
        OSError: If the parent directory does not exist or on write failure.
    """
    ensure_dir(path.parent)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding=encoding) as fh:
            fh.write(content)
        os.replace(tmp_path, path)
    except Exception:
        # Best-effort cleanup of temp file on failure.
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# Image iteration
# ---------------------------------------------------------------------------


def iter_images(
    root: Path,
    extensions: frozenset[str] | None = None,
    *,
    recursive: bool = True,
) -> Iterator[Path]:
    """Yield image file paths under *root* filtered by extension.

    Args:
        root: Directory to scan.
        extensions: Set of lowercase extensions **without** the leading dot.
            Defaults to :data:`IMAGE_EXTENSIONS`.
        recursive: When ``True`` (default) the scan is recursive.
            When ``False`` only the immediate children of *root* are checked.

    Yields:
        :class:`Path` objects for each matched image file, in an
        unspecified but deterministic OS order.

    Raises:
        NotADirectoryError: If *root* is not a directory.
    """
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")

    allowed = extensions if extensions is not None else IMAGE_EXTENSIONS
    pattern = "**/*" if recursive else "*"

    for candidate in root.glob(pattern):
        if candidate.is_file() and extension_of(candidate) in allowed:
            yield candidate


def count_files(root: Path, pattern: str = "**/*") -> int:
    """Count files matching a glob *pattern* under *root*.

    Args:
        root: Directory to scan.
        pattern: Glob pattern relative to *root*.

    Returns:
        Number of matched regular files.
    """
    return sum(1 for p in root.glob(pattern) if p.is_file())


# ---------------------------------------------------------------------------
# String / metadata helpers
# ---------------------------------------------------------------------------


def extension_of(path: Path) -> str:
    """Return the lowercase file extension without the leading dot.

    Args:
        path: Any file path.

    Returns:
        Lowercase extension string, e.g. ``"jpg"`` for ``"photo.JPG"``.
        Returns an empty string if the file has no extension.

    Example::

        assert extension_of(Path("photo.JPG")) == "jpg"
        assert extension_of(Path("Makefile")) == ""
    """
    return path.suffix.lstrip(".").lower()


def human_size(num_bytes: int) -> str:
    """Convert *num_bytes* to a human-readable string.

    Args:
        num_bytes: Raw byte count.  Negative values are supported.

    Returns:
        Formatted string, e.g. ``"1.23 GB"``, ``"456.00 KB"``.

    Example::

        print(human_size(1_234_567_890))  # "1.15 GB"
    """
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes = int(num_bytes / 1024.0)  # type: ignore[assignment]
    return f"{num_bytes:.2f} PB"


def stem_with_suffix(path: Path, suffix: str) -> Path:
    """Return a sibling path whose stem is preserved but extension replaced.

    Args:
        path: Original file path.
        suffix: New extension including the dot, e.g. ``".jpg"``.

    Returns:
        New :class:`Path` in the same directory with the new extension.

    Example::

        p = stem_with_suffix(Path("a/b/image.png"), ".jpg")
        assert p == Path("a/b/image.jpg")
    """
    return path.with_suffix(suffix)
