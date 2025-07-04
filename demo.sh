#!/bin/bash

set -e

echo "🎬 Starting kubectl-ld demo (5 seconds)..."
sleep 1

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
echo -e "\n🎥 Visual rollout playback (auto mode, 1s delay):"
python3 watch_rollout.py --topology rolling --autoplay --delay 1
