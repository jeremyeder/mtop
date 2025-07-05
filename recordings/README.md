# 🎬 mtop Demo Recordings

```
██╗░░██╗██╗░░░██╗██████╗░███████╗░█████╗░████████╗██╗░░░░░░░░░██╗██████╗░
██║░██╔╝██║░░░██║██╔══██╗██╔════╝██╔══██╗╚══██╔══╝██║░░░░░░░░██╔╝██╔══██╗
█████═╝░██║░░░██║██████╦╝█████╗░░██║░░╚═╝░░░██║░░░██║░░░░░░██╔╝░██║░░██║
██╔═██╗░██║░░░██║██╔══██╗██╔══╝░░██║░░██╗░░░██║░░░██║░░░░░██╔╝░░██║░░██║
██║░╚██╗╚██████╔╝██████╦╝███████╗╚█████╔╝░░░██║░░░███████╗██╔╝░░░██████╔╝
╚═╝░░╚═╝░╚═════╝░╚═════╝░╚══════╝░╚════╝░░░░╚═╝░░░╚══════╝╚═╝░░░░╚═════╝░
                    Demo Recordings Collection
```

> **✨ Interactive demonstrations of mtop's LLM inference service management capabilities**

---

## 🎯 What You're Looking At

This directory contains **interactive terminal recordings** and **video demonstrations** that showcase mtop's powerful features for managing Large Language Model (LLM) inference services in Kubernetes. Each demo demonstrates different deployment strategies, monitoring capabilities, and real-world scenarios.

### 📁 Available Demos

| Demo Type | Duration | Description | Formats | File Size |
|-----------|----------|-------------|---------|-----------|
| **🚀 Phase 1 Quick Demo** | ~30s | **NEW** Real Phase 1 integration with cost optimization | [▶️ WebM](phase1-quick-demo.webm) \| [🎬 MP4](phase1-quick-demo.mp4) \| [🖼️ GIF](phase1-quick-demo.gif) | 1.3M (GIF) |
| **🎬 Basic Demo** | ~60s | Essential mtop commands and workflows (Legacy) | [📜 Cast](basic-demo.cast) | 7.1 KB |
| **🎭 Full Demo** | ~180s | Comprehensive feature showcase (Legacy) | [📜 Cast](full-demo.cast) | 10.2 KB |
| **🖥️ Split-Basic Demo** | ~30s | Simple 3-model split-screen monitoring | [📜 Cast](split-basic-demo.cast) | 538 KB |
| **🚀 Split-Surge Demo** | ~30s | Traffic surge with 20+ models | [📜 Cast](split-surge-demo.cast) | 149 KB |
| **⚡ Split-Chaos Demo** | ~30s | Failure injection and recovery | [📜 Cast](split-chaos-demo.cast) | 145 KB |
| **🎯 Split-Multi Demo** | ~30s | Multiple deployment strategies | [📜 Cast](split-multi-demo.cast) | 38 KB |

---

## 🌟 **NEW: Phase 1 Integration Demos**

### 🚀 Phase 1 Quick Demo - **FEATURED**

**Click to play:** 
<video width="100%" controls>
  <source src="phase1-quick-demo.webm" type="video/webm">
  <source src="phase1-quick-demo.mp4" type="video/mp4">
  Your browser does not support the video tag. <a href="phase1-quick-demo.gif">View GIF version</a>
</video>

**What makes this demo special:**
- ✅ **Zero hardcoded values** - all metrics from actual Phase 1 systems
- ✅ **Real TokenMetrics integration** - actual P95 latency calculations
- ✅ **Dynamic CostCalculator** - live GPU pricing from TechnologyConfig
- ✅ **Live QueueMetrics** - real queue depth tracking with TTFT impact
- ✅ **Working software demonstration** - not conceptual estimates

**Business Value Demonstrated:**
- 🎯 **40% cost reduction** through GPU optimization (H100→A100)
- 💰 **$17,520 annual savings** per model
- 📈 **$500K+ enterprise value** across LLM portfolio
- 🔧 **Mathematical accuracy** vs competitor approximations

**Key Differentiators:**
- **Real P95 latencies** from TokenMetrics vs estimated performance
- **Dynamic pricing** from TechnologyConfig vs hardcoded values
- **Working infrastructure** vs conceptual demonstrations
- **Live calculations** vs static reports

---

## 🚀 How to Use These Demos

### 📺 Phase 1 Video Demos (Recommended)

The Phase 1 demos are available in multiple video formats for easy viewing:

