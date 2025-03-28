"""
Database schema definitions for RepoMind.
This module defines the structure of the MongoDB collections used by the application.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, AnyHttpUrl


class Function(BaseModel):
    """Schema for a function extracted from a code file."""
    id: str = Field(None, alias="_id")
    repo_id: str
    file_path: str
    name: str
    signature: str
    description: str = ""
    start_line: int
    end_line: int
    code: str
    language: str
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class FileInfo(BaseModel):
    """Schema for a file stored in the database."""
    id: str = Field(None, alias="_id")
    repo_id: str
    path: str
    language: str = ""
    summary: str = ""
    size_bytes: int = 0
    line_count: int = 0
    content: str
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class Repository(BaseModel):
    """Base repository model."""
    id: str = Field(alias="_id")
    name: str
    status: str = "processing"
    source_type: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    analysis_completed: bool = False
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class QueryResponse(BaseModel):
    """Schema for a response to a query."""
    text: str
    code: Optional[str] = None
    referenced_files: List[str] = []
    confidence: float = 1.0


class Query(BaseModel):
    """Schema for a query stored in the database."""
    id: str = Field(None, alias="_id")
    repo_id: str
    query: str
    response: QueryResponse
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class GitHubRepository(Repository):
    """GitHub repository model."""
    source_type: str = "github"
    source: str
    owner: str
    branch: Optional[str] = None


class ZipRepository(Repository):
    """ZIP repository model."""
    source_type: str = "zip"
    original_filename: str


class LocalRepository(Repository):
    """Local repository model."""
    source_type: str = "local"
    local_path: str


class RepositoryMetrics(BaseModel):
    """Schema for repository metrics."""
    languages: List[Dict[str, Any]] = []
    top_files: List[Dict[str, Any]] = []
    total_files: int = 0
    total_lines: int = 0


class FileAnalysis(BaseModel):
    """Schema for file analysis results."""
    summary: str
    functions: List[Dict[str, str]] = []
    recommendations: Optional[str] = None


class CreateRepositoryRequest(BaseModel):
    """Schema for repository creation request."""
    name: str
    source_type: str
    github_url: Optional[str] = None
    github_branch: Optional[str] = None
    local_path: Optional[str] = None


class UserSettings(BaseModel):
    """Schema for user settings."""
    id: str = Field(None, alias="_id")
    username: str
    theme: str = "light"
    preferred_language: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class RepositoryTag(BaseModel):
    """Schema for repository tags."""
    id: str = Field(None, alias="_id")
    repo_id: str
    name: str
    color: str = "#007bff"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class RepositoryStar(BaseModel):
    """Schema for repository stars (favorites)."""
    id: str = Field(None, alias="_id")
    repo_id: str
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True 