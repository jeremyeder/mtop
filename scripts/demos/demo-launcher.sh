#!/bin/bash

# Sales-Ready Demo Launcher for mtop
# One-click setup for complete demo environment
# Compatible with Unix systems with minimal dependencies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
DEMO_TIMEOUT=1800  # 30 minutes
HEALTH_CHECK_RETRIES=3
SETUP_LOG="demo-setup.log"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$SETUP_LOG"
}

# Error handling
handle_error() {
    echo -e "${RED}❌ Demo setup failed at: $1${NC}"
    echo -e "${YELLOW}📋 Check $SETUP_LOG for details${NC}"
    echo -e "${BLUE}🔧 Run './demo-cleanup.sh' to reset environment${NC}"
    exit 1
}

# Progress indicator
show_progress() {
    local step=$1
    local total=$2
    local description="$3"
    local progress=$((step * 100 / total))
    
    echo -e "${BLUE}[$step/$total] ${description}... ${progress}%${NC}"
}

# Banner
show_banner() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                   🚀 mtop Demo Launcher                      ║"
    echo "║               Sales-Ready LLM Monitoring Demo               ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# System requirements check
check_requirements() {
    log "Checking system requirements..."
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        handle_error "Python3 is required but not installed"
    fi
    
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
        handle_error "Python 3.11+ required, found $python_version"
    fi
    
    # Check available disk space (need at least 100MB)
    available_space=$(df . | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 100000 ]; then
        handle_error "Insufficient disk space (need 100MB+)"
    fi
    
    log "✅ System requirements met (Python $python_version)"
}

# Environment setup
setup_environment() {
    log "Setting up demo environment..."
    
    # Create/activate virtual environment
    if [ ! -d "venv" ]; then
        log "Creating Python virtual environment..."
        python3 -m venv venv || handle_error "Failed to create virtual environment"
    fi
    
    # Activate virtual environment
    source venv/bin/activate || handle_error "Failed to activate virtual environment"
    
    # Install dependencies
    log "Installing dependencies..."
    pip install -r requirements.txt > "$SETUP_LOG" 2>&1 || handle_error "Failed to install dependencies"
    
    # Set environment variables
    export LLD_MODE=mock
    export PYTHONPATH=$(pwd):$PYTHONPATH
    
    log "✅ Environment setup complete"
}

# Validate mock data
validate_mock_data() {
    log "Validating demo data..."
    
    # Check mock directories exist
    required_dirs=("mocks/crs" "mocks/config" "mocks/pod_logs" "mocks/states" "mocks/topologies")
    for dir in "${required_dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            handle_error "Missing required mock data directory: $dir"
        fi
    done
    
    # Count CRs for demo scenarios
    cr_count=$(find mocks/crs -name "*.json" | wc -l)
    if [ "$cr_count" -lt 5 ]; then
        handle_error "Insufficient mock CRs found ($cr_count < 5)"
    fi
    
    log "✅ Demo data validated ($cr_count CRs available)"
}

# Pre-load demo scenarios
preload_scenarios() {
    log "Pre-loading demo scenarios..."
    
    # Test basic functionality
    if ! ./mtop help > /dev/null 2>&1; then
        handle_error "mtop CLI not working"
    fi
    
    # Pre-generate token metrics
    log "Generating sample token metrics..."
    python3 -c "
from mtop.token_metrics import create_token_tracker, create_queue_metrics
from config_loader import load_config

config = load_config()
tracker = create_token_tracker(config.technology, config.slo)

# Generate metrics for popular models
models = ['gpt-4-turbo', 'llama-3-70b-instruct', 'claude-3-haiku', 'mixtral-8x7b-instruct', 'granite-3-8b-instruct']
for model in models:
    tracker.simulate_token_generation(model, target_tokens=200)

print(f'Generated metrics for {len(models)} models')
" || handle_error "Failed to generate token metrics"
    
    log "✅ Demo scenarios pre-loaded"
}

