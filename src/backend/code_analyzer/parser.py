"""
Code parser module.
Analyzes code files to extract metadata, detect languages, and organize parsing results.
"""

import os
import logging
from typing import Dict, Any, List

from src.backend.code_analyzer.language_detector import LanguageDetector
from src.backend.code_analyzer.function_extractor import FunctionExtractor


class CodeParser:
    """Parser for code files."""
    
    def __init__(self):
        """Initialize the code parser."""
        self.logger = logging.getLogger(__name__)
        self.language_detector = LanguageDetector()
        self.function_extractor = FunctionExtractor()
    
    def parse_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Parse a single file to extract metadata and functions.
        
        Args:
            file_path: Path to the file
            content: Content of the file
            
        Returns:
            dict: Parsed file data
        """
        try:
            # Detect language
            language = LanguageDetector.detect_language(file_path, content)
            
            # Extract functions
            functions = self.function_extractor.extract_functions(content, language, file_path)
            
            # Calculate file metrics
            line_count = content.count('\n') + 1
            size_bytes = len(content.encode('utf-8'))
            
            return {
                "path": file_path,
                "language": language,
                "functions": functions,
                "size_bytes": size_bytes,
                "line_count": line_count,
                "content": content  # Keep content for summarization later
            }
        except Exception as e:
            self.logger.error("Error parsing file %s: %s", file_path, str(e))
            return {
                "path": file_path,
                "language": "Unknown",
                "functions": [],
                "size_bytes": len(content.encode('utf-8')),
                "line_count": content.count('\n') + 1,
                "content": content,
                "error": str(e)
            }
    
    def parse_repository(self, repo_files: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Parse all files in a repository.
        
        Args:
            repo_files: Dictionary mapping file paths to file contents and metadata
            
        Returns:
            list: List of parsed file data
        """
        parsed_files = []
        
        for file_path, file_data in repo_files.items():
            # Skip files without content
            if "content" not in file_data:
                continue
            
            parsed_file = self.parse_file(file_path, file_data["content"])
            parsed_files.append(parsed_file)
        
        return parsed_files 