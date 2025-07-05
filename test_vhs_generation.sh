#!/bin/bash

# Test VHS tape generation without full environment setup
set -e

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

# Configuration
TAPE_DIR="tapes"
EXPORTS_DIR="exports"

# Demo scenarios configuration (replicated for testing)
declare -A DEMO_SCENARIOS=(
    ["cost-optimization"]="Cost Optimization - 40% GPU cost reduction"
    ["slo-compliance"]="SLO Compliance - Sub-500ms TTFT guarantee"
    ["gpu-efficiency"]="GPU Efficiency - 3x model density"
    ["load-handling"]="Load Handling - Auto-scaling for traffic spikes"
    ["multi-model"]="Multi-Model - Unified LLM portfolio monitoring"
)

echo -e "${BLUE}🧪 Testing VHS Tape Generation${NC}"

# Create directories
mkdir -p "$TAPE_DIR"
mkdir -p "$EXPORTS_DIR"

# Source the tape creation functions from the main script
source <(grep -A 200 "create_cost_optimization_tape()" scripts/record_sales_demos.sh | head -n 87)

# Test creating one tape
echo -e "${BLUE}📝 Generating cost optimization tape...${NC}"
tape_file=$(create_cost_optimization_tape)

echo -e "${GREEN}✅ Generated tape: $tape_file${NC}"

# Verify the tape file was created
if [[ -f "$tape_file" ]]; then
    echo -e "${GREEN}✅ Tape file exists and is readable${NC}"
    echo -e "${BLUE}📄 First 10 lines of tape:${NC}"
    head -n 10 "$tape_file"
else
    echo -e "❌ Tape file was not created"
    exit 1
fi

echo -e "${GREEN}🎉 VHS tape generation test completed successfully!${NC}"