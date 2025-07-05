#!/bin/bash

# Convert demo recordings to multiple formats
# Supports .cast -> .gif, .mp4, .svg conversion

set -e

# Default values
INPUT_DIR="recordings"
OUTPUT_DIR="demos"
FORMAT="all"
QUALITY="medium"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --input)
            INPUT_DIR="$2"
            shift 2
            ;;
        --output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --format)
            FORMAT="$2"
            shift 2
            ;;
        --quality)
            QUALITY="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--input DIR] [--output DIR] [--format FORMAT] [--quality LEVEL]"
            echo ""
            echo "Options:"
            echo "  --input DIR      Input directory with .cast files (default: recordings)"
            echo "  --output DIR     Output directory (default: demos)"
            echo "  --format FORMAT  Output format: gif, mp4, svg, all (default: all)"
            echo "  --quality LEVEL  Quality: low, medium, high (default: medium)"
            echo ""
            echo "Examples:"
            echo "  $0 --format gif --quality high"
            echo "  $0 --input ./recordings --output ./public/demos"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate format
case $FORMAT in
    gif|mp4|svg|all)
        ;;
    *)
        echo "Error: Invalid format '$FORMAT'"
        echo "Valid formats: gif, mp4, svg, all"
        exit 1
        ;;
esac

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Quality settings
case $QUALITY in
    low)
        GIF_COLS=100
        GIF_ROWS=25
        GIF_SPEED=1.8
        MP4_SCALE="0.8"
        ;;
    medium)
        GIF_COLS=120
        GIF_ROWS=30
        GIF_SPEED=1.4
        MP4_SCALE="1.0"
        ;;
    high)
        GIF_COLS=140
        GIF_ROWS=35
        GIF_SPEED=1.0
        MP4_SCALE="1.2"
        ;;
esac

# Check prerequisites
check_tool() {
    local tool=$1
    local install_cmd=$2
    
    if ! command -v "$tool" &> /dev/null; then
        echo "❌ $tool not found."
        if [ -n "$install_cmd" ]; then
            echo "   Install with: $install_cmd"
        fi
        return 1
    fi
    return 0
}

# Find all .cast files
if [ ! -d "$INPUT_DIR" ]; then
    echo "❌ Input directory not found: $INPUT_DIR"
    exit 1
fi

cast_files=($(find "$INPUT_DIR" -name "*.cast" -type f))

