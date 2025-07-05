# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

mtop is a mock CLI tool for debugging and simulating `LLMInferenceService` CRDs (Custom Resource Definitions) in a Kubernetes-like environment without requiring a live cluster. It's designed for SREs, ML engineers, and platform teams to simulate rollouts, test failure modes, and provide real-time monitoring of LLM-serving infrastructure.

## Architecture

### Core Components
- **Main CLI**: `mtop` script with Python 3.11+ requirement
- **Package Structure**: `mtop/` module with modern dependency injection architecture
- **Interfaces**: Comprehensive Protocol definitions in `mtop/interfaces.py` for type safety
- **Container**: Lightweight DI container in `mtop/container.py` for dependency management
- **Mock System**: `mocks/` directory with CRs, configs, logs, and rollout topologies
- **Configuration**: YAML-based config system with environment variable overrides
- **Monitoring**: Real-time monitoring via `mtop` (like htop for LLMs)

### Key Design Patterns
- **Dependency Injection**: Uses type annotations and automatic resolution
- **Protocol-Based Design**: Strict interface contracts for extensibility
- **Dual-Mode Operation**: Mock mode (local files) vs live mode (actual Kubernetes)
- **Streaming Architecture**: Async operations with caching for performance

## Essential Commands

### Setup and Development
```bash
# Python version check (3.11+ required)
python3 --version

# Install dependencies
pip install -r requirements.txt

# Install with development dependencies
pip install -e .[dev]

# Make CLI executable
chmod +x mtop
```

### Testing
```bash
# Run all 53 tests
python3 -m pytest tests/ -v

# Run with coverage
python3 -m pytest tests/ --cov=. --cov-report=term

# Run specific test categories
python3 -m pytest tests/test_cli.py -v          # CLI integration tests
python3 -m pytest tests/test_new_architecture.py -v  # Architecture tests
python3 -m pytest tests/test_kubectl_ld_unit.py -v  # Unit tests
```

### Code Quality
```bash
# Format code (line length: 100)
black .

# Sort imports
isort .

# Type checking (strict mode enabled)
mypy .

# Linting
pylint mtop/ config_loader.py column_engine.py

# Security scanning
safety check
bandit -r . -f json

# Code complexity
radon cc . --min B
```

### Application Usage
```bash
# Basic operations
./mtop help
./mtop list
./mtop get gpt2
./mtop  # Real-time monitoring

# Mode switching
export LLD_MODE=live    # Use live Kubernetes cluster
export LLD_MODE=mock    # Use local mock files (default)

# Per-command mode override
./mtop --mode live list
./mtop --mode mock simulate canary
```

## Code Style and Conventions

### Formatting
- **Line Length**: 100 characters (black + pylint configured)
- **Type Hints**: Comprehensive typing with strict mypy configuration
- **Import Organization**: isort with black profile

### Naming
- **Classes**: PascalCase (`ConfigLoader`, `ColumnEngine`, `ModelMetrics`)
- **Functions**: snake_case (`load_config`, `get_enabled_columns`)
- **Constants**: UPPER_SNAKE_CASE (`RICH_AVAILABLE`, `CONFIG_AVAILABLE`)
- **Private**: Leading underscore (`_parse_config`, `_apply_env_overrides`)

### Architecture Patterns
- **Dataclasses**: Extensive use for configuration objects
- **Dependency Injection**: Use `@inject` decorator and type annotations
- **Interface Implementation**: Inherit from Protocol classes in `interfaces.py`
- **Error Handling**: Comprehensive validation with graceful fallbacks

## Key Files and Directories

### Core Module (`mtop/`)
- `interfaces.py` - Protocol definitions for type safety
- `container.py` - Dependency injection container
- `cache.py` - LRU and async caching systems
- `logging.py` - Structured logging with JSON formatting
- `implementations.py` - Concrete implementations of interfaces

### Configuration
- `config_loader.py` - YAML configuration with environment overrides
- `config.yaml` - Main configuration file
- `pyproject.toml` - Python packaging and tool configuration

### Mock Data
- `mocks/crs/` - LLMInferenceService custom resources (20 included)
- `mocks/config/` - Global configuration mocks
- `mocks/pod_logs/` - Simulated LLM service logs
- `mocks/topologies/` - Rollout scenario definitions

### Testing
- `tests/test_cli.py` - CLI integration tests
- `tests/test_new_architecture.py` - Architecture and DI tests
- `tests/test_kubectl_ld_unit.py` - Unit tests
- `tests/test_integration.py` - Full integration tests

## Development Workflow

### Adding New Features
1. Define interfaces in `interfaces.py` if needed
2. Implement concrete classes with DI registration
3. Add comprehensive tests with fixtures
4. Update configuration if necessary
5. Test in both mock and live modes

### Testing Strategy
- Use pytest fixtures for setup (`mtop_mock`, `mock_env`)
- Mock external dependencies (kubectl, file system)
- Test both success and failure scenarios
- Maintain comprehensive coverage (excludes test files)

### Configuration Changes
- Update `config.yaml` for new settings
- Add environment variable overrides in `config_loader.py`
- Document new configuration options

## Important Notes

- **Python 3.11+**: Required, version checked at startup
- **Mock vs Live**: Default is mock mode, live mode requires kubectl
- **Type Safety**: Strict mypy configuration enabled
- **Performance**: Async operations with caching for large datasets
- **Security**: Bandit scanning enabled, safety checks for vulnerabilities
- **Collaboration**: Uses GitHub issues for feature tracking and collaboration workflow