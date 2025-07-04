#!/bin/bash

# Helper script for recording demos with consistent settings
# Used by GitHub Actions and local development

set -e

# Default values
DEMO_TYPE="basic"
OUTPUT_DIR="recordings"
QUALITY="high"
HEADLESS=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --type)
            DEMO_TYPE="$2"
            shift 2
            ;;
        --output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --quality)
            QUALITY="$2"
            shift 2
            ;;
        --headless)
            HEADLESS=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--type TYPE] [--output DIR] [--quality LEVEL] [--headless]"
            echo ""
            echo "Options:"
            echo "  --type TYPE      Demo type: basic, full, split-basic, split-surge, split-chaos, split-multi"
            echo "  --output DIR     Output directory (default: recordings)"
            echo "  --quality LEVEL  Quality: low, medium, high (default: high)"
            echo "  --headless       Run in headless mode"
            echo ""
            echo "Examples:"
            echo "  $0 --type basic --headless"
            echo "  $0 --type split-surge --quality medium"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate demo type
case $DEMO_TYPE in
    basic|full|split-basic|split-surge|split-chaos|split-multi)
        ;;
    *)
        echo "Error: Invalid demo type '$DEMO_TYPE'"
        echo "Valid types: basic, full, split-basic, split-surge, split-chaos, split-multi"
        exit 1
        ;;
esac

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Setup environment
export LLD_MODE=mock
export TERM=xterm-256color

# Determine command and settings based on demo type
case $DEMO_TYPE in
    basic)
        COMMAND="./demo.sh"
        TITLE="kubectl-ld Basic Demo"
        DURATION="60s"
        COLS=120
        ROWS=30
        ;;
    full)
        COMMAND="./demo_full.sh"
        TITLE="kubectl-ld Full Demo"
        DURATION="180s"
        COLS=120
        ROWS=35
        ;;
    split-*)
        SCENARIO=${DEMO_TYPE#split-}
        COMMAND="./demo_split.sh --scenario $SCENARIO"
        TITLE="kubectl-ld Split-Screen Demo: $SCENARIO"
        DURATION="180s"
        COLS=140
        ROWS=40
        ;;
esac

# Add headless flag if requested
if [ "$HEADLESS" = true ]; then
    COMMAND="$COMMAND --headless"
fi

# Quality settings
case $QUALITY in
    low)
        COLS=$((COLS * 80 / 100))
        ROWS=$((ROWS * 80 / 100))
        SPEED=1.5
        ;;
    medium)
        SPEED=1.2
        ;;
    high)
        SPEED=1.0
        ;;
esac

# Output files
CAST_FILE="$OUTPUT_DIR/${DEMO_TYPE}-demo.cast"
GIF_FILE="$OUTPUT_DIR/${DEMO_TYPE}-demo.gif"
META_FILE="$OUTPUT_DIR/${DEMO_TYPE}-meta.json"

echo "🎬 Recording demo: $DEMO_TYPE"
echo "📹 Command: $COMMAND"
echo "📏 Dimensions: ${COLS}x${ROWS}"
echo "⏱️  Expected duration: $DURATION"
echo "📁 Output: $CAST_FILE"

# Check prerequisites
if ! command -v asciinema &> /dev/null; then
    echo "❌ asciinema not found. Please install it first:"
    echo "   pip install asciinema"
    echo "   or"
    echo "   brew install asciinema"
    exit 1
fi

# Check if demo script exists
SCRIPT_NAME=$(echo "$COMMAND" | awk '{print $1}')
if [ ! -f "$SCRIPT_NAME" ]; then
    echo "❌ Demo script not found: $SCRIPT_NAME"
    exit 1
fi

# Make sure script is executable
chmod +x "$SCRIPT_NAME"

# Record with asciinema
echo "🎥 Starting recording..."
asciinema rec "$CAST_FILE" \
    --title "$TITLE" \
    --command "$COMMAND" \
    --overwrite

# Validate recording
if [ ! -f "$CAST_FILE" ]; then
    echo "❌ Recording failed: $CAST_FILE not created"
    exit 1
fi

# Check file size
size=$(stat -f%z "$CAST_FILE" 2>/dev/null || stat -c%s "$CAST_FILE")
if [ "$size" -lt 1024 ]; then
    echo "❌ Recording too small: $size bytes"
    exit 1
fi

echo "✅ Recording completed: $size bytes"

# Convert to GIF if agg is available
if command -v agg &> /dev/null; then
    echo "🎨 Converting to GIF..."
    agg "$CAST_FILE" "$GIF_FILE" \
        --cols "$COLS" \
        --rows "$ROWS" \
        --speed "$SPEED"
    
    if [ -f "$GIF_FILE" ]; then
        gif_size=$(stat -f%z "$GIF_FILE" 2>/dev/null || stat -c%s "$GIF_FILE")
        echo "✅ GIF created: $gif_size bytes"
    fi
else
    echo "⚠️  agg not found, skipping GIF conversion"
    echo "   Install with: npm install -g @asciinema/agg"
fi

# Generate metadata
cat > "$META_FILE" << EOF
{
    "demo_type": "$DEMO_TYPE",
    "command": "$COMMAND",
    "title": "$TITLE", 
    "duration": "$DURATION",
    "dimensions": {
        "cols": $COLS,
        "rows": $ROWS
    },
    "quality": "$QUALITY",
    "headless": $HEADLESS,
    "recorded_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "file_size": $size,
    "version": "${VERSION:-dev}",
    "commit": "${COMMIT:-unknown}"
}
EOF

echo "📋 Metadata saved: $META_FILE"

# Summary
echo ""
echo "🎉 Demo recording complete!"
echo "📁 Files created:"
echo "   📹 $CAST_FILE ($size bytes)"
if [ -f "$GIF_FILE" ]; then
    echo "   🎨 $GIF_FILE ($(stat -f%z "$GIF_FILE" 2>/dev/null || stat -c%s "$GIF_FILE") bytes)"
fi
echo "   📋 $META_FILE"
echo ""
echo "🔍 Preview with: asciinema play $CAST_FILE"
if [ -f "$GIF_FILE" ]; then
    echo "🖼️  View GIF: open $GIF_FILE"
fi