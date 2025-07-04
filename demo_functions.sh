#!/bin/bash

# Shared functions for kubectl-ld demo scripts

# Setup virtual environment
setup_environment() {
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
}

# Wait for user input or sleep in headless mode
delay_or_wait() {
    local headless=$1
    local min_delay=${2:-3}  # Default minimum 3 seconds
    
    if [ "$headless" = true ]; then
        echo "⏳ Continuing in ${min_delay} seconds..."
        sleep $min_delay
    else
        echo ""
        echo "👆 Press any key to continue..."
        read -n 1 -s
        echo ""
    fi
}

# Show step with consistent formatting
show_step() {
    local step_num=$1
    local step_title="$2"
    
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "🔸 Step $step_num: $step_title"
    echo "═══════════════════════════════════════════════════════════════"
}

# Show completion message
show_completion() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "✅ Demo complete. kubectl-ld is your LLM debug toolkit!"
    echo "═══════════════════════════════════════════════════════════════"
}