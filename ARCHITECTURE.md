# kubectl-ld Architecture Guide

## Overview

kubectl-ld has been upgraded with a modern, extensible architecture that provides better performance, maintainability, and testing capabilities. This document outlines the key architectural components and design decisions.

## Key Improvements

### 1. Type Safety and Interface Contracts

**Problem Solved**: Runtime errors due to unclear contracts between components

**Implementation**:
- Comprehensive Protocol definitions in `kubectl_ld/interfaces.py`
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
- Lightweight DI container in `kubectl_ld/container.py`
- Automatic dependency resolution via type annotations
- Support for singletons, transients, and factory patterns

**Usage Example**:
```python
from kubectl_ld.container import inject, singleton
from kubectl_ld.interfaces import Logger

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
- Async CLI operations in `kubectl_ld/async_cli.py`
- Concurrent resource fetching and operations
- Non-blocking monitoring with configurable intervals

**Key Features**:
- `AsyncKubectlLD` - Async version of all CLI operations
- `AsyncResourceMonitor` - Real-time resource monitoring
- Batch operations with concurrent execution
- Proper error handling and cancellation support

### 4. Comprehensive Logging Infrastructure

**Problem Solved**: Poor observability and debugging capabilities

**Implementation**:
- Structured logging with JSON output in `kubectl_ld/logging.py`
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
- Intelligent caching system in `kubectl_ld/cache.py`
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
│                    kubectl-ld CLI                          │
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

## Configuration

### Environment Variables

The new architecture supports comprehensive configuration via environment variables:

```bash
# Logging Configuration
export LDCTL_LOG_LEVEL=DEBUG
export LDCTL_LOG_FILE=/var/log/kubectl-ld.log
export LDCTL_LOG_FORMAT=structured  # or 'simple'

# Mode Configuration
export LLD_MODE=live  # or 'mock'

# Configuration File Location
export LDCTL_CONFIG_PATH=/path/to/config.yaml

# Performance Tuning
export LDCTL_CACHE_SIZE=256
export LDCTL_ASYNC_TIMEOUT=30
```

### Configuration Override Hierarchy

1. Environment variables (highest priority)
2. Config file specified by `LDCTL_CONFIG_PATH`
3. User config: `~/.ldctl/config.yaml`
4. System config: `/etc/ldctl/config.yaml`
5. Default config: `./config.yaml`

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
from kubectl_ld.async_cli import AsyncKubectlLD
from kubectl_ld.container import inject

async def main():
    kubectl_ld = AsyncKubectlLD(mode="live")
    crs = await kubectl_ld.list_crs()
```

### For Operators

The CLI interface remains unchanged, but new features are available:

```bash
# Enhanced logging
LDCTL_LOG_LEVEL=DEBUG kubectl-ld list

# Performance monitoring
LDCTL_LOG_FORMAT=structured kubectl-ld ldtop

# Custom configuration
LDCTL_CONFIG_PATH=/etc/my-config.yaml kubectl-ld simulate canary
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
- Memory growth in long-running ldtop sessions
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

This architecture provides a solid foundation for kubectl-ld's continued evolution while maintaining backward compatibility and improving developer experience.