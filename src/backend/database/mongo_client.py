"""
MongoDB client for RepoMind.
Handles connections and operations with the MongoDB database.
"""

import logging
from typing import Dict, List, Any, Optional
from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError

from config import MONGODB_URI, MONGODB_DB_NAME


class MongoDBClient:
    """MongoDB client for RepoMind."""
    
    def __init__(self, connection_string: str = MONGODB_URI):
        """
        Initialize MongoDB connection.
        
        Args:
            connection_string: MongoDB connection URI
        """
        self.connection_string = connection_string
        self.client = None
        self.db = None
        self.logger = logging.getLogger(__name__)
    
    def connect(self) -> bool:
        """
        Connect to MongoDB.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[MONGODB_DB_NAME]
            
            # Test the connection
            self.client.admin.command('ping')
            self.logger.info("Connected to MongoDB: %s", MONGODB_DB_NAME)
            return True
        except ConnectionFailure as e:
            self.logger.error("Failed to connect to MongoDB: %s", str(e))
            return False
    
    def store_repo(self, repo_data: Dict[str, Any]) -> str:
        """
        Store repository data.
        
        Args:
            repo_data: Repository metadata and analysis
            
        Returns:
            str: Repository ID
        """
        try:
            # Remove _id if it exists to let MongoDB generate one
            if "_id" in repo_data:
                del repo_data["_id"]
            
            result = self.db.repositories.insert_one(repo_data)
            repo_id = str(result.inserted_id)
            self.logger.info("Stored repository with ID: %s", repo_id)
            return repo_id
        except PyMongoError as e:
            self.logger.error("Failed to store repository: %s", str(e))
            raise
    
    def get_repo(self, repo_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve repository data.
        
        Args:
            repo_id: Repository ID
            
        Returns:
            dict: Repository data or None if not found
        """
        try:
            repo = self.db.repositories.find_one({"_id": ObjectId(repo_id)})
            if repo:
                repo["_id"] = str(repo["_id"])
            return repo
        except PyMongoError as e:
            self.logger.error("Failed to retrieve repository %s: %s", repo_id, str(e))
            return None
    
    def list_repos(self) -> List[Dict[str, Any]]:
        """
        List all repositories.
        
        Returns:
            list: List of repository metadata
        """
        try:
            repos = list(self.db.repositories.find({}, {
                "_id": 1,
                "name": 1,
                "source": 1,
                "source_type": 1,
                "created_at": 1
            }))
            
            # Convert ObjectId to string
            for repo in repos:
                repo["_id"] = str(repo["_id"])
            
            return repos
        except PyMongoError as e:
            self.logger.error("Failed to list repositories: %s", str(e))
            return []
    
    def store_query(self, repo_id: str, query: str, response: Dict[str, Any]) -> str:
        """
        Store a query and its response.
        
        Args:
            repo_id: Repository ID
            query: User's query
            response: System's response
            
        Returns:
            str: Query ID
        """
        try:
            query_doc = {
                "repo_id": repo_id,
                "query": query,
                "response": response,
                "timestamp": self.db.client.server_info().get("localTime", None)
            }
            result = self.db.queries.insert_one(query_doc)
            query_id = str(result.inserted_id)
            self.logger.info("Stored query with ID: %s", query_id)
            return query_id
        except PyMongoError as e:
            self.logger.error("Failed to store query: %s", str(e))
            raise
    
    def get_query_history(self, repo_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve query history for a repository.
        
        Args:
            repo_id: Repository ID
            
        Returns:
            list: List of query-response pairs
        """
        try:
            queries = list(self.db.queries.find(
                {"repo_id": repo_id},
                {"_id": 1, "query": 1, "response": 1, "timestamp": 1}
            ).sort("timestamp", -1))
            
            # Convert ObjectId to string
            for query in queries:
                query["_id"] = str(query["_id"])
            
            return queries
        except PyMongoError as e:
            self.logger.error("Failed to retrieve query history: %s", str(e))
            return []
    
    def delete_repo(self, repo_id: str) -> bool:
        """
        Delete a repository and its query history.
        
        Args:
            repo_id: Repository ID
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            # Delete repository
            repo_result = self.db.repositories.delete_one({"_id": ObjectId(repo_id)})
            
            # Delete associated queries
            query_result = self.db.queries.delete_many({"repo_id": repo_id})
            
            self.logger.info(
                "Deleted repository %s and %d associated queries",
                repo_id, query_result.deleted_count
            )
            
            return repo_result.deleted_count > 0
        except PyMongoError as e:
            self.logger.error("Failed to delete repository %s: %s", repo_id, str(e))
            return False
    
    def close(self):
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
            self.logger.info("MongoDB connection closed") 