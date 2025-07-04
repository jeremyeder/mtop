# Code Style and Conventions

## Code Formatting
- **Line length**: 100 characters (configured in black and pylint)
- **Formatter**: Black with target Python 3.11/3.12
- **Import sorting**: isort with black profile
- **Type hints**: Used but not strictly enforced (disallow_untyped_defs=false)

## Naming Conventions
- **Classes**: PascalCase (e.g., `ConfigLoader`, `ColumnEngine`, `ModelMetrics`)
- **Functions/Methods**: snake_case (e.g., `load_config`, `get_enabled_columns`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `RICH_AVAILABLE`, `CONFIG_AVAILABLE`)
- **Private methods**: Leading underscore (e.g., `_parse_config`, `_apply_env_overrides`)

## Documentation Style
- **Docstrings**: Present but not following strict format (Google/NumPy style not enforced)
- **Type annotations**: Comprehensive use of typing module (List, Dict, Optional, Union)
- **Comments**: Minimal, code is generally self-documenting

## Data Structures
- **Dataclasses**: Extensive use with @dataclass decorator for configuration objects
- **Type safety**: Strong typing with validation in ConfigLoader
- **Immutability**: Field defaults using field(default_factory=list) pattern

## Error Handling
- **Custom exceptions**: Currently basic, room for improvement
- **Validation**: Comprehensive in ConfigLoader with detailed error messages  
- **Graceful degradation**: Fallback to mock mode when live cluster unavailable

## Testing Patterns
- **Fixtures**: pytest fixtures for test setup (kubectl_ld_mock, mock_env)
- **Mocking**: unittest.mock for external dependencies
- **Integration tests**: Full CLI lifecycle testing
- **Coverage**: Comprehensive excluding test files and version files