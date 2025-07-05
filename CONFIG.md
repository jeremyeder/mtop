# Configuration Schema Documentation

This document describes the complete configuration schema for mtop, including all configuration sections and their properties.

## Overview

mtop uses a unified YAML configuration file (`config.yaml`) for both build-time and runtime settings. The configuration supports environment variable overrides for all values using the `MTOP_*` prefix convention.

## Configuration Sections

### Build Configuration

Controls program identity and branding.

```yaml
build:
  program:
    name: "mtop"                              # Main program name
    monitor_name: "mtop"                      # Monitor command name
    description: "Model Top - Real-time ML monitoring"
    class_prefix: "MTop"                      # Generates MTopMain, MTopMonitor
    
  branding:
    emoji: "📊"
    tagline: "Real-time LLM inference monitoring"
    github_repo: "jeremyeder/mtop"
```

**Environment Variables:**
- `MTOP_MODE` - Override build mode

### Display Configuration

Controls runtime display behavior and column definitions.

```yaml
display:
  columns:
    - name: "Model"                           # Display name
      field: "name"                           # ModelMetrics attribute
      width: 28                               # Column width
      justify: "left"                         # left|center|right
      format: "string"                        # string|int|float|percent|bytes|duration
      truncate: 25                           # Truncate at N chars with "..."
      sortable: true                         # Enable sorting
      sort_key: "name"                       # Sort key identifier
      enabled: true                          # Show/hide column
      color_thresholds:                      # Color coding rules
        - max: 50
          color: "green"
        - max: 80
          color: "yellow" 
        - min: 80
          color: "red"

  sorting:
    default_key: "qps"                       # Default sort key
    available_keys: ["qps", "gpu", "errors", "name"]
    
  summary:
    show_runtime: true                       # Show execution time
    show_sort_key: true                      # Show current sort
    show_mode: true                          # Show mock/live mode
    show_namespace: true                     # Show K8s namespace
```

**Environment Variables:**
- `MTOP_COLOR_ENABLED` - Enable/disable colors
- `MTOP_MAX_WIDTH` - Maximum display width
- `MTOP_SORT_KEY` - Default sort key

### Technology Configuration

Defines GPU types and infrastructure capabilities.

```yaml
technology:
  gpu_types:
    nvidia-a100:
      memory_gb: 80                          # GPU memory in GB
      hourly_cost: 3.00                      # Cost per hour in USD
    nvidia-h100:
      memory_gb: 80
      hourly_cost: 5.00
```

**Data Types:**
- `GPUType`: Represents a GPU configuration
  - `name: str` - GPU type identifier
  - `memory_gb: int` - Memory in gigabytes (must be > 0)
  - `hourly_cost: float` - Cost per hour (must be >= 0)

**Environment Variables:**
- `MTOP_TECHNOLOGY_GPU_A100_MEMORY` - Override A100 memory
- `MTOP_TECHNOLOGY_GPU_A100_COST` - Override A100 cost
- `MTOP_TECHNOLOGY_GPU_H100_MEMORY` - Override H100 memory
- `MTOP_TECHNOLOGY_GPU_H100_COST` - Override H100 cost

**Validation:**
- Memory must be positive (> 0)
- Cost must be non-negative (>= 0)

### SLO Configuration

Service Level Objectives for performance and reliability targets.

```yaml
slo:
  ttft_p95_ms: 500                          # Time to first token, 95th percentile (ms)
  error_rate_percent: 0.1                   # Target error rate (%)
  tokens_per_second: 1000                   # Target throughput (tokens/sec)
```

**Data Types:**
- `SLOConfig`: Service level objective definition
  - `ttft_p95_ms: int` - Time to first token latency (must be > 0)
  - `error_rate_percent: float` - Error rate percentage (0-100)
  - `tokens_per_second: int` - Throughput target (must be > 0)

**Environment Variables:**
- `MTOP_SLO_TTFT_P95_MS` - Override TTFT latency target
- `MTOP_SLO_ERROR_RATE_PERCENT` - Override error rate target
- `MTOP_SLO_TOKENS_PER_SECOND` - Override throughput target

**Validation:**
- TTFT latency must be positive (> 0)
- Error rate must be between 0-100%
- Tokens per second must be positive (> 0)

### Workload Configuration

Load testing and simulation parameters.

```yaml
workload:
  baseline_qps: 100                         # Baseline queries per second
  spike_multiplier: 2.0                     # Spike testing multiplier (2x = 200 QPS)
```

