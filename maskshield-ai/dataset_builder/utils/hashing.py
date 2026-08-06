"""
Cryptographic and perceptual hashing utilities.

Provides:
- :func:`sha256_file` — streaming SHA-256 of a file (no full-read into RAM)
- :func:`sha256_bytes` — SHA-256 of an in-memory buffer
- :func:`perceptual_hash` — ``imagehash`` perceptual hash of an image file
- :func:`hamming_distance` — bit-level distance between two image hashes
- :class:`HashAlgorithm` — enum of supported perceptual hash algorithms

All functions are pure and stateless; no module-level side-effects.
"""

from __future__ import annotations

import hashlib
from enum import Enum
from pathlib import Path

import imagehash
from PIL import Image


                                                                             
           
                                                                             

_SHA256_CHUNK_BYTES: int = 1 << 20                          


                                                                             
              
                                                                             


class HashAlgorithm(str, Enum):
    """Perceptual hash algorithm identifiers supported by ``imagehash``.

    Attributes:
        PHASH: Discrete cosine transform perceptual hash.
        DHASH: Difference hash (gradient-based).
        WHASH: Wavelet hash.
        AHASH: Average hash (simple, fast).
    """

    PHASH = "phash"
    DHASH = "dhash"
    WHASH = "whash"
    AHASH = "ahash"


                                                                             
                       
                                                                             


def sha256_file(path: Path, chunk_size: int = _SHA256_CHUNK_BYTES) -> str:
    """Compute the SHA-256 hex digest of a file using streaming reads.

    The file is read in *chunk_size* byte blocks so arbitrarily large
    files can be hashed without loading them entirely into memory.

    Args:
        path: Absolute or relative path to the target file.
        chunk_size: Number of bytes per read.  Defaults to 1 MiB.

    Returns:
        Lowercase hexadecimal SHA-256 digest string (64 characters).

    Raises:
        FileNotFoundError: If *path* does not exist.
        IsADirectoryError: If *path* is a directory.
        OSError: On any other I/O failure.

    Example::

        digest = sha256_file(Path("datasets/lfw.tgz"))
        assert len(digest) == 64
    """
    hasher = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def sha256_bytes(data: bytes) -> str:
    """Compute the SHA-256 hex digest of an in-memory bytes object.

    Args:
        data: Raw byte string to hash.

    Returns:
        Lowercase hexadecimal SHA-256 digest string (64 characters).

    Example::

        digest = sha256_bytes(b"hello world")
    """
    return hashlib.sha256(data).hexdigest()


                                                                             
                    
                                                                             


def perceptual_hash(
    image_path: Path,
    algorithm: HashAlgorithm = HashAlgorithm.PHASH,
    hash_size: int = 8,
) -> imagehash.ImageHash:
    """Compute a perceptual hash of an image file.

    Perceptual hashes are robust to minor image transformations (resize,
    compression artefacts, brightness changes) and are used for near-
    duplicate detection.

    Args:
        image_path: Path to the image file.  Must be readable by Pillow.
        algorithm: Which perceptual hash algorithm to use.
            Defaults to :attr:`HashAlgorithm.PHASH`.
        hash_size: Internal grid size for the hash algorithm.
            Larger values increase precision but also memory and time.
            Defaults to 8 (producing a 64-bit hash for phash/dhash).

    Returns:
        An :class:`imagehash.ImageHash` instance that supports
        subtraction (Hamming distance) and string conversion.

    Raises:
        FileNotFoundError: If *image_path* does not exist.
        PIL.UnidentifiedImageError: If the file is not a valid image.
        ValueError: If *algorithm* is not a recognised :class:`HashAlgorithm`.

    Example::

        h1 = perceptual_hash(Path("a.jpg"))
        h2 = perceptual_hash(Path("b.jpg"))
        distance = h1 - h2          # Hamming distance
        is_dup = distance <= 10
    """
    with Image.open(image_path) as img:
        img_rgb = img.convert("RGB")

    match algorithm:
        case HashAlgorithm.PHASH:
            return imagehash.phash(img_rgb, hash_size=hash_size)
        case HashAlgorithm.DHASH:
            return imagehash.dhash(img_rgb, hash_size=hash_size)
        case HashAlgorithm.WHASH:
            return imagehash.whash(img_rgb, hash_size=hash_size)
        case HashAlgorithm.AHASH:
            return imagehash.average_hash(img_rgb, hash_size=hash_size)
        case _:
            raise ValueError(f"Unsupported hash algorithm: {algorithm!r}")


def hamming_distance(
    hash_a: imagehash.ImageHash,
    hash_b: imagehash.ImageHash,
) -> int:
    """Return the Hamming distance between two perceptual hashes.

    The Hamming distance counts differing bits.  A distance of 0 means
    the images are perceptually identical; a distance ≤ 10 typically
    indicates near-duplicates.

    Args:
        hash_a: First perceptual hash.
        hash_b: Second perceptual hash.

    Returns:
        Non-negative integer bit-difference count.

    Example::

        dist = hamming_distance(perceptual_hash(p1), perceptual_hash(p2))
        if dist <= 10:
            print("Duplicate detected")
    """
    return int(hash_a - hash_b)
