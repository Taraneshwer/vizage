"""
Image Import Pipeline Utilities.
"""
import os
from typing import List
from loguru import logger

class ImagePipelineUtils:
    """
    Utilities for validating and loading images from disk recursively.
    """
    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

    @classmethod
    def is_valid_image(cls, file_path: str) -> bool:
        """
        Validates the file extension.
        """
        _, ext = os.path.splitext(file_path.lower())
        return ext in cls.SUPPORTED_EXTENSIONS

    @classmethod
    def discover_images(cls, directory: str, recursive: bool = True) -> List[str]:
        """
        Finds all supported images in a directory.
        """
        found_images = []
        if recursive:
            for root, _, files in os.walk(directory):
                for file in files:
                    if cls.is_valid_image(file):
                        found_images.append(os.path.join(root, file))
        else:
            for file in os.listdir(directory):
                path = os.path.join(directory, file)
                if os.path.isfile(path) and cls.is_valid_image(file):
                    found_images.append(path)
                    
        return found_images
