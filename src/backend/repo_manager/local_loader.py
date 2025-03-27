"""
Local repository loader.
Handles loading repositories from local file system.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any

from src.backend.repo_manager.repo_loader import RepoLoader, RepoLoaderFactory


class LocalLoader(RepoLoader):
    """Loader for local repositories."""
    
    def __init__(self):
        """Initialize the local loader."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
    
    def validate(self, source: str) -> bool:
        """
        Validate a local directory path.
        
        Args:
            source: Local directory path
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Check if the path exists and is a directory
        if not os.path.exists(source) or not os.path.isdir(source):
            return False
        
        # Check if the directory is accessible
        if not os.access(source, os.R_OK):
            return False
        
        # Check size
        total_size = 0
        for dirpath, _, filenames in os.walk(source):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
        
        if total_size > self.max_size_bytes:
            self.logger.warning(
                "Repository too large: %s (%d bytes > %d bytes)",
                source, total_size, self.max_size_bytes
            )
            return False
        
        return True
    
    def load(self, source: str) -> Dict[str, Any]:
        """
        Load a repository from a local directory.
        
        Args:
            source: Local directory path
            
        Returns:
            dict: Repository metadata and file contents
        """
        if not self.validate(source):
            raise ValueError(f"Invalid local repository: {source}")
        
        # Use the directory name as the repository name
        repo_name = os.path.basename(os.path.normpath(source))
        
        # Get repository info
        repo_info = {
            "name": repo_name,
            "source": source,
            "source_type": "local",
            "files": {}
        }
        
        # Process all files in the directory
        for root, _, files in os.walk(source):
            for file in files:
                # Skip .git directory
                if ".git" in Path(root).parts:
                    continue
                
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, source)
                
                # Skip binary files
                if self._is_binary_file(rel_path):
                    continue
                
                # Get file size
                file_size = os.path.getsize(file_path)
                
                # Skip large files
                if file_size > 1024 * 1024:  # 1MB
                    self.logger.warning("Skipping large file: %s (%d bytes)", rel_path, file_size)
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        repo_info["files"][rel_path] = {
                            "content": content,
                            "size_bytes": file_size,
                            "line_count": content.count('\n') + 1
                        }
                except UnicodeDecodeError:
                    # Skip files that can't be decoded as text
                    self.logger.warning("Skipping binary file: %s", rel_path)
                    continue
                except Exception as e:
                    self.logger.warning("Error reading file %s: %s", rel_path, str(e))
                    continue
        
        return repo_info


# Register the loader with the factory
RepoLoaderFactory.register("local", LocalLoader) 