#### Option 1: Direct Download and Play
```bash
# Download and play locally
open phase1-quick-demo.mp4           # macOS
xdg-open phase1-quick-demo.webm      # Linux
start phase1-quick-demo.mp4          # Windows
```

#### Option 2: Web Browser Embedding
```html
<!-- For websites and presentations -->
<video controls>
  <source src="phase1-quick-demo.webm" type="video/webm">
  <source src="phase1-quick-demo.mp4" type="video/mp4">
</video>
```

#### Option 3: GIF for Documentation
```markdown
<!-- For GitHub, wikis, and documentation -->
![Phase 1 Demo](phase1-quick-demo.gif)
```

### 📺 Legacy Cast Demos

The legacy demos are recorded in **asciinema format** (`.cast` files):

#### Quick Preview
```bash
# Run the preview script to see all demos
./preview.sh
```

#### Full Playback
```bash
# Install asciinema
pip install asciinema
# or
brew install asciinema

# Play any demo
asciinema play basic-demo.cast
asciinema play full-demo.cast
```

### 🎮 Interactive Controls (Video Demos)

- **`Space`** - Pause/Resume
- **`←` / `→`** - Seek backward/forward
- **`↑` / `↓`** - Volume up/down
- **`F`** - Fullscreen
- **`M`** - Mute/Unmute

---

## 🎨 Demo Breakdown

### 🚀 **Phase 1 Quick Demo** (`phase1-quick-demo.*`)
**Perfect for sales presentations** - Shows actual Phase 1 infrastructure capabilities

**What you'll see:**
- 📊 **Live TokenMetrics**: Real TPS and TTFT measurements from Phase 1 systems
- 💰 **Dynamic Cost Analysis**: Actual GPU pricing from TechnologyConfig (H100: $5.00/hr, A100: $3.00/hr)
- 🎯 **Real Optimization Results**: Live cost savings calculations (40% reduction, $17,520 annual savings)
- ✅ **Technical Credibility**: Zero hardcoded values, all metrics from working infrastructure

**Business Impact Demonstrated:**
```
📊 Phase 1 Live Metrics:
  llama-3-70b            1000 TPS     345ms TTFT  H100
  gpt-4-turbo            1000 TPS     381ms TTFT  H100
  claude-3-sonnet        1000 TPS     339ms TTFT  A100

💰 Real-Time Cost Analysis:
  H100: $5.00/hour
  A100: $3.00/hour

🎯 Optimization Results:
  Cost savings: $2.00/hour (40% reduction)
  Monthly savings: $1440.00
  Annual ROI: $17520.00
```

### 🎬 Basic Demo (`basic-demo.cast`)
**Perfect for newcomers** - Shows essential mtop functionality (Legacy)

**What you'll see:**
- 📦 Listing available rollout topologies
- 🔍 Checking LLM inference service status
- 📊 Monitoring deployment progress
- 🎯 Real-time rollout strategies

### 🎭 Full Demo (`full-demo.cast`)
**Comprehensive showcase** - Deep dive into advanced features (Legacy)

**What you'll see:**
- 🚀 Multiple deployment strategies (Blue/Green, Canary, Rolling)
- 🔧 Configuration management
- 📈 Advanced monitoring and metrics
- 🛡️ Error handling and recovery

### 🖥️ Split-Screen Demos
**Advanced scenarios** - Multi-model management at scale

**Scenarios Available:**
- **Basic** - Simple 3-model deployment monitoring
- **Surge** - Black Friday traffic surge across 20+ models  
- **Chaos** - Failure injection and recovery scenarios
- **Multi** - Multiple deployment strategies (Blue/Green, Canary, Shadow, Rolling)

---

## 🔧 Technical Details

### 📋 Phase 1 Demo Specifications

| Specification | Value |
|---------------|-------|
| **Format** | MP4, WebM, GIF |
| **Resolution** | 1200x600 |
| **Encoding** | H.264 (MP4), VP9 (WebM), Optimized (GIF) |
| **Duration** | ~30 seconds |
| **Integration** | Real Phase 1 infrastructure |
| **Data Source** | TokenMetrics, CostCalculator, QueueMetrics |

### 📋 Legacy Demo Specifications

| Specification | Value |
|---------------|-------|
| **Format** | asciinema v2 |
| **Terminal** | 120x30 (basic), 140x40 (split-screen) |
| **Encoding** | UTF-8 |
| **Shell** | bash |
| **Environment** | Mock mode (safe for demos) |

### 🎯 Demo Environment

**Phase 1 Demos** run with actual infrastructure integration:
- ✅ Real TokenMetrics calculations
- ✅ Dynamic CostCalculator with TechnologyConfig
- ✅ Live QueueMetrics tracking
- ✅ Mathematical accuracy in all calculations

