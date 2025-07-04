#!/bin/bash

set -e

echo "🎬 Starting kubectl-ld demo (5 seconds)..."
sleep 1

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
fi

# Activate mock mode
export LLD_MODE=mock

# Show available topologies
echo -e "\n📦 Listing available rollout topologies:"
./kubectl-ld list-topologies
sleep 1

# Run a quick simulated rollout
echo -e "\n🚀 Simulating 'rolling' rollout topology:"
./kubectl-ld simulate rolling
sleep 1

# Launch visual viewer in autoplay mode with short delay
echo -e "\n🎥 Visual rollout playbook (auto mode, 1s delay):"
python3 watch_rollout.py --topology rolling --autoplay --delay 1
