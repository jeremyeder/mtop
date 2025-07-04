# Technology Stack

## Core Technologies
- **Python 3.11+** (required, version checked at startup)
- **PyYAML** (6.0-7.0) - Configuration file parsing
- **termcolor** (2.3.0-4.0) - Terminal color output
- **rich** (13.0.0-15.0) - Advanced terminal UI for ldtop monitoring
- **readchar** (4.0.0-5.0) - Keyboard input handling for interactive features

## Development Tools
- **pytest** (8.0+) - Testing framework with 53 tests
- **pytest-cov** (4.0+) - Test coverage reporting  
- **black** (23.0+) - Code formatting (100 char line length)
- **isort** (5.12+) - Import sorting
- **mypy** (1.0+) - Type checking (though disallow_untyped_defs=false)
- **pylint** (2.17+) - Code linting
- **radon** (6.0+) - Code complexity analysis

## Security & Quality
- **safety** (3.0+) - Dependency vulnerability scanning
- **bandit** (1.7+) - Security issue detection
- **Coverage reporting** with comprehensive exclusions

## Build System
- **setuptools** (45+) with setuptools_scm for versioning
- **pyproject.toml** configuration for modern Python packaging
- **Entry points**: mtop and watch-rollout scripts

## External Dependencies
- **kubectl** (when in live mode) - Kubernetes CLI tool
- **Darwin/macOS** system (development platform)