#!/bin/bash

set -e

# Parse command line arguments
HEADLESS=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --headless)
            HEADLESS=true
            shift
            ;;
        *)
            echo "Usage: $0 [--headless]"
            echo "  --headless    Run demo automatically with delays (no user interaction)"
            exit 1
            ;;
    esac
done

# Source shared functions
source "$(dirname "$0")/demo_functions.sh"

echo "🎬 Starting kubectl-ld full demo (comprehensive showcase)..."
if [ "$HEADLESS" = true ]; then
    echo "🤖 Running in headless mode with automatic progression"
else
    echo "👆 Interactive mode - press any key between steps"
fi

# Setup environment
setup_environment

echo ""
echo "👋 Welcome to kubectl-ld — your LLM debugging Swiss Army knife."
delay_or_wait $HEADLESS 3

# Step 1: List rollout topologies
show_step 1 "List supported rollout topologies"
./kubectl-ld list-topologies
delay_or_wait $HEADLESS 3

# Step 2: Simulate bluegreen rollout
show_step 2 "Simulate a 'bluegreen' rollout (realistic model upgrade)"
./kubectl-ld simulate bluegreen
delay_or_wait $HEADLESS 3

# Step 3: Visual playback
show_step 3 "Playback that rollout visually"
if [ "$HEADLESS" = true ]; then
    python3 watch_rollout.py --topology bluegreen --autoplay --delay 2
else
    python3 watch_rollout.py --topology bluegreen --autoplay --delay 1
fi
delay_or_wait $HEADLESS 3

# Step 4: Check detailed status
show_step 4 "Check detailed status of a mock service"
./kubectl-ld check gpt2
delay_or_wait $HEADLESS 3

# Step 5: Show CR in YAML
show_step 5 "Show a real CR (gpt2) in YAML format"
./kubectl-ld get gpt2
delay_or_wait $HEADLESS 3

# Step 6: List all models
show_step 6 "View all models with status summary"
./kubectl-ld list
delay_or_wait $HEADLESS 3

show_completion
