# Essential Development Commands

## Setup and Installation
```bash
# Check Python version (required: 3.11+)
python3 --version

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -e .[dev]

# Make CLI executable
chmod +x mtop
```

## Testing Commands
```bash
# Run all tests
python3 -m pytest tests/ -v

# Run with coverage
python3 -m pytest tests/ --cov=. --cov-report=term

# Run specific test categories
python3 -m pytest tests/test_cli.py -v          # CLI tests
python3 -m pytest tests/test_integration.py -v  # Integration tests
python3 -m pytest tests/test_kubectl_ld_unit.py -v  # Unit tests
```

## Code Quality Commands
```bash
# Format code
black .

# Sort imports  
isort .

# Type checking
mypy .

# Linting
pylint kubectl_ld/ config_loader.py column_engine.py

# Security scanning
safety check
bandit -r . -f json

# Code complexity analysis
radon cc . --min B
```

## Running the Application
```bash
# Basic usage
./mtop help
./mtop list
./mtop get gpt2

# Real-time monitoring
./mtop

# Mode switching
export LLD_MODE=live    # Use live Kubernetes cluster
export LLD_MODE=mock    # Use local mock files (default)

# Per-command mode override
./mtop --mode live list
./mtop --mode mock simulate canary
```

## System Commands (Darwin)
```bash
# Standard macOS commands work normally
ls -la
find . -name "*.py" 
grep -r "pattern" .
git status
```