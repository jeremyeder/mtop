# Codebase Structure

## Root Directory Layout
```
kubectl-ld/
├── kubectl-ld                 # Main CLI entry point (Python script)
├── kubectl_ld/               # Python package
│   ├── __init__.py           # Package entry point
│   └── watch_rollout.py      # Rollout watching functionality
├── config_loader.py          # Configuration system (dataclasses, validation)
├── column_engine.py          # Table rendering and display logic
├── build.py                  # Project building utilities
├── mocks/                    # Mock data directory
│   ├── crs/                  # LLMInferenceService CRs (JSON files)
│   ├── config/               # Global configuration mocks
│   ├── pod_logs/             # Simulated log files
│   └── topologies/           # Rollout scenario definitions
├── tests/                    # Test suite (53 tests)
│   ├── test_cli.py           # CLI integration tests
│   ├── test_integration.py   # Full workflow tests
│   ├── test_kubectl_ld.py    # Core functionality tests
│   └── test_*.py             # Additional test modules
├── demo_*.py                 # Demo components (to be refactored to plugins)
├── watch_rollout.py          # Standalone rollout monitoring
└── scripts/                  # Build and utility scripts
```

## Key Components

### Core Classes
- **ConfigLoader**: YAML configuration parsing with validation
- **ColumnEngine**: Table rendering with 17 methods for formatting
- **TableRenderer**: Rich-based table display
- **ModelMetrics**: Real-time metrics simulation for ldtop
- **LLMTopMonitor**: htop-like monitoring interface

### Architecture Patterns
- **Dataclass-heavy**: Configuration objects use @dataclass extensively
- **Plugin-ready**: Column formatters and display strategies (planned)
- **Mode switching**: Mock vs Live operation modes
- **Rich integration**: Advanced terminal UI when available

### File Organization Issues (Identified)
- Demo components in root (should be in plugins/)
- Some duplicate functionality between root and kubectl_ld/
- Entry point architecture recently improved (subprocess → direct import)