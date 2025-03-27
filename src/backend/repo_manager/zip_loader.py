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
from typing import Dict, Any

from config import TEMP_DIR
from src.backend.repo_manager.repo_loader import RepoLoader, RepoLoaderFactory


class ZipLoader(RepoLoader):
    """Loader for ZIP repositories."""
    
    def __init__(self):
        """Initialize the ZIP loader."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
    
    def validate(self, source: str) -> bool:
        """
        Validate a ZIP file path.
        
        Args:
            source: Path to ZIP file
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not os.path.exists(source):
            return False
        
        if not source.lower().endswith('.zip'):
            return False
        
        try:
            with zipfile.ZipFile(source, 'r') as zip_ref:
                # Check if the zip file is valid
                if zip_ref.testzip() is not None:
                    return False
                
                # Check size
                total_size = sum(info.file_size for info in zip_ref.infolist())
                if total_size > self.max_size_bytes:
                    self.logger.warning(
                        "ZIP file too large: %s (%d bytes > %d bytes)",
                        source, total_size, self.max_size_bytes
                    )
                    return False
                
                return True
        except zipfile.BadZipFile:
            return False
    
    def load(self, source: str) -> Dict[str, Any]:
        """
        Extract a ZIP file and load its contents.
        
        Args:
            source: Path to ZIP file
            
        Returns:
            dict: Repository metadata and file contents
        """
        if not self.validate(source):
            raise ValueError(f"Invalid ZIP file: {source}")
        
        # Create a temporary directory for extraction
        extract_dir = TEMP_DIR / f"zip_{os.urandom(4).hex()}"
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Extract the ZIP file
            with zipfile.ZipFile(source, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Determine repository name from ZIP file name
            repo_name = os.path.splitext(os.path.basename(source))[0]
            
            # Get repository info
            repo_info = {
                "name": repo_name,
                "source": source,
                "source_type": "zip",
                "files": {}
            }
            
            # Process all files in the extracted directory
            for root, _, files in os.walk(extract_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, extract_dir)
                    
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
            
            return repo_info
        
        except Exception as e:
            self.logger.error("Error loading ZIP repository: %s", str(e))
            raise
        finally:
            # Clean up the temporary directory
            try:
                shutil.rmtree(extract_dir)
            except Exception as e:
                self.logger.error("Error cleaning up extraction directory: %s", str(e))


# Register the loader with the factory
RepoLoaderFactory.register("zip", ZipLoader) 