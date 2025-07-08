#!/bin/bash

# Demo Status Checker for mtop
# Real-time health monitoring for demo environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
STATUS_LOG="demo-status.log"
HEALTH_TIMEOUT=10

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> "$STATUS_LOG"
}

# Banner
show_banner() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                  📊 mtop Demo Status                        ║"
    echo "║              Real-time Health Monitoring                    ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Parse command line arguments
WATCH_MODE=false
DETAILED=false
JSON_OUTPUT=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --watch|-w)
            WATCH_MODE=true
            shift
            ;;
        --detailed|-d)
            DETAILED=true
            shift
            ;;
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--watch] [--detailed] [--json]"
            echo ""
            echo "Options:"
            echo "  --watch, -w    Continuous monitoring mode (refresh every 5s)"
            echo "  --detailed, -d Show detailed system information"
            echo "  --json         Output status in JSON format"
            echo "  --help, -h     Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./demo-status.sh           # Quick health check"
            echo "  ./demo-status.sh --watch   # Continuous monitoring"
            echo "  ./demo-status.sh --detailed # Detailed system info"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Test with timeout
test_with_timeout() {
    local cmd="$1"
    local timeout_duration="$2"
    
    if timeout "$timeout_duration" bash -c "$cmd" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Check system requirements
check_system() {
    local status="healthy"
    local details=""
    
    # Python version
    if command_exists python3; then
        local python_version=$(python3 --version 2>&1 | awk '{print $2}')
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
            details="Python $python_version ✅"
        else
            details="Python $python_version ❌ (need 3.11+)"
            status="error"
        fi
    else
        details="Python not found ❌"
        status="error"
    fi
    
    # Disk space
    local available_space=$(df . | awk 'NR==2 {print $4}')
    local space_mb=$((available_space / 1024))
    if [ "$available_space" -gt 100000 ]; then
        details="$details | Space: ${space_mb}MB ✅"
    else
        details="$details | Space: ${space_mb}MB ❌ (need 100MB+)"
        status="error"
    fi
    
    echo "$status|$details"
}

# Check virtual environment
check_venv() {
    local status="healthy"
    local details=""
    
    if [ -d "venv" ]; then
        if [ -f "venv/bin/activate" ]; then
            # Test activation
            if source venv/bin/activate 2>/dev/null; then
                details="Virtual env active ✅"
                
                # Check if requirements are installed
                if pip list | grep -q "pytest\|rich" 2>/dev/null; then
                    details="$details | Dependencies installed ✅"
                else
                    details="$details | Dependencies missing ❌"
                    status="warning"
                fi
            else
                details="Virtual env corrupted ❌"
                status="error"
            fi
        else
            details="Virtual env incomplete ❌"
            status="error"
        fi
    else
        details="Virtual env not found ❌"
        status="error"
    fi
    
    echo "$status|$details"
}

# Check mock data
check_mock_data() {
    local status="healthy"
    local details=""
    
    # Count CRs
    if [ -d "mocks/crs" ]; then
        local cr_count=$(find mocks/crs -name "*.json" | wc -l)
        if [ "$cr_count" -ge 5 ]; then
            details="CRs: $cr_count ✅"
        else
            details="CRs: $cr_count ❌ (need 5+)"
            status="error"
        fi
    else
        details="Mock CRs missing ❌"
        status="error"
    fi
    
    # Check other mock directories
    local mock_dirs=("config" "pod_logs" "states" "topologies")
    local missing_dirs=()
    
    for dir in "${mock_dirs[@]}"; do
        if [ ! -d "mocks/$dir" ]; then
            missing_dirs+=("$dir")
        fi
    done
    
    if [ ${#missing_dirs[@]} -eq 0 ]; then
        details="$details | Mock data complete ✅"
    else
        details="$details | Missing: ${missing_dirs[*]} ❌"
        status="error"
    fi
    
    echo "$status|$details"
}

# Check mtop CLI
check_mtop_cli() {
    local status="healthy"
    local details=""
    
    if [ -f "./mtop" ]; then
        if test_with_timeout "./mtop help" $HEALTH_TIMEOUT; then
            details="CLI working ✅"
            
            # Test basic commands
            if test_with_timeout "./mtop list" $HEALTH_TIMEOUT; then
                details="$details | Commands working ✅"
            else
                details="$details | Commands failing ❌"
                status="warning"
            fi
        else
            details="CLI not responding ❌"
            status="error"
        fi
    else
        details="mtop binary missing ❌"
        status="error"
    fi
    
    echo "$status|$details"
}

# Check token metrics system
check_token_metrics() {
    local status="healthy"
    local details=""
    
    # Test token metrics import
    if test_with_timeout "python3 -c 'from mtop.token_metrics import create_token_tracker, QueueMetrics; print(\"OK\")'" $HEALTH_TIMEOUT; then
        details="Token metrics ✅"
        
        # Test functionality
        if test_with_timeout "python3 -c '
import sys
sys.path.insert(0, \".\")
from mtop.token_metrics import create_token_tracker
tracker = create_token_tracker()
metrics = tracker.simulate_token_generation(\"test-model\")
queue_metrics = tracker.get_queue_metrics(\"test-model\")
assert metrics is not None
assert queue_metrics is not None
print(\"Functional\")
'" $HEALTH_TIMEOUT; then
            details="$details | Queue metrics ✅"
        else
            details="$details | Queue metrics ❌"
            status="error"
        fi
    else
        details="Token metrics import failed ❌"
        status="error"
    fi
    
    echo "$status|$details"
}

# Check running processes
check_processes() {
    local status="healthy"
    local details=""
    local processes=()
    
    # Check for mtop processes
    if pgrep -f "mtop" > /dev/null 2>&1; then
        local count=$(pgrep -f "mtop" | wc -l)
        processes+=("mtop:$count")
    fi
    
    # Check for demo processes
    if pgrep -f "watch_rollout.py" > /dev/null 2>&1; then
        local count=$(pgrep -f "watch_rollout.py" | wc -l)
        processes+=("monitor:$count")
    fi
    
    if [ ${#processes[@]} -gt 0 ]; then
        details="Running: ${processes[*]} ✅"
    else
        details="No demo processes ℹ️"
        status="info"
    fi
    
    echo "$status|$details"
}

# Get overall status
get_overall_status() {
    local checks=("$@")
    local error_count=0
    local warning_count=0
    
    for check in "${checks[@]}"; do
        local status=$(echo "$check" | cut -d'|' -f1)
        case "$status" in
            "error") ((error_count++)) ;;
            "warning") ((warning_count++)) ;;
        esac
    done
    
    if [ "$error_count" -gt 0 ]; then
        echo "error"
    elif [ "$warning_count" -gt 0 ]; then
        echo "warning"
    else
        echo "healthy"
    fi
}

# Format status indicator
format_status() {
    local status="$1"
    case "$status" in
        "healthy") echo -e "${GREEN}●${NC}" ;;
        "warning") echo -e "${YELLOW}●${NC}" ;;
        "error") echo -e "${RED}●${NC}" ;;
        "info") echo -e "${CYAN}●${NC}" ;;
        *) echo -e "${BLUE}●${NC}" ;;
    esac
}

# Display status in table format
display_status() {
    local system_check="$1"
    local venv_check="$2"
    local mock_check="$3"
    local cli_check="$4"
    local metrics_check="$5"
    local process_check="$6"
    
    local overall=$(get_overall_status "$system_check" "$venv_check" "$mock_check" "$cli_check" "$metrics_check" "$process_check")
    
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    printf "%-20s %-10s %s\n" "Component" "Status" "Details"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Format each check
    local checks=("System:$system_check" "Virtual Env:$venv_check" "Mock Data:$mock_check" "CLI:$cli_check" "Token Metrics:$metrics_check" "Processes:$process_check")
    
    for check in "${checks[@]}"; do
        local component=$(echo "$check" | cut -d':' -f1)
        local status=$(echo "$check" | cut -d':' -f2 | cut -d'|' -f1)
        local details=$(echo "$check" | cut -d':' -f2 | cut -d'|' -f2-)
        
        printf "%-20s %-10s %s\n" "$component" "$(format_status "$status")" "$details"
    done
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Overall status
    echo ""
    case "$overall" in
        "healthy")
            echo -e "${GREEN}✅ Demo environment is ${GREEN}HEALTHY${NC}"
            echo -e "${BLUE}💡 Ready for demos! Try: ${YELLOW}./demo.sh${NC}"
            ;;
        "warning")
            echo -e "${YELLOW}⚠️  Demo environment has ${YELLOW}WARNINGS${NC}"
            echo -e "${BLUE}💡 Demo may work with reduced functionality${NC}"
            ;;
        "error")
            echo -e "${RED}❌ Demo environment has ${RED}ERRORS${NC}"
            echo -e "${BLUE}💡 Run: ${YELLOW}./demo-launcher.sh${NC} to fix issues"
            ;;
    esac
    
    log "Status check completed - Overall: $overall"
}

