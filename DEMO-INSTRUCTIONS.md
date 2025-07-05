# 🎮 mtop Interactive Demo Instructions
## Professional LLM Infrastructure Monitoring

*Step-by-step guide for conducting live demonstrations*

---

## 🎯 Before You Begin

### System Requirements
- Unix-based system (Linux, macOS)
- Python 3.11+ installed
- 4GB RAM, 2 CPU cores minimum
- 500MB free disk space
- Internet connection for dependencies

### Pre-Demo Checklist
- [ ] Clone repository: `git clone https://github.com/jeremyeder/mtop.git`
- [ ] Change directory: `cd mtop`
- [ ] Run setup: `./demo-launcher.sh`
- [ ] Verify status: `./demo-status.sh`
- [ ] Have sales guide ready: `SALES-DEMO-GUIDE.md`

---

## 🚀 Demo Execution Guide

### Phase 1: Environment Setup (1 minute)

#### Step 1: Launch Demo Environment
```bash
./demo-launcher.sh
```

**What You'll See:**
```
╔══════════════════════════════════════════════════════════════╗
║                   🚀 mtop Demo Launcher                      ║
║               Sales-Ready LLM Monitoring Demo               ║
╚══════════════════════════════════════════════════════════════╝

🔍 Sales Demo Kit - Zero Technical Knowledge Required
Setting up complete LLM monitoring demo environment...

[1/6] Checking system requirements... 100%
✅ System requirements met (Python 3.13.5)

[2/6] Setting up Python environment... 100% 
✅ Environment setup complete

[3/6] Validating demo data... 100%
✅ Demo data validated (30 CRs available)

[4/6] Pre-loading scenarios... 100%
✅ Demo scenarios pre-loaded

[5/6] Running health checks... 100%
✅ All health checks passed

[6/6] Demo environment ready... 100%
⏱️  Setup completed in 12 seconds

✅ Demo Ready!
```

**Talking Points During Setup:**
- "This is our zero-configuration setup - no manual configuration required"
- "The system automatically validates all dependencies and mock data"
- "In production, this same simplicity applies to real Kubernetes clusters"

---

### Phase 2: Cost Optimization Demo (2-3 minutes)

#### Step 2: Show Model-Specific Cost Analysis
```bash
./mtop get llama-3-70b-instruct
```

**What You'll See:**
```
📊 LLMInferenceService: llama-3-70b-instruct
════════════════════════════════════════════════

🎯 Model Configuration
   Name: llama-3-70b-instruct
   Model Size: 70B parameters
   GPU Type: nvidia-h100
   Memory: 80GB allocated

💰 Cost Analysis
   GPU Cost: $4.10/hour
   Utilization: 62%
   Cost per 1M tokens: $2.45
   Monthly cost: $2,952

⚡ Performance Metrics
   TTFT P95: 185ms (target: <500ms) ✅
   Throughput: 1,800 tokens/second
   Queue depth: 2 requests
   SLO compliance: 99.8% ✅

🔧 Optimization Recommendations
   💡 Rightsizing: Move to nvidia-a100 for 40% cost savings
   💡 Potential savings: $1,181/month per model
   💡 Annual ROI: $14,172 per model
```

**Key Talking Points:**
1. **GPU Utilization:** "Notice the 62% utilization - this represents significant waste"
2. **Cost Impact:** "At $4.10/hour, underutilization costs $1,000+ monthly per model"
3. **Optimization:** "Our AI recommends A100 GPU for 40% savings with same performance"
4. **Scale Impact:** "For enterprise portfolios, this saves hundreds of thousands annually"

#### Step 3: Compare Multiple Models
```bash
./mtop list
```

**What You'll See:**
```
📋 LLM Infrastructure Overview
════════════════════════════════════════════════

NAME                     GPU TYPE        COST/HR    UTILIZATION    STATUS
llama-3-70b-instruct    nvidia-h100     $4.10      62%           🟢 Healthy
gpt-4-turbo             nvidia-h100     $4.10      58%           🟢 Healthy  
claude-3-haiku          nvidia-a100     $3.20      89%           🟢 Healthy
mixtral-8x7b-instruct   nvidia-a100     $3.20      76%           🟢 Healthy
granite-3-8b-instruct   nvidia-v100     $2.10      45%           🟢 Healthy

💰 Cost Summary
   Total GPU cost: $15.70/hour
   Optimization potential: $6.28/hour (40% savings)
   Monthly waste: $4,522
   Annual opportunity: $54,264
```

