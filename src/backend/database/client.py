from pymongo import MongoClient
from config import MONGODB_URI, MONGODB_DB_NAME

class DatabaseClient:
    """Client for MongoDB database operations."""
    
    def __init__(self, uri=None, db_name=None):
        """Initialize the database client."""
        self.uri = uri or MONGODB_URI
        self.db_name = db_name or MONGODB_DB_NAME
        self.client = MongoClient(self.uri)
        self.db = self.client[self.db_name]
    
    def close(self):
        """Close the database connection."""
        if self.client:
            self.client.close()