# Health check
health_check() {
    log "Running health checks..."
    
    # Test CLI commands
    local commands=("help" "list" "get gpt2")
    for cmd in "${commands[@]}"; do
        if ! timeout 10 ./mtop $cmd > /dev/null 2>&1; then
            handle_error "Health check failed for: mtop $cmd"
        fi
    done
    
    # Test monitoring display
    if ! timeout 5 python3 -c "
import sys
sys.path.insert(0, '.')
from mtop.token_metrics import create_token_tracker
tracker = create_token_tracker()
tracker.simulate_token_generation('test-model')
print('Monitoring system OK')
" > /dev/null 2>&1; then
        handle_error "Monitoring system health check failed"
    fi
    
    log "✅ All health checks passed"
}

# Demo scenarios summary
show_available_scenarios() {
    echo -e "${GREEN}"
    echo "📋 Available Demo Scenarios:"
    echo "═══════════════════════════════════════════════════════════════"
    echo "1. 🔄 Rolling Deployment Demo"
    echo "   ./demo.sh                    # Interactive version"
    echo "   ./demo.sh --headless        # Automated version"
    echo ""
    echo "2. 📊 Token Metrics Monitoring"
    echo "   ./mtop                      # Real-time monitoring"
    echo "   ./mtop list                 # List all models"
    echo "   ./mtop get <model-name>     # Inspect specific model"
    echo ""
    echo "3. 🎯 Rollout Simulations"
    echo "   ./mtop simulate canary      # Canary deployment"
    echo "   ./mtop simulate bluegreen   # Blue-green deployment"
    echo "   ./mtop simulate rolling     # Rolling deployment"
    echo "   ./mtop simulate shadow      # Shadow deployment"
    echo ""
    echo "4. 📈 Visual Monitoring"
    echo "   python3 watch_rollout.py --topology rolling --autoplay"
    echo ""
    echo "5. 🎬 VHS Recording (Sales Ready)"
    echo "   ./demo_cast.sh              # Record professional demo"
    echo "═══════════════════════════════════════════════════════════════"
    echo -e "${NC}"
}

# Startup timer
start_timer() {
    START_TIME=$(date +%s)
}

# Calculate and show setup time
show_setup_time() {
    END_TIME=$(date +%s)
    SETUP_TIME=$((END_TIME - START_TIME))
    echo -e "${GREEN}⏱️  Setup completed in ${SETUP_TIME} seconds${NC}"
}

# Main execution
main() {
    start_timer
    show_banner
    
    echo -e "${YELLOW}🔍 Sales Demo Kit - Zero Technical Knowledge Required${NC}"
    echo "Setting up complete LLM monitoring demo environment..."
    echo ""
    
    # Execute setup steps
    show_progress 1 6 "Checking system requirements"
    check_requirements
    
    show_progress 2 6 "Setting up Python environment"
    setup_environment
    
    show_progress 3 6 "Validating demo data"
    validate_mock_data
    
    show_progress 4 6 "Pre-loading scenarios"
    preload_scenarios
    
    show_progress 5 6 "Running health checks"
    health_check
    
    show_progress 6 6 "Demo environment ready"
    show_setup_time
    
    echo ""
    echo -e "${GREEN}✅ Demo Ready!${NC}"
    echo ""
    
    show_available_scenarios
    
    echo -e "${BLUE}💡 Demo Tips:${NC}"
    echo "• Start with: ${YELLOW}./demo.sh${NC} for guided experience"
    echo "• Use: ${YELLOW}./demo-status.sh${NC} to check system health"
    echo "• Clean up: ${YELLOW}./demo-cleanup.sh${NC} when finished"
    echo ""
    echo -e "${PURPLE}🎯 Sales Talking Points:${NC}"
    echo "• Real-time LLM inference monitoring and debugging"
    echo "• Kubernetes-native rollout simulation without cluster"
    echo "• Production-ready token metrics and SLO tracking"
    echo "• Zero-downtime deployment validation"
    echo ""
    
    log "Demo environment successfully launched"
}

# Trap errors and cleanup
trap 'handle_error "Unexpected error occurred"' ERR

# Execute main function
main "$@"