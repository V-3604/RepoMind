"""
API routes for RepoMind.
Handles API requests for repositories, files, and queries.
"""

import logging
import os
import sys
import traceback
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from bson import ObjectId

# Add the parent directory to sys.path to make config importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

# Python-multipart is imported implicitly by FastAPI
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, File, UploadFile, Form, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.backend.database.schema import Repository, GitHubRepository, ZipRepository, LocalRepository, FileInfo, Function, Query as QueryModel
from src.backend.database.db_client import DBClient
from src.backend.repo_manager.repo_loader import RepoLoader
from src.backend.analyzer.repo_analyzer import RepoAnalyzer
from src.backend.llm.query_processor import QueryProcessor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["API"])

# Create MongoDB client
try:
    print("Initializing MongoDB client...")
    db_client = DBClient()
    print("MongoDB client initialized successfully")
except Exception as e:
    print(f"Error initializing MongoDB client: {str(e)}")
    sys.exit(1)

# Create temp directory if it doesn't exist
os.makedirs(os.path.join(os.path.dirname(__file__), "../../../temp"), exist_ok=True)
print(f"Using temporary directory: {os.path.join(os.path.dirname(__file__), '../../../temp')}")

# Root endpoint
@router.get("/")
async def root():
    """
    Root endpoint for API health check
    """
    return {"status": "ok", "message": "RepoMind API is running"}

# Health check endpoint
@router.get("/health")
async def health():
    """
    Health check endpoint
    """
    return {"status": "ok"}

class QueryRequest(BaseModel):
    """Request model for a repository query."""
    query: str
    file_path: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    """Request model for chat messages."""
    message: str
    repo_id: Optional[str] = None
    context: Dict[str, Any] = {}


class QueryResponse(BaseModel):
    """Response model for a repository query."""
    text: str
    code: Optional[str] = None
    referenced_files: List[str] = []
    confidence: float = 1.0


@router.get("/repos")
async def get_repositories():
    """
    Get all repositories
    """
    try:
        print("Fetching repositories from database")
        # Get all repositories from the database
        repositories = list(db_client.db.repositories.find())
        print(f"Found {len(repositories)} repositories")
        
        # Convert MongoDB documents to JSON-serializable format
        for repo in repositories:
            # Convert ObjectId to string
            if "_id" in repo and isinstance(repo["_id"], ObjectId):
                repo["_id"] = str(repo["_id"])
            
            # Convert dates to strings
            if "created_at" in repo and repo["created_at"]:
                if isinstance(repo["created_at"], datetime):
                    repo["created_at"] = repo["created_at"].isoformat()
            
            # Ensure source_type is set
            if "source_type" not in repo or not repo["source_type"]:
                if "type" in repo and repo["type"]:
                    repo["source_type"] = repo["type"]
                else:
                    repo["source_type"] = "Unknown"
        
        return repositories
    except Exception as e:
        print(f"Error fetching repositories: {str(e)}")
        traceback.print_exc()
        return {"error": str(e)}


@router.get("/repos/{repo_id}", response_model=Repository)
async def get_repository(repo_id: str):
    """
    Get a repository by ID.
    
    Args:
        repo_id: Repository ID
        
    Returns:
        Repository: Repository details
    """
    try:
        # Try with the original ID first
        repo = db_client.db.repositories.find_one({"_id": repo_id})
        
        # If not found and ID is a valid ObjectId, try with ObjectId
        if not repo and ObjectId.is_valid(repo_id):
            repo = db_client.db.repositories.find_one({"_id": ObjectId(repo_id)})
            
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")
            
        # Convert ObjectId to string for serialization
        if "_id" in repo and isinstance(repo["_id"], ObjectId):
            repo["_id"] = str(repo["_id"])
            
        # Convert dates to strings
        if "created_at" in repo and repo["created_at"]:
            if isinstance(repo["created_at"], datetime):
                repo["created_at"] = repo["created_at"].isoformat()
        
        # Ensure source_type is set
        if "source_type" not in repo or not repo["source_type"]:
            if "type" in repo and repo["type"]:
                repo["source_type"] = repo["type"]
            else:
                repo["source_type"] = "Unknown source"
            
        return Repository(**repo)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch repository: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch repository: {str(e)}")


