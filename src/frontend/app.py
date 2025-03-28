"""
Frontend application for RepoMind.
Serves the web interface and handles client-side requests.
"""

import os
import sys
import logging
from typing import Dict, List, Optional
from pathlib import Path
import httpx

# Add the parent directory to sys.path to make config importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Python-multipart is imported implicitly by FastAPI
from fastapi import FastAPI, APIRouter, Request, Form, File, UploadFile, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from config import STATIC_DIR, TEMPLATES_DIR

# Configure logging
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="RepoMind", 
    description="Repository Exploration and Query Assistant",
)

# Create router for the frontend
router = APIRouter()

# Configure templates and static files
templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.on_event("startup")
async def startup_event():
    """Initialize HTTP client on startup."""
    app.state.client = httpx.AsyncClient(base_url="http://localhost:8001")

@app.on_event("shutdown")
async def shutdown_event():
    """Close HTTP client on shutdown."""
    await app.state.client.aclose()

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the index page."""
    logger.debug("Rendering index page")
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/repos", response_class=HTMLResponse)
async def list_repos(request: Request):
    """Render the repository list page."""
    logger.debug("Rendering repository list page")
    return templates.TemplateResponse("repos.html", {"request": request})


@router.get("/repos/{repo_id}", response_class=HTMLResponse)
async def view_repo(request: Request, repo_id: str):
    """Render the repository details page."""
    logger.debug(f"Rendering repository details page for repo_id: {repo_id}")
    
    try:
        # Create a client if it doesn't exist
        client = getattr(request.app.state, "client", None)
        if not client:
            logger.debug("Creating HTTP client")
            client = httpx.AsyncClient()
            
        # Fetch repository data from the API
        response = await client.get(f"/api/repos/{repo_id}")
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Repository not found")
        elif response.status_code != 200:
            logger.error(f"Error fetching repository: status={response.status_code}, message={response.text}")
            raise HTTPException(status_code=500, detail="Error fetching repository data")
            
        repo = response.json()
        
        return templates.TemplateResponse(
            "repo_details.html", 
            {"request": request, "repo_id": repo_id, "repo": repo}
        )
    except Exception as e:
        logger.error(f"Error rendering repository details: {str(e)}")
        # Still render the template but without repo data
        return templates.TemplateResponse(
            "repo_details.html", 
            {"request": request, "repo_id": repo_id, "repo": {"name": "Repository"}}
        )


@router.get("/repos/{repo_id}/file", response_class=HTMLResponse)
async def view_file(request: Request, repo_id: str, path: str = Query(...)):
    """Render the file view page."""
    logger.debug(f"Rendering file view page for repo_id: {repo_id}, path: {path}")
    return templates.TemplateResponse(
        "file_view.html",
        {"request": request, "repo_id": repo_id, "file_path": path}
    )


@router.get("/chat/{repo_id}", response_class=HTMLResponse)
async def chat_interface(request: Request, repo_id: str):
    """Render the chat interface for a repository."""
    logger.debug(f"Rendering chat interface for repo_id: {repo_id}")
    return templates.TemplateResponse(
        "chat.html", 
        {"request": request, "repo_id": repo_id}
    )


@router.get("/repos/{repo_id}/chat")
async def redirect_to_chat(repo_id: str):
    """Redirect to the chat interface."""
    logger.debug(f"Redirecting to chat interface for repo_id: {repo_id}")
    return RedirectResponse(url=f"/chat/{repo_id}")


@router.get("/upload", response_class=HTMLResponse)
async def upload_form(request: Request):
    """Render the repository upload form."""
    logger.debug("Rendering upload form")
    return templates.TemplateResponse("upload.html", {"request": request})


# Include router in app
app.include_router(router)


# Root endpoint that redirects to the router's root
@app.get("/")
async def root():
    """Redirect to the frontend root."""
    return RedirectResponse(url="/")


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True) 