"""
MongoDB client for RepoMind.
Handles database connections and operations.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from bson import ObjectId

from config import MONGODB_URI, MONGODB_DB, MONGODB_TIMEOUT_MS

logger = logging.getLogger(__name__)

class MongoDBClient:
    """MongoDB client for RepoMind."""
    
    def __init__(self):
        """Initialize the MongoDB client."""
        self.client = None
        self.db = None
        self.uri = MONGODB_URI
        self.db_name = MONGODB_DB
        self.timeout_ms = MONGODB_TIMEOUT_MS
        logger.info(f"Initializing MongoDB client with URI: {self.uri}, DB: {self.db_name}")
    
    def connect(self) -> bool:
        """
        Connect to MongoDB.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            logger.info(f"Connecting to MongoDB at {self.uri}")
            # Set serverSelectionTimeoutMS to fail quickly if the server is not available
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=self.timeout_ms)
            
            # Force connection to verify it works
            self.client.admin.command('ping')
            
            # Set database
            self.db = self.client[self.db_name]
            
            logger.info(f"Successfully connected to MongoDB database '{self.db_name}'")
            return True
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            self.client = None
            self.db = None
            return False
        except Exception as e:
            logger.error(f"Unexpected error when connecting to MongoDB: {str(e)}")
            self.client = None
            self.db = None
            return False
    
    def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            logger.info("Disconnected from MongoDB")
    
    def check_connection(self) -> bool:
        """
        Check if the connection to MongoDB is active.
        
        Returns:
            bool: True if connection is active, False otherwise
        """
        if not self.client:
            logger.warning("MongoDB client is not initialized")
            return False
        
        try:
            # Try to ping the server
            self.client.admin.command('ping')
            logger.debug("MongoDB connection is active")
            return True
        except Exception as e:
            logger.error(f"MongoDB connection check failed: {str(e)}")
            return False
    
    def get_collection(self, collection_name: str):
        """
        Get a collection from the database.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Collection: MongoDB collection
        """
        if not self.db:
            logger.warning(f"Cannot get collection '{collection_name}': No database connection")
            return None
        
        return self.db[collection_name]
    
    def __str__(self) -> str:
        """String representation of the MongoDB client."""
        connection_status = "Connected" if self.check_connection() else "Disconnected"
        return f"MongoDBClient({connection_status}, URI={self.uri}, DB={self.db_name})"

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
            logger.info("Stored repository with ID: %s", repo_id)
            return repo_id
        except Exception as e:
            logger.error("Failed to store repository: %s", str(e))
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
            # Try to find by string ID first
            repo = self.db.repositories.find_one({"_id": repo_id})
            if not repo:
                # Try with ObjectId
                repo = self.db.repositories.find_one({"_id": ObjectId(repo_id)})
            
            if repo and isinstance(repo["_id"], ObjectId):
                repo["_id"] = str(repo["_id"])
            return repo
        except Exception as e:
            logger.error("Failed to retrieve repository %s: %s", repo_id, str(e))
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
                if isinstance(repo["_id"], ObjectId):
                    repo["_id"] = str(repo["_id"])
            
            return repos
        except Exception as e:
            logger.error("Failed to list repositories: %s", str(e))
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
            logger.info("Stored query with ID: %s", query_id)
            return query_id
        except Exception as e:
            logger.error("Failed to store query: %s", str(e))
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
                if isinstance(query["_id"], ObjectId):
                    query["_id"] = str(query["_id"])
            
            return queries
        except Exception as e:
            logger.error("Failed to retrieve query history: %s", str(e))
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
            # Try to delete with string ID first
            repo_result = self.db.repositories.delete_one({"_id": repo_id})
            if repo_result.deleted_count == 0:
                # Try with ObjectId
                repo_result = self.db.repositories.delete_one({"_id": ObjectId(repo_id)})
            
            # Delete associated queries
            query_result = self.db.queries.delete_many({"repo_id": repo_id})
            
            logger.info(
                "Deleted repository %s and %d associated queries",
                repo_id, query_result.deleted_count
            )
            
            return repo_result.deleted_count > 0
        except Exception as e:
            logger.error("Failed to delete repository %s: %s", repo_id, str(e))
            return False 