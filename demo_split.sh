#!/bin/bash

# Split-screen demo for kubectl-ld
# Top pane: Narration and controls
# Bottom pane: Live monitoring with multi-model support

set -e

# Parse command line arguments
HEADLESS=false
SCENARIO="basic"
while [[ $# -gt 0 ]]; do
    case $1 in
        --headless)
            HEADLESS=true
            shift
            ;;
        --scenario)
            SCENARIO="$2"
            shift 2
            ;;
        *)
            echo "Usage: $0 [--headless] [--scenario <type>]"
            echo "  --headless    Run demo automatically with delays"
            echo "  --scenario    Choose scenario: basic, surge, chaos, multi"
            echo ""
            echo "Available scenarios:"
            echo "  basic     - Simple 3-model rollout"
            echo "  surge     - Black Friday traffic spike (20 models)"
            echo "  chaos     - Failure injection and recovery"
            echo "  multi     - Multiple deployment strategies"
            exit 1
            ;;
    esac
done

# Source shared functions
source "$(dirname "$0")/demo_functions.sh"

# Check if tmux is available
if ! command -v tmux &> /dev/null; then
    echo "❌ tmux not found. Installing via brew..."
    if command -v brew &> /dev/null; then
        brew install tmux
    else
        echo "❌ Please install tmux first:"
        echo "   brew install tmux    (macOS)"
        echo "   apt install tmux     (Ubuntu/Debian)"
        echo "   yum install tmux     (CentOS/RHEL)"
        exit 1
    fi
fi

# Setup environment
setup_environment

# Kill any existing demo session
tmux kill-session -t kubectl-ld-demo 2>/dev/null || true

# Create new tmux session with split panes
SESSION_NAME="kubectl-ld-demo"

echo "🎬 Starting split-screen kubectl-ld demo..."
echo "🎯 Scenario: $SCENARIO"
echo "🔧 Setting up tmux environment..."

# Check if we're inside tmux already or don't have a proper terminal (for recording compatibility)
if [ -n "$TMUX" ] || [ ! -t 0 ]; then
    echo "⚠️  Running in compatibility mode - sequential execution"
    
    # Run narrator first
    NARRATOR_CMD="python3 demo_narrator.py --scenario $SCENARIO"
    if [ "$HEADLESS" = true ]; then
        NARRATOR_CMD="$NARRATOR_CMD --headless"
    fi
    
    echo "🎬 Starting narrator..."
    $NARRATOR_CMD &
    NARRATOR_PID=$!
    
    sleep 2
    
    # Run monitor
    MONITOR_CMD="python3 demo_monitor.py --scenario $SCENARIO"
    if [ "$HEADLESS" = true ]; then
        MONITOR_CMD="$MONITOR_CMD --headless"
    fi
    
    echo "📊 Starting monitor..."
    $MONITOR_CMD
    
    # Clean up narrator
    kill $NARRATOR_PID 2>/dev/null || true
    exit 0
fi

# Create tmux session with horizontal split
tmux new-session -d -s "$SESSION_NAME"

# Split horizontally (top 55%, bottom 45%)
tmux split-window -v -t "$SESSION_NAME"

# Wait for panes to be created and get their IDs
sleep 1
PANE0=$(tmux list-panes -t "$SESSION_NAME" -F "#{pane_id}" | sed -n '1p')
PANE1=$(tmux list-panes -t "$SESSION_NAME" -F "#{pane_id}" | sed -n '2p')

# Set up top pane (narrator)
NARRATOR_CMD="python3 demo_narrator.py --scenario $SCENARIO"
if [ "$HEADLESS" = true ]; then
    NARRATOR_CMD="$NARRATOR_CMD --headless"
fi

tmux send-keys -t "$PANE0" "$NARRATOR_CMD" Enter

# Set up bottom pane (monitor)  
MONITOR_CMD="python3 demo_monitor.py --scenario $SCENARIO"
if [ "$HEADLESS" = true ]; then
    MONITOR_CMD="$MONITOR_CMD --headless"
fi

tmux send-keys -t "$PANE1" "$MONITOR_CMD" Enter

# Set focus to the top pane (narrator) where user interaction happens
tmux select-pane -t "$PANE0"

# Attach to session
echo "🚀 Launching split-screen demo..."
echo "💡 Focus is on TOP pane (narrator) - press any key to advance"
echo "💡 Press Q to quit, or Ctrl+B then D to detach from tmux"
sleep 1
tmux attach-session -t "$SESSION_NAME"

# Cleanup when done
tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true
echo "✅ Demo session ended."