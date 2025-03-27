"""
API routes for RepoMind.
Handles API requests for repositories, files, and queries.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, File, UploadFile, Form, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.backend.database.schema import Repository, GitHubRepository, ZipRepository, LocalRepository, FileInfo, Function, Query as QueryModel
from src.backend.database.mongo_client import MongoDBClient
from src.backend.repo_manager.repo_loader import RepoLoader
from src.backend.analyzer.repo_analyzer import RepoAnalyzer
from src.backend.llm.query_processor import QueryProcessor

# Create API router
router = APIRouter(prefix="/api", tags=["API"])

# Initialize database client
db_client = MongoDBClient()
db_client.connect()


class QueryRequest(BaseModel):
    """Request model for a repository query."""
    query: str
    file_path: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class QueryResponse(BaseModel):
    """Response model for a repository query."""
    text: str
    code: Optional[str] = None
    referenced_files: List[str] = []
    confidence: float = 1.0


@router.get("/repos", response_model=List[Repository])
async def list_repositories():
    """
    List all repositories.
    
    Returns:
        List[Repository]: List of repositories
    """
    try:
        repos = db_client.db.repositories.find()
        return [Repository(**repo) for repo in repos]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch repositories: {str(e)}")


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
        repo = db_client.db.repositories.find_one({"_id": repo_id})
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")
        return Repository(**repo)
    except HTTPException:
        raise
    except Exception as e:
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
        repo = db_client.db.repositories.find_one({"_id": repo_id})
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        # Build tree structure
        files = db_client.db.files.find({"repo_id": repo_id}, {"path": 1, "language": 1})
        
        # Create root node
        root = {
            "type": "directory",
            "name": repo["name"],
            "path": "",
            "children": []
        }
        
        for file in files:
            path_parts = file["path"].split("/")
            current_node = root
            
            # Build directory structure
            for i, part in enumerate(path_parts):
                if i == len(path_parts) - 1:
                    # Last part is a file
                    current_node["children"].append({
                        "type": "file",
                        "name": part,
                        "path": file["path"],
                        "language": file.get("language", "")
                    })
                else:
                    # Directory
                    dir_path = "/".join(path_parts[:i+1])
                    dir_node = next((n for n in current_node["children"] if n["type"] == "directory" and n["name"] == part), None)
                    
                    if not dir_node:
                        dir_node = {
                            "type": "directory",
                            "name": part,
                            "path": dir_path,
                            "children": []
                        }
                        current_node["children"].append(dir_node)
                    
                    current_node = dir_node
        
        return root
    except HTTPException:
        raise
    except Exception as e:
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
        repo = db_client.db.repositories.find_one({"_id": repo_id})
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        queries = db_client.db.queries.find(
            {"repo_id": repo_id},
            sort=[("timestamp", -1)],
            limit=limit
        )
        
        return list(queries)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch repository queries: {str(e)}")


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
        repo_loader = RepoLoader(db_client)
        
        if repo_type == "github" and github_url:
            repo_id = await repo_loader.load_from_github(
                name,
                github_url,
                branch=github_branch
            )
        elif repo_type == "zip" and zip_file:
            repo_id = await repo_loader.load_from_zip(
                name,
                zip_file
            )
        elif repo_type == "local" and local_path:
            repo_id = await repo_loader.load_from_local(
                name,
                local_path
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid repository type or missing required parameters"
            )
        
        # Start analysis in background
        analyzer = RepoAnalyzer(db_client)
        background_tasks.add_task(analyzer.analyze_repository, repo_id)
        
        return {"id": repo_id, "name": name, "status": "processing"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create repository: {str(e)}") 