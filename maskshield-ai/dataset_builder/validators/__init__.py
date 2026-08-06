"""
Validators package for MaskShield AI Dataset Builder.

Provides two validator classes at two granularities:

* :class:`~validators.image_validator.ImageValidator` — validates a single
  image file (format, decodability, size, aspect ratio, blur, brightness).
* :class:`~validators.dataset_validator.DatasetValidator` — validates an
  entire directory tree and detects perceptual near-duplicates.

Example::

    from config.loader import load_config
    from validators import DatasetValidator, ImageValidator

    cfg = load_config()
    img_val = ImageValidator(cfg.validation)
    ds_val  = DatasetValidator(cfg.validation)
"""

from validators.dataset_validator import (
    DatasetValidationReport,
    DatasetValidator,
    DuplicateGroup,
)
from validators.image_validator import (
    ImageValidationResult,
    ImageValidator,
    RejectionReason,
)

__all__ = [
                     
    "ImageValidator",
    "ImageValidationResult",
    "RejectionReason",
                       
    "DatasetValidator",
    "DatasetValidationReport",
    "DuplicateGroup",
]