**Data Types:**
- `WorkloadConfig`: Workload simulation parameters
  - `baseline_qps: int` - Base load in queries per second (must be > 0)
  - `spike_multiplier: float` - Spike test multiplier (must be >= 1.0)

**Environment Variables:**
- `MTOP_WORKLOAD_BASELINE_QPS` - Override baseline QPS
- `MTOP_WORKLOAD_SPIKE_MULTIPLIER` - Override spike multiplier

**Validation:**
- Baseline QPS must be positive (> 0)
- Spike multiplier must be >= 1.0 (no reduction in load)

## Complete Configuration Example

```yaml
# Build-time Configuration (Program Identity)
build:
  program:
    name: "mtop"
    monitor_name: "mtop"
    description: "Model Top - Real-time ML monitoring"
    class_prefix: "MTop"
  branding:
    emoji: "📊"
    tagline: "Real-time LLM inference monitoring"
    github_repo: "jeremyeder/mtop"

# Runtime Configuration (Display & Behavior)
display:
  columns:
    - name: "Model"
      field: "name"
      width: 28
      justify: "left"
      truncate: 25
    - name: "Status" 
      field: "status"
      width: 12
      justify: "center"
    - name: "QPS"
      field: "current_qps" 
      width: 8
      justify: "right"
      format: "int"
      sortable: true
      sort_key: "qps"
    - name: "GPU %util"
      field: "cpu_percent"
      width: 9 
      justify: "center"
      format: "percent"
      color_thresholds:
        - max: 50
          color: "green"
        - max: 80
          color: "yellow" 
        - min: 80
          color: "red"
      sortable: true
      sort_key: "gpu"
    - name: "Errors"
      field: "error_rate"
      width: 7
      justify: "center"
      format: "percent"
      color_thresholds:
        - max: 1.0
          color: "green"
        - max: 3.0
          color: "yellow"
        - min: 3.0
          color: "red"
      sortable: true
      sort_key: "errors"
    - name: "Latency"
      field: "latency_p95"
      width: 8
      justify: "center"
      format: "duration"
    - name: "Replicas"
      field: "replicas"
      width: 8
      justify: "center"
      format: "int"
  sorting:
    default_key: "qps"
    available_keys: ["qps", "gpu", "errors", "name"]
  summary:
    show_runtime: true
    show_sort_key: true
    show_mode: true
    show_namespace: true

# Technology Configuration (GPU & Infrastructure)
technology:
  gpu_types:
    nvidia-a100:
      memory_gb: 80
      hourly_cost: 3.00
    nvidia-h100:
      memory_gb: 80
      hourly_cost: 5.00

# SLO Definitions (Service Level Objectives)
slo:
  ttft_p95_ms: 500
  error_rate_percent: 0.1
  tokens_per_second: 1000

# Workload Configuration (Load Testing & Simulation)
workload:
  baseline_qps: 100
  spike_multiplier: 2.0
```

## Environment Variable Override System

All configuration values can be overridden using environment variables with the `MTOP_` prefix. The system automatically:

1. **Type Conversion**: Converts string values to appropriate types (int, float, bool)
2. **Section Creation**: Creates missing configuration sections if needed
3. **Nested Access**: Supports deep path access using underscore notation

### Examples

```bash
# Override SLO targets
export MTOP_SLO_TTFT_P95_MS=300
export MTOP_SLO_ERROR_RATE_PERCENT=0.05

# Override workload parameters  
export MTOP_WORKLOAD_BASELINE_QPS=500
export MTOP_WORKLOAD_SPIKE_MULTIPLIER=3.0

# Override GPU configurations
export MTOP_TECHNOLOGY_GPU_A100_COST=2.50
export MTOP_TECHNOLOGY_GPU_H100_MEMORY=96
```

## Configuration Loading

The configuration system:

1. **Loads** YAML file (default: `config.yaml`)
2. **Applies** environment variable overrides
3. **Validates** all values and data types
4. **Caches** parsed configuration for performance
5. **Provides** type-safe access through dataclasses

## Error Handling

The configuration system provides comprehensive validation:

- **Type Checking**: Ensures values match expected types
- **Range Validation**: Validates numeric ranges and constraints  
- **Required Fields**: Checks for mandatory configuration sections
- **Graceful Fallbacks**: Uses defaults for optional sections
- **Clear Error Messages**: Provides specific validation failure details

## Optional Sections

The following sections are optional and default to `None` if not provided:

- `technology` - GPU and infrastructure configuration
- `slo` - Service level objectives
- `workload` - Load testing parameters

Required sections:
- `build` - Program identity and branding
- `display` - Display configuration and columns