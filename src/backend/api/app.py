"""
API application for RepoMind.
Initializes and configures the FastAPI API.
"""

import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add the parent directory to sys.path to make config importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from src.backend.api.routes import router

# Create FastAPI app
app = FastAPI(
    title="RepoMind API",
    description="API for the RepoMind Repository Exploration and Query Assistant",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint that returns API info."""
    return {
        "name": "RepoMind API",
        "version": "1.0.0",
        "documentation": "/docs",
        "endpoints": [
            "/api/repos",
            "/api/repos/{repo_id}"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8001, reload=True) 