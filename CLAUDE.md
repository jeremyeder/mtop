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
# Python version check (3.12 preferred, 3.11+ required)
python3 --version

# Use virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install with development dependencies
pip install -e .[dev]

# Make CLI executable
chmod +x mtop
```

### Testing
```bash
# Run all tests
python3 -m pytest tests/ -v

# Run with coverage
python3 -m pytest tests/ --cov=. --cov-report=term

# Run specific test categories
python3 -m pytest tests/test_cli.py -v          # CLI integration tests
python3 -m pytest tests/test_new_architecture.py -v  # Architecture tests
python3 -m pytest tests/test_kubectl_ld_unit.py -v  # Unit tests

# Run single test
python3 -m pytest tests/test_cli.py::test_specific_function -v
```

### Code Quality and Linting
```bash
# MUST run all linters before pushing code to GitHub

# Use the automated lint script (recommended)
./scripts/lint.sh

# Or run individual tools:
# Format code (line length: 100)
black .

# Sort imports
isort .

# Basic syntax validation
python -m py_compile tests/*.py
python -m py_compile mtop/*.py
python -m py_compile config_loader.py
python -m py_compile column_engine.py

# Install pre-commit hooks (one-time setup)
pre-commit install

# Run pre-commit on all files
pre-commit run --all-files
```

### Linting Strategy for Legacy Codebases
- **Start Minimal**: Begin with formatting + syntax validation, gradually increase strictness
- **Focus on New Code**: Enforce quality on tests and new features rather than fixing everything at once
- **Enforcement Pattern**: Local tools auto-fix issues, CI tools check-only and fail if violations found
- **Pre-commit Hooks**: Essential for catching issues before they reach CI

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

### Demo Configuration Framework
```bash
# List all available demo scenarios
./scripts/demo.py --list

# Run pre-configured demo scenarios
./scripts/demo.py startup              # Small startup demo
./scripts/demo.py enterprise           # Large enterprise demo
./scripts/demo.py canary-failure       # Deployment failure demo
./scripts/demo.py cost-optimization    # Cost analysis demo
./scripts/demo.py research-lab         # Research environment demo

# Demo execution modes
./scripts/demo.py startup --dry-run           # Preview without execution
./scripts/demo.py enterprise --no-interactive # Perfect for presentations

# Create custom demo scenarios
./scripts/config-mixer.py               # Interactive demo creator
./scripts/config-mixer.py --quick       # Quick preset selection

# Test all demos work correctly
./test-demos.sh
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

### Technical Infrastructure Patterns
- **Virtual Environments**: Recreate rather than repair when corrupted
- **Build Artifacts**: Keep `dist/` directories clean of source files to avoid mypy conflicts
- **CI Pipeline Design**: Format → Lint → Test sequence with proper timeouts
- **Branch Protection**: Require status checks + PR approval + admin inclusion for enforcement

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

### Demo Framework
- `demos/recipes/` - Pre-configured demo scenarios (startup, enterprise, canary-failure, cost-optimization, research-lab)
- `demos/README.md` - Quick reference guide for demo framework
- `DEMO-GUIDE.md` - Comprehensive "explain like I'm 5" demo documentation
- `scripts/demo.py` - One-command demo execution tool
- `scripts/config-mixer.py` - Interactive demo configuration creator
- `test-demos.sh` - Automated testing for entire demo framework

### Testing
- `tests/test_cli_basics.py` - Basic CLI functionality tests
- `tests/test_config_basics.py` - Configuration loading tests
- `tests/test_container.py` - Dependency injection tests
- `tests/test_dataclasses.py` - Data structure validation tests
- `tests/test_imports.py` - Import and module structure tests

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

## GitHub Repository Management

### Branch Protection Setup
- **Private Repository Limitation**: GitHub free tier cannot set branch protection via API on private repos
- **Workaround**: Temporarily make repository public, configure protection, then make private again
- **API Command**: Use `gh api repos/:owner/:repo/branches/main/protection --method PUT --input protection.json`
- **Persistence**: Protection rules persist when going public→private but are lost on private→public→private transitions

### Repository Project Configuration
- **Always use repository-level projects**, never user-level projects
- Provides better integration with issues, PRs, and team workflows
- Repository projects appear in the "Projects" tab of the repo

### CI/CD Enforcement Strategy
- **CI checks alone are advisory only** - they don't prevent merging
- **Branch protection is required** for actual enforcement of quality gates
- **Essential protection settings**:
  - Require status checks to pass before merging
  - Require branches to be up to date before merging  
  - Require pull request reviews (minimum 1 approval)
  - Include administrators in restrictions
  - Disable force pushes and deletions

## Important Notes

- **Python 3.12**: Preferred version for development and testing (3.11+ minimum)
- **Mock vs Live**: Default is mock mode, live mode requires kubectl
- **Type Safety**: Strict mypy configuration enabled
- **Performance**: Async operations with caching for large datasets
- **Security**: Bandit scanning enabled, safety checks for vulnerabilities
- **Collaboration**: Uses GitHub issues for feature tracking and collaboration workflow
- **Git Workflow**: Always squash commits, sign releases with git signature, frequent commits with succinct messages
- **Virtual Environments**: Always use Python virtual environments to avoid affecting system packages

## Strategic Implementation Approaches

### Clean Slate Strategy for Technical Debt
- **Test Suite Rewrite**: Sometimes deletion and minimal rebuild is more efficient than incremental fixes
- **Incremental Enforcement**: Start with basic checks (formatting + syntax), gradually increase rigor
- **Infrastructure First**: Set up enforcement mechanisms before adding more rules
- **Focus on Prevention**: Better to prevent new problems than fix all existing ones at once

### Common Technical Pitfalls and Solutions
- **Duplicate Module Conflicts**: Check for source files in `dist/` directories causing mypy errors
- **Virtual Environment Corruption**: Recreate from scratch rather than attempting repairs
- **CI Timeout Issues**: Clean slate test approach often solves hanging/slow test suites
- **Linting Overwhelm**: Use minimal linting strategy for legacy codebases, focus on new code quality

## Demo Configuration Framework Patterns

### YAML Recipe Design
- **Simple Structure**: Use clear sections (environment, overrides, models, steps, outcomes)
- **Human-Readable**: Prioritize clarity over brevity in field names and descriptions
- **Environment Variable Integration**: Support MTOP_* overrides for real-time demo customization
- **Validation**: Include expected outcomes section for verification

### One-Command Execution Pattern
- **Simple Interface**: `./scripts/demo.py [scenario]` should be the primary entry point
- **Mode Support**: Always implement `--dry-run`, `--no-interactive`, and `--list` options
- **Error Handling**: Graceful failure with helpful error messages and suggestions
- **Path Resolution**: Use `Path(__file__).parent.parent` for reliable script-relative paths

### Mix-and-Match Architecture
- **Component Categories**: Environment (dev/prod/enterprise) + Topology (edge/enterprise/research) + Scenario (normal/spike/failure)
- **Combinatorial Design**: Each combination should produce a valid, meaningful demo
- **Custom Settings**: Allow QPS, costs, error rates to be overridden per demo
- **Save and Reuse**: Generated configurations should be saveable as new recipes

### Tool Integration Best Practices
- **Executable Scripts**: Always `chmod +x` demo tools for direct execution
- **Command Evolution**: Update demo scripts when underlying CLI commands change (e.g., `monitor` → `ldtop`)
- **Environment Validation**: Check for required executables before attempting demo execution
- **Fallback Strategies**: Provide meaningful alternatives when tools are missing

## Documentation Strategy: "Explain Like I'm 5"

### Simplification Techniques
- **Use Analogies**: Demos = video games, recipes = instruction cards, configuration = choosing game settings
- **Visual Hierarchy**: Emojis (🎯🚀🏢) and clear section headers improve scan-ability
- **Progressive Complexity**: Start with copy-paste commands, build to advanced customization
- **Real Examples**: Always provide working commands users can run immediately

### Multi-Format Documentation
- **Quick Reference**: `demos/README.md` for experienced users who need command reminders
- **Comprehensive Guide**: `DEMO-GUIDE.md` for step-by-step learning and troubleshooting
- **In-Tool Help**: `--help` flags and `--list` commands for contextual assistance
- **Test Documentation**: Automated validation that examples actually work

## Advanced Git Workflow Patterns

### Large Feature Integration
- **Separate Concerns**: Commit demo framework separately from other feature work when possible
- **Descriptive Messages**: Include usage examples and business impact in commit messages
- **PR Evolution**: Update existing PR descriptions when merging additional features to same branch
- **Lint Handling**: Expect and plan for formatting fixes after large feature additions

### Development Velocity Optimization
- **Start with Examples**: Create 2-3 working demo recipes before building the framework
- **Test Early**: Validate each component works independently before integration
- **Modular Architecture**: Separate recipe loading, environment setup, and execution concerns
- **User-Centric Design**: Optimize for the actual workflow of demo creators and presenters

### Pre-commit Hook Management
- **Python Version Specificity**: Use `python3` explicitly in hooks for cross-platform compatibility
- **Tool Sequence**: black → isort → syntax check provides good balance of auto-fix and validation
- **Incremental Adoption**: Start with basic formatting, gradually add stricter type and style checks
- **CI Alignment**: Local hooks should auto-fix, CI hooks should check-only and fail on violations