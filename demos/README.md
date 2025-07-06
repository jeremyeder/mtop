# 🎯 mtop Demo Framework

**Super simple demo configurations for mtop - like having a magic wand for demos!**

## Quick Start ⚡

```bash
# See all available demo scenarios
./scripts/demo.py --list

# Run a quick startup demo
./scripts/demo.py startup

# Run enterprise demo without pauses
./scripts/demo.py enterprise --no-interactive

# Create your own custom demo
./scripts/config-mixer.py
```

## What's Included? 📦

### 🚀 **Ready-to-Use Demo Recipes**
- **startup**: Small company with limited resources
- **enterprise**: Large-scale multi-tenant deployment  
- **canary-failure**: Deployment failure and recovery
- **cost-optimization**: GPU cost comparison scenarios
- **research-lab**: Experimental research environment

### 🛠️ **Tools**
- **`scripts/demo.py`**: One-command demo runner
- **`scripts/config-mixer.py`**: Interactive demo creator  
- **`test-demos.sh`**: Test all demos work correctly

### 📚 **Documentation**
- **`DEMO-GUIDE.md`**: Complete "explain like I'm 5" guide
- **`demos/recipes/`**: All demo configurations
- **This README**: Quick reference

## Example Demo Session 🎬

```bash
$ ./scripts/demo.py startup

🚀 Startup Demo
===============
Small startup with 1-2 models, limited GPU resources, development environment

🔧 Environment Setup:
  MTOP_MODE=mock
  MTOP_TECHNOLOGY_GPU_A100_COST=2.5
  MTOP_WORKLOAD_BASELINE_QPS=50

🎬 Step 1: Show current model deployments
Running: ./mtop-main list
[Shows list of available models]

🎬 Step 2: Inspect the main model  
Running: ./mtop-main get gpt2
[Shows detailed model configuration]

🎬 Step 3: Watch real-time metrics
Running: ./mtop-main ldtop
[Shows live monitoring dashboard]

✅ Expected Outcomes:
  • 2 models running with modest resource usage
  • Low cost per hour (under $5)
  • Development-friendly settings enabled
```

## Creating Custom Demos 🎨

### Option 1: Interactive Creator
```bash
./scripts/config-mixer.py
```
Guides you through choosing:
- Environment (startup, enterprise, research)
- Topology (simple, complex, experimental)  
- Scenario (normal, failure, cost-optimization)
- Custom settings (costs, QPS, error rates)

### Option 2: Copy and Modify
```bash
cp demos/recipes/startup.yaml demos/recipes/my-demo.yaml
# Edit my-demo.yaml
./scripts/demo.py my-demo
```

## Demo Recipe Format 📋

```yaml
name: "My Demo"
description: "What this demo shows"
emoji: "🎯"

environment:
  mode: "mock"
  config: "production-config.json"
  topology: "enterprise"

overrides:
  MTOP_WORKLOAD_BASELINE_QPS: 200
  MTOP_TECHNOLOGY_GPU_A100_COST: 3.00

models:
  - "gpt-4-turbo"
  - "claude-3-haiku"

steps:
  - action: "list"
    description: "Show all models"
  - action: "ldtop"
    duration: 30
    description: "Monitor live metrics"

outcomes:
  - "Models running smoothly"
  - "Cost under budget"
```

## Available Actions 🎭

- **`list`**: Show all deployed models
- **`get`**: Inspect specific model (requires `target`)
- **`ldtop`**: Live monitoring dashboard
- **`simulate`**: Run deployment scenario (requires `type`)
- **`cost_analysis`**: Cost breakdown analysis
- **`cost_report`**: Cost optimization recommendations

## Environment Variables 🎛️

Quick tweaks without editing files:

```bash
# Cost controls
export MTOP_TECHNOLOGY_GPU_A100_COST=2.50

# Traffic controls  
export MTOP_WORKLOAD_BASELINE_QPS=100

# Quality controls
export MTOP_SLO_ERROR_RATE_PERCENT=1.0
```

## Testing 🧪

```bash
# Test all demos work
./test-demos.sh

# Test specific demo
./scripts/demo.py startup --dry-run

# Test config mixer
./scripts/config-mixer.py --help
```

## Pro Tips 💡

1. **Always dry-run first**: `--dry-run` shows what will happen
2. **Use non-interactive for presentations**: `--no-interactive`
3. **Environment variables for quick tweaks**: Great for live adjustments
4. **Start with existing recipes**: Easier than creating from scratch
5. **Save good configurations**: Use `config-mixer.py --save`

## Need Help? 🆘

- **List demos**: `./scripts/demo.py --list`
- **See what demo does**: `./scripts/demo.py DEMO --dry-run`  
- **Read full guide**: Open `DEMO-GUIDE.md`
- **Create new demo**: `./scripts/config-mixer.py`

---

*All demos use safe "mock" mode by default - no real infrastructure affected!* 🎉