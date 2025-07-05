# Project Overview: kubectl-ld

## Purpose
kubectl-ld is a **mock CLI tool** for debugging and simulating `LLMInferenceService` CRDs (Custom Resource Definitions) in a Kubernetes-like environment **without requiring a live cluster**. It's designed for SREs, ML engineers, and platform teams to:

- Simulate rollouts and test failure modes offline
- Inspect the status of LLM-serving infrastructure
- Provide real-time monitoring (kubectl-ldtop) like htop for LLMs
- Support both mock mode (local files) and live mode (actual kubectl)

## Key Features
- **Offline simulation** of up to 100 LLMInferenceService CRs
- **Full CRUD support** on mocked CRs
- **Realistic rollout playback** with multiple topology types (canary, blue-green, rolling, shadow)
- **Real-time monitoring** via kubectl-ldtop with QPS, CPU, error metrics
- **Dual-mode operation**: mock (local files) vs live (actual Kubernetes cluster)
- **Configurable display** via YAML configuration files

## Architecture
- **Main CLI**: `kubectl-ld` script with Python 3.11+ requirement
- **Package structure**: `kubectl_ld/` module for proper Python packaging
- **Mock data**: `mocks/` directory with CRs, configs, logs, and rollout topologies
- **Configuration system**: YAML-based config with environment variable overrides
- **Column engine**: Flexible table rendering with Rich library integration
- **Testing**: Comprehensive test suite with 53 tests including integration tests