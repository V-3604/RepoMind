"""
Repository analyzer for RepoMind.
Analyzes repository code and extracts metadata.
"""

import logging
import asyncio
import os
from typing import Dict, List, Any, Optional
from bson import ObjectId
from src.backend.database.db_client import DBClient
from src.backend.code_analyzer.parser import CodeParser
from src.backend.code_analyzer.language_detector import LanguageDetector
from src.backend.code_analyzer.function_extractor import FunctionExtractor
from src.backend.code_analyzer.summarizer import CodeSummarizer
from src.agents.llm_client import LLMClient
from src.backend.models.repository import Repository


class RepoAnalyzer:
    """Repository analyzer class for extracting and analyzing code metadata."""
    
    def __init__(self, db_client):
        """
        Initialize the analyzer with a database client.
        
        Args:
            db_client: MongoDB client instance
        """
        self.db_client = db_client
        self.logger = logging.getLogger(__name__)
        self.llm_client = LLMClient()
        self.parser = CodeParser()
        self.summarizer = CodeSummarizer(llm_client=self.llm_client)
    
    def analyze_repository(self, repo_id: str) -> Dict:
        """
        Analyze repository code and extract metadata
        """
        try:
            # Start analysis
            self.logger.info(f"Starting analysis for repository {repo_id}")
            self.db_client.update_repository_status(repo_id, "analyzing")
            
            # Get repository from database
            repository = self.db_client.get_repository(repo_id)
            if not repository:
                self.logger.error(f"Repository {repo_id} not found")
                return {"error": "Repository not found"}
                
            # Get temp directory
            temp_dir = repository.get_local_path()
            if not temp_dir or not os.path.exists(temp_dir):
                self.logger.error(f"Repository directory not found: {temp_dir}")
                return {"error": "Repository directory not found"}
                
            # List all files in the repository
            all_files = []
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    # Skip hidden files and directories
                    if file.startswith('.') or '/.git/' in root:
                        continue
                    
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, temp_dir)
                    all_files.append(rel_path)
                    
            # Process files in batches
            batch_size = 10
            file_batches = [all_files[i:i + batch_size] for i in range(0, len(all_files), batch_size)]
            
            all_processed_files = []
            for batch in file_batches:
                processed_batch = self._process_file_batch(repository, temp_dir, batch)
                all_processed_files.extend(processed_batch)
                
            # Calculate repository metrics
            metrics = self._calculate_repository_metrics(all_processed_files)
            
            # Generate repository summary
            try:
                summary = self.summarizer.summarize_repository(all_processed_files, repository.name)
            except Exception as e:
                self.logger.error(f"Error generating repository summary: {str(e)}")
                summary = f"Failed to generate summary: {str(e)}"
                
            # Update repository in database
            self.db_client.update_repository(
                repo_id=repo_id,
                summary=summary,
                metrics=metrics,
                status="analyzed"
            )
            
            self.logger.info(f"Analysis complete for repository {repo_id}")
            return {
                "status": "success",
                "summary": summary,
                "metrics": metrics
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing repository {repo_id}: {str(e)}")
            self.db_client.update_repository_status(repo_id, "error")
            return {"error": str(e)}
    
    async def analyze_file(self, repo_id: str, file_path: str) -> Dict[str, Any]:
        """
        Analyze a specific file and generate insights.
        
        Args:
            repo_id: Repository ID
            file_path: Path to the file
            
        Returns:
            dict: Analysis results
        """
        try:
            # Get file from database
            file = self.db_client.db.files.find_one({"repo_id": repo_id, "path": file_path})
            if not file:
                self.logger.error(f"File {file_path} not found in repository {repo_id}")
                return {"error": "File not found"}
            
            # Get file content and metadata
            content = file.get("content", "")
            language = file.get("language", "")
            
            # Get functions in this file
            functions = list(self.db_client.db.functions.find({"repo_id": repo_id, "file_path": file_path}))
            
            # Generate insights using LLM
            prompt = f"""
            Analyze the following code file and provide insights:
            
            File path: {file_path}
            Language: {language}
            
            Code:
            ```{language}
            {content}
            ```
            
            Functions/Classes in this file:
            {', '.join([func.get('name', '') for func in functions])}
            
            Please provide:
            1. A summary of what this file does
            2. Key functions/components and their purposes
            3. How this file fits into the overall project
            4. Any potential improvements or recommendations
            """
            
            try:
                response = self.llm_client.generate_text(prompt, max_tokens=1000)
            except Exception as e:
                self.logger.error(f"Error generating analysis: {str(e)}")
                response = f"Error analyzing file: {str(e)}"
            
            # Parse response to extract structured information
            lines = response.strip().split('\n')
            summary = ""
            functions_info = []
            recommendations = ""
            
            section = "summary"
            for line in lines:
                if "Key functions" in line or "Key components" in line:
                    section = "functions"
                    continue
                elif "fits into" in line or "overall project" in line:
                    section = "fit"
                    continue
                elif "improvements" in line or "recommendations" in line:
                    section = "recommendations"
                    continue
                
                if section == "summary":
                    summary += line + " "
                elif section == "functions" and line.strip().startswith("-"):
                    func_name = line.strip()[1:].split(":")[0].strip()
                    func_desc = line.split(":", 1)[1].strip() if ":" in line else ""
                    functions_info.append({"name": func_name, "description": func_desc})
                elif section == "recommendations":
                    recommendations += line + " "
            
            return {
                "summary": summary.strip(),
                "functions": functions_info,
                "recommendations": recommendations.strip()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing file {file_path}: {str(e)}")
            return {"error": str(e)}
    
    async def calculate_repository_metrics(self, repo_id: str) -> Dict[str, Any]:
        """
        Calculate metrics for a repository.
        
        Args:
            repo_id: Repository ID
            
        Returns:
            dict: Repository metrics
        """
        try:
            # Count files by language
            language_pipeline = [
                {"$match": {"repo_id": repo_id}},
                {"$group": {"_id": "$language", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            languages = list(self.db_client.db.files.aggregate(language_pipeline))
            
            # Count functions by file
            function_pipeline = [
                {"$match": {"repo_id": repo_id}},
                {"$group": {"_id": "$file_path", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            top_files = list(self.db_client.db.functions.aggregate(function_pipeline))
            
            # Get total lines and file count
            total_lines = 0
            file_count = 0
            files_cursor = self.db_client.db.files.find({"repo_id": repo_id})
            for file in files_cursor:
                total_lines += file.get("line_count", 0)
                file_count += 1
            
            return {
                "languages": [{"name": lang["_id"], "count": lang["count"]} for lang in languages],
                "top_files": [{"path": file["_id"], "function_count": file["count"]} for file in top_files],
                "total_files": file_count,
                "total_lines": total_lines
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating repository metrics for {repo_id}: {str(e)}")
            return {"error": str(e)}

    def _process_file(self, repository: Repository, file_path: str, temp_dir: str) -> Dict:
        """
        Process a single file from the repository
        """
        try:
            full_path = os.path.join(temp_dir, file_path)
            if not os.path.exists(full_path) or os.path.isdir(full_path):
                self.logger.warning(f"File not found or is directory: {full_path}")
                return None

            # Skip large files
            if os.path.getsize(full_path) > 10 * 1024 * 1024:  # 10MB
                self.logger.warning(f"File too large to process: {file_path}")
                return None

            # Skip binary files
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                self.logger.warning(f"Binary file, skipping: {file_path}")
                return None

            # Parse language and extract info
            language = self.parser.language_detector.detect_language(file_path, content)
            functions = self.parser.function_extractor.extract_functions(content, language, file_path)
            documentation = self.parser.extract_documentation(content, language)
            
            file_data = {
                "path": file_path,
                "language": language,
                "content": content,
                "functions": functions,
                "documentation": documentation
            }
            
            # Generate summary
            try:
                summary = self.summarizer.summarize_file(
                    file_path=file_path, 
                    content=content, 
                    language=language, 
                    functions=functions
                )
                file_data["summary"] = summary
            except Exception as e:
                self.logger.error(f"Error generating summary for {file_path}: {str(e)}")
                file_data["summary"] = ""
                
            return file_data
            
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {str(e)}")
            return None

    def _process_file_batch(self, repository: "Repository", temp_dir: str, files: List[str]) -> List[Dict]:
        """
        Process a batch of files from the repository
        """
        results = []
        for file_path in files:
            try:
                processed_file = self._process_file(repository, file_path, temp_dir)
                if processed_file:
                    results.append(processed_file)
                    
                    # Save file to database
                    self.db_client.save_file(
                        repository_id=repository.id,
                        file_path=processed_file["path"],
                        language=processed_file["language"],
                        content=processed_file["content"],
                        functions=processed_file["functions"],
                        documentation=processed_file["documentation"],
                        summary=processed_file.get("summary", "")
                    )
            except Exception as e:
                self.logger.error(f"Error in file batch processing for {file_path}: {str(e)}")
        return results

    def _calculate_repository_metrics(self, files: List[Dict]) -> Dict:
        """
        Calculate metrics for the repository
        """
        try:
            languages = {}
            file_count = len(files)
            function_count = 0
            
            for file in files:
                language = file.get("language", "Unknown")
                functions = file.get("functions", [])
                
                # Count by language
                languages[language] = languages.get(language, 0) + 1
                
                # Count functions
                function_count += len(functions)
                
            return {
                "file_count": file_count,
                "function_count": function_count,
                "languages": languages
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating repository metrics: {str(e)}")
            return {"error": str(e)}
