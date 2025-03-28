# RepoMind

<div align="center">
  <h3>Repository Exploration and Query Assistant</h3>
  <p>Understand any codebase through natural language interaction</p>
</div>

## Overview

RepoMind is a Python-based application that allows developers to load, analyze, and query code repositories using natural language. The system understands repository structure, summarizes files, extracts functions, and stores all this information in a MongoDB database, enabling intuitive exploration of codebases.

## Key Features

- **Natural Language Queries** - Ask questions about code in plain English
- **Repository Analysis** - Automatically extract structure, metadata, and insights from code
- **Multi-Source Support** - Load repositories from GitHub, ZIP files, or local directories
- **Interactive Chat Interface** - Have a conversation about your codebase
- **Component Detection** - Identify key components and their relationships
- **File Structure Visualization** - Browse through repository files easily

## Architecture

RepoMind is structured into a frontend and a backend, each with its own FastAPI application:

### Backend Components

- **LLM Client** - Handles interactions with language models (OpenAI)
- **Database** - MongoDB integration for storing repository data
- **Query Processor** - Processes natural language queries
- **Repository Manager** - Handles loading repositories from different sources
- **Code Analyzer** - Extracts metadata, functions, and summaries from code

### Frontend Components

- **Web Interface** - FastAPI application with templates and static files
- **Interactive Chat** - Ask questions and get responses about the code
- **Repository Browser** - View repository structure and file details

## Getting Started

### Prerequisites

- Python 3.9+
- MongoDB
- API key for OpenAI or compatible LLM provider

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/repomind.git
   cd repomind
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:

   ```bash
   cp .env.example .env
   # Edit .env with your API keys and settings
   ```

5. Start MongoDB (if not already running):

   ```bash
   # If using Docker
   docker run -d -p 27017:27017 --name mongodb mongo:latest
   ```

6. Run the application:

   ```bash
   python src/main.py --port 8001
   ```

7. Open your browser and navigate to:

   ```
   http://localhost:8001
   ```

## Usage

### Loading a Repository

1. Navigate to the "Upload" section
2. Choose import method (GitHub URL, ZIP file, or local path)
3. Enter repository details and submit
4. Wait for the analysis to complete (status will change from "processing" to "ready")

### Exploring Code

1. Select a repository from your list
2. Click "View Details" to browse the repository structure
3. Click on files to view their contents
4. View key components and repository overview

### Chatting with Your Codebase

1. Select a repository
2. Click "Chat with Repository"
3. Enter your question in the chat box, for example:
   - "Explain the overall structure of this repository"
   - "What does the file X do?"
   - "Show me functions related to Y"
4. Review the AI-generated response and referenced code sections

## API Endpoints

RepoMind offers several API endpoints:

- **GET /api/repos** - List all repositories
- **GET /api/repos/{repo_id}** - Get repository details
- **GET /api/repos/{repo_id}/structure** - Get repository file structure
- **GET /api/repos/{repo_id}/components** - Get key components
- **POST /api/chat/{repo_id}** - Chat with the repository
- **POST /api/repos** - Create a new repository
- **DELETE /api/repos/{repo_id}** - Delete a repository

## Project Structure

- **src/**: Main source code
  - **backend/**: Backend API and processing
    - **api/**: API endpoints and routes
    - **analyzer/**: Code analysis utilities
    - **database/**: Database models and clients
    - **llm/**: LLM integration for queries
    - **repo_manager/**: Repository loading and management
  - **frontend/**: Web interface
    - **templates/**: HTML templates
    - **static/**: CSS, JavaScript, and other static assets
  - **agents/**: AI agents for code analysis
  - **main.py**: Application entry point

## Known Issues

- Some date formatting issues exist in the repository list display
- LLM integration occasionally returns errors with certain queries
- Code generation functionality may be limited or unreliable
- Metadata display can be inconsistent for certain repository types

## Limitations

While RepoMind is a useful tool, it has some limitations:

1. Analysis of very large repositories can be slow and resource-intensive
2. Some niche languages may not be properly detected or analyzed
3. Complex code patterns may not be analyzed correctly
4. Quality of responses depends on the underlying LLM provider
5. Using commercial LLM APIs may incur costs based on token usage
6. Code is sent to external LLM providers unless using a self-hosted model
7. Binary files, large assets, and compiled code are not analyzed
8. Poorly documented code may yield less insightful analysis

## Troubleshooting

If you encounter any issues:

1. Check MongoDB connection is active
2. Verify OpenAI API key is valid and has sufficient credits
3. For "proxies" errors with OpenAI, ensure you're using the latest version
4. If repository details don't display correctly, check browser console for errors
5. Restart the server if chat functionality stops working

## License

This project is licensed under the MIT License - see the LICENSE file for details.