#!/bin/bash
set -e

echo "🔧 Running code formatters..."
black .
isort .

echo "🔍 Running basic checks..."
# Basic syntax validation - ensures code compiles
python -m py_compile tests/*.py
python -m py_compile mtop/*.py
python -m py_compile config_loader.py
python -m py_compile column_engine.py

echo "✅ All linting passed!"