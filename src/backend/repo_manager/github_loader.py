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

from config import TEMP_DIR
from src.backend.repo_manager.repo_loader import RepoLoader, RepoLoaderFactory


class GitHubLoader(RepoLoader):
    """Loader for GitHub repositories."""
    
    def __init__(self):
        """Initialize the GitHub loader."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
    
    def validate(self, source: str) -> bool:
        """
        Validate a GitHub URL.
        
        Args:
            source: GitHub repository URL
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Simple pattern for GitHub URLs
        pattern = r'^https?://github\.com/[^/]+/[^/]+/?.*$'
        return bool(re.match(pattern, source))
    
    def parse_github_url(self, url: str) -> Tuple[str, str, Optional[str]]:
        """
        Parse a GitHub URL into owner, repo name, and optional branch.
        
        Args:
            url: GitHub repository URL
            
        Returns:
            tuple: (owner, repo_name, branch)
        """
        # Extract owner and repo name
        pattern = r'github\.com/([^/]+)/([^/]+)/?.*'
        match = re.search(pattern, url)
        
        if not match:
            raise ValueError(f"Invalid GitHub URL: {url}")
        
        owner, repo = match.groups()
        
        # Extract branch if specified in the URL
        branch_pattern = r'github\.com/[^/]+/[^/]+/tree/([^/]+)'
        branch_match = re.search(branch_pattern, url)
        branch = branch_match.group(1) if branch_match else None
        
        # Remove .git suffix if present
        if repo.endswith('.git'):
            repo = repo[:-4]
        
        return owner, repo, branch
    
    def load(self, source: str) -> Dict[str, Any]:
        """
        Clone a GitHub repository and load its contents.
        
        Args:
            source: GitHub repository URL
            
        Returns:
            dict: Repository metadata and file contents
        """
        if not self.validate(source):
            raise ValueError(f"Invalid GitHub URL: {source}")
        
        owner, repo_name, branch = self.parse_github_url(source)
        
        # Create a unique directory name
        repo_dir = TEMP_DIR / f"{owner}_{repo_name}_{os.urandom(4).hex()}"
        repo_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("Cloning repository %s/%s to %s", owner, repo_name, repo_dir)
        
        try:
            # Clone the repository
            git_repo = git.Repo.clone_from(source, repo_dir)
            
            # Checkout specific branch if provided
            if branch:
                git_repo.git.checkout(branch)
            
            # Get repository info
            repo_info = {
                "name": repo_name,
                "source": source,
                "source_type": "github",
                "owner": owner,
                "files": {}
            }
            
            # Process all files in the repository
            for root, _, files in os.walk(repo_dir):
                for file in files:
                    # Skip .git directory
                    if ".git" in Path(root).parts:
                        continue
                    
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, repo_dir)
                    
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
        
        except (GitCommandError, InvalidGitRepositoryError) as e:
            self.logger.error("Error cloning repository: %s", str(e))
            raise
        finally:
            # Clean up the temporary directory
            try:
                git.rmtree(repo_dir)
            except Exception as e:
                self.logger.error("Error cleaning up repository directory: %s", str(e))


# Register the loader with the factory
RepoLoaderFactory.register("github", GitHubLoader) 