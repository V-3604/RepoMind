"""
Repository loader factory.
"""

import logging
from typing import Dict, Type, Optional, Any, Callable


class RepoLoaderFactory:
    """Factory for creating repository loaders."""
    
    _loaders: Dict[str, Type[Any]] = {}
    
    @classmethod
    def register(cls, loader_type: str) -> Callable:
        """
        Decorator to register a loader class with the factory.
        
        Args:
            loader_type: Type of loader (e.g., "github", "local", "zip")
            
        Returns:
            Callable: Decorator function
        """
        def decorator(loader_class: Type[Any]) -> Type[Any]:
            cls._loaders[loader_type] = loader_class
            return loader_class
        return decorator
    
    @classmethod
    def get_loader(cls, loader_type: str) -> Optional[Type[Any]]:
        """
        Get a loader class by type.
        
        Args:
            loader_type: Type of loader
            
        Returns:
            Type[Any]: Loader class or None if not found
        """
        if loader_type not in cls._loaders:
            logging.error(f"Loader type not found: {loader_type}")
            return None
            
        return cls._loaders.get(loader_type) 