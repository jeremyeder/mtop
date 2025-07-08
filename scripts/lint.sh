#!/bin/bash
set -e

echo "🔧 Running code formatters..."
black .
isort .

echo "🔍 Running basic checks..."
# Basic syntax validation - ensures code compiles
python3 -m py_compile tests/*.py
python3 -m py_compile mtop/*.py

echo "✅ All linting passed!"