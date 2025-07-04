#!/bin/bash

# Script to record asciinema of the demo

set -e

echo "🎬 Recording kubectl-ld demo with asciinema..."

# Check if virtual environment exists, if not create it
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
    echo "📦 Installing dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt > /dev/null 2>&1
else
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
fi

# Check if asciinema is installed
if ! command -v asciinema &> /dev/null; then
    echo "❌ asciinema not found. Please install it first:"
    echo "   brew install asciinema"
    echo "   or"
    echo "   pip install asciinema"
    exit 1
fi

# Record the demo
asciinema rec kubectl-ld-demo.cast -c "./demo.sh" --title "kubectl-ld Demo" --overwrite