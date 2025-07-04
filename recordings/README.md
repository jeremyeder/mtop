# 🎬 kubectl-ld Demo Recordings

```
██╗░░██╗██╗░░░██╗██████╗░███████╗░█████╗░████████╗██╗░░░░░░░░░██╗██████╗░
██║░██╔╝██║░░░██║██╔══██╗██╔════╝██╔══██╗╚══██╔══╝██║░░░░░░░░██╔╝██╔══██╗
█████═╝░██║░░░██║██████╦╝█████╗░░██║░░╚═╝░░░██║░░░██║░░░░░░██╔╝░██║░░██║
██╔═██╗░██║░░░██║██╔══██╗██╔══╝░░██║░░██╗░░░██║░░░██║░░░░░██╔╝░░██║░░██║
██║░╚██╗╚██████╔╝██████╦╝███████╗╚█████╔╝░░░██║░░░███████╗██╔╝░░░██████╔╝
╚═╝░░╚═╝░╚═════╝░╚═════╝░╚══════╝░╚════╝░░░░╚═╝░░░╚══════╝╚═╝░░░░╚═════╝░
                    Demo Recordings Collection
```

> **✨ Interactive demonstrations of kubectl-ld's LLM inference service management capabilities**

---

## 🎯 What You're Looking At

This directory contains **interactive terminal recordings** that showcase kubectl-ld's powerful features for managing Large Language Model (LLM) inference services in Kubernetes. Each demo demonstrates different deployment strategies, monitoring capabilities, and real-world scenarios.

### 📁 Available Demos

| Demo Type | Duration | Description | File Size |
|-----------|----------|-------------|-----------|
| **🎬 Basic Demo** | ~60s | Essential kubectl-ld commands and workflows | 7.1 KB |
| **🎭 Full Demo** | ~180s | Comprehensive feature showcase | 10.2 KB |
| **🖥️ Split-Basic Demo** | ~30s | Simple 3-model split-screen monitoring | 538 KB |
| **🚀 Split-Surge Demo** | ~30s | Traffic surge with 20+ models | 149 KB |
| **⚡ Split-Chaos Demo** | ~30s | Failure injection and recovery | 145 KB |
| **🎯 Split-Multi Demo** | ~30s | Multiple deployment strategies | 38 KB |

---

## 🚀 How to Use These Demos

### 📺 Playing Recordings

The demos are recorded in **asciinema format** (`.cast` files) - the gold standard for terminal recordings.

#### Option 1: Quick Preview (Recommended for First-Time Viewers)
```bash
# Run the preview script to see all demos
./preview.sh
```

#### Option 2: Full Playback
```bash
# Install asciinema
pip install asciinema
# or
brew install asciinema

# Play any demo
asciinema play basic-demo.cast
asciinema play full-demo.cast
```

#### Option 3: Web Browser
```bash
# Upload to asciinema.org for web viewing
asciinema upload basic-demo.cast
```

### 🎮 Interactive Controls

While playing demos, you can use these controls:

- **`Space`** - Pause/Resume
- **`←` / `→`** - Rewind/Fast-forward
- **`↑` / `↓`** - Speed up/Slow down
- **`q`** - Quit
- **`.`** - Step forward (when paused)
- **`,`** - Step backward (when paused)

---

## 🎨 Demo Breakdown

### 🎬 Basic Demo (`basic-demo.cast`)
**Perfect for newcomers** - Shows essential kubectl-ld functionality

**What you'll see:**
- 📦 Listing available rollout topologies
- 🔍 Checking LLM inference service status
- 📊 Monitoring deployment progress
- 🎯 Real-time rollout strategies

**Key Commands Demonstrated:**
```bash
kubectl-ld list topologies
kubectl-ld check status
kubectl-ld watch rollout
```

### 🎭 Full Demo (`full-demo.cast`)
**Comprehensive showcase** - Deep dive into advanced features

**What you'll see:**
- 🚀 Multiple deployment strategies (Blue/Green, Canary, Rolling)
- 🔧 Configuration management
- 📈 Advanced monitoring and metrics
- 🛡️ Error handling and recovery

**Key Commands Demonstrated:**
```bash
kubectl-ld deploy --strategy canary
kubectl-ld rollback --to-revision 2
kubectl-ld scale --replicas 5
```

### 🖥️ Split-Screen Demos
**Advanced scenarios** - Multi-model management at scale