@router.delete("/repos/{repo_id}")
async def delete_repository(repo_id: str):
    """
    Delete a repository.
    
    Args:
        repo_id: Repository ID
        
    Returns:
        dict: Success message
    """
    try:
        result = db_client.db.repositories.delete_one({"_id": repo_id})
        if result.deleted_count == 0:
            # Try with ObjectId if string ID didn't work
            if ObjectId.is_valid(repo_id):
                result = db_client.db.repositories.delete_one({"_id": ObjectId(repo_id)})
                if result.deleted_count == 0:
                    raise HTTPException(status_code=404, detail="Repository not found")
        
        # Delete all related data
        db_client.db.files.delete_many({"repo_id": repo_id})
        db_client.db.functions.delete_many({"repo_id": repo_id})
        db_client.db.queries.delete_many({"repo_id": repo_id})
        
        return {"message": "Repository deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete repository: {str(e)}")


@router.get("/repos/{repo_id}/files")
async def get_file_content(repo_id: str, path: str = Query(...)):
    """
    Get file content from a repository.
    
    Args:
        repo_id: Repository ID
        path: File path
        
    Returns:
        dict: File content and metadata
    """
    try:
        file = db_client.db.files.find_one({"repo_id": repo_id, "path": path})
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get functions in this file
        functions = db_client.db.functions.find({"repo_id": repo_id, "file_path": path})
        
        return {
            "path": file["path"],
            "content": file["content"],
            "size_bytes": len(file["content"]),
            "line_count": file["content"].count('\n') + 1,
            "language": file["language"],
            "functions": list(functions)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch file: {str(e)}")


@router.get("/repos/{repo_id}/structure")
async def get_repository_structure(repo_id: str):
    """
    Get the file structure of a repository.
    
    Args:
        repo_id: Repository ID
        
    Returns:
        dict: Repository file structure
    """
    try:
        # Try to find repository by ID
        repo = None
        try:
            if ObjectId.is_valid(repo_id):
                repo = db_client.db.repositories.find_one({"_id": ObjectId(repo_id)})
            
            if not repo:
                repo = db_client.db.repositories.find_one({"_id": repo_id})
                
            if not repo:
                raise HTTPException(status_code=404, detail="Repository not found")
        except Exception as e:
            logger.error(f"Error finding repository: {str(e)}")
            raise HTTPException(status_code=404, detail=f"Repository not found: {str(e)}")
        
        try:
            # Build tree structure
            files_cursor = db_client.db.files.find({"repo_id": repo_id}, {"path": 1, "language": 1})
            files = list(files_cursor)
            
            if not files:
                logger.warning(f"No files found for repository {repo_id}")
                # Return empty structure if no files
                return {
                    "type": "directory",
                    "name": repo.get("name", "Unknown"),
                    "path": "",
                    "children": []
                }
            
            # Create root node
            root = {
                "type": "directory",
                "name": repo.get("name", "Unknown"),
                "path": "",
                "children": []
            }
            
            # Helper function to get or create directory node
            def get_or_create_dir(path_parts, current_index, parent_node):
                if not path_parts or current_index >= len(path_parts):
                    return parent_node
                    
                current_part = path_parts[current_index]
                if not current_part:  # Skip empty path parts
                    return get_or_create_dir(path_parts, current_index + 1, parent_node)
                    
                current_path = "/".join(path_parts[:current_index+1])
                
                # Find or create directory node
                dir_node = next((n for n in parent_node["children"] 
                                if n["type"] == "directory" and n["name"] == current_part), None)
                    
                if not dir_node:
                    dir_node = {
                        "type": "directory",
                        "name": current_part,
                        "path": current_path,
                        "children": []
                    }
                    parent_node["children"].append(dir_node)
                    
                # Recursively process the rest of the path
                if current_index < len(path_parts) - 1:
                    return get_or_create_dir(path_parts, current_index + 1, dir_node)
                else:
                    return dir_node
            
            for file in files:
                if not file or "path" not in file or not file["path"]:
                    logger.warning(f"Skipping invalid file record: {file}")
                    continue
                    
                try:
                    path_parts = file["path"].split("/")
                    
                    if len(path_parts) == 1:
                        # File is in the root directory
                        root["children"].append({
                            "type": "file",
                            "name": path_parts[0],
                            "path": file["path"],
                            "language": file.get("language", "")
                        })
                    else:
                        # File is in a subdirectory
                        dir_path_parts = path_parts[:-1]
                        file_name = path_parts[-1]
                        
                        # Get or create the parent directory
                        parent_dir = get_or_create_dir(dir_path_parts, 0, root)
                        
                        # Add file to the parent directory
                        parent_dir["children"].append({
                            "type": "file",
                            "name": file_name,
                            "path": file["path"],
                            "language": file.get("language", "")
                        })
                except Exception as file_error:
                    logger.error(f"Error processing file {file.get('path', 'unknown')}: {str(file_error)}")
                    continue
            
            return root
        except Exception as e:
            logger.error(f"Error building file structure: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Failed to build repository structure: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch repository structure: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch repository structure: {str(e)}")


@router.get("/repos/{repo_id}/components")
async def get_repository_components(repo_id: str):
    """
    Get key components of a repository.
    
    Args:
        repo_id: Repository ID
        
    Returns:
        List[dict]: List of key components
    """
    try:
        # Try with ObjectId if valid
        if ObjectId.is_valid(repo_id):
            repo = db_client.db.repositories.find_one({"_id": ObjectId(repo_id)})
        
        # If not found, try with string ID
        if not repo:
            repo = db_client.db.repositories.find_one({"_id": repo_id})
            
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        # Get important files based on function count and complexity
        files = list(db_client.db.files.find(
            {"repo_id": repo_id},
            {"path": 1, "summary": 1, "language": 1}
        ))
        
        # Group files by directory/component
        components = []
        directories = {}
        
        for file in files:
            dir_path = "/".join(file["path"].split("/")[:-1]) or "root"
            if dir_path not in directories:
                directories[dir_path] = {
                    "name": dir_path,
                    "description": f"Files in {dir_path} directory",
                    "files": []
                }
            
            directories[dir_path]["files"].append({
                "path": file["path"],
                "summary": file.get("summary", ""),
                "language": file.get("language", "")
            })
        
        # Convert to list and sort by file count
        components = list(directories.values())
        components.sort(key=lambda x: len(x["files"]), reverse=True)
        
        # Limit to top 10 components
        return components[:10]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch repository components: {str(e)}")


@router.post("/repos/{repo_id}/analyze")
async def analyze_repository_element(repo_id: str, query_request: QueryRequest):
    """
    Analyze a specific element of the repository.
    
    Args:
        repo_id: Repository ID
        query_request: Analysis request
        
    Returns:
        dict: Analysis results
    """
    try:
        # Try with ObjectId if valid
        if ObjectId.is_valid(repo_id):
            repo = db_client.db.repositories.find_one({"_id": ObjectId(repo_id)})
        
        # If not found, try with string ID
        if not repo:
            repo = db_client.db.repositories.find_one({"_id": repo_id})
            
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        processor = QueryProcessor(db_client)
        
        # Process the query
        response = await processor.process_query(
            repo_id,
            query_request.query,
            file_path=query_request.file_path,
            context=query_request.context
        )
        
        # Save query and response
        query_doc = {
            "repo_id": repo_id,
            "query": query_request.query,
            "response": response,
            "timestamp": datetime.utcnow()
        }
        db_client.db.queries.insert_one(query_doc)
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze repository: {str(e)}")


@router.get("/repos/{repo_id}/queries")
async def get_repository_queries(repo_id: str, limit: int = 10):
    """
    Get previous queries for a repository.
    
    Args:
        repo_id: Repository ID
        limit: Maximum number of queries to return
        
    Returns:
        List[dict]: List of queries and responses
    """
    try:
        repo = None
        # Try with ObjectId first if valid
        if ObjectId.is_valid(repo_id):
            repo = db_client.db.repositories.find_one({"_id": ObjectId(repo_id)})
        
        # If not found, try with string ID
        if not repo:
            repo = db_client.db.repositories.find_one({"_id": repo_id})
            
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        queries = list(db_client.db.queries.find(
            {"repo_id": repo_id},
            sort=[("timestamp", -1)],
            limit=limit
        ))
        
        # Convert ObjectId to string for JSON serialization
        for query in queries:
            if "_id" in query and isinstance(query["_id"], ObjectId):
                query["_id"] = str(query["_id"])
                
            # Convert timestamp to ISO format if it's a datetime
            if "timestamp" in query and query["timestamp"] and isinstance(query["timestamp"], datetime):
                query["timestamp"] = query["timestamp"].isoformat()
        
        return queries
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch repository queries: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch repository queries: {str(e)}")


# Direct chat endpoint at /api/chat/{repo_id}
@router.post("/chat/{repo_id}")
async def chat_with_repository(repo_id: str, request: ChatRequest):
    """
    Chat with a repository.
    
    Args:
        repo_id: Repository ID
        request: Chat request
        
    Returns:
        dict: Chat response
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
        
        # Process the query using the message field
        processor = QueryProcessor(db_client)
        response = await processor.process_query(
            repo_id,
            request.message,
            context=request.context
        )
        
        # Store the query and response in the database
        query_doc = {
            "repo_id": repo_id,
            "query": request.message,
            "response": response,
            "timestamp": datetime.utcnow()
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


@router.post("/repos", status_code=201)
async def create_repository(
    background_tasks: BackgroundTasks,
    repo_type: str = Form(...),
    name: str = Form(...),
    github_url: Optional[str] = Form(None),
    github_branch: Optional[str] = Form(None),
    zip_file: Optional[UploadFile] = File(None),
    local_path: Optional[str] = Form(None)
):
    """
    Create a new repository.
    
    Args:
        background_tasks: Background tasks
        repo_type: Repository type (github, zip, local)
        name: Repository name
        github_url: GitHub repository URL
        github_branch: GitHub repository branch
        zip_file: ZIP file upload
        local_path: Local repository path
        
    Returns:
        dict: Repository details
    """
    try:
        # Check MongoDB connection
        if not db_client.client:
            raise HTTPException(
                status_code=500,
                detail="Database connection is not available. Please check MongoDB connection."
            )
        
        # Log the request details
        print(f"Creating repository - Type: {repo_type}, Name: {name}, GitHub URL: {github_url}")
        print(f"Request parameters - repo_type: {repo_type}, name: {name}, github_url: {github_url}, zip_file: {zip_file}, local_path: {local_path}")
        
        # Create repo loader
        repo_loader = RepoLoader(db_client)

        if repo_type == "github" and github_url:
            try:
                repo_id = await repo_loader.load_from_github(
                    name,
                    github_url,
                    branch=github_branch
                )
            except Exception as e:
                print(f"GitHub loading error: {str(e)}")
                print(traceback.format_exc())
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to load GitHub repository: {str(e)}"
                )
        elif repo_type == "zip" and zip_file:
            try:
                repo_id = await repo_loader.load_from_zip(
                    name,
                    zip_file
                )
            except Exception as e:
                print(f"ZIP loading error: {str(e)}")
                print(traceback.format_exc())
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to load ZIP repository: {str(e)}"
                )
        elif repo_type == "local" and local_path:
            try:
                repo_id = await repo_loader.load_from_local(
                    name,
                    local_path
                )
            except Exception as e:
                print(f"Local path loading error: {str(e)}")
                print(traceback.format_exc())
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to load local repository: {str(e)}"
                )
        else:
            error_detail = f"Invalid repository type or missing required parameters. Got repo_type={repo_type}, github_url={github_url}, zip_file={zip_file}, local_path={local_path}"
            print(error_detail)
            raise HTTPException(
                status_code=400,
                detail=error_detail
            )
        
        # Start analysis in background
        try:
            analyzer = RepoAnalyzer(db_client)
            background_tasks.add_task(analyzer.analyze_repository, repo_id)
        except Exception as e:
            print(f"Failed to start analysis: {str(e)}")
            print(traceback.format_exc())
            # Don't fail the request if analysis fails to start
        
        # Return a redirect response to the repository page
        return {"id": repo_id, "name": name, "status": "processing"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error creating repository: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to create repository: {str(e)}")


# Include other API endpoints from endpoints directory
# Make sure the routes don't clash with the ones defined here
# If you have both /api/chat/{repo_id} defined here and in endpoints/chat.py,
# you'll get a duplicate route error.
try:
    from src.backend.api.endpoints.repo import router as repo_router
    router.include_router(repo_router, prefix="/repos-ext", tags=["repositories-ext"])
except ImportError:
    logger.warning("Could not import repo_router from endpoints")

try:
    from src.backend.api.endpoints.auth import router as auth_router
    router.include_router(auth_router, prefix="/auth", tags=["auth"])
except ImportError:
    logger.warning("Could not import auth_router from endpoints")