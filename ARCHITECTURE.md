# mtop Architecture Guide

## Overview

mtop has been upgraded with a modern, extensible architecture that provides better performance, maintainability, and testing capabilities. This document outlines the key architectural components and design decisions.

## Key Improvements

### 1. Type Safety and Interface Contracts

**Problem Solved**: Runtime errors due to unclear contracts between components

**Implementation**:
- Comprehensive Protocol definitions in `mtop/interfaces.py`
- Strict mypy configuration with full type checking enabled
- Abstract base classes for extensibility

**Key Interfaces**:
- `Formatter` - Column formatting with sort key support
- `Renderer` - Table rendering abstraction  
- `Monitor` - Real-time monitoring protocols
- `FileSystem` - File operations abstraction
- `KubernetesClient` - Kubernetes API operations
- `ConfigProvider` - Configuration management
- `Logger` - Structured logging interface

### 2. Dependency Injection Architecture

**Problem Solved**: Hard-coded dependencies making testing and extension difficult

**Implementation**:
- Lightweight DI container in `mtop/container.py`
- Automatic dependency resolution via type annotations
- Support for singletons, transients, and factory patterns

**Usage Example**:
```python
from mtop.container import inject, singleton
from mtop.interfaces import Logger

@singleton(Logger)
class MyLogger:
    def info(self, message: str) -> None:
        print(message)

# Automatic injection
def my_function(logger: Logger = inject(Logger)) -> None:
    logger.info("Hello, World!")
```

### 3. Async/Concurrency Support

**Problem Solved**: Blocking operations in live mode, poor performance with multiple resources

**Implementation**:
- Async CLI operations in `mtop/async_cli.py`
- Concurrent resource fetching and operations
- Non-blocking monitoring with configurable intervals

**Key Features**:
- `AsyncMTop` - Async version of all CLI operations
- `AsyncResourceMonitor` - Real-time resource monitoring
- Batch operations with concurrent execution
- Proper error handling and cancellation support

### 4. Comprehensive Logging Infrastructure

**Problem Solved**: Poor observability and debugging capabilities

**Implementation**:
- Structured logging with JSON output in `mtop/logging.py`
- Context-aware logging with operation tracking
- Configurable log levels and output formats
- Rotating file handlers with size limits

**Features**:
- Environment variable configuration
- Operation timing and context tracking
- Structured JSON logs for analysis
- Debug/trace modes for development

### 5. Performance and Memory Optimization

**Problem Solved**: Poor performance with large datasets, memory leaks in long-running processes

**Implementation**:
- Intelligent caching system in `mtop/cache.py`
- LRU cache with TTL support
- Async cache for concurrent operations
- Memory-efficient data structures

**Key Components**:
- `LRUCache` - Thread-safe LRU cache with TTL
- `AsyncCache` - Async-aware cache with deduplication
- `CacheManager` - Global cache coordination
- `StreamingJSONParser` - Memory-efficient JSON parsing

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                       mtop CLI                             │
├─────────────────────────────────────────────────────────────┤
│                 Dependency Injection                       │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│  │   Logger    │ │ FileSystem   │ │  KubernetesClient    │ │
│  └─────────────┘ └──────────────┘ └──────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Core Services                           │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│  │   Async     │ │    Cache     │ │     Monitoring       │ │
│  │   CLI       │ │   Manager    │ │     Service          │ │
│  └─────────────┘ └──────────────┘ └──────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                 Data Layer                                 │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│  │   Mock      │ │    Live      │ │     Configuration    │ │
│  │   Data      │ │  Kubernetes  │ │     System           │ │
│  └─────────────┘ └──────────────┘ └──────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Configuration Architecture

### Unified Configuration System

mtop uses a comprehensive YAML-based configuration system with full environment variable override support. The configuration includes:

- **Build Configuration**: Program identity and branding
- **Display Configuration**: Runtime display and column definitions  
- **Technology Configuration**: GPU types and infrastructure capabilities
- **SLO Configuration**: Service Level Objectives for performance targets
- **Workload Configuration**: Load testing and simulation parameters

### Configuration Schema

```yaml
build:                           # Program identity (required)
  program: { name, monitor_name, description, class_prefix }
  branding: { emoji, tagline, github_repo }

display:                         # Display behavior (required)
  columns: [ { name, field, width, format, ... } ]
  sorting: { default_key, available_keys }
  summary: { show_runtime, show_sort_key, ... }

technology:                      # Infrastructure (optional)
  gpu_types:
    nvidia-a100: { memory_gb: 80, hourly_cost: 3.00 }
    nvidia-h100: { memory_gb: 80, hourly_cost: 5.00 }

slo:                            # Performance targets (optional)
  ttft_p95_ms: 500              # Time to first token (ms)
  error_rate_percent: 0.1       # Error rate (%)
  tokens_per_second: 1000       # Throughput (tokens/sec)

workload:                       # Load testing (optional)
  baseline_qps: 100             # Baseline queries per second
  spike_multiplier: 2.0         # Spike test multiplier
```

