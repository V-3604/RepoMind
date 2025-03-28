from typing import Optional
from datetime import datetime
from bson.objectid import ObjectId

class RepoLoader:
    async def load_from_github(self, name: str, github_url: str, branch: Optional[str] = None) -> str:
        """
        Load a repository from GitHub.
        
        Args:
            name: Repository name
            github_url: GitHub repository URL
            branch: Optional branch name
            
        Returns:
            str: Repository ID
        """
        try:
            self.logger.info(f"Loading repository from GitHub: {github_url}")
            
            # Use the GitHub loader
            github_loader = GitHubLoader(github_url, branch)
            
            # Download and extract the repository
            repo_data = await github_loader.load()
            
            # Set repository name if provided
            if name:
                repo_data["name"] = name
            
            # Add metadata
            repo_data["_id"] = str(ObjectId())
            repo_data["source_type"] = "GitHub"
            repo_data["type"] = "github"
            repo_data["url"] = github_url
            repo_data["status"] = "processing"
            repo_data["created_at"] = datetime.utcnow()
            
            # Store in database
            self.db_client.db.repositories.insert_one(repo_data)
            
            return repo_data["_id"]
            
        except Exception as e:
            self.logger.error(f"Error loading repository from GitHub: {str(e)}")
            raise 