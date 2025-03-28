"""
GitHub repository loader.
Handles loading repositories from GitHub URLs.
"""

import os
import re
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import git
from git.exc import GitCommandError, InvalidGitRepositoryError
import requests
from github import Github
from github.GithubException import GithubException

from config import TEMP_DIR
# Fix circular import
# from src.backend.repo_manager.repo_loader import RepoLoader, RepoLoaderFactory
from src.backend.repo_manager.repo_loader_factory import RepoLoaderFactory


# Base class definition to avoid circular import
class BaseRepoLoader:
    """Base class for repository loaders."""
    
    def __init__(self):
        """Initialize the base loader."""
        self.logger = logging.getLogger(__name__)
    
    def _is_binary_file(self, file_path: str) -> bool:
        """
        Check if a file is binary.
        
        Args:
            file_path: Path to the file
            
        Returns:
            bool: True if binary, False otherwise
        """
        # Common binary file extensions
        binary_extensions = {
            '.pyc', '.so', '.o', '.a', '.lib', '.dll', '.exe', '.bin',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.tif', '.tiff',
            '.zip', '.tar', '.gz', '.bz2', '.xz', '.rar', '.7z',
            '.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx',
            '.db', '.sqlite', '.db3',
        }
        
        _, ext = os.path.splitext(file_path.lower())
        return ext in binary_extensions


@RepoLoaderFactory.register("github")
class GitHubLoader:
    """
    GitHub repository loader
    """
    
    def __init__(self):
        """
        Initialize the GitHub loader
        """
        self.logger = logging.getLogger(__name__)
    
    def validate(self, url: str) -> bool:
        """
        Validate a GitHub URL
        
        Args:
            url: GitHub repository URL
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            if not url.startswith(("http://github.com/", "https://github.com/")):
                return False
                
            # Extract owner and repo name
            parts = url.strip("/").split("/")
            if len(parts) < 5:
                return False
                
            owner = parts[-2]
            repo = parts[-1]
            
            # Validate that repo exists
            response = requests.head(f"https://github.com/{owner}/{repo}")
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"Error validating GitHub URL: {str(e)}")
            return False
    
    def load(self, url: str, target_dir: str = None) -> Dict[str, Any]:
        """
        Load a GitHub repository
        
        Args:
            url: GitHub repository URL
            target_dir: Target directory for cloning
            
        Returns:
            dict: Repository data
        """
        try:
            self.logger.info(f"Loading GitHub repository from {url}")
            
            # Extract owner and repo name
            parts = url.strip("/").split("/")
            owner = parts[-2]
            repo_name = parts[-1]
            
            # Create temporary directory if not provided
            if not target_dir:
                target_dir = tempfile.mkdtemp()
            
            # Clone repository
            clone_url = f"https://github.com/{owner}/{repo_name}.git"
            os.system(f"git clone {clone_url} {target_dir}")
            
            # Get repository info
            g = Github()
            repo = g.get_repo(f"{owner}/{repo_name}")
            
            # Build repository data
            repo_data = {
                "name": repo_name,
                "type": "github",
                "url": url,
                "local_path": target_dir,
                "owner": owner,
                "description": repo.description,
                "stars": repo.stargazers_count,
                "language": repo.language
            }
            
            return repo_data
            
        except GithubException as e:
            self.logger.error(f"GitHub API error: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error loading GitHub repository: {str(e)}")
            raise 