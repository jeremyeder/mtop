# mtop Quick Start Guide

## 🚀 Get Running in 15 Minutes

This guide gets you up and running with mtop LLM monitoring in under 15 minutes, perfect for evaluation and demonstration.

## 📋 Prerequisites

### Required
- **Python 3.11+** (3.12 recommended)
- **Git** for repository access
- **Terminal/Shell** with basic command-line knowledge

### Optional for Full Experience
- **Kubernetes cluster** (local or cloud) for live monitoring
- **kubectl** configured for cluster access

## ⚡ Quick Setup (5 minutes)

### 1. Clone and Setup
```bash
# Clone the repository
git clone https://github.com/jeremyeder/mtop.git
cd mtop

# Create virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Verify Installation
```bash
# Test the CLI
python3 mtop-main help

# Expected output: Help text showing available commands
```

### 3. Run First Demo
```bash
# Run the quick demonstration
python3 scripts/demo_phase1_quick.py

# Expected output: Cost optimization demonstration with real metrics
```

## 🎯 Core Features Demo (10 minutes)

### Basic Monitoring
```bash
# List all available LLM services (mock mode)
python3 mtop-main list

# Get details for a specific model
python3 mtop-main get gpt-4-turbo

# Show global configuration
python3 mtop-main config
```

### Real-time Monitoring
```bash
# Launch interactive monitoring dashboard
python3 mtop-main

# Use 'q' to quit the dashboard
# Use arrow keys to navigate (if interactive features available)
```

### SLO Dashboard
```bash
# Launch SLO compliance dashboard
python3 mtop-main slo-dashboard --demo

# View real-time SLO metrics and convergence
```

### Cost Optimization Demo
```bash
# Run comprehensive cost optimization demonstration
python3 scripts/demo_phase1_cost_optimization.py

# Shows 40% GPU cost reduction scenarios
```

## 📊 What You'll See

### Mock Data Overview
- **34 LLM models** with realistic configurations
- **Real-time metrics** including TTFT, TPS, costs
- **GPU utilization** across multiple vendors (H100, A100, V100)
- **Cost tracking** with per-hour and monthly projections

### Business Value Demonstrations
- **40% cost reduction** through GPU rightsizing
- **Sub-500ms TTFT** performance guarantees
- **3x model density** through GPU fractioning
- **Enterprise portfolio** monitoring across 15+ models

### Technical Capabilities
- **Real-time dashboards** with live metric updates
- **SLO compliance monitoring** with automatic convergence
- **Multi-format output** (terminal, web-ready)
- **Professional visualizations** suitable for presentations

## 🎬 Professional Recordings

### Sales Demo Recordings
Access pre-recorded professional demonstrations:
```bash
# View available recordings
ls recordings/sales/

# Available formats:
# - cost-optimization.{gif,mp4,webm}
# - slo-compliance.{gif,mp4,webm}  
# - gpu-efficiency.{gif,mp4,webm}
# - load-handling.{gif,mp4,webm}
# - multi-model.{gif,mp4,webm}
```

### Demo Package
```bash
# Extract complete sales demo package
unzip mtop-sales-demo-package.zip
cd sales-demo-package/

# Professional demonstrations ready for:
# - Sales presentations
# - Executive briefings  
# - Technical evaluations
# - Training materials
```

## ✅ Validation Checklist

### Basic Functionality
- [ ] `python3 mtop-main help` shows command help
- [ ] `python3 mtop-main list` shows 34 models
- [ ] `python3 mtop-main get gpt-4-turbo` shows model details
- [ ] Demo scripts run without errors

### Interactive Features
- [ ] `python3 mtop-main` launches monitoring dashboard
- [ ] `python3 mtop-main slo-dashboard --demo` shows SLO metrics
- [ ] All demos complete successfully
- [ ] Professional recordings are accessible

## 🚨 Troubleshooting

### Common Issues

#### Python Version Error
```bash
Error: mtop requires Python 3.11 or later
```
**Solution**: Install Python 3.12+ or use virtual environment with correct version

#### Missing Dependencies
```bash
ModuleNotFoundError: No module named 'rich'
```
**Solution**: Install dependencies with `pip install -r requirements.txt`

#### Permission Denied
```bash
Permission denied: ./mtop-main
```
**Solution**: Make executable with `chmod +x mtop-main`

#### Demo Script Errors
```bash
FileNotFoundError: No such file or directory
```
**Solution**: Ensure you're in the mtop repository root directory

## 🎯 Next Steps

### For Evaluation
1. **Try all demo scenarios** - Run each sales demo recording
2. **Explore configuration** - Modify `config.yaml` settings  
3. **Test with live cluster** - Set `LLD_MODE=live` environment variable

### For Development
1. **Read the full guides** - [Development Setup](development/setup.md)
2. **Run the test suite** - `python3 -m pytest tests/ -v`
3. **Explore the architecture** - [Architecture Documentation](../architecture/)

### For Production
1. **Review deployment guides** - [Production Setup](deployment/production.md)
2. **Understand security** - [Security Documentation](../security/)
3. **Plan capacity** - [Performance Documentation](../performance/)

## 📚 Related Resources
- [Installation Guide](installation.md) - Complete installation instructions
- [First Demo](first-demo.md) - Detailed first demonstration
- [Examples](../examples/) - Working examples and use cases
- [Demo Guide](../../DEMO-GUIDE.md) - Comprehensive demo instructions

---

*Quick start guide for professional LLM monitoring evaluation*