"""
ZIP repository loader.
Handles loading repositories from ZIP files.
"""

import os
import zipfile
import tempfile
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, BinaryIO

from config import TEMP_DIR
from src.backend.repo_manager.repo_loader import RepoLoader, RepoLoaderFactory


@RepoLoaderFactory.register("zip")
class ZipLoader:
    """
    ZIP repository loader
    """
    
    def __init__(self):
        """
        Initialize the ZIP loader
        """
        self.logger = logging.getLogger(__name__)
    
    def validate(self, file_path: str) -> bool:
        """
        Validate a ZIP file
        
        Args:
            file_path: Path to ZIP file
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not os.path.isfile(file_path):
            return False
            
        if not file_path.lower().endswith(".zip"):
            return False
            
        try:
            with zipfile.ZipFile(file_path) as zf:
                return True
        except zipfile.BadZipFile:
            return False
    
    def load(self, file_object: BinaryIO, target_dir: str = None) -> Dict[str, Any]:
        """
        Load a repository from a ZIP file
        
        Args:
            file_object: File object (usually from a form upload)
            target_dir: Target directory
            
        Returns:
            dict: Repository data
        """
        try:
            self.logger.info("Loading repository from ZIP file")
            
            # Create target directory if not provided
            if not target_dir:
                target_dir = tempfile.mkdtemp()
            
            # Save uploaded file
            temp_file = os.path.join(target_dir, "upload.zip")
            with open(temp_file, "wb") as f:
                shutil.copyfileobj(file_object, f)
            
            # Extract ZIP file
            with zipfile.ZipFile(temp_file, "r") as zip_ref:
                zip_ref.extractall(target_dir)
            
            # Clean up the uploaded file
            os.remove(temp_file)
            
            # Get repository info
            repo_name = os.path.basename(target_dir)
            
            # Build repository data
            repo_data = {
                "name": repo_name,
                "type": "zip",
                "local_path": target_dir,
                "original_file": getattr(file_object, "filename", "unknown")
            }
            
            return repo_data
            
        except Exception as e:
            self.logger.error(f"Error loading ZIP repository: {str(e)}")
            raise 