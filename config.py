"""
Configuration settings for RepoMind.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = Path(os.getenv("TEMP_DIR", BASE_DIR / "temp"))
STATIC_DIR = BASE_DIR / "src" / "frontend" / "static"
TEMPLATES_DIR = BASE_DIR / "src" / "frontend" / "templates"

# MongoDB settings
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/repomind")
MONGODB_DB = os.getenv("MONGODB_DB", "repomind")
MONGODB_TIMEOUT_MS = int(os.getenv("MONGODB_TIMEOUT_MS", "5000"))

# LLM API settings
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_API_URL = os.getenv("LLM_API_URL", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

# Application settings
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# File size limits
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))  # 10MB
MAX_REPO_SIZE_MB = int(os.getenv("MAX_REPO_SIZE_MB", "100"))  # 100MB

# Analysis settings
DEFAULT_CHUNK_SIZE = 1000  # Default chunk size for code analysis
MAX_TOKENS = 8192  # Maximum tokens for LLM context

# Create necessary directories if they don't exist
os.makedirs(TEMP_DIR, exist_ok=True)

# Log configuration at startup
print(f"Configuration loaded from {BASE_DIR}")
print(f"MONGODB_URI: {MONGODB_URI}")
print(f"MONGODB_DB: {MONGODB_DB}")
print(f"TEMP_DIR: {TEMP_DIR}")
print(f"API_HOST: {API_HOST}")
print(f"API_PORT: {API_PORT}")
print(f"DEBUG: {DEBUG}")
print(f"LOG_LEVEL: {LOG_LEVEL}") 