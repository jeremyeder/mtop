#!/bin/bash

# Script to record asciinema of the demo

set -e

# Parse command line arguments
HEADLESS=false
DEMO_SCRIPT="./demo.sh"
while [[ $# -gt 0 ]]; do
    case $1 in
        --headless)
            HEADLESS=true
            shift
            ;;
        --full)
            DEMO_SCRIPT="./demo_full.sh"
            shift
            ;;
        *)
            echo "Usage: $0 [--headless] [--full]"
            echo "  --headless    Record demo in headless mode (automatic progression)"
            echo "  --full        Record the full demo instead of the basic demo"
            exit 1
            ;;
    esac
done

# Source shared functions
source "$(dirname "$0")/demo_functions.sh"

echo "🎬 Recording kubectl-ld demo with asciinema..."

# Setup environment
setup_environment

# Check if asciinema is installed
if ! command -v asciinema &> /dev/null; then
    echo "❌ asciinema not found. Please install it first:"
    echo "   brew install asciinema"
    echo "   or"
    echo "   pip install asciinema"
    exit 1
fi

# Prepare command
if [ "$HEADLESS" = true ]; then
    DEMO_CMD="$DEMO_SCRIPT --headless"
else
    DEMO_CMD="$DEMO_SCRIPT"
fi

# Record the demo
OUTPUT_FILE="kubectl-ld-demo.cast"
if [[ "$DEMO_SCRIPT" == *"full"* ]]; then
    OUTPUT_FILE="kubectl-ld-demo-full.cast"
fi

echo "📹 Recording: $DEMO_CMD"
echo "💾 Output: $OUTPUT_FILE"
asciinema rec "$OUTPUT_FILE" -c "$DEMO_CMD" --title "kubectl-ld Demo" --overwrite