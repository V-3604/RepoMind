from typing import Optional, Dict, List, Any
from datetime import datetime
import os
from pydantic import BaseModel, Field


class Repository(BaseModel):
    """
    Base repository model
    """
    id: Optional[str] = Field(None, alias="_id")
    name: str
    type: str
    url: Optional[str] = None
    local_path: Optional[str] = None
    status: str = "processing"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    summary: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
    
    def get_local_path(self) -> str:
        """
        Get the local path of the repository
        """
        return self.local_path 