# JSON output
display_json() {
    local system_check="$1"
    local venv_check="$2"
    local mock_check="$3"
    local cli_check="$4"
    local metrics_check="$5"
    local process_check="$6"
    
    local overall=$(get_overall_status "$system_check" "$venv_check" "$mock_check" "$cli_check" "$metrics_check" "$process_check")
    
    cat << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "overall_status": "$overall",
  "components": {
    "system": {
      "status": "$(echo "$system_check" | cut -d'|' -f1)",
      "details": "$(echo "$system_check" | cut -d'|' -f2-)"
    },
    "virtual_env": {
      "status": "$(echo "$venv_check" | cut -d'|' -f1)",
      "details": "$(echo "$venv_check" | cut -d'|' -f2-)"
    },
    "mock_data": {
      "status": "$(echo "$mock_check" | cut -d'|' -f1)",
      "details": "$(echo "$mock_check" | cut -d'|' -f2-)"
    },
    "cli": {
      "status": "$(echo "$cli_check" | cut -d'|' -f1)",
      "details": "$(echo "$cli_check" | cut -d'|' -f2-)"
    },
    "token_metrics": {
      "status": "$(echo "$metrics_check" | cut -d'|' -f1)",
      "details": "$(echo "$metrics_check" | cut -d'|' -f2-)"
    },
    "processes": {
      "status": "$(echo "$process_check" | cut -d'|' -f1)",
      "details": "$(echo "$process_check" | cut -d'|' -f2-)"
    }
  }
}
EOF
}

