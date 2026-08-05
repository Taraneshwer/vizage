"""
Utils package — shared stateless helpers for MaskShield AI Dataset Builder.

Sub-modules
-----------
* :mod:`utils.hashing`      — SHA-256 and perceptual hashing
* :mod:`utils.file_ops`     — filesystem operations (mkdir, copy, move, iterate)
* :mod:`utils.image_utils`  — image load/save, quality metrics, transforms
* :mod:`utils.logging_setup` — Loguru sink configuration

Example::

    from utils.hashing import sha256_file, perceptual_hash, HashAlgorithm
    from utils.file_ops import ensure_dir, iter_images
    from utils.image_utils import load_image_bgr, laplacian_variance
    from utils.logging_setup import configure_logging
"""

from utils.file_ops import (
    IMAGE_EXTENSIONS,
    count_files,
    ensure_dir,
    extension_of,
    human_size,
    iter_images,
    list_subdirs,
    remove_empty_dirs,
    safe_copy,
    safe_move,
    stem_with_suffix,
)
from utils.hashing import (
    HashAlgorithm,
    hamming_distance,
    perceptual_hash,
    sha256_bytes,
    sha256_file,
)
from utils.image_utils import (
    ImageDimensions,
    ImageLoadError,
    apply_clahe,
    bgr_to_rgb,
    image_dimensions,
    is_grayscale,
    laplacian_variance,
    letterbox_resize,
    load_image_bgr,
    load_image_rgb,
    load_pil,
    mean_brightness,
    save_image,
)
from utils.logging_setup import configure_logging, configure_logging_minimal

__all__ = [
    # file_ops
    "IMAGE_EXTENSIONS",
    "count_files",
    "ensure_dir",
    "extension_of",
    "human_size",
    "iter_images",
    "list_subdirs",
    "remove_empty_dirs",
    "safe_copy",
    "safe_move",
    "stem_with_suffix",
    # hashing
    "HashAlgorithm",
    "hamming_distance",
    "perceptual_hash",
    "sha256_bytes",
    "sha256_file",
    # image_utils
    "ImageDimensions",
    "ImageLoadError",
    "apply_clahe",
    "bgr_to_rgb",
    "image_dimensions",
    "is_grayscale",
    "laplacian_variance",
    "letterbox_resize",
    "load_image_bgr",
    "load_image_rgb",
    "load_pil",
    "mean_brightness",
    "save_image",
    # logging_setup
    "configure_logging",
    "configure_logging_minimal",
]
