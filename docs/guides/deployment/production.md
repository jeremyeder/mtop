# Production Deployment Guide

## 🏭 Enterprise Production Deployment

This guide provides comprehensive instructions for deploying mtop in production environments with enterprise-grade reliability, security, and scalability.

## 📋 Prerequisites

### Infrastructure Requirements
- **Kubernetes 1.24+** (1.28+ recommended)
- **Persistent Storage** with ReadWriteMany support
- **Load Balancer** for ingress traffic
- **DNS Management** for service discovery

### Resource Requirements
```yaml
Minimum Production Setup:
  CPU: 2 cores per mtop instance
  Memory: 4GB per mtop instance
  Storage: 100GB for metrics and logs
  Network: 1Gbps for monitoring traffic

Recommended Production Setup:
  CPU: 4 cores per mtop instance
  Memory: 8GB per mtop instance  
  Storage: 500GB for metrics and logs
  Network: 10Gbps for monitoring traffic
```

### Security Prerequisites
- **TLS Certificates** for HTTPS endpoints
- **Service Accounts** with minimal required permissions
- **Network Policies** for traffic segmentation
- **Secrets Management** system (e.g., HashiCorp Vault)

## 🚀 Deployment Process

### 1. Pre-Deployment Planning

#### Capacity Planning
```bash
# Calculate resource requirements
# For N LLM services:
# - CPU: N * 0.1 cores + 2 base cores
# - Memory: N * 50MB + 2GB base memory
# - Storage: N * 10MB/day + 1GB base storage

# Example for 100 LLM services:
# - CPU: 100 * 0.1 + 2 = 12 cores
# - Memory: 100 * 50MB + 2GB = 7GB
# - Storage: 100 * 10MB/day + 1GB = 2GB/day
```

#### Network Planning
```yaml
Network Requirements:
  Ingress: HTTPS (443), Management API (8080)
  Cluster Internal: Metrics collection (9090), Health checks (8081)
  External: Webhook notifications (443), Alert routing (various)
  
Bandwidth Planning:
  Monitoring Traffic: ~10MB/hour per monitored service
  Alert Traffic: ~1KB per alert
  Dashboard Traffic: ~100KB per user session
```

### 2. Security Configuration

#### Service Account Setup
```yaml
# mtop-service-account.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: mtop-monitor
  namespace: mtop-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: mtop-monitor
rules:
- apiGroups: [""]
  resources: ["pods", "services", "nodes"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["serving.kserve.io"]
  resources: ["inferenceservices"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: mtop-monitor
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: mtop-monitor
subjects:
- kind: ServiceAccount
  name: mtop-monitor
  namespace: mtop-system
```

#### Network Policies
```yaml
# mtop-network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: mtop-system-policy
  namespace: mtop-system
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 443
    - protocol: TCP
      port: 6443
```

### 3. Production Configuration

#### Main Configuration
```yaml
# production-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mtop-config
  namespace: mtop-system
data:
  config.yaml: |
    monitoring:
      interval: 30s
      retention: 30d
      batch_size: 1000
      
    performance:
      cache_size: 1000
      max_connections: 100
      timeout: 30s
      
    security:
      tls_enabled: true
      rbac_enabled: true
      audit_enabled: true
      
    alerts:
      enabled: true
      smtp_server: "smtp.company.com"
      webhook_url: "https://alerts.company.com/webhook"
      
    storage:
      type: "persistent"
      path: "/data/mtop"
      backup_enabled: true
      backup_schedule: "0 2 * * *"
```

#### Resource Limits
```yaml
# mtop-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mtop-monitor
  namespace: mtop-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mtop-monitor
  template:
    metadata:
      labels:
        app: mtop-monitor
    spec:
      serviceAccountName: mtop-monitor
      containers:
      - name: mtop
        image: mtop:production-v1.0.0
        ports:
        - containerPort: 8080
          name: api
        - containerPort: 8081
          name: health
        resources:
          requests:
            cpu: "2"
            memory: "4Gi"
          limits:
            cpu: "4"
            memory: "8Gi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8081
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8081
          initialDelaySeconds: 10
          periodSeconds: 5
        env:
        - name: MTOP_CONFIG_FILE
          value: "/config/config.yaml"
        - name: MTOP_MODE
          value: "live"
        - name: MTOP_LOG_LEVEL
          value: "INFO"
        volumeMounts:
        - name: config
          mountPath: /config
        - name: data
          mountPath: /data
      volumes:
      - name: config
        configMap:
          name: mtop-config
      - name: data
        persistentVolumeClaim:
          claimName: mtop-data
```

### 4. Storage Configuration

#### Persistent Volume Setup
```yaml
# mtop-storage.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mtop-data
  namespace: mtop-system
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 500Gi
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mtop-backup
  namespace: mtop-system
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: backup-storage
  resources:
    requests:
      storage: 1Ti
```

### 5. Ingress and Load Balancing

#### Ingress Configuration
```yaml
# mtop-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: mtop-ingress
  namespace: mtop-system
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - mtop.company.com
    secretName: mtop-tls
  rules:
  - host: mtop.company.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: mtop-service
            port:
              number: 8080
```

#### Service Configuration
```yaml
# mtop-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: mtop-service
  namespace: mtop-system
spec:
  selector:
    app: mtop-monitor
  ports:
  - name: api
    port: 8080
    targetPort: 8080
  - name: health
    port: 8081
    targetPort: 8081
  type: ClusterIP
```

