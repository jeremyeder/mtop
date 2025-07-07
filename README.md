# mtop

Real-time monitoring for LLM inference infrastructure. Like `htop` for AI workloads.

![mtop-demo](recordings/sales/multi-model.gif)

**Cut GPU costs by 40%. Ensure 99.9% uptime. Zero cluster required.**

## Quick Start

```bash
./mtop-main                      # Monitor LLM services in real-time
./mtop-main slo-dashboard        # Track SLO compliance & convergence
./mtop-main simulate canary      # Test deployments without risk
```

## Why mtop?

- **💰 Cost Optimization**: Identify underutilized GPUs and rightsize deployments
- **🎯 SLO Monitoring**: Track TTFT, latency, and throughput in real-time
- **🔥 GPU Efficiency**: Monitor utilization across H100, A100, and DRA clusters
- **📊 Executive Dashboards**: Business-ready metrics and ROI calculations

## Key Features

### Cost Optimization
![cost-optimization](recordings/sales/cost-optimization.gif)

Automatically identify GPU waste and recommend optimal configurations. Save 40% on infrastructure costs.

### SLO Compliance Monitoring
![slo-compliance](recordings/sales/slo-compliance.gif)

Real-time tracking of Time-to-First-Token (TTFT) and request latency with automated convergence optimization.

### GPU Efficiency Tracking
![gpu-efficiency](recordings/sales/gpu-efficiency.gif)

Monitor GPU utilization across your entire fleet with heartbeat visualization and capacity planning.

### Multi-Model Management
![multi-model](recordings/sales/multi-model.gif)

Manage dozens of LLM deployments from a single interface with real-time metrics and health status.

## Installation

```bash
# 1. Requirements: Python 3.12+
python3 --version

# 2. Install
pip install -r requirements.txt
chmod +x mtop-main

# 3. Verify
./mtop-main help
```

## Usage Examples

```bash
# Monitor all LLM services
./mtop-main

# Check specific model
./mtop-main get gpt-4-turbo

# View deployment logs
./mtop-main logs llama-3-70b-instruct

# Run cost optimization analysis
./mtop-main slo-dashboard --focus cost

# Simulate deployment strategies
./mtop-main simulate canary --model gpt-4-turbo
./mtop-main simulate bluegreen --model llama-3-70b
```

## Architecture

mtop operates in two modes:

- **Mock Mode** (default): Use local simulation data for demos and testing
- **Live Mode**: Connect to real Kubernetes clusters with LLMInferenceService CRDs

```bash
# Switch modes
export LLD_MODE=live    # Use live cluster
export LLD_MODE=mock    # Use mock data (default)
```

## Demo Framework

Pre-configured scenarios for different use cases:

```bash
./scripts/demo.py startup           # Small startup scenario
./scripts/demo.py enterprise        # Large enterprise deployment
./scripts/demo.py cost-optimization # Cost reduction demo
```

## Documentation

- 📚 [Full Documentation](docs/README.md)
- 🎬 [Demo Guide](DEMO-GUIDE.md)
- 💼 [Sales Demo Guide](SALES-DEMO-GUIDE.md)
- 🏗️ [Architecture](ARCHITECTURE.md)

## Contributing

We welcome contributions! See [COLLABORATION.md](COLLABORATION.md) for our development workflow.

### Development

```bash
# Setup development environment
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]

# Run tests
pytest tests/ -v

# Run linters (required before pushing)
./scripts/lint.sh
```

## License

MIT - See [LICENSE](LICENSE) for details.

---

Built with ❤️ by the Red Hat AI Engineering team. Part of the [llm-d](https://llm-d.ai) project.