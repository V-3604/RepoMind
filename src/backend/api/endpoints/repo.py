from typing import Annotated, Union
import os
import uuid
import logging
from datetime import datetime
from fastapi import BackgroundTasks, HTTPException, File, UploadFile, Form
from fastapi import APIRouter, Depends
from src.backend.models.repo_form import GitHubRepoForm, LocalRepoForm
from src.backend.database.db_client import DBClient
from src.backend.repo_manager.repo_loader_factory import RepoLoaderFactory
from src.backend.models.repository import Repository
from src.backend.analyzer.repo_analyzer import RepoAnalyzer
import config

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency to get DB client
def get_db_client():
    return DBClient()

# Dependency to parse and validate repository form
async def get_repo_form(
    type: str = Form(...),
    name: str = Form(...),
    url: str = Form(None),
    file: UploadFile = File(None)
):
    if type == "github":
        if not url:
            raise HTTPException(status_code=400, detail="URL is required for GitHub repositories")
        return GitHubRepoForm(type=type, name=name, url=url)
    elif type == "local":
        if not file:
            raise HTTPException(status_code=400, detail="File is required for local repositories")
        return LocalRepoForm(type=type, name=name, file=file)
    else:
        raise HTTPException(status_code=400, detail=f"Invalid repository type: {type}")

@router.post("/repos")
async def create_repository(
    repo_form: Annotated[
        Union[GitHubRepoForm, LocalRepoForm], 
        Depends(get_repo_form)
    ], 
    db_client: DBClient = Depends(get_db_client)
) -> Repository:
    """
    Create a new repository from GitHub URL or local file
    """
    try:
        logger.info(f"Creating repository from {repo_form.type} with name {repo_form.name}")
        
        # Create temporary directory
        temp_dir = os.path.join(config.TEMP_DIR, f"{repo_form.name}_{uuid.uuid4().hex}")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Initialize repository loader based on type
        try:
            loader = RepoLoaderFactory.get_loader(repo_form.type)
            if not loader:
                logger.error(f"Invalid repository type: {repo_form.type}")
                raise HTTPException(status_code=400, detail=f"Invalid repository type: {repo_form.type}")
        except Exception as e:
            logger.error(f"Error initializing repository loader: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error initializing repository loader: {str(e)}")
        
        # Load repository
        try:
            if repo_form.type == "github":
                repo_data = loader.load(repo_form.url, temp_dir)
            else:
                # For local repositories
                repo_data = loader.load(repo_form.file.file, temp_dir)
        except Exception as e:
            logger.error(f"Error loading repository: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error loading repository: {str(e)}")
        
        # Create repository in the database
        try:
            repo = Repository(
                name=repo_form.name,
                type=repo_form.type,
                url=getattr(repo_form, "url", None),
                local_path=temp_dir,
                status="processing",
                created_at=datetime.now()
            )
            
            # Save repository to database
            repo_id = db_client.save_repository(repo)
            repo.id = repo_id
            
            # Start background analysis task
            analyzer = RepoAnalyzer(db_client=db_client)
            
            # Run analysis in the background
            background_tasks = BackgroundTasks()
            background_tasks.add_task(lambda: analyzer.analyze_repository(str(repo_id)))
            
            logger.info(f"Repository {repo.name} created with ID {repo_id}")
            return repo
            
        except Exception as e:
            logger.error(f"Error creating repository in database: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error creating repository in database: {str(e)}")
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error creating repository: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error creating repository: {str(e)}") 