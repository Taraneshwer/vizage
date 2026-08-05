"""
Factory for instantiating InputSources based on type.
"""
from typing import Type, Dict, Any
from app.input.base import InputSource
from loguru import logger

class InputSourceFactory:
    """
    Creates and returns the appropriate InputSource provider based on the type string.
    """
    _registry: Dict[str, Type[InputSource]] = {}

    @classmethod
    def register(cls, source_type: str, provider_class: Type[InputSource]):
        """Registers a new provider class."""
        cls._registry[source_type] = provider_class
        logger.debug(f"Registered InputSource provider: {source_type}")

    @classmethod
    def create(cls, source_type: str, source_uri: str, **kwargs) -> InputSource:
        """Instantiates a provider."""
        if source_type not in cls._registry:
            logger.error(f"Unknown input source type requested: {source_type}")
            raise ValueError(f"Provider for type '{source_type}' not found.")
        
        provider_class = cls._registry[source_type]
        return provider_class(source_uri=source_uri, **kwargs)
