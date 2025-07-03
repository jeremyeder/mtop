# kubectl-ld Fixup Plan

## Overview

This document outlines the critical issues found in the ChatGPT-generated kubectl-ld codebase and provides a comprehensive plan to fix them.

## Critical Issues Identified

### 1. Main Script (`kubectl-ld`) - Completely Broken Structure

The main kubectl-ld file has catastrophic structural issues:

- **Nested function definitions**: Functions are defined inside other functions with broken indentation
- **Duplicate imports**: `yaml` and `Path` are imported multiple times throughout the file
- **Duplicate function definitions**: `simulate_rollout`, `list_topologies`, and `print_output` are defined multiple times
- **Missing imports**: `yaml` and `Path` are used before being imported
- **Unreachable code**: Code after `if __name__ == "__main__"` block
- **Mixed conditional blocks**: `if/elif` statements mixed with function definitions
- **Incomplete implementations**: Several commands mentioned in tests/docs are not implemented

### 2. Missing Command Implementations

The following commands are referenced in tests or documentation but not implemented:
- `create` - Create new CRs from files
- `update` - Update CR fields
- `watch` - Monitor CR status changes in real-time
- `play rollout` - Different from `simulate`, should apply rollout steps

### 3. Minor Issues

- `watch_rollout.py` has indentation error at lines 42-43
- No error handling for file operations
- No input validation
- Tests expect functionality that doesn't exist

## Streamlined Fix Plan

### Phase 1: Critical Fixes (30 minutes)

#### 1.1 Complete Rewrite of `kubectl-ld`

```python
#!/usr/bin/env python3
"""
kubectl-ld - Mock CLI tool for debugging LLMInferenceService CRDs
"""

import os
import json
import yaml
import argparse
import subprocess
import sys
import time
import shutil
from pathlib import Path
from termcolor import colored

# Configuration
MOCK_ROOT = Path(__file__).parent / "mocks"
CRS_DIR = MOCK_ROOT / "crs"
CONFIG_PATH = MOCK_ROOT / "config" / "llminferenceserviceconfig.json"
LOGS_DIR = MOCK_ROOT / "pod_logs"
STATES_DIR = MOCK_ROOT / "states" / "rollout"

MODE = os.environ.get("LLD_MODE", "mock")

class KubectlLD:
    def __init__(self, mode="mock"):
        self.mode = mode
        self.is_live = (mode == "live")
    
    # ... implement all methods properly ...
```

#### 1.2 Fix `watch_rollout.py` Indentation

Fix the try/except block indentation issue.

### Phase 2: Feature Implementation (15 minutes)

#### 2.1 Implement Missing Commands

- `create`: Read JSON/YAML file and create new CR
- `update`: Modify existing CR fields
- `watch`: Monitor file changes or kubectl watch
- `play rollout`: Apply rollout steps with delays

#### 2.2 Add Error Handling

- File not found errors
- Invalid JSON/YAML
- kubectl command failures
- Invalid arguments

### Phase 3: Testing & Quality (10 minutes)

#### 3.1 Update Tests

- Add tests for new commands
- Test error scenarios
- Test both mock and live modes

#### 3.2 Add Type Hints and Documentation

- Add type hints to all functions
- Add docstrings
- Update README with accurate examples

## Implementation Priority

1. **Fix kubectl-ld structure** - Without this, nothing works
2. **Implement missing commands** - Tests expect these
3. **Add error handling** - Improve user experience
4. **Enhance tests** - Ensure reliability

## Estimated Timeline

- Phase 1: 30 minutes (mostly rewriting kubectl-ld)
- Phase 2: 15 minutes (straightforward implementations)
- Phase 3: 10 minutes (testing and documentation)

**Total: ~55 minutes**

## Success Criteria

- [ ] All tests pass
- [ ] No duplicate code or imports
- [ ] All documented commands work
- [ ] Proper error messages for failures
- [ ] Clean code structure with proper indentation