# Run single status check
run_status_check() {
    if [ "$JSON_OUTPUT" = false ]; then
        echo -e "${YELLOW}🔍 Checking demo environment health...${NC}"
    fi
    
    # Run all checks
    local system_check=$(check_system)
    local venv_check=$(check_venv)
    local mock_check=$(check_mock_data)
    local cli_check=$(check_mtop_cli)
    local metrics_check=$(check_token_metrics)
    local process_check=$(check_processes)
    
    # Display results
    if [ "$JSON_OUTPUT" = true ]; then
        display_json "$system_check" "$venv_check" "$mock_check" "$cli_check" "$metrics_check" "$process_check"
    else
        display_status "$system_check" "$venv_check" "$mock_check" "$cli_check" "$metrics_check" "$process_check"
        
        if [ "$DETAILED" = true ]; then
            echo ""
            echo -e "${CYAN}📋 Additional Details:${NC}"
            echo "• Log file: $STATUS_LOG"
            echo "• Demo scripts: demo-launcher.sh, demo-cleanup.sh, demo-status.sh"
            echo "• Mock data: $(find mocks -name "*.json" | wc -l) files"
            echo "• Available models: $(ls mocks/crs/*.json | wc -l)"
            echo "• System load: $(uptime | awk -F'load average:' '{print $2}')"
            echo "• Memory usage: $(free -h 2>/dev/null | awk '/^Mem:/ {print $3"/"$2}' || echo "N/A")"
        fi
    fi
}

# Watch mode
run_watch_mode() {
    echo -e "${YELLOW}👁️  Starting continuous monitoring (Ctrl+C to exit)...${NC}"
    echo ""
    
    while true; do
        clear
        show_banner
        run_status_check
        
        echo ""
        echo -e "${BLUE}🔄 Refreshing in 5 seconds... (Ctrl+C to exit)${NC}"
        sleep 5
    done
}

# Main execution
main() {
    if [ "$JSON_OUTPUT" = false ] && [ "$WATCH_MODE" = false ]; then
        show_banner
    fi
    
    if [ "$WATCH_MODE" = true ]; then
        run_watch_mode
    else
        run_status_check
    fi
}

# Handle Ctrl+C gracefully in watch mode
trap 'echo -e "\n${BLUE}👋 Monitoring stopped${NC}"; exit 0' INT

# Execute main function
main "$@"