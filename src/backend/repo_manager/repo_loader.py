"""
Repository loading interface.
Handles loading repositories from different sources (GitHub, ZIP, local).
"""

import os
import uuid
import logging
import tempfile
from typing import Dict, Any, Optional
from bson import ObjectId
from datetime import datetime

# Remove circular imports
# from src.backend.repo_manager.github_loader import GitHubLoader
# from src.backend.repo_manager.zip_loader import ZipLoader
# from src.backend.repo_manager.local_loader import LocalLoader

# Import the factory
from src.backend.repo_manager.repo_loader_factory import RepoLoaderFactory


class RepoLoader:
    """Repository loader class for loading repositories from various sources."""
    
    def __init__(self, db_client=None):
        """
        Initialize the repository loader.
        
        Args:
            db_client: MongoDB client instance
        """
        self.db_client = db_client
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing RepoLoader")
    
    async def load_from_github(self, name: str, github_url: str, branch: Optional[str] = None) -> str:
        """
        Load a repository from GitHub.
        
        Args:
            name: Repository name
            github_url: GitHub repository URL
            branch: Optional branch name
            
        Returns:
            str: Repository ID
        """
        try:
            self.logger.info(f"Loading repository from GitHub: {github_url}")
            
            # Use the factory to get the GitHub loader
            github_loader_class = RepoLoaderFactory.get_loader("github")
            if not github_loader_class:
                raise ValueError(f"GitHub loader not found")
                
            github_loader = github_loader_class()
            
            # Validate GitHub URL
            if not github_loader.validate(github_url):
                raise ValueError(f"Invalid GitHub URL: {github_url}")
            
            # Create temporary directory
            temp_dir = tempfile.mkdtemp()
            
            # Load repository data
            repo_data = github_loader.load(github_url, temp_dir)
            
            # Set repository name if provided
            if name:
                repo_data["name"] = name
            
            # Generate repository ID
            repo_id = str(ObjectId())
            
            # Add metadata
            repo_data["_id"] = repo_id
            repo_data["status"] = "processing"
            
            # Store in database
            self.db_client.db.repositories.insert_one(repo_data)
            self.logger.info(f"Repository stored in database with ID {repo_id}")
            
            return repo_id
            
        except Exception as e:
            self.logger.error(f"Error loading repository from GitHub: {str(e)}")
            raise
    
    async def load_from_zip(self, name: str, zip_file) -> str:
        """
        Load a repository from a ZIP file.
        
        Args:
            name: Repository name
            zip_file: ZIP file upload
            
        Returns:
            str: Repository ID
        """
        try:
            self.logger.info(f"Loading repository from ZIP: {zip_file.filename}")
            
            # Use the factory to get the ZIP loader
            zip_loader_class = RepoLoaderFactory.get_loader("zip")
            if not zip_loader_class:
                raise ValueError(f"ZIP loader not found")
                
            zip_loader = zip_loader_class()
            
            # Create temporary directory
            temp_dir = tempfile.mkdtemp()
            
            # Load repository data
            repo_data = zip_loader.load(zip_file, temp_dir)
            
            # Set repository name if provided
            if name:
                repo_data["name"] = name
            
            # Generate repository ID
            repo_id = str(ObjectId())
            
            # Add metadata
            repo_data["_id"] = repo_id
            repo_data["status"] = "processing"
            repo_data["source_type"] = "ZIP"
            repo_data["created_at"] = datetime.utcnow()
            
            # Store in database
            self.db_client.db.repositories.insert_one(repo_data)
            self.logger.info(f"Repository stored in database with ID {repo_id}")
            
            return repo_id
            
        except Exception as e:
            self.logger.error(f"Error loading repository from ZIP: {str(e)}")
            raise
    
    async def load_from_local(self, name: str, local_path: str) -> str:
        """
        Load a repository from a local path.
        
        Args:
            name: Repository name
            local_path: Local repository path
            
        Returns:
            str: Repository ID
        """
        try:
            self.logger.info(f"Loading repository from local path: {local_path}")
            
            # Use the factory to get the local loader
            local_loader_class = RepoLoaderFactory.get_loader("local")
            if not local_loader_class:
                raise ValueError(f"Local loader not found")
                
            local_loader = local_loader_class()
            
            # Validate local path
            if not local_loader.validate(local_path):
                raise ValueError(f"Invalid local path: {local_path}")
            
            # Load repository data
            repo_data = local_loader.load(local_path)
            
            # Set repository name if provided
            if name:
                repo_data["name"] = name
            
            # Generate repository ID
            repo_id = str(ObjectId())
            
            # Add metadata
            repo_data["_id"] = repo_id
            repo_data["status"] = "processing"
            repo_data["source_type"] = "Local"
            repo_data["created_at"] = datetime.utcnow()
            
            # Store in database
            self.db_client.db.repositories.insert_one(repo_data)
            self.logger.info(f"Repository stored in database with ID {repo_id}")
            
            return repo_id
            
        except Exception as e:
            self.logger.error(f"Error loading repository from local path: {str(e)}")
            raise
    
    async def _process_files(self, repo_id: str, files: Dict[str, Any]) -> None:
        """
        Process files and store them in the database.
        
        Args:
            repo_id: Repository ID
            files: Dictionary of files
        """
        try:
            # Store files in the database
            batch_size = 50
            file_entries = []
            
            for path, file_data in files.items():
                file_entry = {
                    "repo_id": repo_id,
                    "path": path,
                    "content": file_data.get("content", ""),
                    "size_bytes": file_data.get("size_bytes", 0),
                    "line_count": file_data.get("line_count", 0)
                }
                
                file_entries.append(file_entry)
                
                # Insert in batches to avoid memory issues
                if len(file_entries) >= batch_size:
                    if file_entries:
                        self.db_client.db.files.insert_many(file_entries)
                    file_entries = []
            
            # Insert remaining files
            if file_entries:
                self.db_client.db.files.insert_many(file_entries)
                
        except Exception as e:
            self.logger.error(f"Error processing repository files: {str(e)}")
            
            # Update repository status to failed
            self.db_client.db.repositories.update_one(
                {"_id": repo_id},
                {"$set": {"status": "failed"}}
            )
            
            raise 