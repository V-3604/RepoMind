"""
Query processor for RepoMind.
Handles processing of natural language queries about repositories.
"""

import logging
import re
import traceback
import json
from typing import Dict, List, Any, Optional
from bson import ObjectId

from src.agents.llm_client import LLMClient
from config import MAX_TOKENS


class QueryProcessor:
    """Query processor class for handling repository queries."""
    
    def __init__(self, db_client):
        """
        Initialize the processor with a database client.
        
        Args:
            db_client: MongoDB client instance
        """
        self.db_client = db_client
        self.logger = logging.getLogger(__name__)
        self.llm_client = LLMClient()
        
    async def process_query(self, repo_id: str, query: str, file_path: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a query about a repository.
        
        Args:
            repo_id: Repository ID
            query: User query
            file_path: Optional specific file path to restrict query context
            context: Optional additional context
            
        Returns:
            dict: Response with text, code, and references
        """
        try:
            self.logger.info(f"Processing query for repository {repo_id}: {query}")
            
            # Get repository information
            try:
                if ObjectId.is_valid(repo_id):
                    # Try with ObjectId first
                    repo = self.db_client.db.repositories.find_one({"_id": ObjectId(repo_id)})
                if not repo:
                    # Try with string ID
                    repo = self.db_client.db.repositories.find_one({"_id": repo_id})
            except Exception as e:
                self.logger.error(f"Error finding repository: {str(e)}")
                repo = None
                
            if not repo:
                self.logger.error(f"Repository {repo_id} not found")
                return {
                    "text": f"Repository not found or could not be accessed. Please make sure the repository exists.",
                    "code": None,
                    "referenced_files": [],
                    "confidence": 0.0
                }
            
            # Prepare context for LLM query
            context_data = await self._prepare_context(repo_id, query, file_path)
            
            # Add user-provided context if available
            if context:
                context_data.update(context)
            
            # Define the prompt for the LLM
            prompt = self._build_prompt(query, repo, context_data)
            
            # Log the context data
            self.logger.info(f"Generated context for query: Files: {len(context_data.get('relevant_files', []))}, Repo summary length: {len(context_data.get('repo_summary', ''))}")
            
            # Get response from LLM
            llm_response = self.llm_client.generate_text(prompt, max_tokens=1500)
            
            # Check if there's an error in the response
            if "Error generating text:" in llm_response:
                self.logger.error(f"Error from LLM: {llm_response}")
                return {
                    "text": f"I'm sorry, I encountered an error while analyzing this repository. Please try a different question or try again later.",
                    "code": None,
                    "referenced_files": [],
                    "confidence": 0.0
                }
            
            # Parse the response
            parsed_response = self._parse_response(llm_response)
            
            # Save the query and response
            self._save_query(repo_id, query, parsed_response)
            
            return parsed_response
            
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {
                "text": f"I encountered an error while processing your query. Please try asking a different question.",
                "code": None,
                "referenced_files": [],
                "confidence": 0.0
            }
    
    async def _prepare_context(self, repo_id: str, query: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Prepare context for the query.
        
        Args:
            repo_id: Repository ID
            query: User query
            file_path: Optional specific file path
            
        Returns:
            dict: Context data
        """
        context = {}
        
        # If a specific file is provided, use it as context
        if file_path:
            file = self.db_client.db.files.find_one({"repo_id": repo_id, "path": file_path})
            if file:
                context["current_file"] = {
                    "path": file_path,
                    "content": file.get("content", ""),
                    "language": file.get("language", ""),
                    "summary": file.get("summary", "")
                }
                
                # Get functions in this file
                functions = list(self.db_client.db.functions.find({"repo_id": repo_id, "file_path": file_path}))
                context["functions"] = functions
                
                self.logger.info(f"Added specific file context: {file_path}")
        
        # Get repository summary
        try:
            if ObjectId.is_valid(repo_id):
                repo = self.db_client.db.repositories.find_one({"_id": ObjectId(repo_id)})
            if not repo:
                repo = self.db_client.db.repositories.find_one({"_id": repo_id})
                
            if repo:
                context["repo_summary"] = repo.get("summary", "")
                context["repo_name"] = repo.get("name", "Unknown Repository")
                context["repo_type"] = repo.get("type", repo.get("source_type", "Unknown"))
        except Exception as e:
            self.logger.error(f"Error getting repository for context: {str(e)}")
        
        # Get list of all files in the repository
        try:
            all_files = list(self.db_client.db.files.find({"repo_id": repo_id}, {"path": 1, "_id": 0}))
            file_paths = [f["path"] for f in all_files if "path" in f]
            context["all_files"] = file_paths
            self.logger.info(f"Added {len(file_paths)} files to context")
        except Exception as e:
            self.logger.error(f"Error getting all files: {str(e)}")
            context["all_files"] = []
        
        # Select relevant files based on the query
        relevant_files = await self._find_relevant_files(repo_id, query)
        context["relevant_files"] = relevant_files[:5]  # Limit to top 5 relevant files
        self.logger.info(f"Found {len(relevant_files)} relevant files, using top 5")
        
        return context
    
    async def _find_relevant_files(self, repo_id: str, query: str) -> List[Dict[str, Any]]:
        """
        Find files relevant to the query.
        
        Args:
            repo_id: Repository ID
            query: User query
            
        Returns:
            list: Relevant files with metadata
        """
        # Extract keywords from the query
        keywords = self._extract_keywords(query)
        self.logger.info(f"Extracted keywords from query: {keywords}")
        
        relevant_files = []
        
        # Check for files that match keywords in path or summary
        for keyword in keywords:
            # Use case-insensitive regex search in path and summary
            try:
                files = self.db_client.db.files.find({
                    "repo_id": repo_id,
                    "$or": [
                        {"path": {"$regex": keyword, "$options": "i"}},
                        {"summary": {"$regex": keyword, "$options": "i"}}
                    ]
                }, {"path": 1, "summary": 1, "language": 1, "content": 1, "_id": 0})
                
                for file in files:
                    # Only add if not already in the list
                    if file not in relevant_files:
                        # Add the file content but limit its size
                        if "content" in file and file["content"]:
                            # Truncate content to avoid token limits
                            file["content"] = file["content"][:MAX_TOKENS//10]
                        relevant_files.append(file)
            except Exception as e:
                self.logger.error(f"Error searching for files with keyword {keyword}: {str(e)}")
        
        # Check for functions that match keywords
        for keyword in keywords:
            try:
                functions = self.db_client.db.functions.find({
                    "repo_id": repo_id,
                    "$or": [
                        {"name": {"$regex": keyword, "$options": "i"}},
                        {"description": {"$regex": keyword, "$options": "i"}}
                    ]
                }, {"file_path": 1, "name": 1, "description": 1, "code": 1, "_id": 0})
                
                for func in functions:
                    file_path = func.get("file_path", "")
                    # Get the file data if it exists
                    file = self.db_client.db.files.find_one({"repo_id": repo_id, "path": file_path}, {"path": 1, "summary": 1, "language": 1, "content": 1, "_id": 0})
                    
                    if file and file not in relevant_files:
                        # Add function data to the file
                        if "functions" not in file:
                            file["functions"] = []
                        file["functions"].append(func)
                        
                        # Add the file content but limit its size
                        if "content" in file and file["content"]:
                            # Truncate content to avoid token limits
                            file["content"] = file["content"][:MAX_TOKENS//10]
                            
                        relevant_files.append(file)
            except Exception as e:
                self.logger.error(f"Error searching for functions with keyword {keyword}: {str(e)}")
        
        # If no relevant files found, try to get some common important files
        if not relevant_files:
            common_files = ["README.md", "setup.py", "requirements.txt", "package.json", "main.py", "app.py", "index.js"]
            for file_name in common_files:
                try:
                    file = self.db_client.db.files.find_one({
                        "repo_id": repo_id,
                        "path": {"$regex": file_name + "$", "$options": "i"}
                    }, {"path": 1, "summary": 1, "language": 1, "content": 1, "_id": 0})
                    
                    if file and file not in relevant_files:
                        # Add the file content but limit its size
                        if "content" in file and file["content"]:
                            # Truncate content to avoid token limits
                            file["content"] = file["content"][:MAX_TOKENS//10]
                        relevant_files.append(file)
                except Exception as e:
                    self.logger.error(f"Error searching for common file {file_name}: {str(e)}")
        
        return relevant_files
    
    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract keywords from the query.
        
        Args:
            query: User query
            
        Returns:
            list: Keywords from the query
        """
        # Remove common stop words
        stop_words = {"the", "a", "an", "in", "on", "at", "is", "are", "was", "were", "and", "or", "but", "of", "for", "with", "about", "to", "from"}
        words = query.lower().split()
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Extract quoted phrases
        quoted_phrases = re.findall(r'"([^"]*)"', query)
        
        # Extract file extensions and potential file names
        file_extensions = [word for word in words if word.startswith('.') and len(word) > 1]
        potential_files = [word for word in words if '.' in word and not word.startswith('.') and not word.endswith('.')]
        
        return keywords + quoted_phrases + file_extensions + potential_files
    
    def _build_prompt(self, query: str, repo: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Build a prompt for the LLM based on the query and context.
        
        Args:
            query: User query
            repo: Repository information
            context: Context data
            
        Returns:
            str: Prompt for the LLM
        """
        repo_name = repo.get('name', 'Unknown Repository')
        repo_summary = context.get('repo_summary', 'No summary available')
        
        prompt = f"""
        You are RepoMind, an AI assistant specialized in analyzing and explaining code repositories.
        
        Repository: {repo_name}
        Repository Summary: {repo_summary}
        
        User Query: {query}
        
        """
        
        # Add all available files list for reference
        if "all_files" in context and context["all_files"]:
            prompt += "\nFiles in this repository:\n"
            for file_path in context["all_files"][:50]:  # Limit to 50 files to avoid token issues
                prompt += f"- {file_path}\n"
            
            if len(context["all_files"]) > 50:
                prompt += f"... and {len(context['all_files']) - 50} more files\n"
        
        # Add current file context if available
        if "current_file" in context:
            file = context["current_file"]
            prompt += f"""
            Current File: {file.get('path', '')}
            Language: {file.get('language', '')}
            File Summary: {file.get('summary', '')}
            
            File Content:
            ```{file.get('language', '')}
            {file.get('content', '')[:MAX_TOKENS//4]}  # Limit content to avoid token limits
            ```
            
            """
        
        # Add relevant files
        if "relevant_files" in context and context["relevant_files"]:
            prompt += "\nRelevant Files:\n"
            for file in context["relevant_files"]:
                file_path = file.get('path', 'Unknown file')
                file_summary = file.get('summary', 'No summary available')
                file_language = file.get('language', '')
                file_content = file.get('content', '')
                
                prompt += f"--- File: {file_path} ---\n"
                prompt += f"Language: {file_language}\n"
                prompt += f"Summary: {file_summary}\n"
                
                # Add truncated content
                if file_content:
                    prompt += f"Content snippet:\n```{file_language}\n{file_content[:MAX_TOKENS//5]}\n```\n"
                
                # Add functions in this file if available
                if "functions" in file and file["functions"]:
                    prompt += "Functions in this file:\n"
                    for func in file["functions"][:3]:  # Limit to 3 functions per file
                        prompt += f"- {func.get('name', '')}: {func.get('description', '')[:100]}...\n"
                    
                    if len(file["functions"]) > 3:
                        prompt += f"... and {len(file['functions']) - 3} more functions\n"
                
                prompt += "\n"
        
        # Add functions if available
        if "functions" in context and context["functions"]:
            prompt += "\nRelevant Functions:\n"
            for func in context["functions"][:5]:  # Limit to 5 functions
                prompt += f"- {func.get('name', '')}: {func.get('description', '')[:100]}...\n"
            
            if len(context["functions"]) > 5:
                prompt += f"... and {len(context['functions']) - 5} more functions\n"
        
        prompt += """
        Please provide a detailed, informative response to the user's query based on the repository context provided.
        If you don't have enough information to answer the query, please acknowledge this limitation instead of speculating.
        If the query asks for code, include relevant, well-structured code snippets.
        
        Format your response as follows:
        
        ANSWER: <detailed explanation answering the user's query>
        
        CODE (if applicable):
        ```language
        <code snippets if requested or helpful>
        ```
        
        REFERENCES:
        <list of specific files or functions referenced in your answer>
        """
        
        return prompt
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the LLM response into a structured format.
        
        Args:
            response: Raw LLM response
            
        Returns:
            dict: Structured response
        """
        text = ""
        code = None
        referenced_files = []
        confidence = 0.9  # Default confidence
        
        # Extract answer
        answer_match = re.search(r'ANSWER:(.*?)(?:CODE:|REFERENCES:|$)', response, re.DOTALL)
        if answer_match:
            text = answer_match.group(1).strip()
        else:
            text = response.strip()
        
        # Extract code
        code_match = re.search(r'CODE.*?:\s*```.*?\n(.*?)```', response, re.DOTALL)
        if code_match:
            code = code_match.group(1).strip()
        
        # Extract references
        refs_match = re.search(r'REFERENCES:(.*?)$', response, re.DOTALL)
        if refs_match:
            refs_text = refs_match.group(1).strip()
            referenced_files = [ref.strip() for ref in refs_text.split('\n') if ref.strip()]
        
        return {
            "text": text,
            "code": code,
            "referenced_files": referenced_files,
            "confidence": confidence
        }
    
    def _save_query(self, repo_id: str, query: str, response: Dict[str, Any]) -> None:
        """
        Save the query and response to the database.
        
        Args:
            repo_id: Repository ID
            query: User query
            response: Processed response
        """
        try:
            query_doc = {
                "repo_id": repo_id,
                "query": query,
                "response": response,
                "timestamp": self.db_client.db.client.server_info().get("localTime", None)
            }
            
            self.db_client.db.queries.insert_one(query_doc)
            
        except Exception as e:
            self.logger.error(f"Error saving query: {str(e)}")
    
    async def get_query_history(self, repo_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get query history for a repository.
        
        Args:
            repo_id: Repository ID
            limit: Maximum number of queries to return
            
        Returns:
            list: Query history
        """
        try:
            queries = list(self.db_client.db.queries.find(
                {"repo_id": repo_id},
                {"query": 1, "response": 1, "timestamp": 1, "_id": 0}
            ).sort("timestamp", -1).limit(limit))
            
            return queries
            
        except Exception as e:
            self.logger.error(f"Error getting query history: {str(e)}")
            return []