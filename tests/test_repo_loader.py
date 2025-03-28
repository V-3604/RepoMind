"""
Unit tests for the RepoLoader class.
"""

import pytest
from unittest.mock import patch, MagicMock
from bson import ObjectId

# Import just the base class to avoid circular imports
from src.backend.repo_manager.repo_loader import RepoLoader
from src.backend.repo_manager.repo_loader_factory import RepoLoaderFactory


class TestRepoLoader:
    """Tests for the RepoLoader class."""
    
    @pytest.fixture
    def repo_loader(self):
        """Create a RepoLoader instance for testing."""
        db_client = MagicMock()
        return RepoLoader(db_client=db_client)
    
    def test_init(self, repo_loader):
        """Test RepoLoader initialization."""
        assert repo_loader.db_client is not None
        assert repo_loader.logger is not None


class TestRepoLoaderFactory:
    """Tests for the RepoLoaderFactory class."""
    
    def test_register_and_get_loader(self):
        """Test registering and retrieving a loader."""
        # Create a mock loader class
        MockLoader = MagicMock()
        
        # Register the loader
        RepoLoaderFactory.register("test", MockLoader)
        
        # Get the loader
        loader = RepoLoaderFactory.get_loader("test")
        
        # Verify
        assert loader == MockLoader
    
    def test_get_loader_invalid_type(self):
        """Test getting a loader for an invalid type."""
        with pytest.raises(ValueError):
            RepoLoaderFactory.get_loader("invalid_type") 