"""
Configuration module for RepoMind.
Loads environment variables and provides configuration settings for the application.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# MongoDB settings
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/repomind")
MONGODB_DB_NAME = MONGODB_URI.split("/")[-1]

# LLM API settings
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_API_URL = os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")

# Application settings
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key")

# Repository settings
TEMP_DIR = BASE_DIR / "temp"
MAX_REPO_SIZE_MB = 100  # Maximum repository size in MB

# Analysis settings
DEFAULT_CHUNK_SIZE = 1000  # Default chunk size for code analysis
MAX_TOKENS = 8192  # Maximum tokens for LLM context

# API settings
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Frontend settings
STATIC_DIR = BASE_DIR / "src" / "frontend" / "static"
TEMPLATES_DIR = BASE_DIR / "src" / "frontend" / "templates"

# Create necessary directories if they don't exist
TEMP_DIR.mkdir(exist_ok=True) 