## 📊 Production Monitoring

### Health Checks
```bash
# Application health endpoints
curl -f http://mtop-service:8081/health
curl -f http://mtop-service:8081/ready
curl -f http://mtop-service:8081/metrics

# Kubernetes health validation
kubectl get pods -n mtop-system
kubectl describe deployment mtop-monitor -n mtop-system
kubectl logs -f deployment/mtop-monitor -n mtop-system
```

### Performance Monitoring
```yaml
# Monitoring integration
prometheus:
  enabled: true
  scrape_interval: 30s
  retention: 15d
  
grafana:
  enabled: true
  dashboards:
    - mtop-overview
    - mtop-performance  
    - mtop-alerts
    
alertmanager:
  enabled: true
  routes:
    - receiver: "mtop-alerts"
      match:
        service: "mtop"
```

### Log Management
```yaml
# Log configuration
logging:
  level: INFO
  format: json
  output: stdout
  
fluentd:
  enabled: true
  forward_to: "elasticsearch.logging.svc.cluster.local"
  
elasticsearch:
  index_pattern: "mtop-logs-*"
  retention: "30d"
```

## 🔒 Security Hardening

### TLS Configuration
```bash
# Generate production certificates
openssl req -new -x509 -days 365 -nodes \
  -out mtop.crt \
  -keyout mtop.key \
  -subj "/CN=mtop.company.com"

# Create Kubernetes secret
kubectl create secret tls mtop-tls \
  --cert=mtop.crt \
  --key=mtop.key \
  -n mtop-system
```

### Pod Security Standards
```yaml
# mtop-pod-security.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: mtop-system
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### Security Context
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 10001
  runAsGroup: 10001
  fsGroup: 10001
  seccompProfile:
    type: RuntimeDefault
  capabilities:
    drop:
    - ALL
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
```

## 📈 Scaling Configuration

### Horizontal Pod Autoscaling
```yaml
# mtop-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mtop-hpa
  namespace: mtop-system
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mtop-monitor
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Vertical Pod Autoscaling
```yaml
# mtop-vpa.yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: mtop-vpa
  namespace: mtop-system
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mtop-monitor
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: mtop
      maxAllowed:
        cpu: "8"
        memory: "16Gi"
      minAllowed:
        cpu: "1"
        memory: "2Gi"
```

## 🚨 Disaster Recovery

### Backup Configuration
```bash
# Automated backup script
#!/bin/bash
# backup-mtop.sh

BACKUP_DIR="/backups/mtop/$(date +%Y%m%d)"
kubectl create ns mtop-backup

# Backup configuration
kubectl get configmap mtop-config -n mtop-system -o yaml > "$BACKUP_DIR/config.yaml"

# Backup data
kubectl exec -n mtop-system deployment/mtop-monitor -- tar czf - /data/mtop | \
  kubectl run backup-pod --rm -i --image=alpine --restart=Never -- \
  sh -c "cat > /backup/mtop-data-$(date +%Y%m%d).tar.gz"

# Backup to cloud storage
aws s3 cp "$BACKUP_DIR" s3://company-backups/mtop/ --recursive
```

### Recovery Procedures
```bash
# Recovery from backup
#!/bin/bash
# restore-mtop.sh

BACKUP_DATE=$1
BACKUP_DIR="/backups/mtop/$BACKUP_DATE"

# Scale down deployment
kubectl scale deployment mtop-monitor --replicas=0 -n mtop-system

# Restore configuration
kubectl apply -f "$BACKUP_DIR/config.yaml"

# Restore data
kubectl run restore-pod --rm -i --image=alpine --restart=Never -- \
  sh -c "cd /data && tar xzf -" < "$BACKUP_DIR/mtop-data-$BACKUP_DATE.tar.gz"

# Scale up deployment
kubectl scale deployment mtop-monitor --replicas=3 -n mtop-system
```

## ✅ Production Readiness Checklist

### Infrastructure
- [ ] Kubernetes cluster hardened and updated
- [ ] Persistent storage configured and tested
- [ ] Load balancer configured with health checks
- [ ] DNS records configured and validated
- [ ] Network policies implemented and tested

### Security
- [ ] TLS certificates installed and validated
- [ ] RBAC policies configured and tested
- [ ] Service accounts with minimal permissions
- [ ] Pod security standards enforced
- [ ] Network segmentation implemented

### Monitoring & Alerting
- [ ] Health check endpoints responding
- [ ] Prometheus metrics collection enabled
- [ ] Grafana dashboards configured
- [ ] Alert routing configured and tested
- [ ] Log aggregation working

### Operations
- [ ] Backup procedures tested
- [ ] Recovery procedures documented and tested
- [ ] Scaling policies configured
- [ ] Performance baselines established
- [ ] Operational runbooks created

### Documentation
- [ ] Production architecture documented
- [ ] Operational procedures documented
- [ ] Troubleshooting guides available
- [ ] Contact information updated
- [ ] Change management procedures defined

## 📚 Related Resources
- [Security Guide](../security/) - Comprehensive security documentation
- [Performance Guide](../../performance/) - Performance optimization
- [Operational Guide](../operations/) - Day-to-day operations
- [Troubleshooting Guide](../operations/troubleshooting.md) - Problem resolution

---

*Enterprise production deployment for professional LLM monitoring*