**Scenarios Available:**
- **Basic** - Simple 3-model deployment monitoring
- **Surge** - Black Friday traffic surge across 20+ models  
- **Chaos** - Failure injection and recovery scenarios
- **Multi** - Multiple deployment strategies (Blue/Green, Canary, Shadow, Rolling)

These demos showcase kubectl-ld's advanced monitoring capabilities with realistic traffic patterns and deployment strategies.

---

## 🔧 Technical Details

### 📋 Recording Specifications

| Specification | Value |
|---------------|-------|
| **Format** | asciinema v2 |
| **Terminal** | 120x30 (basic), 140x40 (split-screen) |
| **Encoding** | UTF-8 |
| **Shell** | bash |
| **Environment** | Mock mode (safe for demos) |

### 🎯 Demo Environment

All demos run in **mock mode** - a safe simulation environment that:
- ✅ Shows realistic kubectl-ld behavior
- ✅ Doesn't require actual Kubernetes cluster
- ✅ Uses synthetic data for demonstrations
- ✅ Safe to run anywhere

### 📊 Metadata Files

Each demo includes a metadata file (`.json`) with:
```json
{
  "demo_type": "basic",
  "command": "./demo.sh --headless",
  "duration": "60s",
  "recorded_at": "2024-01-04T12:00:00Z",
  "version": "v1.0.0"
}
```

---

## 🛠️ Creating Your Own Demos

### 📝 Record New Demo
```bash
# Using our recording helper
./scripts/record_demo.sh --type basic --headless

# Manual recording
asciinema rec my-demo.cast --title "My kubectl-ld Demo"
```

### 🎨 Convert to Other Formats
```bash
# Install converter
npm install -g @asciinema/agg

# Convert to GIF
agg basic-demo.cast basic-demo.gif --cols 120 --rows 30

# Convert to multiple formats
./scripts/convert_demos.sh --format all
```

---

## 🎪 Demo Gallery

### 🎬 Basic Demo Preview
```
🔧 Mode: mock
📦 Available rollout topologies:
  - bluegreen
  - canary  
  - rolling
  - shadow
⏳ Continuing in 3 seconds...
```

### 🎭 Full Demo Preview
```
🚀 Starting comprehensive kubectl-ld demonstration...
🎯 Scenario: Full feature showcase
🔧 Setting up mock environment...
═══════════════════════════════════════════════════════════════
🔸 Step 1: Cluster Overview
═══════════════════════════════════════════════════════════════
```

---

## 🏆 Best Practices

### 🎯 For Viewers
1. **Watch in fullscreen** for best experience
2. **Pause frequently** to understand commands
3. **Try commands yourself** in mock mode
4. **Use slow playback** for complex scenarios

### 🛠️ For Developers
1. **Keep demos under 3 minutes** for attention span
2. **Use clear narration** and step markers
3. **Test in mock mode** before recording
4. **Include error scenarios** for realism

---

## 🆘 Troubleshooting

### Common Issues

**❌ "asciinema command not found"**
```bash
# Install asciinema
pip install asciinema
# or
brew install asciinema
```

**❌ "Demo playback too fast/slow"**
```bash
# Control playback speed
asciinema play demo.cast --speed 0.5  # Half speed
asciinema play demo.cast --speed 2.0  # Double speed
```

**❌ "Demo won't start"**
```bash
# Check file integrity
file basic-demo.cast
# Should show: JSON text data

# Validate asciinema format
asciinema cat basic-demo.cast | head -1
# Should show: {"version": 2, ...}
```

**❌ "Split-screen demo issues"**
```bash
# Test tmux availability
tmux -V
# Should show: tmux 3.x

# Manual execution
./demo_split.sh --scenario basic
# Or try without tmux
./demo_narrator.py --scenario basic --headless
```

---

## 🌟 Credits

**Demo Recordings:** Automatically generated using GitHub Actions  
**Recording Tools:** asciinema, tmux, rich (Python)  
**Conversion Tools:** @asciinema/agg, ffmpeg  
**Mock Environment:** kubectl-ld mock mode  

---

## 🔗 Quick Links

- 📚 [Main kubectl-ld Documentation](../README.md)
- 🚀 [Getting Started Guide](../README.md#getting-started)
- 🛠️ [Installation Instructions](../README.md#installation)
- 🐛 [Issue Tracker](https://github.com/jeder/ldctl/issues)

---

<div align="center">

**🎬 Lights, Camera, kubectl-ld! 🎭**

*Made with ❤️ by the kubectl-ld team*

</div>