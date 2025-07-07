# Examples Documentation

## 💡 Working Examples & Use Cases

This directory contains practical examples, use cases, and demonstration scenarios for the mtop LLM monitoring system.

## 📋 Contents

### Demo Scenarios
- **[Cost Optimization](demos/cost-optimization/)** - 40% GPU cost reduction demonstrations
- **[SLO Compliance](demos/slo-compliance/)** - Sub-500ms TTFT performance monitoring
- **[GPU Efficiency](demos/gpu-efficiency/)** - 3x model density through fractioning
- **[Load Handling](demos/load-handling/)** - Auto-scaling for traffic spikes
- **[Multi-Model Management](demos/multi-model/)** - Unified LLM portfolio monitoring

### Real-World Use Cases
- **[Enterprise Deployment](use-cases/enterprise/)** - Large-scale enterprise scenarios
- **[Startup Environment](use-cases/startup/)** - Resource-constrained deployments
- **[Research Lab](use-cases/research/)** - Academic and research configurations
- **[Edge Computing](use-cases/edge/)** - Edge deployment patterns

### Integration Examples
- **[OpenShift AI](integrations/openshift-ai/)** - Integration with Red Hat OpenShift AI
- **[Kubernetes Native](integrations/kubernetes/)** - Pure Kubernetes deployments
- **[Cloud Platforms](integrations/cloud/)** - AWS, GCP, Azure specific examples
- **[Monitoring Systems](integrations/monitoring/)** - Prometheus, Grafana, DataDog

### Configuration Examples
- **[Basic Setup](configs/basic/)** - Simple single-cluster setup
- **[Multi-Cluster](configs/multi-cluster/)** - Cross-cluster monitoring
- **[High Availability](configs/ha/)** - HA configurations
- **[Security Hardened](configs/security/)** - Security-focused setups

## 🎯 Example Standards

### Quality Requirements
- **Working Code** - All examples must run successfully
- **Realistic Scenarios** - Based on actual use cases
- **Well Documented** - Clear explanations and context
- **Maintained** - Regularly updated and tested

### Example Structure
```
example-name/
├── README.md          # Overview and instructions
├── config.yaml        # Configuration files
├── manifests/         # Kubernetes manifests
├── scripts/           # Setup and demo scripts
├── data/              # Sample data if needed
└── docs/              # Additional documentation
```

### Documentation Format
Each example should include:
- **Purpose** - What this example demonstrates
- **Prerequisites** - Required setup and dependencies
- **Instructions** - Step-by-step setup and execution
- **Expected Results** - What you should see
- **Variations** - Common modifications and alternatives

## 🚀 Quick Start Examples

### For Evaluation (5 minutes)
- [Quick Demo](demos/quick-start/) - Fastest way to see mtop in action

### For Development (15 minutes)
- [Development Setup](configs/development/) - Local development environment

### For Production (30 minutes)
- [Production Example](use-cases/production/) - Production-ready deployment

## 📊 Demo Categories

### Business Value Demos
Focus on ROI and business impact:
- Cost optimization and savings
- SLO compliance and reliability
- Operational efficiency gains

### Technical Demos
Showcase technical capabilities:
- Real-time monitoring and alerting
- GPU utilization optimization
- Auto-scaling and load management

### Integration Demos
Show ecosystem integration:
- CI/CD pipeline integration
- Monitoring system integration
- Cloud platform integration

## 🔧 Running Examples

### Prerequisites
- Kubernetes cluster (local or cloud)
- mtop installed and configured
- kubectl configured for cluster access

### General Process
1. Choose appropriate example for your use case
2. Review prerequisites and setup requirements
3. Follow step-by-step instructions
4. Validate expected results
5. Explore variations and customizations

## 🔗 Related Resources
- [Guides](../guides/) - Detailed setup and operation guides
- [Reference](../reference/) - Configuration and API reference
- [Recordings](../artifacts/recordings/) - Video demonstrations

---

*Practical examples for professional LLM monitoring*