**Key Talking Points:**
1. **Portfolio View:** "Single dashboard shows entire LLM infrastructure"
2. **Cost Visibility:** "Real-time cost tracking across all models and GPU types"
3. **Optimization Opportunity:** "$54K annual savings through rightsizing alone"
4. **Operational Efficiency:** "No more spreadsheets or manual cost tracking"

---

### Phase 3: Performance & Reliability Demo (2-3 minutes)

#### Step 4: Real-Time Monitoring
```bash
./mtop
```

**What You'll See:**
```
🔴 mtop - LLM Infrastructure Monitor (Press 'q' to quit)
════════════════════════════════════════════════════════════════

📊 Token Generation Metrics                     🕐 Last Update: 14:23:45

MODEL                    TPS     TTFT(ms)  QUEUE   GPU%    COST/HR
llama-3-70b-instruct    1,847    182      3       64%     $4.10
gpt-4-turbo             2,156    165      1       61%     $4.10
claude-3-haiku          3,204    98       0       87%     $3.20
mixtral-8x7b-instruct   1,923    201      2       78%     $3.20
granite-3-8b-instruct   4,107    76       1       47%     $2.10

🎯 SLO Compliance
   TTFT Target: <500ms          ✅ All models compliant
   Throughput Target: >1000 TPS ✅ All models meeting target
   Queue Depth: <5 requests     ✅ All queues healthy
   Uptime: 99.97%               ✅ Exceeding 99.9% target

💡 Live Recommendations
   • Move llama-3-70b to A100 for $1,181/month savings
   • Increase granite-3-8b capacity - queue growing
   • Consider model serving optimization for gpt-4-turbo
```

**Key Talking Points:**
1. **Real-Time Visibility:** "Live monitoring of token generation across all models"
2. **SLO Tracking:** "Automatic compliance monitoring - see all green checkmarks"
3. **Proactive Recommendations:** "System identifies optimization opportunities in real-time"
4. **Operational Excellence:** "Like htop for AI infrastructure - essential for operations teams"

*Press 'q' to exit monitoring view*

#### Step 5: Rollout Simulation
```bash
./mtop simulate canary
```

**What You'll See:**
```
🎯 Simulating canary deployment for model update...
════════════════════════════════════════════════

📈 Deployment Progress
   Strategy: Canary (10% → 50% → 100%)
   
   Step 1: 10% traffic → new version
   ⚡ TTFT: 178ms (baseline: 182ms) ✅ 2.2% improvement
   📊 Throughput: 1,901 TPS ✅ Within tolerance
   🎯 Error rate: 0.05% ✅ Under 0.1% threshold
   
   Step 2: 50% traffic → new version  
   ⚡ TTFT: 176ms ✅ Consistent improvement
   📊 Throughput: 1,934 TPS ✅ Performance stable
   🎯 Error rate: 0.03% ✅ Actually improving
   
   Step 3: 100% traffic → new version
   ✅ Deployment successful
   📊 Final metrics: 1,956 TPS, 176ms TTFT
   💰 Performance improvement: 3.8%

🏆 Deployment completed safely with zero downtime
```

**Key Talking Points:**
1. **Zero-Downtime Deployments:** "Safe model updates without service interruption"
2. **Automated Validation:** "System validates performance at each step"
3. **Risk Mitigation:** "Automatic rollback if any SLO violations detected"
4. **Production Ready:** "Same deployment patterns used in enterprise environments"

---

### Phase 4: Advanced Features Demo (2-3 minutes)

#### Step 6: Visual Monitoring Dashboard
```bash
python3 watch_rollout.py --topology rolling --autoplay --delay 2
```

**What You'll See:**
```
🎬 Rolling Deployment Visualization
════════════════════════════════════════════════

🔄 Step 1/3: Initial State
   Replica 1: ████████████ v1.0 (TTFT: 182ms)
   Replica 2: ████████████ v1.0 (TTFT: 185ms)  
   Replica 3: ████████████ v1.0 (TTFT: 180ms)
   
🔄 Step 2/3: Rolling Update
   Replica 1: ████████████ v2.0 (TTFT: 176ms) ✅
   Replica 2: ████████████ v1.0 (TTFT: 185ms)
   Replica 3: ████████████ v1.0 (TTFT: 180ms)
   
🔄 Step 3/3: Deployment Complete  
   Replica 1: ████████████ v2.0 (TTFT: 176ms) ✅
   Replica 2: ████████████ v2.0 (TTFT: 174ms) ✅
   Replica 3: ████████████ v2.0 (TTFT: 178ms) ✅

🏆 Rolling deployment completed successfully
   Performance improvement: 4.1%
   Zero downtime achieved
   All SLOs maintained
```

