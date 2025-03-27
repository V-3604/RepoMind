"""
Database schema definitions for RepoMind.
This module defines the structure of the MongoDB collections used by the application.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, AnyHttpUrl


class Function(BaseModel):
    """Schema for a function extracted from a code file."""
    name: str
    signature: str
    description: str = ""
    start_line: int
    end_line: int
    code: str


class FileInfo(BaseModel):
    """Schema for information about a file in a repository."""
    path: str
    language: str
    summary: str = ""
    functions: List[Function] = []
    size_bytes: int = 0
    line_count: int = 0
    last_modified: Optional[datetime] = None


class Repository(BaseModel):
    """Schema for a repository stored in the database."""
    id: str = Field(None, alias="_id")
    name: str
    source: str
    source_type: str  # "github", "zip", or "local"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    summary: str = ""
    files: List[FileInfo] = []
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class QueryResponse(BaseModel):
    """Schema for a response to a query."""
    text: str
    code: Optional[str] = None
    references: List[Dict[str, Any]] = []


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


class GitHubRepository(BaseModel):
    """Schema for a GitHub repository."""
    url: AnyHttpUrl
    branch: Optional[str] = None
    auth_token: Optional[str] = None


class ZipRepository(BaseModel):
    """Schema for a ZIP repository."""
    file_path: str


class LocalRepository(BaseModel):
    """Schema for a local repository."""
    directory_path: str 