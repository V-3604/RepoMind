import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from bson import ObjectId
import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from config import MONGODB_URI, MONGODB_DB


class DBClient:
    """Database client for MongoDB interactions."""
    
    def __init__(self, uri: str = None, db_name: str = None):
        """
        Initialize the database client.
        
        Args:
            uri: MongoDB URI (defaults to config)
            db_name: Database name (defaults to config)
        """
        self.logger = logging.getLogger(__name__)
        self.uri = uri or MONGODB_URI
        self.db_name = db_name or MONGODB_DB
        
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            self.db = self.client[self.db_name]
            
            # Check connection
            self.client.admin.command('ping')
            self.logger.info(f"Connected to MongoDB at {self.uri}")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            self.logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    def get_repository(self, repo_id: str) -> Optional[Dict]:
        """
        Get a repository by ID.
        
        Args:
            repo_id: Repository ID
            
        Returns:
            dict: Repository data or None if not found
        """
        try:
            # Try different ways to find the repository
            repo = None
            
            # Try with the original ID first
            repo = self.db.repositories.find_one({"_id": repo_id})
            
            # If not found and ID is a valid ObjectId, try with ObjectId
            if not repo and ObjectId.is_valid(repo_id):
                repo = self.db.repositories.find_one({"_id": ObjectId(repo_id)})
            
            if repo:
                # Convert ObjectId to string for serialization
                if "_id" in repo and isinstance(repo["_id"], ObjectId):
                    repo["_id"] = str(repo["_id"])
                
                # If created_at is a datetime, convert to string
                if "created_at" in repo and isinstance(repo["created_at"], datetime):
                    repo["created_at"] = repo["created_at"].isoformat()
            
                # Convert repository data to Repository object
                from src.backend.models.repository import Repository
                return Repository(**repo)
                
            self.logger.warning(f"Repository not found: {repo_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting repository {repo_id}: {str(e)}")
            return None
    
    def save_repository(self, repository) -> str:
        """
        Save a repository to the database.
        
        Args:
            repository: Repository object
            
        Returns:
            str: Repository ID
        """
        try:
            # Convert to dict
            repo_dict = repository.dict(by_alias=True)
            
            # Remove ID if None
            if "_id" in repo_dict and repo_dict["_id"] is None:
                del repo_dict["_id"]
            
            # Insert into database
            result = self.db.repositories.insert_one(repo_dict)
            
            # Return ID
            return str(result.inserted_id)
            
        except Exception as e:
            self.logger.error(f"Error saving repository: {str(e)}")
            raise
    
    def update_repository_status(self, repo_id: str, status: str) -> bool:
        """
        Update the status of a repository.
        
        Args:
            repo_id: Repository ID
            status: New status
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert string ID to ObjectId if needed
            if not isinstance(repo_id, ObjectId) and ObjectId.is_valid(repo_id):
                repo_id = ObjectId(repo_id)
                
            # Update status
            self.db.repositories.update_one(
                {"_id": repo_id},
                {"$set": {"status": status}}
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating repository status: {str(e)}")
            return False
    
    def update_repository(self, repo_id: str, **kwargs) -> bool:
        """
        Update repository fields.
        
        Args:
            repo_id: Repository ID
            **kwargs: Fields to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert string ID to ObjectId if needed
            if not isinstance(repo_id, ObjectId) and ObjectId.is_valid(repo_id):
                repo_id = ObjectId(repo_id)
                
            # Update fields
            self.db.repositories.update_one(
                {"_id": repo_id},
                {"$set": kwargs}
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating repository: {str(e)}")
            return False
    
    def save_file(self, repository_id: str, file_path: str, language: str, 
                 content: str, functions: List[Dict], documentation: List[Dict], 
                 summary: str = "") -> bool:
        """
        Save a file to the database.
        
        Args:
            repository_id: Repository ID
            file_path: File path
            language: Programming language
            content: File content
            functions: Extracted functions
            documentation: Extracted documentation
            summary: File summary
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert string ID to ObjectId if needed
            if not isinstance(repository_id, ObjectId) and ObjectId.is_valid(repository_id):
                repository_id = ObjectId(repository_id)
                
            # Create file document
            file_doc = {
                "repo_id": repository_id,
                "path": file_path,
                "language": language,
                "content": content,
                "functions": functions,
                "documentation": documentation,
                "summary": summary,
                "created_at": datetime.utcnow()
            }
            
            # Insert or update
            self.db.files.update_one(
                {"repo_id": repository_id, "path": file_path},
                {"$set": file_doc},
                upsert=True
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving file {file_path}: {str(e)}")
            return False 