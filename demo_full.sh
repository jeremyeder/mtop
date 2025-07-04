#!/bin/bash

set -e

echo "🎬 Starting kubectl-ld full demo (narrated)..."
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

export LLD_MODE=mock

echo ""
echo "👋 Welcome to kubectl-ld — your LLM debugging Swiss Army knife."
sleep 2

echo ""
echo "📦 Step 1: List supported rollout topologies..."
sleep 1
./kubectl-ld list-topologies
sleep 2

echo ""
echo "🧪 Step 2: Simulate a 'bluegreen' rollout (realistic model upgrade)..."
sleep 1
./kubectl-ld simulate bluegreen
sleep 2

echo ""
echo "🎥 Step 3: Playback that rollout visually (autoplay with 1s delay)..."
sleep 2
python3 watch_rollout.py --topology bluegreen --autoplay --delay 1
sleep 2

echo ""
echo "🧠 Step 4: Check detailed status of a mock service..."
sleep 1
./kubectl-ld check gpt2
sleep 2

echo ""
echo "📜 Step 5: Show a real CR (gpt2) in YAML format..."
sleep 1
./kubectl-ld get gpt2
sleep 2

echo ""
echo "📊 Step 6: View all models with status summary..."
sleep 1
./kubectl-ld list
sleep 1

echo ""
echo "✅ Demo complete. kubectl-ld is your LLM debug toolkit!"