**Key Talking Points:**
1. **Visual Operations:** "Clear visualization of deployment progress"
2. **Performance Tracking:** "Real-time validation during updates"
3. **Safety First:** "Rolling updates ensure continuous service availability"
4. **Enterprise Ready:** "Production-grade deployment orchestration"

#### Step 7: Health Status Check
```bash
./demo-status.sh
```

**What You'll See:**
```
╔══════════════════════════════════════════════════════════════╗
║                  📊 mtop Demo Status                        ║
║              Real-time Health Monitoring                    ║
╚══════════════════════════════════════════════════════════════╝

🔍 Checking demo environment health...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Component            Status     Details
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
System               ●          Python 3.13.5 ✅ | Space: 2,048MB ✅
Virtual Env          ●          Virtual env active ✅ | Dependencies installed ✅
Mock Data            ●          CRs: 30 ✅ | Mock data complete ✅
CLI                  ●          CLI working ✅ | Commands working ✅
Token Metrics        ●          Token metrics ✅ | Queue metrics ✅
Processes            ●          No demo processes ℹ️
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Demo environment is HEALTHY
💡 Ready for demos! Try: ./demo.sh
```

**Key Talking Points:**
1. **System Health:** "Comprehensive health monitoring for all components"
2. **Operational Readiness:** "Everything green means ready for production"
3. **Proactive Monitoring:** "Catch issues before they impact users"
4. **DevOps Integration:** "JSON output available for automation and alerting"

---

## 🎯 Advanced Demo Scenarios

### Interactive Guided Demo
```bash
./demo.sh
```
- Full guided experience with step-by-step instructions
- Interactive prompts for sales presentation pacing
- Comprehensive tour of all mtop capabilities

### Automated Demo (For Presentations)
```bash
./demo.sh --headless
```
- Fully automated demo with realistic timing
- Perfect for screen sharing or recorded presentations
- No user interaction required

### Continuous Monitoring Demo
```bash
./demo-status.sh --watch
```
- Real-time health monitoring dashboard
- Updates every 5 seconds
- Professional operations center feel

---

## 🛠️ Troubleshooting

### Common Issues & Solutions

#### "Command not found" errors
```bash
# Ensure scripts are executable
chmod +x demo-launcher.sh demo-cleanup.sh demo-status.sh

# Check current directory
pwd  # Should be in mtop repository root
```

#### "Permission denied" on virtual environment
```bash
# Clean restart
./demo-cleanup.sh --force
./demo-launcher.sh
```

#### Slow performance during demo
```bash
# Use headless mode for better performance
./demo.sh --headless

# Check system resources
./demo-status.sh --detailed
```

#### Demo environment corruption
```bash
# Complete reset
./demo-cleanup.sh --force
rm -rf venv/  # Nuclear option
./demo-launcher.sh
```

---

## 📋 Demo Timing Guide

### 5-Minute Lightning Demo
1. Quick setup (30s): `./demo-launcher.sh`
2. Cost analysis (2m): `./mtop get llama-3-70b-instruct`
3. Live monitoring (2m): `./mtop`
4. Cleanup (30s): `./demo-cleanup.sh`

### 10-Minute Standard Demo
1. Setup (1m): `./demo-launcher.sh`
2. Cost optimization (3m): Multiple models analysis
3. Performance monitoring (3m): Real-time dashboard + simulation
4. Advanced features (2m): Visual monitoring
5. Q&A + cleanup (1m)

### 15-Minute Deep Dive
- Include all scenarios from sales guide
- Add customer-specific use cases
- Technical Q&A session
- Implementation discussion

---

## 🏆 Success Metrics

### Technical Success Indicators
- All commands execute without errors
- Performance metrics display correctly
- Cost calculations are accurate
- Monitoring dashboards function properly

### Sales Success Indicators
- Customer asks follow-up technical questions
- Request for trial license or POC
- Discussion of implementation timeline
- Introduction to additional stakeholders

---

## 📞 Post-Demo Actions

### Immediate Follow-Up
1. **Share resources:** Send technical documentation and ROI calculator
2. **Schedule follow-up:** Technical deep-dive with customer's engineering team
3. **Provide trial access:** 30-day evaluation license
4. **Connect with services:** Introduction to Professional Services team

### Documentation to Share
- Complete technical architecture guide
- Customer reference stories and case studies
- Implementation timeline and project plan template
- Support and training program overview

---

*Demo guide last updated: 2025-07-05*  
*Compatible with mtop version: 1.0*