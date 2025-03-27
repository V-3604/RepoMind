# RepoMind

## Repository Exploration and Query Assistant

RepoMind is a powerful tool that allows developers to load, analyze, and query code repositories using natural language. The system understands repository structure, summarizes files, extracts functions, and stores all this information in a MongoDB database, enabling intuitive exploration of codebases.

### Core Features

- **Repository Ingestion**: Load repositories from GitHub URLs, ZIP files, or local paths
- **Comprehensive Analysis**: Automatic language detection, function extraction, and file summarization
- **Natural Language Queries**: Ask questions about the codebase and get intelligent responses
- **Code Generation**: Generate code snippets based on repository context
- **Conversation History**: Track and reference previous queries and responses

### Getting Started

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/macOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and add your configuration
6. Run the application: `python src/main.py`

### Usage

1. Load a repository using the web interface or API
2. Wait for the analysis to complete
3. Start asking questions about the codebase
4. Explore file summaries, functions, and repository structure

### Requirements

- Python 3.9+
- MongoDB
- OpenAI API key (or compatible LLM API)