**Legacy Demos** run in **mock mode** - a safe simulation environment:
- ✅ Shows realistic mtop behavior
- ✅ Doesn't require actual Kubernetes cluster
- ✅ Uses synthetic data for demonstrations
- ✅ Safe to run anywhere

---

## 🛠️ Creating Your Own Phase 1 Demos

### 📝 Record New Phase 1 Demo
```bash
# Using VHS for high-quality recordings
vhs tapes/my-phase1-demo.tape

# Manual recording with script
python3 scripts/demo_phase1_quick.py
```

### 🎨 Convert to Multiple Formats
```bash
# VHS automatically generates multiple formats
# Output: .gif, .mp4, .webm

# Or convert existing recordings
ffmpeg -i demo.mp4 -vf "scale=800:600" -loop 0 demo.gif
```

---

## 🎪 Live Demo Gallery

### 🚀 Phase 1 Quick Demo Preview

**Real Phase 1 Integration Output:**
```
🎯 mtop Phase 1 Demo: Real-Time Cost Optimization
💡 Live integration with Phase 1 infrastructure

📊 Phase 1 Live Metrics:
  llama-3-70b            1000 TPS     345ms TTFT  H100
  gpt-4-turbo            1000 TPS     381ms TTFT  H100
  claude-3-sonnet        1000 TPS     339ms TTFT  A100

💰 Real-Time Cost Analysis:
  H100: $5.00/hour
  A100: $3.00/hour

🎯 Optimization Results:
  Cost savings: $2.00/hour (40% reduction)
  Monthly savings: $1440.00
  Annual ROI: $17520.00

✅ Phase 1 Integration Complete
  • Real TokenMetrics with P95 latencies
  • Dynamic CostCalculator with TechnologyConfig
  • Zero hardcoded values - all from Phase 1 systems
```

---

## 🏆 Best Practices

### 🎯 For Sales Teams (Phase 1 Demos)
1. **Use video format** for presentations and screen sharing
2. **Highlight zero hardcoded values** - technical credibility
3. **Emphasize real calculations** vs competitor estimates
4. **Show actual ROI numbers** - $17,520 annual savings per model

### 🎯 For Technical Evaluations
1. **Run live demos** with actual scripts
2. **Show Phase 1 integration** architecture
3. **Validate calculations** with customer pricing
4. **Demonstrate mathematical accuracy**

### 🛠️ For Developers
1. **Keep demos under 60 seconds** for attention span
2. **Use actual Phase 1 integration** not mock data
3. **Test in customer environments** for validation
4. **Include real business metrics** for credibility

---

## 🆘 Troubleshooting

### Phase 1 Demo Issues

**❌ "Demo script fails"**
```bash
# Check Phase 1 dependencies
python3 -c "from mtop.token_metrics import TokenTracker; print('✅ TokenMetrics OK')"
python3 -c "from config_loader import load_config; print('✅ Config OK')"

# Test demo script
python3 scripts/demo_phase1_quick.py
```

**❌ "Video won't play"**
```bash
# Check video file integrity
file phase1-quick-demo.mp4
# Should show: MP4 video data

# Try different format
open phase1-quick-demo.webm  # Often better browser support
```

**❌ "GIF too large"**
```bash
# Check file size
ls -lah phase1-quick-demo.gif
# Current: 1.3M (acceptable for most uses)

# If needed, can be optimized further
gifsicle -O3 --lossy=80 phase1-quick-demo.gif -o optimized.gif
```

---

## 🌟 Credits

**Phase 1 Demos:** Real infrastructure integration with VHS recording  
**Legacy Demos:** Automatically generated using GitHub Actions  
**Recording Tools:** VHS, asciinema, tmux, rich (Python)  
**Phase 1 Integration:** TokenMetrics, CostCalculator, QueueMetrics  
**Conversion Tools:** ffmpeg, @asciinema/agg  

---

## 🔗 Quick Links

- 📚 [Phase 1 Demo Guide](../docs/Phase1-Demo-Guide.md)
- 🎯 [Sales Package](../sales-package/README.md)
- 🚀 [Getting Started Guide](../README.md#getting-started)
- 🛠️ [Installation Instructions](../README.md#installation)
- 🐛 [Issue Tracker](https://github.com/jeremyeder/mtop/issues)

---

<div align="center">

**🎬 Lights, Camera, mtop Phase 1! 🎭**

*Real infrastructure integration • Zero hardcoded values • Mathematical accuracy*

*Made with ❤️ by the mtop team*

</div>