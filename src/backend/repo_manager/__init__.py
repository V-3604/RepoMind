"""
Repository Manager Module
"""

from src.backend.repo_manager.repo_loader_factory import RepoLoaderFactory
from src.backend.repo_manager.github_loader import GitHubLoader
from src.backend.repo_manager.local_loader import LocalLoader
from src.backend.repo_manager.zip_loader import ZipLoader

# Import the main loader class
from src.backend.repo_manager.repo_loader import RepoLoader
