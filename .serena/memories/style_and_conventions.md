# Code Style and Conventions

## Code Style
- **Type Hints**: Extensive use of type hints (from typing import Optional, List, etc.)
- **Docstrings**: Google-style docstrings for all classes and methods
- **Naming**: snake_case for variables and functions, PascalCase for classes
- **Error Handling**: Try-except blocks with fallback behavior
- **Data Classes**: Uses @dataclass for data models with field() for default factories

## Code Patterns Observed
- **Session Management**: Uses requests.Session() for connection reuse
- **Fallback Strategy**: When scraping fails, falls back to RSS summary
- **Configuration**: Headers configured to mimic real browsers
- **Delay Strategy**: Built-in delays between requests to avoid rate limiting

## Architecture Patterns
- **Separation of Concerns**: Clear separation between scraping, RSS monitoring, content generation
- **Data Models**: Centralized data models in core/models.py
- **Service Classes**: Each functionality wrapped in service classes
- **Legacy Support**: Backward compatibility with @property decorators

## Current Code Quality Issues
- No linting tools configured (Black, isort, flake8)
- No type checking (mypy)
- No testing framework set up
- No pre-commit hooks
- Hard-coded user agents and headers