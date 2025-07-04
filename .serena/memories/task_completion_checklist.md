# Task Completion Checklist

## Required Steps After Code Changes

### 1. Code Quality (Always Required)
```bash
# Format and organize code
black .
isort .

# Type checking
mypy .

# Linting (address major issues)
pylint kubectl_ld/ config_loader.py column_engine.py
```

### 2. Testing (Always Required)
```bash
# Run all tests - must pass
python3 -m pytest tests/ -v

# Check coverage if adding new functionality
python3 -m pytest tests/ --cov=. --cov-report=term
```

### 3. Security Scanning (For Dependencies/New Code)
```bash
# Dependency vulnerability check
safety check

# Security issue detection  
bandit -r . -f json
```

### 4. Integration Testing (For CLI Changes)
```bash
# Test basic CLI functionality
./kubectl-ld help
./kubectl-ld list
./kubectl-ld config

# Test mode switching
LLD_MODE=mock ./kubectl-ld list
```

### 5. Documentation Updates (When Applicable)
- Update README.md for new features
- Update COLLABORATION.md for workflow changes
- Add/update docstrings for new public methods

### 6. Git Workflow
```bash
# Commit with descriptive messages
git add .
git commit -m "feat: add new functionality"

# Jeremy's preference: squash commits, sign releases
git rebase -i HEAD~n  # if needed
```

## Success Criteria
- ✅ All tests pass (53 tests)
- ✅ No major linting errors
- ✅ Type checking passes
- ✅ Security scans clean
- ✅ CLI functions correctly in both modes
- ✅ Code follows project conventions