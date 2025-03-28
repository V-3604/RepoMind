"""
Summarizer module.
Generates summaries for code files and repositories using LLM.
"""

import logging
from typing import Dict, Any, List, Optional

from src.agents.llm_client import LLMClient


class CodeSummarizer:
    """Summarizes code files and repositories."""
    
    def __init__(self, db_client=None):
        """
        Initialize the code summarizer.
        
        Args:
            db_client: Optional database client
        """
        self.db_client = db_client
        self.logger = logging.getLogger(__name__)
        self.llm_client = LLMClient()
        
        # Templates for LLM prompts
        self.file_summary_template = """
        Please provide a concise summary of the following code file.
        Focus on what the code does, its main purpose, and key functionality.
        Keep the summary brief (150 words max) but informative.
        
        File path: {file_path}
        Language: {language}
        
        Number of functions/methods: {function_count}
        Function names: {function_names}
        
        Code Content:
        ```{language}
        {content}
        ```
        
        Summary:
        """
        
        self.repo_summary_template = """
        Please provide a concise summary of this code repository.
        Focus on the repository's purpose, architecture, and key components.
        
        Repository name: {repo_name}
        Number of files: {file_count}
        
        Top languages used:
        {languages}
        
        Key components/directories:
        {directories}
        
        File summaries:
        {file_summaries}
        
        Based on the information above, provide a comprehensive summary of the repository.
        Include information about the repository's purpose, architecture, main components, 
        and how they work together. Keep the summary concise (250 words max) but informative.
        
        Repository Summary:
        """
    
    def summarize_file(self, file_path: str, content: str, language: str, 
                      functions: List[Dict] = None) -> str:
        """
        Generate a summary for a code file.
        
        Args:
            file_path: Path to the file
            content: File content
            language: Programming language
            functions: Optional list of functions in the file
            
        Returns:
            str: Summary text
        """
        try:
            # Prepare prompt for LLM
            prompt = f"""
            Summarize the following {language} code file:
            
            File path: {file_path}
            
            ```{language}
            {content[:4000]}  # Truncate long files
            ```
            
            {"Functions: " + ", ".join([f.get('name', '') for f in (functions or [])]) if functions else ""}
            
            Please provide a concise summary of what this file does and its main components.
            Focus on the overall purpose, key functions/classes, and how it might fit into a larger codebase.
            """
            
            response = self.llm_client.generate_text(prompt, max_tokens=500)
            return response.strip()
            
        except Exception as e:
            self.logger.error(f"Error summarizing file {file_path}: {str(e)}")
            return f"Error: {str(e)}"
    
    def summarize_repository(self, parsed_files: List[Dict[str, Any]], repo_name: str = "Unknown Repository") -> str:
        """
        Generate a summary for an entire repository.
        
        Args:
            parsed_files: List of parsed file data
            repo_name: Name of the repository (optional)
            
        Returns:
            str: Repository summary
        """
        try:
            # Count file types
            language_counts = {}
            for file in parsed_files:
                lang = file.get("language", "Unknown")
                language_counts[lang] = language_counts.get(lang, 0) + 1
            
            # Sort languages by count
            sorted_languages = sorted(language_counts.items(), key=lambda x: x[1], reverse=True)
            languages_str = "\n".join([f"- {lang}: {count} files" for lang, count in sorted_languages[:5]])
            
            # Get directories
            directories = {}
            for file in parsed_files:
                path = file.get("path", "")
                parts = path.split("/")
                if len(parts) > 1:
                    dir_name = parts[0]
                    directories[dir_name] = directories.get(dir_name, 0) + 1
            
            # Sort directories by file count
            sorted_dirs = sorted(directories.items(), key=lambda x: x[1], reverse=True)
            directories_str = "\n".join([f"- {dir_name}: {count} files" for dir_name, count in sorted_dirs[:5]])
            
            # Get summaries for important files
            important_files = self._select_important_files(parsed_files)
            file_summaries = []
            
            for file in important_files:
                # If the file already has a summary, use it, otherwise generate one
                if "summary" in file and file["summary"]:
                    summary = file["summary"]
                else:
                    summary = self.summarize_file(file["path"], file.get("content", ""), file.get("language", "Unknown"), file.get("functions", []))
                
                file_summaries.append(f"- {file['path']}: {summary}")
            
            # Format file summaries as string
            file_summaries_str = "\n".join(file_summaries)
            
            # Format the prompt
            prompt = self.repo_summary_template.format(
                repo_name=repo_name,
                file_count=len(parsed_files),
                languages=languages_str,
                directories=directories_str,
                file_summaries=file_summaries_str
            )
            
            # Call LLM to generate summary
            summary = self.llm_client.generate_text(prompt)
            return summary.strip()
        
        except Exception as e:
            self.logger.error("Error summarizing repository %s: %s", repo_name, str(e))
            return f"Failed to generate repository summary: {str(e)}"
    
    def _select_important_files(self, parsed_files: List[Dict[str, Any]], max_files: int = 10) -> List[Dict[str, Any]]:
        """
        Select the most important files from a repository for summarization.
        
        Args:
            parsed_files: List of parsed file data
            max_files: Maximum number of files to select
            
        Returns:
            list: List of important files
        """
        # Calculate importance score for each file
        scored_files = []
        for file in parsed_files:
            path = file.get("path", "")
            
            # Skip certain files
            if (path.endswith((".md", ".txt", ".json", ".yml", ".yaml", ".toml", ".ini")) or
                "test" in path.lower() or
                "vendor" in path.lower() or
                "node_modules" in path.lower()):
                continue
            
            # Score based on number of functions
            function_score = len(file.get("functions", []))
            
            # Score based on file size
            size_score = min(file.get("size_bytes", 0) / 1000, 5)  # Cap at 5
            
            # Score based on file name importance
            name_score = 0
            important_names = ["main", "index", "app", "server", "client", "core", "util", "base"]
            for name in important_names:
                if name in path.lower():
                    name_score += 2
            
            # Calculate total score
            total_score = function_score + size_score + name_score
            
            scored_files.append((file, total_score))
        
        # Sort files by score and take top N
        sorted_files = sorted(scored_files, key=lambda x: x[1], reverse=True)
        important_files = [file for file, _ in sorted_files[:max_files]]
        
        return important_files 