### Type-Safe Configuration

The system uses dataclasses for type safety and validation:

```python
@dataclass
class SLOConfig:
    ttft_p95_ms: int
    error_rate_percent: float  
    tokens_per_second: int
    
    def __post_init__(self):
        # Comprehensive validation
        if self.ttft_p95_ms <= 0:
            raise ValueError("TTFT latency must be positive")
        if not 0 <= self.error_rate_percent <= 100:
            raise ValueError("Error rate must be 0-100%")
```

### Environment Variable Overrides

All configuration values support environment variable overrides using the `MTOP_*` prefix:

```bash
# SLO Configuration
export MTOP_SLO_TTFT_P95_MS=300
export MTOP_SLO_ERROR_RATE_PERCENT=0.05
export MTOP_SLO_TOKENS_PER_SECOND=1500

# Workload Configuration  
export MTOP_WORKLOAD_BASELINE_QPS=500
export MTOP_WORKLOAD_SPIKE_MULTIPLIER=3.0

# Technology Configuration
export MTOP_TECHNOLOGY_GPU_A100_COST=2.50
export MTOP_TECHNOLOGY_GPU_H100_MEMORY=96

# Display Configuration
export MTOP_COLOR_ENABLED=true
export MTOP_MAX_WIDTH=120
export MTOP_SORT_KEY=gpu

# Mode Configuration
export LLD_MODE=live  # or 'mock'
```

### Configuration Loading Process

1. **Load YAML**: Parse `config.yaml` (or specified path)
2. **Apply Overrides**: Process environment variables with type conversion
3. **Validate**: Run comprehensive validation on all sections
4. **Cache**: Store parsed configuration for performance
5. **Provide Access**: Type-safe access through dataclasses

### Configuration File Hierarchy

1. Environment variables (highest priority)
2. Specified config path via CLI argument
3. Default config: `./config.yaml`
4. Fallback to embedded defaults for optional sections

## Testing Strategy

### Unit Tests
- Interface implementations tested in isolation
- Dependency injection container functionality
- Cache performance and correctness
- Async operation behavior

### Integration Tests
- End-to-end CLI workflows
- Mock vs live mode switching
- Configuration loading and validation
- Resource monitoring accuracy

### Performance Tests
- Cache hit/miss ratios
- Concurrent operation throughput
- Memory usage with large datasets
- Async operation latency

## Migration Guide

### For Developers

**Old Pattern**:
```python
# Hard-coded dependencies
kubectl_ld = KubectlLD(mode="live")
kubectl_ld.list_crs()
```

**New Pattern**:
```python
# Dependency injection
from mtop.async_cli import AsyncMTop
from mtop.container import inject

async def main():
    mtop = AsyncMTop(mode="live")
    crs = await mtop.list_crs()
```

### For Operators

The CLI interface remains unchanged, but new features are available:

```bash
# Enhanced logging
LDCTL_LOG_LEVEL=DEBUG mtop list

# Performance monitoring
LDCTL_LOG_FORMAT=structured mtop

# Custom configuration
LDCTL_CONFIG_PATH=/etc/my-config.yaml mtop simulate canary
```

## Future Extensibility

The new architecture provides clean extension points:

1. **Formatters**: Add new column types via the `Formatter` protocol
2. **Renderers**: Support new output formats via the `Renderer` protocol  
3. **Monitors**: Create custom monitoring implementations
4. **Clients**: Support additional Kubernetes distributions
5. **Caches**: Implement specialized caching strategies

## Performance Characteristics

### Before Architecture Update
- Synchronous operations blocking UI
- No caching of configuration or resources
- Memory growth in long-running mtop sessions
- Poor error handling and debugging

### After Architecture Update
- Concurrent operations with async/await
- Intelligent caching with TTL and LRU eviction
- Memory-efficient data structures and streaming
- Comprehensive logging and error context

## Dependencies

### Core Runtime
- No additional dependencies for basic functionality
- Optional performance dependencies available

### Development
- `pytest-asyncio` for async test support
- `ijson` for streaming JSON parsing (optional)
- Enhanced mypy configuration for strict typing

This architecture provides a solid foundation for mtop's continued evolution while maintaining backward compatibility and improving developer experience.