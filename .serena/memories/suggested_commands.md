# Suggested Development Commands

## Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On macOS/Linux

# Install dependencies  
pip install -r requirements.txt

# Install development dependencies (none currently defined)
# pip install -r requirements-dev.txt
```

## Running the Application
```bash
# Run with default settings (5 articles from each feed)
python src/content_pipeline/main.py

# Configure article limits per feed
python src/content_pipeline/main.py --freightwaves-limit 10 --freightcaviar-limit 3

# Disable a specific feed
python src/content_pipeline/main.py --disable-freightcaviar

# View all options
python src/content_pipeline/main.py --help
```

## Development Workflow Commands

### Code Quality (NOT CURRENTLY CONFIGURED)
```bash
# These would be ideal but are not set up yet:
# black .                    # Code formatting
# isort .                    # Import sorting
# flake8                     # Linting
# mypy src/                  # Type checking
```

### Testing (NOT CURRENTLY SET UP)
```bash
# No tests directory exists yet
# pytest                     # Run tests
# pytest --cov              # Run with coverage
```

### Git Workflow
```bash
git status
git add .
git commit -m "message"
git push
```

## System Commands (macOS)
```bash
ls -la                      # List files
find . -name "*.py"         # Find Python files
grep -r "pattern" src/      # Search in files
```

## Notes
- No testing framework is currently configured
- No linting/formatting tools are set up in requirements
- Project needs development tooling improvements