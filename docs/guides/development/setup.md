# Development Environment Setup

## 🛠️ Complete Development Environment Configuration

This guide sets up a complete development environment for contributing to the mtop LLM monitoring system.

## 📋 Prerequisites

### Required Software
- **Python 3.12** (preferred) or Python 3.11+ (minimum)
- **Git** 2.30+ for version control
- **Make** for build automation
- **Docker** (optional, for containerized testing)

### Recommended Tools
- **VS Code** or **PyCharm** for development
- **kubectl** for Kubernetes testing
- **k3d** or **kind** for local Kubernetes clusters

## 🚀 Setup Process

### 1. Repository Setup
```bash
# Fork the repository (if contributing)
gh repo fork jeremyeder/mtop --clone

# Or clone directly
git clone https://github.com/jeremyeder/mtop.git
cd mtop

# Add upstream remote (if forked)
git remote add upstream https://github.com/jeremyeder/mtop.git
```

### 2. Python Environment
```bash
# Verify Python version
python3 --version  # Should be 3.11+, preferably 3.12+

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Upgrade pip
pip install --upgrade pip

# Install development dependencies
pip install -r requirements.txt
pip install -e .[dev]
```

### 3. Pre-commit Hooks
```bash
# Install pre-commit hooks
pre-commit install

# Test pre-commit hooks
pre-commit run --all-files

# Expected: All hooks pass with potential auto-fixes
```

### 4. Development Tools Setup
```bash
# Make CLI executable
chmod +x mtop-main

# Verify installation
python3 mtop-main help
python3 -m pytest tests/ -v

# All tests should pass
```

## 🧪 Development Workflow

### Code Quality Tools
```bash
# Format code automatically
black .                    # Code formatting
isort .                    # Import sorting

# Run linters
pylint mtop/              # Code analysis
mypy mtop/                # Type checking
bandit -r mtop/           # Security scanning

# Or use the automated script
./scripts/lint.sh
```

### Testing
```bash
# Run all tests
python3 -m pytest tests/ -v

# Run with coverage
python3 -m pytest tests/ --cov=mtop --cov-report=term

# Run specific test categories
python3 -m pytest tests/test_cli_basics.py -v
python3 -m pytest tests/test_executive_view.py -v

# Run single test
python3 -m pytest tests/test_cli_basics.py::test_help_command -v
```

### Local Development
```bash
# Development with hot reload
export MTOP_DEV_MODE=true

# Use development configuration
export MTOP_CONFIG_FILE=config/development.yaml

# Run with verbose logging
export MTOP_LOG_LEVEL=DEBUG
```

## 📝 Code Style Guidelines

### Python Code Standards
- **Line Length**: 100 characters (configured in black and pylint)
- **Type Hints**: Required for all new code
- **Docstrings**: Google-style docstrings for public APIs
- **Import Organization**: isort with black profile

### Naming Conventions
```python
# Classes: PascalCase
class ModelMetrics:
    pass

# Functions: snake_case
def get_model_metrics():
    pass

# Constants: UPPER_SNAKE_CASE
CACHE_TIMEOUT = 300

# Private: Leading underscore
def _internal_function():
    pass
```

### Architecture Patterns
```python
# Use dataclasses for configuration
@dataclass
class Config:
    interval: int = 30
    enabled: bool = True

# Use protocols for interfaces
class MetricsProvider(Protocol):
    def get_metrics(self) -> List[Metric]:
        ...

# Use dependency injection
@inject
def service(provider: MetricsProvider) -> None:
    metrics = provider.get_metrics()
```

## 🔧 IDE Configuration

### VS Code Setup
Create `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.linting.mypyEnabled": true,
    "editor.rulers": [100],
    "editor.formatOnSave": true
}
```

### PyCharm Setup
1. **File → Settings → Project → Python Interpreter**
2. **Select existing environment**: `.venv/bin/python`
3. **Tools → External Tools**: Configure black, isort, pytest
4. **Editor → Code Style → Python**: Line length 100

## 🐳 Containerized Development

### Docker Setup
```bash
# Build development container
docker build -t mtop-dev .

# Run development container
docker run -it --rm \
  -v $(pwd):/workspace \
  -w /workspace \
  mtop-dev bash

# Inside container
pip install -r requirements.txt
python3 -m pytest tests/
```

### Local Kubernetes
```bash
# Create local cluster with k3d
k3d cluster create mtop-dev

# Or with kind
kind create cluster --name mtop-dev

# Test live mode
export LLD_MODE=live
python3 mtop-main list
```

## 📊 Development Environment Validation

### Functionality Tests
```bash
# Basic CLI functionality
python3 mtop-main help                     # ✓ Shows help
python3 mtop-main list                     # ✓ Lists models
python3 mtop-main get gpt-4-turbo         # ✓ Shows details

# Interactive features
python3 mtop-main                          # ✓ Launches dashboard
python3 mtop-main slo-dashboard --demo     # ✓ Shows SLO dashboard

# Demo scripts
python3 scripts/demo_phase1_quick.py       # ✓ Runs successfully
python3 scripts/demo_phase1_cost_optimization.py  # ✓ Completes
```

### Development Tools
```bash
# Code quality tools
black --check .                           # ✓ Code formatted
isort --check .                           # ✓ Imports sorted
python -m py_compile mtop/*.py            # ✓ Syntax valid
mypy mtop/                                # ✓ Type checking passes

# Testing infrastructure
python3 -m pytest tests/ -v              # ✓ All tests pass
python3 -m pytest --cov=mtop             # ✓ Coverage report
pre-commit run --all-files               # ✓ Pre-commit hooks pass
```

## 🚨 Troubleshooting

### Python Environment Issues
```bash
# Virtual environment not working
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Module not found errors
pip install -e .[dev]  # Install in development mode
```

### Import/Module Issues
```bash
# PYTHONPATH issues
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or use development install
pip install -e .
```

### Test Failures
```bash
# Clean test environment
python3 -m pytest --cache-clear tests/

# Verbose test output
python3 -m pytest tests/ -v -s

# Run tests in isolation
python3 -m pytest tests/test_cli_basics.py::test_help_command -v
```

### Git/Pre-commit Issues
```bash
# Reinstall pre-commit hooks
pre-commit uninstall
pre-commit install

# Fix pre-commit hook issues
pre-commit autoupdate
pre-commit run --all-files
```

## 📚 Development Resources
- [Contributing Guide](contributing.md) - How to contribute changes
- [Testing Guide](testing.md) - Testing best practices
- [Architecture](../../architecture/) - System architecture documentation
- [Examples](../../examples/) - Working code examples

---

*Complete development environment for professional LLM monitoring*