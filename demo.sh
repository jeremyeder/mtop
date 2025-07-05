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

echo "🎬 Starting mtop demo..."
if [ "$HEADLESS" = true ]; then
    echo "🤖 Running in headless mode with automatic progression"
else
    echo "👆 Interactive mode - press any key between steps"
fi

# Setup environment
setup_environment

# Step 1: Show available topologies
show_step 1 "Listing available rollout topologies"
./mtop-main list-topologies
delay_or_wait $HEADLESS 3

# Step 2: Run a quick simulated rollout
show_step 2 "Simulating 'rolling' rollout topology"
./mtop-main simulate rolling
delay_or_wait $HEADLESS 3

# Step 3: Launch visual viewer
show_step 3 "Visual rollout playback"
if [ "$HEADLESS" = true ]; then
    python3 watch_rollout.py --topology rolling --autoplay --delay 2
else
    python3 watch_rollout.py --topology rolling --autoplay --delay 1
fi

show_completion
