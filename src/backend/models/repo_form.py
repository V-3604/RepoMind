from typing import Optional
from fastapi import UploadFile
from pydantic import BaseModel


class BaseRepoForm(BaseModel):
    """
    Base repository form model
    """
    type: str
    name: str


class GitHubRepoForm(BaseRepoForm):
    """
    GitHub repository form model
    """
    url: str
    
    class Config:
        schema_extra = {
            "example": {
                "type": "github",
                "name": "flask",
                "url": "https://github.com/pallets/flask"
            }
        }


class LocalRepoForm(BaseRepoForm):
    """
    Local repository form model
    """
    file: UploadFile
    
    class Config:
        schema_extra = {
            "example": {
                "type": "local",
                "name": "my-project",
                "file": "file_content"
            }
        }
        arbitrary_types_allowed = True 