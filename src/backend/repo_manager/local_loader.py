"""
Local repository loader.
Handles loading repositories from local file system.
"""

import os
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, BinaryIO

from src.backend.repo_manager.repo_loader import RepoLoader, RepoLoaderFactory


@RepoLoaderFactory.register("local")
class LocalLoader:
    """
    Local repository loader
    """
    
    def __init__(self):
        """
        Initialize the local loader
        """
        self.logger = logging.getLogger(__name__)
    
    def validate(self, path: str) -> bool:
        """
        Validate a local path
        
        Args:
            path: Local path
            
        Returns:
            bool: True if valid, False otherwise
        """
        return os.path.exists(path) and os.path.isdir(path)
    
    def load(self, file_object: BinaryIO, target_dir: str = None) -> Dict[str, Any]:
        """
        Load a local repository from a file
        
        Args:
            file_object: File object (usually from a form upload)
            target_dir: Target directory
            
        Returns:
            dict: Repository data
        """
        try:
            self.logger.info("Loading local repository")
            
            # Create target directory if not provided
            if not target_dir:
                target_dir = tempfile.mkdtemp()
            
            # Save uploaded file
            temp_file = os.path.join(target_dir, "upload.zip")
            with open(temp_file, "wb") as f:
                shutil.copyfileobj(file_object, f)
            
            # Extract file if it's a zip
            if temp_file.endswith(".zip"):
                import zipfile
                with zipfile.ZipFile(temp_file, "r") as zip_ref:
                    zip_ref.extractall(target_dir)
                
                # Remove zip file
                os.remove(temp_file)
            
            # Get repository info
            repo_name = os.path.basename(target_dir)
            
            # Build repository data
            repo_data = {
                "name": repo_name,
                "type": "local",
                "local_path": target_dir,
                "original_file": getattr(file_object, "filename", "unknown")
            }
            
            return repo_data
            
        except Exception as e:
            self.logger.error(f"Error loading local repository: {str(e)}")
            raise 