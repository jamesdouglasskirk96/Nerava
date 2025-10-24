# Multi-Datacenter Deployment Guide

## Overview

This document outlines the strategy for deploying Nerava across multiple datacenters for high availability and disaster recovery.

## Architecture

### Primary-Secondary Model
- **Primary DC**: Handles all write operations
- **Secondary DCs**: Read-only replicas for failover
- **Global Load Balancer**: Routes traffic based on health and latency

### Data Replication
- **Database**: Master-slave replication with automatic failover
- **Cache**: Redis Cluster with cross-DC replication
- **Static Assets**: CDN distribution

## Deployment Strategy

### Phase 1: Single DC with Multi-Region Readiness
1. Deploy in primary datacenter
2. Configure cross-region replication
3. Test failover procedures
4. Monitor performance and costs

### Phase 2: Active-Passive Multi-DC
1. Deploy secondary datacenter
2. Configure read replicas
3. Implement automated failover
4. Test disaster recovery

### Phase 3: Active-Active Multi-DC
1. Implement conflict resolution
2. Configure global load balancing
3. Optimize data synchronization
4. Full disaster recovery testing

## Configuration

### Environment Variables by Region

#### Primary Region (us-east-1)
```bash
REGION=us-east-1
PRIMARY_REGION=us-east-1
DATABASE_URL=postgresql://user:pass@primary-db:5432/nerava
READ_DATABASE_URL=postgresql://user:pass@primary-db:5432/nerava
REDIS_URL=redis://primary-redis:6379/0
```

#### Secondary Region (eu-west-1)
```bash
REGION=eu-west-1
PRIMARY_REGION=us-east-1
DATABASE_URL=postgresql://user:pass@secondary-db:5432/nerava
READ_DATABASE_URL=postgresql://user:pass@secondary-db:5432/nerava
REDIS_URL=redis://secondary-redis:6379/0
```

### Helm Values by Region

#### Primary Region
```yaml
env:
  REGION: "us-east-1"
  PRIMARY_REGION: "us-east-1"
  DATABASE_URL: "postgresql://user:pass@primary-db:5432/nerava"
  READ_DATABASE_URL: "postgresql://user:pass@primary-db:5432/nerava"
  REDIS_URL: "redis://primary-redis:6379/0"

affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
    - labelSelector:
        matchExpressions:
        - key: app
          operator: In
          values:
          - nerava-api
      topologyKey: kubernetes.io/hostname
```

#### Secondary Region
```yaml
env:
  REGION: "eu-west-1"
  PRIMARY_REGION: "us-east-1"
  DATABASE_URL: "postgresql://user:pass@secondary-db:5432/nerava"
  READ_DATABASE_URL: "postgresql://user:pass@secondary-db:5432/nerava"
  REDIS_URL: "redis://secondary-redis:6379/0"

replicaCount: 2
autoscaling:
  enabled: false
```

## Traffic Management

### Global Load Balancer Configuration

#### AWS CloudFront
```yaml
cloudfront:
  enabled: true
  distribution:
    origins:
      - domain: nerava-api-us-east-1.example.com
        originPath: /
        customOriginConfig:
          httpPort: 80
          httpsPort: 443
          originProtocolPolicy: https-only
      - domain: nerava-api-eu-west-1.example.com
        originPath: /
        customOriginConfig:
          httpPort: 80
          httpsPort: 443
          originProtocolPolicy: https-only
    defaultCacheBehavior:
      targetOriginId: us-east-1
      viewerProtocolPolicy: redirect-to-https
      cachePolicyId: 4135ea2d-6df8-44a3-9df3-4b5a84be39ad
    priceClass: PriceClass_100
```

#### Route 53 Health Checks
```yaml
route53:
  healthChecks:
    - name: nerava-api-us-east-1
      resourcePath: /healthz
      port: 8000
      protocol: HTTPS
      failureThreshold: 3
      requestInterval: 30
    - name: nerava-api-eu-west-1
      resourcePath: /healthz
      port: 8000
      protocol: HTTPS
      failureThreshold: 3
      requestInterval: 30
```

### Canary Deployment

#### Traffic Splitting
```yaml
# 10% traffic to new version
canary:
  enabled: true
  weight: 10
  analysis:
    interval: 1m
    threshold: 5
    baseline: 2m
    max: 50
```

#### Blue-Green Deployment
```bash
# Deploy green environment
helm install nerava-api-green ./charts/nerava-api \
  --set image.tag=v0.9.1 \
  --namespace nerava-green

# Test green environment
kubectl port-forward svc/nerava-api-green 8001:8000

# Switch traffic (update ingress)
kubectl patch ingress nerava-api -p '{"spec":{"rules":[{"host":"nerava.app","http":{"paths":[{"path":"/","pathType":"Prefix","backend":{"service":{"name":"nerava-api-green","port":{"number":8000}}}}]}}]}}'

# Monitor for 5 minutes
sleep 300

# Complete deployment or rollback
if [ $? -eq 0 ]; then
  echo "Deployment successful"
  kubectl delete deployment nerava-api-blue
else
  echo "Rolling back"
  kubectl patch ingress nerava-api -p '{"spec":{"rules":[{"host":"nerava.app","http":{"paths":[{"path":"/","pathType":"Prefix","backend":{"service":{"name":"nerava-api-blue","port":{"number":8000}}}}]}}]}}'
fi
```

