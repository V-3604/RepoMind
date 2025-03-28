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
            language = self.language_detector.detect_language(file_path, content)
            
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
        
    def extract_documentation(self, content: str, language: str) -> List[Dict[str, Any]]:
        """
        Extract documentation comments from code.
        
        Args:
            content: File content
            language: Programming language
            
        Returns:
            list: Extracted documentation
        """
        documentation = []
        
        # Different comment styles by language
        doc_patterns = {
            "Python": {
                "single": "#",
                "multi_start": '"""',
                "multi_end": '"""',
                "alternate_multi_start": "'''",
                "alternate_multi_end": "'''"
            },
            "JavaScript": {
                "single": "//",
                "multi_start": "/*",
                "multi_end": "*/",
                "jsdoc_start": "/**",
                "jsdoc_end": "*/"
            },
            "TypeScript": {
                "single": "//",
                "multi_start": "/*",
                "multi_end": "*/",
                "jsdoc_start": "/**",
                "jsdoc_end": "*/"
            },
            "Java": {
                "single": "//",
                "multi_start": "/*",
                "multi_end": "*/",
                "javadoc_start": "/**",
                "javadoc_end": "*/"
            },
            "C": {
                "single": "//",
                "multi_start": "/*",
                "multi_end": "*/"
            },
            "C++": {
                "single": "//",
                "multi_start": "/*",
                "multi_end": "*/"
            },
            "Ruby": {
                "single": "#",
                "multi_start": "=begin",
                "multi_end": "=end"
            },
            "Go": {
                "single": "//",
                "multi_start": "/*",
                "multi_end": "*/"
            }
        }
        
        # Default to C-style comments
        lang_patterns = doc_patterns.get(language, {
            "single": "//",
            "multi_start": "/*",
            "multi_end": "*/"
        })
        
        # Simple logic to extract multi-line comments
        lines = content.split('\n')
        in_multi_comment = False
        current_comment = ""
        
        for i, line in enumerate(lines):
            line_content = line.strip()
            
            # Check for multi-line comment start
            if not in_multi_comment:
                for start_pattern in [lang_patterns.get("multi_start"), 
                                     lang_patterns.get("jsdoc_start"),
                                     lang_patterns.get("alternate_multi_start")]:
                    if start_pattern and line_content.startswith(start_pattern):
                        in_multi_comment = True
                        current_comment = line_content[len(start_pattern):].strip()
                        if current_comment and any(end_pattern in current_comment for end_pattern in 
                                                 [lang_patterns.get("multi_end"), 
                                                  lang_patterns.get("jsdoc_end"),
                                                  lang_patterns.get("alternate_multi_end")] if end_pattern):
                            # Comment starts and ends on the same line
                            for end_pattern in [lang_patterns.get("multi_end"), 
                                               lang_patterns.get("jsdoc_end"),
                                               lang_patterns.get("alternate_multi_end")]:
                                if end_pattern and end_pattern in current_comment:
                                    current_comment = current_comment[:current_comment.find(end_pattern)].strip()
                                    break
                            if current_comment:
                                documentation.append({
                                    "type": "multi",
                                    "content": current_comment,
                                    "line": i + 1
                                })
                            in_multi_comment = False
                            current_comment = ""
                        break
            # Check for multi-line comment end
            elif in_multi_comment:
                for end_pattern in [lang_patterns.get("multi_end"), 
                                   lang_patterns.get("jsdoc_end"),
                                   lang_patterns.get("alternate_multi_end")]:
                    if end_pattern and end_pattern in line_content:
                        current_comment += " " + line_content[:line_content.find(end_pattern)].strip()
                        documentation.append({
                            "type": "multi",
                            "content": current_comment,
                            "line": i + 1
                        })
                        in_multi_comment = False
                        current_comment = ""
                        break
                if in_multi_comment:
                    # Still in multi-line comment
                    current_comment += " " + line_content
            
            # Check for single-line comments
            single_comment = lang_patterns.get("single")
            if single_comment and not in_multi_comment and line_content.startswith(single_comment):
                comment_text = line_content[len(single_comment):].strip()
                if comment_text:
                    documentation.append({
                        "type": "single",
                        "content": comment_text,
                        "line": i + 1
                    })
        
        return documentation 

    def extract_functions(self, content: str, language: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract functions from code content.
        
        Args:
            content: File content
            language: Programming language
            file_path: Path to the file
            
        Returns:
            list: Extracted functions
        """
        return self.function_extractor.extract_functions(content, language, file_path) 