if [ ${#cast_files[@]} -eq 0 ]; then
    echo "❌ No .cast files found in $INPUT_DIR"
    exit 1
fi

echo "🎬 Found ${#cast_files[@]} demo recordings to convert"

# Convert each file
for cast_file in "${cast_files[@]}"; do
    basename=$(basename "$cast_file" .cast)
    echo ""
    echo "🎨 Converting: $basename"
    
    # Convert to GIF
    if [ "$FORMAT" = "gif" ] || [ "$FORMAT" = "all" ]; then
        gif_file="$OUTPUT_DIR/${basename}.gif"
        
        if check_tool "agg" "npm install -g @asciinema/agg"; then
            echo "  📹 Creating GIF..."
            agg "$cast_file" "$gif_file" \
                --cols "$GIF_COLS" \
                --rows "$GIF_ROWS" \
                --speed "$GIF_SPEED" \
                --font-size 14
                
            if [ -f "$gif_file" ]; then
                size=$(stat -f%z "$gif_file" 2>/dev/null || stat -c%s "$gif_file")
                echo "  ✅ GIF: $(basename "$gif_file") ($size bytes)"
            fi
        else
            echo "  ⚠️  Skipping GIF conversion"
        fi
    fi
    
    # Convert to MP4
    if [ "$FORMAT" = "mp4" ] || [ "$FORMAT" = "all" ]; then
        mp4_file="$OUTPUT_DIR/${basename}.mp4"
        
        # First convert to GIF, then to MP4
        if check_tool "agg" "npm install -g @asciinema/agg" && check_tool "ffmpeg" "brew install ffmpeg"; then
            echo "  🎥 Creating MP4..."
            
            # Create temporary high-quality GIF
            temp_gif="/tmp/${basename}_temp.gif"
            agg "$cast_file" "$temp_gif" \
                --cols "$((GIF_COLS + 20))" \
                --rows "$((GIF_ROWS + 5))" \
                --speed "$GIF_SPEED" \
                --font-size 16
            
            # Convert GIF to MP4
            ffmpeg -i "$temp_gif" \
                -vf "scale=iw*${MP4_SCALE}:ih*${MP4_SCALE}" \
                -c:v libx264 \
                -pix_fmt yuv420p \
                -crf 23 \
                -y "$mp4_file" 2>/dev/null
            
            # Cleanup
            rm -f "$temp_gif"
            
            if [ -f "$mp4_file" ]; then
                size=$(stat -f%z "$mp4_file" 2>/dev/null || stat -c%s "$mp4_file")
                echo "  ✅ MP4: $(basename "$mp4_file") ($size bytes)"
            fi
        else
            echo "  ⚠️  Skipping MP4 conversion"
        fi
    fi
    
    # Convert to SVG
    if [ "$FORMAT" = "svg" ] || [ "$FORMAT" = "all" ]; then
        svg_file="$OUTPUT_DIR/${basename}.svg"
        
        if check_tool "asciinema" "pip install asciinema"; then
            echo "  🎨 Creating SVG..."
            
            # Use asciinema's built-in SVG export
            # Note: This creates a static SVG of the final frame
            asciinema cat "$cast_file" | tail -1 > /tmp/final_frame.txt 2>/dev/null || true
            
            # For now, create a simple SVG placeholder
            # A full SVG animation would require more sophisticated tooling
            cat > "$svg_file" << EOF
<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" fill="#000"/>
  <text x="50%" y="50%" fill="#0f0" text-anchor="middle" font-family="monospace" font-size="16">
    Demo: $basename
  </text>
  <text x="50%" y="60%" fill="#fff" text-anchor="middle" font-family="monospace" font-size="12">
    Play with: asciinema play ${basename}.cast
  </text>
</svg>
EOF
            
            if [ -f "$svg_file" ]; then
                size=$(stat -f%z "$svg_file" 2>/dev/null || stat -c%s "$svg_file")
                echo "  ✅ SVG: $(basename "$svg_file") ($size bytes)"
            fi
        else
            echo "  ⚠️  Skipping SVG conversion"
        fi
    fi
done

# Create index file
echo ""
echo "📋 Creating demo index..."

cat > "$OUTPUT_DIR/index.html" << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>mtop Demo Recordings</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 40px; }
        .demo { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
        .demo h3 { margin-top: 0; color: #333; }
        .formats { margin: 10px 0; }
        .format-link { margin-right: 15px; padding: 5px 10px; background: #f0f0f0; text-decoration: none; border-radius: 4px; }
        img { max-width: 100%; height: auto; }
    </style>
</head>
<body>
    <h1>🎬 mtop Demo Recordings</h1>
    <p>Interactive demonstrations of mtop features and capabilities.</p>
EOF

# Add demo entries
for cast_file in "${cast_files[@]}"; do
    basename=$(basename "$cast_file" .cast)
    demo_title=$(echo "$basename" | sed 's/-/ /g' | sed 's/\b\w/\U&/g')
    
    cat >> "$OUTPUT_DIR/index.html" << EOF
    <div class="demo">
        <h3>$demo_title</h3>
        <div class="formats">
EOF

    # Add format links
    if [ -f "$OUTPUT_DIR/${basename}.gif" ]; then
        cat >> "$OUTPUT_DIR/index.html" << EOF
            <a href="${basename}.gif" class="format-link">🎨 GIF</a>
EOF
    fi
    
    if [ -f "$OUTPUT_DIR/${basename}.mp4" ]; then
        cat >> "$OUTPUT_DIR/index.html" << EOF
            <a href="${basename}.mp4" class="format-link">🎥 MP4</a>
EOF
    fi
    
    if [ -f "$OUTPUT_DIR/${basename}.svg" ]; then
        cat >> "$OUTPUT_DIR/index.html" << EOF
            <a href="${basename}.svg" class="format-link">🎨 SVG</a>
EOF
    fi
    
    cat >> "$OUTPUT_DIR/index.html" << EOF
            <a href="../$cast_file" class="format-link">⚡ .cast</a>
        </div>
EOF

    # Embed GIF if available
    if [ -f "$OUTPUT_DIR/${basename}.gif" ]; then
        cat >> "$OUTPUT_DIR/index.html" << EOF
        <img src="${basename}.gif" alt="$demo_title Demo" />
EOF
    fi
    
    cat >> "$OUTPUT_DIR/index.html" << EOF
    </div>
EOF
done

cat >> "$OUTPUT_DIR/index.html" << 'EOF'
    
    <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #666;">
        <p>Generated automatically by mtop demo conversion script.</p>
        <p>To play .cast files: <code>asciinema play filename.cast</code></p>
    </footer>
</body>
</html>
EOF

echo "✅ Demo index created: $OUTPUT_DIR/index.html"

# Summary
echo ""
echo "🎉 Conversion complete!"
echo "📁 Output directory: $OUTPUT_DIR"
echo "🌐 View demos: open $OUTPUT_DIR/index.html"

# Count output files
gif_count=$(find "$OUTPUT_DIR" -name "*.gif" -type f | wc -l)
mp4_count=$(find "$OUTPUT_DIR" -name "*.mp4" -type f | wc -l) 
svg_count=$(find "$OUTPUT_DIR" -name "*.svg" -type f | wc -l)

echo "📊 Files created:"
echo "   🎨 GIFs: $gif_count"
echo "   🎥 MP4s: $mp4_count"
echo "   🎨 SVGs: $svg_count"