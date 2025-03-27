"""
Language detector module.
Detects programming languages of code files based on file extensions and content patterns.
"""

import os
import re
from typing import Dict, Optional


class LanguageDetector:
    """Detector for programming languages in code files."""
    
    # Mapping of file extensions to languages
    EXTENSION_MAP: Dict[str, str] = {
        # Web
        '.html': 'HTML',
        '.htm': 'HTML',
        '.xhtml': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.sass': 'Sass',
        '.less': 'Less',
        '.js': 'JavaScript',
        '.jsx': 'JavaScript (React)',
        '.ts': 'TypeScript',
        '.tsx': 'TypeScript (React)',
        '.vue': 'Vue.js',
        '.svelte': 'Svelte',
        
        # Python
        '.py': 'Python',
        '.pyx': 'Cython',
        '.ipynb': 'Jupyter Notebook',
        
        # Java/JVM
        '.java': 'Java',
        '.class': 'Java bytecode',
        '.kt': 'Kotlin',
        '.kts': 'Kotlin Script',
        '.scala': 'Scala',
        '.groovy': 'Groovy',
        '.clj': 'Clojure',
        
        # C-family
        '.c': 'C',
        '.h': 'C header',
        '.cpp': 'C++',
        '.cc': 'C++',
        '.cxx': 'C++',
        '.hpp': 'C++ header',
        '.hxx': 'C++ header',
        '.cs': 'C#',
        '.vb': 'Visual Basic',
        
        # Systems
        '.go': 'Go',
        '.rs': 'Rust',
        '.swift': 'Swift',
        '.d': 'D',
        
        # Scripting
        '.rb': 'Ruby',
        '.rbw': 'Ruby',
        '.php': 'PHP',
        '.pl': 'Perl',
        '.pm': 'Perl module',
        '.t': 'Perl test',
        '.sh': 'Shell script',
        '.bash': 'Bash script',
        '.zsh': 'Zsh script',
        '.ps1': 'PowerShell',
        '.lua': 'Lua',
        
        # Functional
        '.hs': 'Haskell',
        '.lhs': 'Literate Haskell',
        '.ml': 'OCaml',
        '.mli': 'OCaml interface',
        '.fs': 'F#',
        '.fsi': 'F# interface',
        '.fsx': 'F# script',
        '.elm': 'Elm',
        '.erl': 'Erlang',
        '.ex': 'Elixir',
        '.exs': 'Elixir script',
        
        # Data/Config
        '.json': 'JSON',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.xml': 'XML',
        '.toml': 'TOML',
        '.ini': 'INI',
        '.csv': 'CSV',
        '.tsv': 'TSV',
        '.sql': 'SQL',
        
        # Documentation
        '.md': 'Markdown',
        '.rst': 'reStructuredText',
        '.tex': 'LaTeX',
        
        # Other
        '.r': 'R',
        '.dart': 'Dart',
        '.jl': 'Julia',
        '.nim': 'Nim',
        '.zig': 'Zig',
        '.v': 'V',
        '.crystal': 'Crystal',
    }
    
    # Mapping of patterns to languages for files without clear extensions
    PATTERN_MAP = [
        (r'^\s*<\?php', 'PHP'),
        (r'^\s*<\?=', 'PHP'),
        (r'^\s*#!/usr/bin/env\s+python', 'Python'),
        (r'^\s*#!/usr/bin/python', 'Python'),
        (r'^\s*#!/bin/bash', 'Bash script'),
        (r'^\s*#!/bin/sh', 'Shell script'),
        (r'^\s*#!/usr/bin/env\s+node', 'JavaScript'),
        (r'^\s*#!/usr/bin/env\s+ruby', 'Ruby'),
        (r'^\s*#!/usr/bin/ruby', 'Ruby'),
        (r'^\s*#!/usr/bin/env\s+perl', 'Perl'),
        (r'^\s*#!/usr/bin/perl', 'Perl'),
        (r'^\s*import\s+React', 'JavaScript (React)'),
        (r'^\s*package\s+main', 'Go'),
        (r'^\s*using\s+System;', 'C#'),
    ]
    
    @classmethod
    def detect_language(cls, file_path: str, content: Optional[str] = None) -> str:
        """
        Detect the programming language of a file.
        
        Args:
            file_path: Path to the file
            content: Optional file content (will be read if not provided)
            
        Returns:
            str: Detected programming language or "Unknown"
        """
        # First, try to detect by file extension
        _, ext = os.path.splitext(file_path.lower())
        if ext in cls.EXTENSION_MAP:
            return cls.EXTENSION_MAP[ext]
        
        # If extension detection failed and content is provided, try pattern matching
        if content:
            for pattern, language in cls.PATTERN_MAP:
                if re.search(pattern, content, re.MULTILINE):
                    return language
        
        # If all else fails, try to guess from the name
        filename = os.path.basename(file_path).lower()
        
        if filename == 'makefile' or filename.startswith('makefile.'):
            return 'Makefile'
        elif filename == 'dockerfile' or filename.startswith('dockerfile.'):
            return 'Dockerfile'
        elif filename == 'vagrantfile':
            return 'Ruby (Vagrant)'
        elif filename == 'jenkinsfile':
            return 'Groovy (Jenkins)'
        elif filename in ('package.json', 'package-lock.json'):
            return 'JSON (npm)'
        elif filename == 'gemfile':
            return 'Ruby (Bundler)'
        elif filename == 'rakefile':
            return 'Ruby (Rake)'
        elif filename in ('requirements.txt', 'setup.py'):
            return 'Python (Package)'
        elif filename in ('cargo.toml', 'cargo.lock'):
            return 'TOML (Rust)'
        
        # If we still couldn't determine the language
        return "Unknown" 