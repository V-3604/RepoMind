"""
Function extractor module.
Extracts functions and methods from code files based on language-specific rules.
"""

import re
import ast
import logging
from typing import List, Dict, Any, Optional, Tuple


class FunctionExtractor:
    """Extracts functions from code files."""
    
    def __init__(self):
        """Initialize the function extractor."""
        self.logger = logging.getLogger(__name__)
    
    def extract_functions(self, file_content: str, language: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract functions from file content based on language.
        
        Args:
            file_content: Content of the file
            language: Programming language
            file_path: Path to the file (for logging)
            
        Returns:
            list: List of extracted functions with metadata
        """
        # Normalize language name for handler selection
        normalized_lang = language.lower().split()[0].split('(')[0]
        
        try:
            # Dispatch to specific handler based on language
            if normalized_lang == 'python':
                return self._extract_python_functions(file_content, file_path)
            elif normalized_lang in ('javascript', 'typescript'):
                return self._extract_js_ts_functions(file_content, file_path)
            elif normalized_lang in ('c', 'c++', 'cpp'):
                return self._extract_c_cpp_functions(file_content, file_path)
            elif normalized_lang == 'java':
                return self._extract_java_functions(file_content, file_path)
            elif normalized_lang in ('ruby', 'rb'):
                return self._extract_ruby_functions(file_content, file_path)
            elif normalized_lang == 'go':
                return self._extract_go_functions(file_content, file_path)
            elif normalized_lang == 'rust':
                return self._extract_rust_functions(file_content, file_path)
            else:
                # For unsupported languages, try a generic regex approach
                return self._extract_generic_functions(file_content, file_path)
        except Exception as e:
            self.logger.error("Error extracting functions from %s: %s", file_path, str(e))
            return []
    
    def _extract_python_functions(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract functions from Python code."""
        functions = []
        
        try:
            tree = ast.parse(content)
            
            # Helper function to get code lines for a node
            def get_node_code(node):
                lines = content.splitlines()
                return "\n".join(lines[node.lineno-1:node.end_lineno])
            
            for node in ast.walk(tree):
                # Extract functions
                if isinstance(node, ast.FunctionDef):
                    # Get function signature
                    args = []
                    for arg in node.args.args:
                        args.append(arg.arg)
                    
                    # Handle keyword arguments
                    if node.args.kwarg:
                        args.append(f"**{node.args.kwarg.arg}")
                    
                    # Get function signature as string
                    signature = f"def {node.name}({', '.join(args)})"
                    
                    # Get function docstring if it exists
                    docstring = ast.get_docstring(node) or ""
                    
                    functions.append({
                        "name": node.name,
                        "signature": signature,
                        "description": docstring,
                        "start_line": node.lineno,
                        "end_line": node.end_lineno,
                        "code": get_node_code(node)
                    })
                
                # Extract class methods
                elif isinstance(node, ast.ClassDef):
                    for child in node.body:
                        if isinstance(child, ast.FunctionDef):
                            # Get method signature
                            args = []
                            for arg in child.args.args:
                                args.append(arg.arg)
                            
                            # Handle keyword arguments
                            if child.args.kwarg:
                                args.append(f"**{child.args.kwarg.arg}")
                            
                            # Get method signature as string
                            signature = f"def {child.name}({', '.join(args)})"
                            
                            # Get method docstring if it exists
                            docstring = ast.get_docstring(child) or ""
                            
                            functions.append({
                                "name": f"{node.name}.{child.name}",
                                "signature": signature,
                                "description": docstring,
                                "start_line": child.lineno,
                                "end_line": child.end_lineno,
                                "code": get_node_code(child)
                            })
            
            return functions
        except SyntaxError:
            self.logger.warning("Syntax error in Python file: %s", file_path)
            return self._extract_generic_functions(content, file_path)
    
    def _extract_js_ts_functions(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract functions from JavaScript/TypeScript code."""
        functions = []
        
        # Function declaration patterns
        patterns = [
            # Function declarations
            r'function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(([^)]*)\)\s*{',
            # Arrow functions with explicit name (const/let/var)
            r'(?:const|let|var)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>\s*{',
            # Method definitions in classes
            r'(?:async\s+)?([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(([^)]*)\)\s*{',
            # Class methods
            r'class\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*{',
        ]
        
        # Find all potential functions
        lines = content.splitlines()
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                start_pos = match.start()
                line_no = content[:start_pos].count('\n') + 1
                
                # Get the function name
                if 'class' in pattern:
                    # For classes, we need to extract methods separately
                    class_name = match.group(1)
                    class_start = line_no
                    class_end = self._find_closing_brace(content, match.end())
                    class_body = content[match.end():class_end]
                    
                    # Find methods in class
                    method_pattern = r'(?:async\s+)?([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(([^)]*)\)\s*{'
                    method_matches = re.finditer(method_pattern, class_body)
                    for method_match in method_matches:
                        method_name = method_match.group(1)
                        method_params = method_match.group(2)
                        method_start_pos = match.end() + method_match.start()
                        method_line_no = content[:method_start_pos].count('\n') + 1
                        method_end = self._find_closing_brace(content, method_start_pos + method_match.end() - method_match.start())
                        method_code = content[method_start_pos:method_end]
                        
                        functions.append({
                            "name": f"{class_name}.{method_name}",
                            "signature": f"{method_name}({method_params})",
                            "description": "",  # JS/TS doesn't have standard docstrings
                            "start_line": method_line_no,
                            "end_line": content[:method_end].count('\n') + 1,
                            "code": method_code
                        })
                else:
                    # Regular functions or named arrow functions
                    function_name = match.group(1)
                    params = match.group(2) if len(match.groups()) > 1 else ""
                    
                    # Find the end of the function (closing brace)
                    end_pos = self._find_closing_brace(content, match.end())
                    end_line = content[:end_pos].count('\n') + 1
                    
                    functions.append({
                        "name": function_name,
                        "signature": f"{function_name}({params})",
                        "description": "",  # JS/TS doesn't have standard docstrings
                        "start_line": line_no,
                        "end_line": end_line,
                        "code": content[start_pos:end_pos]
                    })
        
        return functions
    
    def _extract_c_cpp_functions(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract functions from C/C++ code."""
        functions = []
        
        # Function declaration pattern (simplified)
        # This is a simplified pattern and won't catch all C/C++ functions
        pattern = r'(?:[\w:]+\s+)+(\w+)\s*\(([^)]*)\)\s*(?:const)?\s*(?:override)?\s*(?:final)?\s*(?:=\s*(?:default|delete|0))?\s*(?:noexcept)?\s*{(?:[^{}]|{(?:[^{}]|{[^{}]*})*})*}'
        
        matches = re.finditer(pattern, content, re.DOTALL)
        for match in matches:
            function_name = match.group(1)
            params = match.group(2)
            
            # Get line numbers
            start_pos = match.start()
            end_pos = match.end()
            start_line = content[:start_pos].count('\n') + 1
            end_line = content[:end_pos].count('\n') + 1
            
            functions.append({
                "name": function_name,
                "signature": f"{function_name}({params})",
                "description": "",
                "start_line": start_line,
                "end_line": end_line,
                "code": match.group(0)
            })
        
        return functions
    
    def _extract_java_functions(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract methods from Java code."""
        functions = []
        
        # Class pattern
        class_pattern = r'class\s+(\w+)'
        classes = re.finditer(class_pattern, content)
        
        current_class = None
        for class_match in classes:
            current_class = class_match.group(1)
        
        # Method pattern (simplified)
        method_pattern = r'(?:public|private|protected|static|\s) +(?:[\w\<\>\[\]]+\s+)+(\w+) *\([^\)]*\) *(?:throws [^{]+)? *\{'
        
        matches = re.finditer(method_pattern, content)
        for match in matches:
            method_name = match.group(1)
            
            # Get method body
            start_pos = match.start()
            end_pos = self._find_closing_brace(content, match.end())
            
            # Get line numbers
            start_line = content[:start_pos].count('\n') + 1
            end_line = content[:end_pos].count('\n') + 1
            
            # Extract parameters
            params_match = re.search(r'\((.*?)\)', content[start_pos:match.end()])
            params = params_match.group(1) if params_match else ""
            
            full_name = f"{current_class}.{method_name}" if current_class else method_name
            
            functions.append({
                "name": full_name,
                "signature": f"{method_name}({params})",
                "description": "",
                "start_line": start_line,
                "end_line": end_line,
                "code": content[start_pos:end_pos]
            })
        
        return functions
    
    def _extract_ruby_functions(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract methods from Ruby code."""
        functions = []
        
        # Class pattern
        class_pattern = r'class\s+(\w+)'
        classes = re.finditer(class_pattern, content)
        
        current_class = None
        for class_match in classes:
            current_class = class_match.group(1)
        
        # Method pattern
        method_pattern = r'def\s+(\w+)(?:\(([^)]*)\))?'
        
        matches = re.finditer(method_pattern, content)
        for match in matches:
            method_name = match.group(1)
            params = match.group(2) if match.group(2) else ""
            
            # Get method body
            start_pos = match.start()
            
            # Find the end of the method (end keyword)
            end_pattern = r'\bend\b'
            end_matches = re.finditer(end_pattern, content[match.end():])
            
            # Take the first end that matches the method level
            if end_matches:
                end_match = next(end_matches, None)
                if end_match:
                    end_pos = match.end() + end_match.end()
                else:
                    end_pos = len(content)
            else:
                end_pos = len(content)
            
            # Get line numbers
            start_line = content[:start_pos].count('\n') + 1
            end_line = content[:end_pos].count('\n') + 1
            
            full_name = f"{current_class}.{method_name}" if current_class else method_name
            
            functions.append({
                "name": full_name,
                "signature": f"{method_name}({params})",
                "description": "",
                "start_line": start_line,
                "end_line": end_line,
                "code": content[start_pos:end_pos]
            })
        
        return functions
    
    def _extract_go_functions(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract functions from Go code."""
        functions = []
        
        # Function pattern
        func_pattern = r'func\s+(\w+)\s*\(([^)]*)\)\s*(?:\([^)]*\))?\s*{'
        
        matches = re.finditer(func_pattern, content)
        for match in matches:
            func_name = match.group(1)
            params = match.group(2)
            
            # Get function body
            start_pos = match.start()
            end_pos = self._find_closing_brace(content, match.end())
            
            # Get line numbers
            start_line = content[:start_pos].count('\n') + 1
            end_line = content[:end_pos].count('\n') + 1
            
            functions.append({
                "name": func_name,
                "signature": f"{func_name}({params})",
                "description": "",
                "start_line": start_line,
                "end_line": end_line,
                "code": content[start_pos:end_pos]
            })
        
        return functions
    
    def _extract_rust_functions(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract functions from Rust code."""
        functions = []
        
        # Function pattern
        func_pattern = r'(?:pub\s+)?fn\s+(\w+)\s*(?:<[^>]*>)?\s*\(([^)]*)\)(?:\s*->\s*[^{]*)?'
        
        matches = re.finditer(func_pattern, content)
        for match in matches:
            func_name = match.group(1)
            params = match.group(2)
            
            # Get function body start
            start_pos = match.start()
            
            # Find the opening brace
            open_brace_pos = content.find('{', match.end())
            if open_brace_pos == -1:
                continue
            
            end_pos = self._find_closing_brace(content, open_brace_pos + 1)
            if end_pos == -1:
                continue
            
            # Get line numbers
            start_line = content[:start_pos].count('\n') + 1
            end_line = content[:end_pos].count('\n') + 1
            
            functions.append({
                "name": func_name,
                "signature": f"{func_name}({params})",
                "description": "",
                "start_line": start_line,
                "end_line": end_line,
                "code": content[start_pos:end_pos]
            })
        
        return functions
    
    def _extract_generic_functions(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Generic function extraction for unsupported languages.
        This is a fallback method that uses simple regex patterns.
        """
        functions = []
        
        # Generic function patterns (will catch many common forms but not all)
        patterns = [
            # Standard function declaration
            r'(?:function|func|def|fn)\s+(\w+)\s*\(([^)]*)\)',
            # Method declaration
            r'(?:public|private|protected|static)?\s+(?:\w+\s+)*(\w+)\s*\(([^)]*)\)\s*{',
            # Arrow function with name
            r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                func_name = match.group(1)
                params = match.group(2) if len(match.groups()) > 1 else ""
                
                # Get approximate function body
                start_pos = match.start()
                # Look for an opening brace if not already at one
                if content[match.end()-1] != '{':
                    open_brace = content.find('{', match.end())
                    if open_brace == -1:
                        continue
                    end_pos = self._find_closing_brace(content, open_brace + 1)
                else:
                    end_pos = self._find_closing_brace(content, match.end())
                
                if end_pos == -1:
                    continue
                
                # Get line numbers
                start_line = content[:start_pos].count('\n') + 1
                end_line = content[:end_pos].count('\n') + 1
                
                functions.append({
                    "name": func_name,
                    "signature": f"{func_name}({params})",
                    "description": "",
                    "start_line": start_line,
                    "end_line": end_line,
                    "code": content[start_pos:end_pos]
                })
        
        return functions
    
    def _find_closing_brace(self, content: str, start_pos: int) -> int:
        """
        Find the position of the closing brace that matches the opening brace.
        
        Args:
            content: The content to search in
            start_pos: Position after the opening brace
            
        Returns:
            int: Position of the closing brace, or -1 if not found
        """
        stack = 1  # Start with the opening brace already on the stack
        pos = start_pos
        
        while pos < len(content):
            if content[pos] == '{':
                stack += 1
            elif content[pos] == '}':
                stack -= 1
                if stack == 0:
                    return pos + 1  # Return position after the closing brace
            pos += 1
        
        return -1  # Closing brace not found 