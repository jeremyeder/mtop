# 🎯 mtop Demo Guide: Ridiculously Simple Edition

*"Like you're 5 years old" documentation for creating and running demo permutations*

## What is this? 🤔

Think of mtop demos like **different video games you can play**:
- 🚀 Startup Game: Small company with 1-2 computers
- 🏢 Enterprise Game: Big company with lots of computers  
- 🚨 Failure Game: Things break and you fix them
- 💰 Money Game: Make things cheaper and faster

Each "game" has its own rules, settings, and challenges!

## Super Quick Start (30 seconds) ⚡

```bash
# 1. See what games you can play
./scripts/demo.py --list

# 2. Play the startup game
./scripts/demo.py startup

# 3. Play the big company game  
./scripts/demo.py enterprise

# 4. Play the failure game (fun!)
./scripts/demo.py canary-failure
```

That's it! You're now a demo wizard! 🧙‍♂️

## The Magic Pieces 🧩

### 1. Recipe Files (`demos/recipes/*.yaml`)
These are like **instruction cards** for each game:
- What kind of computers to use (GPUs, memory)
- How many players (models) 
- What challenges to face (traffic, errors)
- What happens step by step

### 2. Demo Runner (`scripts/demo.py`)
This is your **game controller** - it reads the instruction cards and makes everything happen automatically.

### 3. Configuration Mixer (`scripts/config-mixer.py`)
This is your **game creator** - helps you design new games by choosing different options.

## Available Games (Recipes) 🎮

### 🚀 **Startup Game** (`startup.yaml`)
- **What**: Small company with limited money
- **Who**: 2 models on cheap computers
- **Challenge**: Keep costs low while serving customers
- **Learn**: Resource efficiency, development workflows

### 🏢 **Enterprise Game** (`enterprise.yaml`)
- **What**: Big company with multiple teams
- **Who**: 8+ models across different departments
- **Challenge**: High availability, security, compliance
- **Learn**: Multi-tenant operations, production scale

### 🚨 **Canary Failure Game** (`canary-failure.yaml`)
- **What**: Testing new software that starts failing
- **Who**: Old reliable model vs new experimental model
- **Challenge**: Detect problems and roll back safely
- **Learn**: Deployment safety, failure detection

### 💰 **Cost Optimization Game** (`cost-optimization.yaml`)
- **What**: Making things cheaper without breaking them
- **Who**: Different GPU types and scaling strategies
- **Challenge**: Minimize costs while meeting performance goals
- **Learn**: Resource optimization, ROI analysis

### 🔬 **Research Lab Game** (`research-lab.yaml`)
- **What**: Academic research environment
- **Who**: Experimental cutting-edge models
- **Challenge**: Flexibility for rapid experimentation
- **Learn**: Research workflows, model comparison

## Creating Your Own Games 🎨

### Option 1: Use the Interactive Creator
```bash
./scripts/config-mixer.py
```

The creator will ask you simple questions:
1. **Environment**: What kind of place? (startup, enterprise, research lab)
2. **Topology**: How are things organized? (simple, complex, experimental)
3. **Scenario**: What kind of challenge? (normal, spike, failure, cost-saving)
4. **Custom Settings**: Special tweaks (costs, speeds, error tolerance)

### Option 2: Copy and Modify Existing Recipes
```bash
# Copy an existing recipe
cp demos/recipes/startup.yaml demos/recipes/my-custom-demo.yaml

# Edit it with your favorite editor
vim demos/recipes/my-custom-demo.yaml

# Run your custom demo
./scripts/demo.py my-custom-demo
```

## Understanding Demo Recipes 📋

Every recipe has these sections:

```yaml
# Basic Info
name: "My Cool Demo"
description: "What this demo shows"
emoji: "🎯"

# Environment Setup
environment:
  mode: "mock"                    # Use fake data (safe!)
  config: "production-config.json" # What kind of environment
  topology: "enterprise"          # How things are organized

# Custom Settings
overrides:
  MTOP_WORKLOAD_BASELINE_QPS: 200        # How busy (queries per second)
  MTOP_TECHNOLOGY_GPU_A100_COST: 3.00    # GPU cost per hour
  MTOP_SLO_ERROR_RATE_PERCENT: 1.0       # How many errors are OK

# Which Models to Show
models:
  - "gpt-4-turbo"
  - "claude-3-haiku"

# What Happens Step by Step
steps:
  - action: "list"
    description: "Show all models"
  - action: "monitor"
    duration: 30
    description: "Watch real-time metrics"

# What You Should See
outcomes:
  - "Models running smoothly"
  - "Costs under $10/hour"
```

## Magic Environment Variables 🎛️

You can change things on the fly without editing files:

### 💸 **Cost Controls**
```bash
# Make GPUs cheaper for demo
export MTOP_TECHNOLOGY_GPU_A100_COST=1.50

# Make GPUs more expensive (enterprise pricing)
export MTOP_TECHNOLOGY_GPU_A100_COST=8.00
```

