#!/bin/bash

# Generate VHS Tapes for Sales Demos
# Creates all 5 VHS tape files without running VHS recording

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
TAPE_DIR="tapes"
RECORDINGS_DIR="recordings/sales"

# Demo scenarios configuration
declare -A DEMO_SCENARIOS=(
    ["cost-optimization"]="Cost Optimization - 40% GPU cost reduction"
    ["slo-compliance"]="SLO Compliance - Sub-500ms TTFT guarantee"
    ["gpu-efficiency"]="GPU Efficiency - 3x model density"
    ["load-handling"]="Load Handling - Auto-scaling for traffic spikes"
    ["multi-model"]="Multi-Model - Unified LLM portfolio monitoring"
)

# Banner
show_banner() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║               📝 VHS Tape Generator                          ║"
    echo "║           Sales Demo Recording Tape Creation                ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Logging function
log() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Create all VHS tapes
generate_all_tapes() {
    log "${BLUE}📝 Generating all VHS tape files...${NC}"
    
    mkdir -p "$TAPE_DIR"
    mkdir -p "$RECORDINGS_DIR"
    
    # Cost Optimization Tape
    cat > "$TAPE_DIR/cost-optimization.tape" << 'EOF'
# Cost Optimization Demo - 40% GPU Cost Reduction
# Duration: ~2 minutes

Output recordings/sales/cost-optimization.gif
Output recordings/sales/cost-optimization.mp4
Output recordings/sales/cost-optimization.webm

Require echo

Set FontSize 14
Set Width 120
Set Height 30
Set Theme "Dracula"

# Setup
Type "clear"
Enter
Sleep 1s

# Title
Type "echo '🎯 mtop Sales Demo: Cost Optimization'"
Enter
Type "echo '💰 Demonstrate 40% GPU cost reduction through intelligent rightsizing'"
Enter
Type "echo ''"
Enter
Sleep 2s

# Show current expensive GPU usage
Type "echo '📊 Current GPU Analysis:'"
Enter
Type "./mtop get llama-3-70b-instruct"
Enter
Sleep 4s

# Highlight the cost issue
Type "echo ''"
Enter
Type "echo '💡 Key Insight: 62% utilization on $4.10/hour H100 = $1,000+ monthly waste'"
Enter
Type "echo '🎯 Recommendation: Move to A100 GPU for 40% cost savings'"
Enter
Sleep 3s

# Show cost comparison
Type "echo ''"
Enter
Type "echo '📈 ROI Analysis:'"
Enter
Type "echo '   Current cost: $4.10/hour (H100)'"
Enter
Type "echo '   Recommended: $2.50/hour (A100)'"
Enter 
Type "echo '   Monthly savings: $1,182 per model'"
Enter
Type "echo '   Annual ROI: $14,184 per model'"
Enter
Sleep 4s

# Show portfolio view
Type "echo ''"
Enter
Type "echo '🏢 Enterprise Portfolio Impact:'"
Enter
Type "./mtop list"
Enter
Sleep 4s

# Summary
Type "echo ''"
Enter
Type "echo '✅ Result: $54K annual savings through GPU rightsizing'"
Enter
Type "echo '🚀 Scale this across your LLM infrastructure for maximum ROI'"
Enter
Sleep 3s

Type "clear"
Enter
EOF

    # SLO Compliance Tape
    cat > "$TAPE_DIR/slo-compliance.tape" << 'EOF'
# SLO Compliance Demo - Performance Guarantees
# Duration: ~2 minutes

Output recordings/sales/slo-compliance.gif
Output recordings/sales/slo-compliance.mp4
Output recordings/sales/slo-compliance.webm

Require echo

Set FontSize 14
Set Width 120
Set Height 30
Set Theme "Dracula"

# Setup
Type "clear"
Enter
Sleep 1s

# Title
Type "echo '⚡ mtop Sales Demo: SLO Compliance'"
Enter
Type "echo '🎯 Guarantee sub-500ms response times with automatic scaling'"
Enter
Type "echo ''"
Enter
Sleep 2s

# Show TTFT performance
Type "echo '📊 Real-time Performance Monitoring:'"
Enter
Type "./mtop get gpt-4-turbo"
Enter
Sleep 4s

# Highlight SLO compliance
Type "echo ''"
Enter
Type "echo '✅ Key Metrics:'"
Enter
Type "echo '   TTFT P95: 180ms (target: <500ms) ✅'"
Enter
Type "echo '   Queue depth: 3 requests (optimal)'"
Enter
Type "echo '   Throughput: 2,000 tokens/second'"
Enter
Type "echo '   SLO compliance: 99.9% uptime'"
Enter
Sleep 4s

# Show scaling simulation
Type "echo ''"
Enter
Type "echo '🔄 Demonstrating Auto-Scaling:'"
Enter
Type "./mtop simulate canary"
Enter
Sleep 6s

# Live monitoring
Type "echo ''"
Enter
Type "echo '📈 Live System Monitoring:'"
Enter
Type "./mtop"
Enter
Sleep 3s
Type "q"

# Summary
Type "echo ''"
Enter
Type "echo '🎯 Guaranteed Performance:'"
Enter
Type "echo '   ✅ Sub-500ms TTFT maintained during 10x traffic spikes'"
Enter
Type "echo '   ✅ 99.9% uptime through predictive capacity management'"
Enter
Type "echo '   ✅ Zero-downtime deployments with automatic validation'"
Enter
Sleep 3s

Type "clear"
Enter
EOF

    # GPU Efficiency Tape
    cat > "$TAPE_DIR/gpu-efficiency.tape" << 'EOF'
# GPU Efficiency Demo - Resource Optimization
# Duration: ~2 minutes

Output recordings/sales/gpu-efficiency.gif
Output recordings/sales/gpu-efficiency.mp4
Output recordings/sales/gpu-efficiency.webm

Require echo

Set FontSize 14
Set Width 120
Set Height 30
Set Theme "Dracula"

# Setup
Type "clear"
Enter
Sleep 1s

# Title
Type "echo '📊 mtop Sales Demo: GPU Efficiency'"
Enter
Type "echo '🎯 Maximize GPU utilization through intelligent fractioning'"
Enter
Type "echo ''"
Enter
Sleep 2s

# Show multi-model efficiency
Type "echo '🔧 Multi-Model GPU Fractioning:'"
Enter
Type "./mtop list"
Enter
Sleep 4s

# Highlight efficiency gains
Type "echo ''"
Enter
Type "echo '💡 Efficiency Breakdown:'"
Enter
Type "echo '   Single H100 GPU running 3 models simultaneously'"
Enter
Type "echo '   Granite-3B: 30% | Phi-3: 25% | Available: 45%'"
Enter
Type "echo '   Total utilization: 85% (vs 60% single-model)'"
Enter
Sleep 4s

# Show visual monitoring
Type "echo ''"
Enter
Type "echo '📈 Visual Resource Allocation:'"
Enter
Type "python3 watch_rollout.py --topology rolling --autoplay --delay 1"
Enter
Sleep 6s

# Cost efficiency analysis
Type "echo ''"
Enter
Type "echo '💰 Cost Efficiency Analysis:'"
Enter
Type "echo '   Models per GPU: 3 (vs 1 traditional)'"
Enter
Type "echo '   Cost per inference: 60% reduction'"
Enter
Type "echo '   Infrastructure efficiency: 3x improvement'"
Enter
Type "echo '   ROI on GPU investment: 300% increase'"
Enter
Sleep 4s

# Summary
Type "echo ''"
Enter
Type "echo '🚀 Results:'"
Enter
Type "echo '   ✅ 3x model density = 3x ROI on GPU investment'"
Enter
Type "echo '   ✅ Dynamic reallocation based on demand'"
Enter
Type "echo '   ✅ 85% utilization vs 60% traditional approach'"
Enter
Sleep 3s

Type "clear"
Enter
EOF

    # Load Handling Tape
    cat > "$TAPE_DIR/load-handling.tape" << 'EOF'
# Load Handling Demo - Auto-Scaling
# Duration: ~2 minutes

Output recordings/sales/load-handling.gif
Output recordings/sales/load-handling.mp4
Output recordings/sales/load-handling.webm

Require echo

Set FontSize 14
Set Width 120
Set Height 30
Set Theme "Dracula"

# Setup
Type "clear"
Enter
Sleep 1s

# Title
Type "echo '🔄 mtop Sales Demo: Load Handling'"
Enter
Type "echo '⚡ Handle traffic spikes without human intervention'"
Enter
Type "echo ''"
Enter
Sleep 2s

# Show baseline state
Type "echo '📊 Baseline System State:'"
Enter
Type "./mtop list"
Enter
Sleep 3s

# Simulate traffic spike
Type "echo ''"
Enter
Type "echo '🚨 Simulating 10x Traffic Spike:'"
Enter
Type "./demo.sh --headless"
Enter
Sleep 8s

# Show real-time response
Type "echo ''"
Enter
Type "echo '⚡ System Response Analysis:'"
Enter
Type "echo '   Traffic spike detected: 10x normal load'"
Enter
Type "echo '   Queue depth increase: 3 → 15 requests'"
Enter
Type "echo '   Auto-scale triggered: Adding GPU capacity'"
Enter
Type "echo '   Response time: <500ms maintained'"
Enter
Type "echo '   Scale completion: 30 seconds'"
Enter
Sleep 4s

# Show monitoring during spike
Type "echo ''"
Enter
Type "echo '📈 Live Monitoring During Spike:'"
Enter
Type "./mtop"
Enter
Sleep 3s
Type "q"

# Cost optimization aspect
Type "echo ''"
Enter
Type "echo '💰 Cost Optimization:'"
Enter
Type "echo '   Scale up: Only when needed (30 seconds)'"
Enter
Type "echo '   Scale down: Automatic when traffic normalizes'"
Enter
Type "echo '   Resource efficiency: 95% utilization'"
Enter
Type "echo '   Cost impact: Pay only for what you use'"
Enter
Sleep 4s

# Summary
Type "echo ''"
Enter
Type "echo '🎯 Auto-Scaling Benefits:'"
Enter
Type "echo '   ✅ Response time <500ms during 10x spike'"
Enter
Type "echo '   ✅ 30-second auto-scale time'"
Enter
Type "echo '   ✅ No human intervention required'"
Enter
Type "echo '   ✅ Cost-optimized resource allocation'"
Enter
Sleep 3s

Type "clear"
Enter
EOF

    # Multi-Model Tape
    cat > "$TAPE_DIR/multi-model.tape" << 'EOF'
# Multi-Model Demo - Enterprise Portfolio
# Duration: ~2 minutes

Output recordings/sales/multi-model.gif
Output recordings/sales/multi-model.mp4
Output recordings/sales/multi-model.webm

Require echo

Set FontSize 14
Set Width 120
Set Height 30
Set Theme "Dracula"

# Setup
Type "clear"
Enter
Sleep 1s

# Title
Type "echo '🤖 mtop Sales Demo: Multi-Model Portfolio'"
Enter
Type "echo '📊 Manage diverse LLM portfolio with unified monitoring'"
Enter
Type "echo ''"
Enter
Sleep 2s

# Show enterprise portfolio
Type "echo '🏢 Enterprise LLM Portfolio:'"
Enter
Type "./mtop list"
Enter
Sleep 4s

# Real-time monitoring
Type "echo ''"
Enter
Type "echo '📈 Unified Real-time Monitoring:'"
Enter
Type "./mtop"
Enter
Sleep 4s
Type "q"

# Model comparison analysis
Type "echo ''"
Enter
Type "echo '🔍 Cross-Model Performance Analysis:'"
Enter
Type "echo '   Claude: 3,204 TPS | TTFT: 98ms | Cost: $3.20/hr'"
Enter
Type "echo '   GPT-4: 2,156 TPS | TTFT: 165ms | Cost: $4.10/hr'"
Enter
Type "echo '   Llama: 1,847 TPS | TTFT: 182ms | Cost: $4.10/hr'"
Enter
Type "echo '   Mixtral: 1,923 TPS | TTFT: 201ms | Cost: $3.20/hr'"
Enter
Type "echo '   Granite: 4,107 TPS | TTFT: 76ms | Cost: $2.10/hr'"
Enter
Sleep 5s

# Cost analysis
Type "echo ''"
Enter
Type "echo '💰 Portfolio Cost Analysis:'"
Enter
Type "echo '   Total models monitored: 15+ simultaneously'"
Enter
Type "echo '   Cost visibility: Per-token pricing across all models'"
Enter
Type "echo '   Optimization potential: $54K+ annual savings'"
Enter
Type "echo '   Operational overhead: 90% reduction vs manual'"
Enter
Sleep 4s

# Operational benefits
Type "echo ''"
Enter
Type "echo '⚡ Operational Excellence:'"
Enter
Type "echo '   Single pane of glass for entire LLM infrastructure'"
Enter
Type "echo '   Real-time token generation rates across all models'"
Enter
Type "echo '   Automated cost tracking and optimization recommendations'"
Enter
Type "echo '   Performance benchmarking and SLO compliance monitoring'"
Enter
Sleep 4s

# Summary
Type "echo ''"
Enter
Type "echo '🎯 Enterprise Value:'"
Enter
Type "echo '   ✅ Unified monitoring: Claude, GPT-4, Llama, Mixtral, Granite'"
Enter
Type "echo '   ✅ Real-time performance tracking across all models'"
Enter
Type "echo '   ✅ Per-model cost optimization recommendations'"
Enter
Type "echo '   ✅ 90% reduction in operational overhead'"
Enter
Sleep 3s

Type "clear"
Enter
EOF

    log "${GREEN}✅ Generated all 5 VHS tape files${NC}"
    
    # List generated tapes
    echo -e "${BLUE}📄 Generated tapes:${NC}"
    for scenario in "${!DEMO_SCENARIOS[@]}"; do
        echo "  • $TAPE_DIR/$scenario.tape - ${DEMO_SCENARIOS[$scenario]}"
    done
}

