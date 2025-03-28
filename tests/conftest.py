"""
Pytest configuration file with common fixtures for testing.
"""

import os
import pytest
import tempfile
from unittest.mock import MagicMock, patch
from pymongo.database import Database
from bson import ObjectId

from src.backend.database.client import DatabaseClient
from src.agents.llm_client import LLMClient


@pytest.fixture
def mock_db_client():
    """Create a mock database client."""
    client = MagicMock(spec=DatabaseClient)
    client.db = MagicMock(spec=Database)
    
    # Setup collections
    client.db.repositories = MagicMock()
    client.db.files = MagicMock()
    client.db.functions = MagicMock()
    client.db.conversations = MagicMock()
    
    # Setup find_one method for repositories
    client.db.repositories.find_one.return_value = {
        "_id": ObjectId("6072f7a81c9d440000000000"),
        "name": "test-repo",
        "description": "A test repository",
        "path": "/path/to/repo",
        "status": "completed",
        "file_count": 10,
        "size_bytes": 5000,
        "language_stats": {"python": 80, "javascript": 20}
    }
    
    return client


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    client = MagicMock(spec=LLMClient)
    
    # Setup generate_text method
    client.generate_text.return_value = "Generated text response"
    
    # Setup generate_text_async method
    async def async_generate():
        return "Generated text response async"
    
    client.generate_text_async.side_effect = async_generate
    
    # Setup answer_question method
    client.answer_question.return_value = ("Answer to the question", ["file1.py:10-15"])
    
    # Setup analyze_code method
    async def async_analyze():
        return "Code analysis result"
    
    client.analyze_code.side_effect = async_analyze
    
    return client


@pytest.fixture
def temp_repo_dir():
    """Create a temporary directory for testing repositories."""
    temp_dir = tempfile.mkdtemp()
    
    # Create sample files
    file1_path = os.path.join(temp_dir, "main.py")
    with open(file1_path, "w") as f:
        f.write("""
def main():
    print("Hello, World!")
    return True

if __name__ == "__main__":
    main()
""")
    
    file2_path = os.path.join(temp_dir, "utils.py")
    with open(file2_path, "w") as f:
        f.write("""
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
""")
    
    # Create a subdirectory with more files
    sub_dir = os.path.join(temp_dir, "src")
    os.makedirs(sub_dir)
    
    file3_path = os.path.join(sub_dir, "app.py")
    with open(file3_path, "w") as f:
        f.write("""
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello!"

if __name__ == "__main__":
    app.run(debug=True)
""")
    
    yield temp_dir
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_repo_data():
    """Return sample repository data."""
    return {
        "_id": ObjectId("6072f7a81c9d440000000000"),
        "name": "test-repo",
        "description": "A test repository",
        "path": "/path/to/repo",
        "status": "completed",
        "file_count": 10,
        "size_bytes": 5000,
        "source": "github",
        "url": "https://github.com/user/test-repo",
        "language_stats": {
            "python": {"count": 8, "bytes": 4000, "percentage": 80},
            "javascript": {"count": 2, "bytes": 1000, "percentage": 20}
        },
        "created_at": "2023-03-01T12:00:00Z",
        "updated_at": "2023-03-01T12:30:00Z",
        "analysis_completed": True
    }


@pytest.fixture
def sample_file_data():
    """Return sample file data."""
    return {
        "_id": ObjectId("6072f7a81c9d440000000001"),
        "repo_id": ObjectId("6072f7a81c9d440000000000"),
        "path": "src/main.py",
        "relative_path": "main.py",
        "language": "python",
        "size_bytes": 1024,
        "summary": "Main entry point for the application",
        "content": "def main():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    main()",
        "line_count": 5,
        "created_at": "2023-03-01T12:00:00Z"
    }


@pytest.fixture
def sample_function_data():
    """Return sample function data."""
    return {
        "_id": ObjectId("6072f7a81c9d440000000002"),
        "repo_id": ObjectId("6072f7a81c9d440000000000"),
        "file_id": ObjectId("6072f7a81c9d440000000001"),
        "file_path": "src/main.py",
        "name": "main",
        "signature": "def main():",
        "start_line": 1,
        "end_line": 2,
        "code": "def main():\n    print('Hello, World!')",
        "summary": "Main function that prints a greeting",
        "complexity": 1,
        "parameters": []
    }


@pytest.fixture
def sample_conversation_data():
    """Return sample conversation data."""
    return {
        "_id": ObjectId("6072f7a81c9d440000000003"),
        "repo_id": ObjectId("6072f7a81c9d440000000000"),
        "messages": [
            {
                "role": "user",
                "content": "How does this code work?",
                "timestamp": "2023-03-01T12:35:00Z"
            },
            {
                "role": "assistant",
                "content": "The code defines a main function that prints 'Hello, World!' and runs it when the script is executed directly.",
                "references": ["src/main.py:1-5"],
                "timestamp": "2023-03-01T12:35:05Z"
            }
        ],
        "created_at": "2023-03-01T12:35:00Z",
        "updated_at": "2023-03-01T12:35:05Z"
    } 