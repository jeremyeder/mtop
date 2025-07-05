#!/bin/bash

# Demo Cleanup Script for mtop
# Graceful cleanup after demo completion

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
CLEANUP_LOG="demo-cleanup.log"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$CLEANUP_LOG"
}

# Banner
show_banner() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                  🧹 mtop Demo Cleanup                       ║"
    echo "║              Graceful Environment Reset                     ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Parse command line arguments
FORCE_CLEANUP=false
KEEP_VENV=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE_CLEANUP=true
            shift
            ;;
        --keep-venv)
            KEEP_VENV=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--force] [--keep-venv]"
            echo ""
            echo "Options:"
            echo "  --force      Force cleanup without confirmation"
            echo "  --keep-venv  Keep virtual environment for faster restarts"
            echo "  --help       Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Confirmation prompt
ask_confirmation() {
    if [ "$FORCE_CLEANUP" = true ]; then
        return 0
    fi
    
    echo -e "${YELLOW}🤔 Are you sure you want to clean up the demo environment?${NC}"
    echo "This will:"
    echo "• Stop any running demo processes"
    echo "• Clear temporary files and logs"
    if [ "$KEEP_VENV" = false ]; then
        echo "• Remove virtual environment (use --keep-venv to preserve)"
    fi
    echo ""
    read -p "Continue? [y/N]: " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}ℹ️  Cleanup cancelled${NC}"
        exit 0
    fi
}

# Stop running processes
stop_processes() {
    log "Stopping demo processes..."
    
    # Kill any mtop processes
    if pgrep -f "mtop" > /dev/null 2>&1; then
        echo -e "${YELLOW}🛑 Stopping mtop processes...${NC}"
        pkill -f "mtop" || true
        sleep 2
    fi
    
    # Kill any demo monitoring processes
    if pgrep -f "watch_rollout.py" > /dev/null 2>&1; then
        echo -e "${YELLOW}🛑 Stopping monitoring processes...${NC}"
        pkill -f "watch_rollout.py" || true
        sleep 2
    fi
    
    # Kill any Python demo processes
    if pgrep -f "demo_monitor.py" > /dev/null 2>&1; then
        echo -e "${YELLOW}🛑 Stopping demo monitors...${NC}"
        pkill -f "demo_monitor.py" || true
        sleep 2
    fi
    
    log "✅ Demo processes stopped"
}

# Clean temporary files
clean_temp_files() {
    log "Cleaning temporary files..."
    
    # Remove log files
    local log_files=(
        "demo-setup.log"
        "demo-cleanup.log"
        "mtop.log"
        "*.log"
    )
    
    for pattern in "${log_files[@]}"; do
        if ls $pattern 1> /dev/null 2>&1; then
            echo -e "${BLUE}🗑️  Removing logs: $pattern${NC}"
            rm -f $pattern
        fi
    done
    
    # Clean Python cache
    if [ -d "__pycache__" ]; then
        echo -e "${BLUE}🗑️  Removing Python cache...${NC}"
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find . -name "*.pyc" -delete 2>/dev/null || true
    fi
    
    # Clean pytest cache
    if [ -d ".pytest_cache" ]; then
        echo -e "${BLUE}🗑️  Removing pytest cache...${NC}"
        rm -rf .pytest_cache
    fi
    
    # Clean any demo recordings if left over
    if [ -d "recordings/tmp" ]; then
        echo -e "${BLUE}🗑️  Removing temporary recordings...${NC}"
        rm -rf recordings/tmp
    fi
    
    log "✅ Temporary files cleaned"
}

# Remove virtual environment
clean_venv() {
    if [ "$KEEP_VENV" = true ]; then
        echo -e "${YELLOW}📦 Keeping virtual environment (--keep-venv specified)${NC}"
        log "Virtual environment preserved"
        return 0
    fi
    
    if [ -d "venv" ]; then
        echo -e "${BLUE}🗑️  Removing virtual environment...${NC}"
        rm -rf venv
        log "✅ Virtual environment removed"
    else
        log "No virtual environment found"
    fi
}

# Reset environment variables
reset_environment() {
    log "Resetting environment variables..."
    
    unset LLD_MODE
    unset PYTHONPATH
    
    # If virtual environment was active, deactivate it
    if [ -n "$VIRTUAL_ENV" ]; then
        echo -e "${YELLOW}📤 Deactivating virtual environment...${NC}"
        deactivate 2>/dev/null || true
    fi
    
    log "✅ Environment variables reset"
}

# Health check after cleanup
verify_cleanup() {
    log "Verifying cleanup..."
    
    # Check for remaining processes
    if pgrep -f "mtop\|watch_rollout\|demo_monitor" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Some demo processes may still be running${NC}"
        echo "Run: ps aux | grep -E 'mtop|watch_rollout|demo_monitor' to check"
    fi
    
    # Check virtual environment
    if [ "$KEEP_VENV" = false ] && [ -d "venv" ]; then
        echo -e "${YELLOW}⚠️  Virtual environment directory still exists${NC}"
    fi
    
    log "✅ Cleanup verification complete"
}

# Show cleanup summary
show_summary() {
    echo ""
    echo -e "${GREEN}✅ Demo cleanup complete!${NC}"
    echo ""
    echo -e "${BLUE}📋 Summary:${NC}"
    echo "• Demo processes stopped"
    echo "• Temporary files removed"
    if [ "$KEEP_VENV" = false ]; then
        echo "• Virtual environment removed"
    else
        echo "• Virtual environment preserved"
    fi
    echo "• Environment variables reset"
    echo ""
    echo -e "${PURPLE}🔄 To restart demo:${NC}"
    echo "• Run: ${YELLOW}./demo-launcher.sh${NC}"
    echo ""
    echo -e "${BLUE}💡 Tips:${NC}"
    echo "• Use ${YELLOW}--keep-venv${NC} flag to preserve Python environment"
    echo "• Use ${YELLOW}--force${NC} flag for automated cleanup"
    echo ""
    
    log "Demo cleanup completed successfully"
}

# Main execution
main() {
    show_banner
    
    echo -e "${YELLOW}🧹 Cleaning up mtop demo environment...${NC}"
    echo ""
    
    # Ask for confirmation unless forced
    ask_confirmation
    
    echo ""
    echo -e "${BLUE}🔧 Starting cleanup process...${NC}"
    echo ""
    
    # Execute cleanup steps
    stop_processes
    clean_temp_files
    reset_environment
    clean_venv
    verify_cleanup
    
    show_summary
}

# Execute main function
main "$@"