## Data Synchronization

### Database Replication

#### PostgreSQL Streaming Replication
```sql
-- Primary database configuration
ALTER SYSTEM SET wal_level = replica;
ALTER SYSTEM SET max_wal_senders = 3;
ALTER SYSTEM SET max_replication_slots = 3;
SELECT pg_reload_conf();

-- Create replication user
CREATE USER replicator REPLICATION LOGIN PASSWORD 'replicator_password';

-- Secondary database configuration
-- Add to postgresql.conf
hot_standby = on
```

#### Redis Cluster Configuration
```yaml
redis:
  cluster:
    enabled: true
    nodes:
      - host: redis-us-east-1-1
        port: 6379
      - host: redis-us-east-1-2
        port: 6379
      - host: redis-us-east-1-3
        port: 6379
      - host: redis-eu-west-1-1
        port: 6379
      - host: redis-eu-west-1-2
        port: 6379
      - host: redis-eu-west-1-3
        port: 6379
```

### Conflict Resolution

#### Last-Write-Wins Strategy
```python
# In application code
def resolve_conflict(local_data, remote_data):
    if local_data['timestamp'] > remote_data['timestamp']:
        return local_data
    else:
        return remote_data
```

#### Operational Transform
```python
# For complex data structures
def apply_operation(base_data, operation):
    if operation['type'] == 'insert':
        base_data.insert(operation['position'], operation['value'])
    elif operation['type'] == 'delete':
        base_data.pop(operation['position'])
    return base_data
```

## Monitoring and Observability

### Cross-DC Monitoring

#### Prometheus Federation
```yaml
# Primary region Prometheus
federation:
  targets:
    - "nerava-api-us-east-1:9090"
    - "nerava-api-eu-west-1:9090"
  scrape_interval: 30s
```

#### Grafana Dashboards
- Global service health
- Cross-DC latency comparison
- Data replication lag
- Traffic distribution

### Alerting

#### Critical Alerts
- Cross-DC connectivity loss
- Data replication lag > 5 minutes
- Primary region failure
- Traffic routing issues

#### Warning Alerts
- High latency between regions
- Replication lag > 1 minute
- Unusual traffic patterns
- Resource utilization > 80%

## Disaster Recovery

### RTO/RPO Targets
- **RTO (Recovery Time Objective)**: 15 minutes
- **RPO (Recovery Point Objective)**: 5 minutes
- **Availability**: 99.99% (4.38 minutes downtime/year)

### Failover Procedures

#### Automated Failover
```bash
#!/bin/bash
# failover.sh

PRIMARY_REGION="us-east-1"
SECONDARY_REGION="eu-west-1"

# Check primary region health
if ! curl -f https://nerava-api-us-east-1.example.com/healthz; then
  echo "Primary region unhealthy, initiating failover"
  
  # Update DNS to point to secondary
  aws route53 change-resource-record-sets \
    --hosted-zone-id Z123456789 \
    --change-batch file://failover-dns.json
  
  # Scale up secondary region
  kubectl scale deployment nerava-api --replicas=5 -n nerava-eu-west-1
  
  # Update application configuration
  kubectl patch configmap nerava-config -n nerava-eu-west-1 \
    --patch '{"data":{"PRIMARY_REGION":"eu-west-1"}}'
  
  echo "Failover completed"
fi
```

#### Manual Failover
1. Assess the situation
2. Notify stakeholders
3. Execute failover procedures
4. Monitor secondary region
5. Communicate status updates
6. Plan recovery

### Recovery Procedures

#### Primary Region Recovery
```bash
#!/bin/bash
# recovery.sh

# Verify primary region is healthy
if curl -f https://nerava-api-us-east-1.example.com/healthz; then
  echo "Primary region recovered"
  
  # Sync data from secondary
  pg_dump nerava-eu-west-1 | psql nerava-us-east-1
  
  # Update DNS to point back to primary
  aws route53 change-resource-record-sets \
    --hosted-zone-id Z123456789 \
    --change-batch file://recovery-dns.json
  
  # Scale down secondary region
  kubectl scale deployment nerava-api --replicas=2 -n nerava-eu-west-1
  
  echo "Recovery completed"
fi
```

## Testing

### Chaos Engineering
```bash
# Network partition between regions
kubectl apply -f - <<EOF
apiVersion: v1
kind: NetworkPolicy
metadata:
  name: block-cross-region
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  egress:
  - to: []
EOF

# Database connection failure
kubectl delete pod -l app=postgresql

# Redis cluster node failure
kubectl delete pod -l app=redis
```

### Load Testing
```bash
# Test cross-DC latency
k6 run --vus 100 --duration 5m load-test-cross-dc.js

# Test failover scenarios
k6 run --vus 50 --duration 10m load-test-failover.js
```

## Cost Optimization

### Resource Allocation
- **Primary Region**: 70% of resources
- **Secondary Region**: 30% of resources
- **Auto-scaling**: Based on traffic patterns

### Data Transfer Costs
- Minimize cross-DC data transfer
- Use CDN for static assets
- Compress data replication
- Optimize cache strategies

### Monitoring Costs
- Use cost-effective monitoring solutions
- Implement data retention policies
- Optimize log storage
- Use spot instances where appropriate
