# RepoMind Test Suite

This directory contains tests for the RepoMind application components.

## Test Organization

The tests are organized according to the components they test:

- `test_llm_client.py`: Tests for the LLM client that integrates with external AI services
- `test_code_analyzer.py`: Tests for code analysis components (language detection, function extraction, etc.)
- `test_repo_analyzer.py`: Tests for the repository analysis functionality
- `test_query_processor.py`: Tests for natural language query processing
- `test_repo_loader.py`: Tests for repository loading functionality
- `test_api_routes.py`: Tests for API endpoints

## Running Tests

You can run the entire test suite with:

```bash
python -m pytest tests/
```

Or run specific tests with:

```bash
# Run a specific test file
python -m pytest tests/test_llm_client.py

# Run with verbose output
python -m pytest tests/test_llm_client.py -v

# Run a specific test
python -m pytest tests/test_llm_client.py::TestLLMClient::test_init_openai
```

## Test Status

Current test status:
- Total tests: 21
- Passing: 12
- Skipped: 9

Note: Some tests are currently skipped due to their dependency on external services or complex setup.

## Test Development

When adding new tests:

1. Follow the existing test structure and naming conventions
2. Use fixtures for reusable setup
3. Mock external dependencies where appropriate
4. Include both unit tests and integration tests where applicable
5. Handle async operations correctly with pytest.mark.asyncio

## Troubleshooting

If you encounter test failures:

1. Check that all dependencies are installed (`pip install -r requirements.txt`)
2. Ensure environment variables for API keys are set if testing against real services
3. Verify that MongoDB is running if testing database operations
4. Check for circular imports which can cause test failures 