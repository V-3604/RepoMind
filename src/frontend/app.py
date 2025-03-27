"""
Frontend application for RepoMind.
Serves the web interface and handles client-side requests.
"""

import os
from typing import Dict, List, Optional
from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from config import STATIC_DIR, TEMPLATES_DIR

# Create FastAPI app
app = FastAPI(title="RepoMind", description="Repository Exploration and Query Assistant")

# Configure templates and static files
templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the index page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/repos", response_class=HTMLResponse)
async def list_repos(request: Request):
    """Render the repository list page."""
    return templates.TemplateResponse("repos.html", {"request": request})


@app.get("/repos/{repo_id}", response_class=HTMLResponse)
async def view_repo(request: Request, repo_id: str):
    """Render the repository details page."""
    return templates.TemplateResponse(
        "repo_details.html", 
        {"request": request, "repo_id": repo_id}
    )


@app.get("/repos/{repo_id}/file", response_class=HTMLResponse)
async def view_file(request: Request, repo_id: str, path: str = Query(...)):
    """Render the file view page."""
    return templates.TemplateResponse(
        "file_view.html",
        {"request": request, "repo_id": repo_id, "file_path": path}
    )


@app.get("/chat/{repo_id}", response_class=HTMLResponse)
async def chat_interface(request: Request, repo_id: str):
    """Render the chat interface for a repository."""
    return templates.TemplateResponse(
        "chat.html", 
        {"request": request, "repo_id": repo_id}
    )


@app.get("/repos/{repo_id}/chat")
async def redirect_to_chat(repo_id: str):
    """Redirect to the chat interface."""
    return RedirectResponse(url=f"/chat/{repo_id}")


@app.get("/upload", response_class=HTMLResponse)
async def upload_form(request: Request):
    """Render the repository upload form."""
    return templates.TemplateResponse("upload.html", {"request": request})


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True) 