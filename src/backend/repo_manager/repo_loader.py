"""
Repository loading interface.
Handles loading repositories from different sources (GitHub, ZIP, local).
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type

from config import MAX_REPO_SIZE_MB


class RepoLoader(ABC):
    """Abstract base class for repository loaders."""
    
    def __init__(self):
        """Initialize the loader."""
        self.logger = logging.getLogger(__name__)
        self.max_size_bytes = MAX_REPO_SIZE_MB * 1024 * 1024
    
    @abstractmethod
    def load(self, source: str) -> Dict[str, Any]:
        """
        Load repository from source.
        
        Args:
            source: Source identifier (URL, file path, etc.)
            
        Returns:
            dict: Repository metadata and file contents
        """
        pass
    
    @abstractmethod
    def validate(self, source: str) -> bool:
        """
        Validate the source.
        
        Args:
            source: Source identifier to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        pass
    
    def _is_binary_file(self, path: str) -> bool:
        """
        Check if a file is binary.
        
        Args:
            path: File path
            
        Returns:
            bool: True if binary, False otherwise
        """
        # List of file extensions to ignore
        binary_extensions = {
            # Images
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.ico', '.svg',
            # Audio/Video
            '.mp3', '.wav', '.mp4', '.avi', '.mov', '.flv', '.wmv',
            # Archives
            '.zip', '.tar', '.gz', '.rar', '.7z',
            # Documents
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            # Executables
            '.exe', '.dll', '.so', '.dylib',
            # Other binary formats
            '.bin', '.dat', '.db', '.sqlite', '.pyc', '.pyo',
        }
        
        return any(path.lower().endswith(ext) for ext in binary_extensions)


class RepoLoaderFactory:
    """Factory for creating repository loaders."""
    
    _loaders: Dict[str, Type[RepoLoader]] = {}
    
    @classmethod
    def register(cls, source_type: str, loader_class: Type[RepoLoader]):
        """
        Register a loader class for a source type.
        
        Args:
            source_type: Type of source ("github", "zip", or "local")
            loader_class: RepoLoader subclass to register
        """
        cls._loaders[source_type] = loader_class
    
    @classmethod
    def get_loader(cls, source_type: str) -> Optional[RepoLoader]:
        """
        Get a loader for the specified source type.
        
        Args:
            source_type: Type of source ("github", "zip", or "local")
            
        Returns:
            RepoLoader: Instance of the appropriate loader class, or None if not found
        """
        loader_class = cls._loaders.get(source_type)
        if loader_class:
            return loader_class()
        return None 