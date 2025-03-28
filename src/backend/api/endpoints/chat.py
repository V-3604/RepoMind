"""
Chat endpoints for RepoMind.
Handles API requests for chat functionality.
"""

import logging
import traceback
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from bson import ObjectId

from src.backend.database.db_client import DBClient
from src.backend.llm.query_processor import QueryProcessor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Use the db_client from the main application
from src.backend.api.routes import db_client

# Initialize query processor
query_processor = QueryProcessor(db_client)


class ChatRequest(BaseModel):
    """Request model for chat messages."""
    message: str
    repo_id: Optional[str] = None
    context: Dict[str, Any] = {}


class QueryRequest(BaseModel):
    """Request model for a repository query."""
    query: str
    file_path: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Response model for chat messages."""
    text: str
    code: Optional[str] = None
    referenced_files: list = []


@router.post("/{repo_id}")
async def process_chat_message(repo_id: str, request: ChatRequest):
    """
    Process a chat message for a specific repository.
    
    Args:
        repo_id: Repository ID
        request: Chat message request
        
    Returns:
        ChatResponse: Response to the chat message
    """
    try:
        logger.info(f"Processing chat message for repository {repo_id}")
        
        # Check if repository exists
        repo = None
        try:
            # Try with ObjectId first if valid
            if ObjectId.is_valid(repo_id):
                repo = db_client.db.repositories.find_one({"_id": ObjectId(repo_id)})
                
            # If not found, try with string ID
            if not repo:
                repo = db_client.db.repositories.find_one({"_id": repo_id})
                
            if not repo:
                raise HTTPException(status_code=404, detail="Repository not found")
        except Exception as e:
            logger.error(f"Error finding repository: {str(e)}")
            raise HTTPException(status_code=404, detail=f"Repository not found: {str(e)}")
        
        # Process the query - use message field as the query for compatibility with frontend
        response = await query_processor.process_query(
            repo_id,
            request.message,
            context=request.context
        )
        
        # Store the query and response in the database
        query_doc = {
            "repo_id": repo_id,
            "query": request.message,
            "response": response,
            "timestamp": db_client.db.client.server_info().get("localTime", None)
        }
        db_client.db.queries.insert_one(query_doc)
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        logger.error(traceback.format_exc())
        return {"text": f"Sorry, I encountered an error while processing your request. Please try again later.", 
                "code": None, 
                "referenced_files": []}