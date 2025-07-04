#!/bin/bash

# Quick preview script for kubectl-ld demos
# Shows first 10 seconds of each demo

echo "🎬 kubectl-ld Demo Previews"
echo "=========================="

for demo in *.cast; do
    if [ -f "$demo" ]; then
        echo ""
        echo "🎯 Preview: $demo"
        echo "----------------------------------------"
        
        # Show first 10 seconds at 2x speed
        timeout 5s asciinema play "$demo" --speed 2.0 2>/dev/null || echo "Preview completed"
        
        echo ""
        echo "Full demo: asciinema play $demo"
        echo "----------------------------------------"
    fi
done

echo ""
echo "🌟 To play any demo in full:"
echo "   asciinema play <demo-name>.cast"
echo ""
echo "🎮 Controls while playing:"
echo "   Space - Pause/Resume"
echo "   ← → - Rewind/Fast-forward"
echo "   ↑ ↓ - Speed up/Slow down"
echo "   q - Quit"