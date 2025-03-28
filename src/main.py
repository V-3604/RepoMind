"""
Main entry point for RepoMind.
Initializes and starts the application server.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add the parent directory to sys.path to make config importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import configuration
from config import TEMP_DIR, STATIC_DIR, TEMPLATES_DIR, LOG_LEVEL

# Import application components
from src.frontend.app import app as frontend_app, templates
from src.backend.api.app import app as backend_app
from src.backend.database.mongo_client import MongoDBClient

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application
    """
    # Create main FastAPI app
    app = FastAPI(
        title="RepoMind",
        description="Repository Exploration and Query Assistant",
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
    
    # Include the API router directly instead of mounting
    from src.backend.api.routes import router
    app.include_router(router)
    
    # Mount frontend app
    app.mount("/", frontend_app)
    
    return app

def main():
    """Initialize and start the application server."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="RepoMind Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()
    
    # Create temp directory
    os.makedirs(TEMP_DIR, exist_ok=True)
    logger.info(f"Using temporary directory: {TEMP_DIR}")
    
    # Verify MongoDB connection
    db_client = MongoDBClient()
    conn_success = db_client.connect()
    if conn_success:
        logger.info("Successfully connected to MongoDB")
    else:
        logger.warning("Failed to connect to MongoDB. Some features will be unavailable.")
    
    # Initialize and start server
    app = create_app()
    
    # Configure Uvicorn logging
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
    log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
    
    # Set log level based on debug mode
    log_level = "debug" if args.debug else "info"
    
    logger.info(f"Starting server on {args.host}:{args.port} (debug={args.debug})")
    
    # Start Uvicorn server
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level=log_level,
        log_config=log_config,
    )

if __name__ == "__main__":
    main() 