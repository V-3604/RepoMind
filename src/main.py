"""
Main entry point for the RepoMind application.
This module initializes and runs both the backend API and frontend web server.
"""

import argparse
import asyncio
import sys
import uvicorn
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add the parent directory to the path to allow imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import API_HOST, API_PORT, DEBUG
from src.frontend.app import app as frontend_app
from src.backend.api.routes import router as api_router


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="RepoMind: Repository Exploration and Query Assistant")
    parser.add_argument(
        "--host",
        default=API_HOST,
        help=f"Host address to bind the server to (default: {API_HOST})"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=API_PORT,
        help=f"Port to bind the server to (default: {API_PORT})"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=DEBUG,
        help="Run in debug mode (default: %(default)s)"
    )
    return parser.parse_args()


async def main():
    """Run the RepoMind application."""
    args = parse_args()
    
    # Create a combined app with both frontend and API
    app = FastAPI(title="RepoMind", description="Repository Exploration and Query Assistant")
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Change this in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Mount the frontend app
    app.mount("/", frontend_app)
    
    # Include API routes
    app.include_router(api_router)
    
    # Start the server
    config = uvicorn.Config(
        app=app,
        host=args.host,
        port=args.port,
        reload=args.debug,
        log_level="info" if args.debug else "error",
    )
    server = uvicorn.Server(config)
    
    print(f"Starting RepoMind on http://{args.host}:{args.port}")
    await server.serve()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down RepoMind...")
        sys.exit(0) 