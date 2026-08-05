"""
Factory for creating sources dynamically.
Supports self-registration via decorators.
"""
from typing import Type, Dict
from app.sources.base import BaseSource
from app.sources.schemas import BaseSourceConfig
from loguru import logger

class SourceFactory:
    """
    Registry and factory for universal sources.
    """
    _registry: Dict[str, Type[BaseSource]] = {}

    @classmethod
    def register(cls, source_type: str):
        """
        Decorator to self-register provider classes.
        """
        def wrapper(wrapped_class: Type[BaseSource]):
            cls._registry[source_type] = wrapped_class
            logger.debug(f"Registered source provider: {source_type}")
            return wrapped_class
        return wrapper

    @classmethod
    def create(cls, source_type: str, config: BaseSourceConfig) -> BaseSource:
        if source_type not in cls._registry:
            logger.error(f"Unknown source type requested: {source_type}")
            raise ValueError(f"Provider '{source_type}' is not registered.")
        
        provider_class = cls._registry[source_type]
        return provider_class(config)