### 🚦 **Traffic Controls**
```bash
# Light traffic (startup)
export MTOP_WORKLOAD_BASELINE_QPS=50

# Heavy traffic (enterprise)
export MTOP_WORKLOAD_BASELINE_QPS=1000

# Traffic spikes (2x normal)
export MTOP_WORKLOAD_SPIKE_MULTIPLIER=2.0
```

### 🎯 **Quality Controls**
```bash
# Strict quality (0.1% errors OK)
export MTOP_SLO_ERROR_RATE_PERCENT=0.1

# Relaxed quality (5% errors OK)
export MTOP_SLO_ERROR_RATE_PERCENT=5.0

# Fast response required (200ms)
export MTOP_SLO_TTFT_P95_MS=200
```

## Common Demo Scenarios 🎬

### **"Show me a small startup"**
```bash
export MTOP_WORKLOAD_BASELINE_QPS=25
export MTOP_TECHNOLOGY_GPU_A100_COST=2.00
./scripts/demo.py startup
```

### **"Show me enterprise scale"**
```bash
export MTOP_WORKLOAD_BASELINE_QPS=800
export MTOP_SLO_ERROR_RATE_PERCENT=0.1
./scripts/demo.py enterprise
```

### **"Show me a deployment going wrong"**
```bash
./scripts/demo.py canary-failure
# Watch error rates climb and automatic rollback!
```

### **"Show me cost savings"**
```bash
# Before: Expensive setup
export MTOP_TECHNOLOGY_GPU_A100_COST=5.00
./scripts/demo.py cost-optimization

# After: Show savings
export MTOP_TECHNOLOGY_GPU_A100_COST=2.50
./scripts/demo.py cost-optimization
```

## Troubleshooting 🔧

### **"My demo won't start"**
1. Make sure scripts are executable:
   ```bash
   chmod +x scripts/demo.py
   chmod +x scripts/config-mixer.py
   chmod +x mtop
   ```

2. Check you have the right Python packages:
   ```bash
   pip install -r requirements.txt
   ```

### **"I see 'mtop command not found'"**
Make the main mtop script executable:
```bash
chmod +x mtop
```

### **"My custom recipe doesn't work"**
1. Check YAML syntax:
   ```bash
   python3 -c "import yaml; yaml.safe_load(open('demos/recipes/my-recipe.yaml'))"
   ```

2. Test with dry-run first:
   ```bash
   ./scripts/demo.py my-recipe --dry-run
   ```

### **"I want to see what's happening"**
Use dry-run mode to see what would happen:
```bash
./scripts/demo.py enterprise --dry-run
```

## Advanced: Custom Demo Variations 🚀

### **Multi-Step Cost Comparison**
Create a recipe that shows before/after cost scenarios:

```yaml
scenarios:
  - name: "current_state"
    overrides:
      MTOP_TECHNOLOGY_GPU_A100_COST: 5.00
  - name: "optimized_state"  
    overrides:
      MTOP_TECHNOLOGY_GPU_A100_COST: 2.50
```

### **Failure Injection Patterns**
Add realistic failure patterns:

```yaml
failure_simulation:
  start_step: 2
  error_rate_progression: [0.1, 2.0, 5.0, 8.0]
  latency_degradation: true
```

### **Custom Model Sets**
Focus on specific model categories:

```yaml
# Code generation focus
models:
  - "stable-code-instruct-3b"
  - "codellama-34b-instruct"

# Conversational AI focus  
models:
  - "gpt-4-turbo"
  - "claude-3-haiku"
  - "llama-3-70b-instruct"
```

## Pro Tips 💡

1. **Start Simple**: Use existing recipes before creating custom ones
2. **Use Dry-Run**: Always test with `--dry-run` first
3. **Save Good Configs**: Use `config-mixer.py --save` for reusable recipes
4. **Environment Variables**: Great for quick tweaks without file editing
5. **Interactive Mode**: Default mode pauses between steps - great for explaining
6. **Non-Interactive**: Use `--no-interactive` for automated presentations

## Recipe Collection 📚

Want more recipes? Check out:
- `demos/recipes/` - All available recipes
- `mocks/config/` - Environment configurations  
- `mocks/topologies/` - Deployment layouts
- `mocks/states/rollout/` - Deployment scenarios

## Getting Help 🆘

- **List available demos**: `./scripts/demo.py --list`
- **See what a demo would do**: `./scripts/demo.py DEMO_NAME --dry-run`
- **Create new demo interactively**: `./scripts/config-mixer.py`
- **Quick preset demos**: `./scripts/config-mixer.py --quick`

## Next Steps 🎯

1. **Try all the built-in recipes** to understand the patterns
2. **Create your first custom recipe** using the mixer tool
3. **Experiment with environment variables** to see live changes
4. **Build a presentation** by chaining multiple demo scenarios
5. **Share your cool recipes** with the team!

---

*Remember: These are all safe "mock" demos - no real infrastructure is affected! Play around and have fun!* 🎉