# Create package manifest
create_package_manifest() {
    log "${BLUE}📦 Creating tape package manifest...${NC}"
    
    cat > "$TAPE_DIR/manifest.json" << EOF
{
  "package": "mtop-vhs-tapes",
  "version": "1.0",
  "generated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "description": "VHS tape files for mtop sales demo recordings",
  "scenarios": [
$(for scenario in "${!DEMO_SCENARIOS[@]}"; do
    echo "    {"
    echo "      \"id\": \"$scenario\","
    echo "      \"title\": \"${DEMO_SCENARIOS[$scenario]}\","
    echo "      \"tape_file\": \"$scenario.tape\","
    echo "      \"outputs\": ["
    echo "        \"recordings/sales/$scenario.gif\","
    echo "        \"recordings/sales/$scenario.mp4\","
    echo "        \"recordings/sales/$scenario.webm\""
    echo "      ]"
    echo "    },"
done | sed '$ s/,$//')
  ],
  "usage": {
    "command": "vhs <tape_file>",
    "requirements": ["vhs", "ffmpeg"],
    "install": "brew install vhs ffmpeg"
  }
}
EOF

    log "${GREEN}✅ Package manifest created${NC}"
}

# Main execution
main() {
    show_banner
    
    echo -e "${YELLOW}📝 VHS Tape Generator${NC}"
    echo "Creating all 5 VHS tape files for professional sales demo recordings..."
    echo ""
    
    generate_all_tapes
    create_package_manifest
    
    echo ""
    echo -e "${GREEN}🎉 VHS Tape Generation Complete!${NC}"
    echo ""
    echo -e "${BLUE}📦 Deliverables:${NC}"
    echo "• 5 professional VHS tape files ready for recording"
    echo "• Package manifest with metadata and usage instructions"
    echo "• Ready for VHS recording with: vhs <tape_file>"
    echo ""
    echo -e "${PURPLE}🎬 Next Steps:${NC}"
    echo "1. Install VHS: brew install vhs ffmpeg"
    echo "2. Record demos: vhs tapes/cost-optimization.tape"
    echo "3. Distribute recordings for sales conversations"
    
    log "VHS tape generation completed successfully"
}

# Execute main function
main "$@"