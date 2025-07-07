# Reference Documentation

## 📋 API Documentation & Technical Reference

This directory contains comprehensive API documentation, specifications, and technical reference materials for the mtop LLM monitoring system.

## 📋 Contents

### API Reference
- **[CLI Reference](cli/)** - Complete command-line interface documentation
- **[REST API](api/)** - RESTful API endpoints and specifications
- **[Kubernetes API](k8s-api/)** - Custom Resource Definitions and Kubernetes APIs
- **[Metrics API](metrics/)** - Monitoring metrics and data formats

### Configuration Reference
- **[Configuration Schema](config/schema.md)** - Complete configuration options
- **[Environment Variables](config/environment.md)** - Environment variable reference
- **[Advanced Configuration](config/advanced.md)** - Advanced configuration patterns
- **[Migration Guides](config/migration.md)** - Configuration migration between versions

### Data Formats
- **[Metric Formats](formats/metrics.md)** - Monitoring metric data structures
- **[Event Formats](formats/events.md)** - Event and alert data formats
- **[Export Formats](formats/exports.md)** - Data export and import formats
- **[Protocol Specifications](formats/protocols.md)** - Communication protocol specs

### Integration Reference
- **[Webhook Specifications](integrations/webhooks.md)** - Webhook payload formats
- **[Plugin API](integrations/plugins.md)** - Plugin development interface
- **[Extension Points](integrations/extensions.md)** - System extension mechanisms
- **[SDK Documentation](integrations/sdk.md)** - Software development kit reference

## 🔧 API Categories

### Core APIs
- **Monitoring API** - Real-time LLM monitoring data
- **Configuration API** - System configuration management
- **Alert API** - Alert and notification management
- **Metrics API** - Performance and utilization metrics

### Management APIs
- **Cluster API** - Multi-cluster management
- **User API** - User and access management
- **Audit API** - Audit trail and compliance data
- **Health API** - System health and status

### Integration APIs
- **Webhook API** - External system integration
- **Export API** - Data export and reporting
- **Import API** - Data import and migration
- **Plugin API** - Custom extension development

## 📖 Documentation Standards

### API Documentation Format
```yaml
Endpoint: /api/v1/metrics
Method: GET
Parameters:
  - name: cluster
    type: string
    required: false
    description: Filter by cluster name
Response:
  type: object
  properties:
    metrics:
      type: array
      items:
        $ref: '#/components/schemas/Metric'
Examples:
  - request: GET /api/v1/metrics?cluster=prod
  - response: { "metrics": [...] }
```

### Configuration Documentation Format
```yaml
Property: monitoring.interval
Type: duration
Default: 30s
Description: Interval between monitoring data collection
Valid Values: 1s-5m
Examples:
  - monitoring.interval: "15s"
  - monitoring.interval: "2m"
Environment Variable: MTOP_MONITORING_INTERVAL
```

## 🚀 Quick Reference

### Essential Commands
```bash
# Basic monitoring
mtop list                    # List all LLM services
mtop get <service-name>      # Get service details
mtop logs <service-name>     # View service logs

# Real-time monitoring  
mtop                         # Interactive dashboard
mtop slo-dashboard          # SLO compliance dashboard

# Configuration
mtop config                 # Show current configuration
mtop config set <key> <val> # Update configuration
```

### Common Configuration
```yaml
# Basic configuration
monitoring:
  interval: 30s
  retention: 7d

# Advanced configuration
gpu:
  fractioning: enabled
  heartbeat_interval: 5s

slo:
  ttft_threshold: 500ms
  error_rate_threshold: 1%
```

### API Examples
```bash
# REST API usage
curl -X GET "http://localhost:8080/api/v1/metrics"
curl -X POST "http://localhost:8080/api/v1/alerts" \
  -d '{"name":"high-latency","threshold":"1000ms"}'

# Webhook integration
curl -X POST "http://external-system/webhook" \
  -H "Content-Type: application/json" \
  -d '{"event":"slo_violation","service":"gpt-4"}'
```

## 📊 Data Models

### Core Data Types
- **Metric** - Individual monitoring measurement
- **Event** - System event or alert
- **Service** - LLM inference service
- **Cluster** - Kubernetes cluster representation

### Metric Types
- **Counter** - Incrementing values (requests, errors)
- **Gauge** - Point-in-time values (CPU, memory)
- **Histogram** - Distribution data (latency, response size)
- **Summary** - Statistical summaries (percentiles)

### Time Series Data
- **Timestamp** - RFC3339 formatted timestamps
- **Labels** - Key-value metadata
- **Values** - Numeric measurements
- **Annotations** - Additional context data

## 🔗 External References
- [Prometheus Metrics](https://prometheus.io/docs/concepts/metric_types/)
- [Kubernetes API Reference](https://kubernetes.io/docs/reference/kubernetes-api/)
- [OpenAPI Specification](https://spec.openapis.org/oas/v3.0.3)

---

*Complete technical reference for professional LLM monitoring*