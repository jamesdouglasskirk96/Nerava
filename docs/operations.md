# Nerava Operations Guide

## Overview

This document provides operational guidance for running Nerava in production environments.

## SLOs (Service Level Objectives)

### Performance Targets
- **API Response Time**: p95 < 200ms for `/v1/energyhub/windows`
- **Charge Stop Time**: p95 < 500ms for `/v1/energyhub/events/charge-stop`
- **Availability**: 99.9% uptime
- **Error Rate**: < 0.1% for critical endpoints

### Monitoring

#### Key Metrics
- `http_requests_total` - Total HTTP requests by endpoint
- `http_request_duration_seconds` - Request duration histogram
- `http_active_requests` - Currently active requests
- `wallet_credits_total` - Total wallet credits processed
- `charging_sessions_total` - Total charging sessions

#### Alerts
- High error rate (> 1%)
- High response time (p95 > 500ms)
- Service unavailable
- Database connection failures
- Redis connection failures

## Deployment

### Docker
```bash
# Build image
docker build -t nerava-backend:latest .

# Run container
docker run -d \
  --name nerava-api \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/nerava \
  -e REDIS_URL=redis://host:6379/0 \
  nerava-backend:latest
```

### Kubernetes
```bash
# Install Helm chart
helm install nerava-api ./charts/nerava-api \
  --set image.tag=v0.9.0 \
  --set env.DATABASE_URL=postgresql://user:pass@host:5432/nerava \
  --set env.REDIS_URL=redis://host:6379/0
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | Database connection string | `sqlite:///./nerava.db` | Yes |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` | Yes |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `RATE_LIMIT_PER_MINUTE` | Rate limit per minute | `120` | No |
| `CACHE_TTL_WINDOWS` | Cache TTL for windows | `60` | No |
| `ENABLE_SYNC_CREDIT` | Enable sync wallet credits | `false` | No |

### Feature Flags
- `ENERGYHUB_ALLOW_DEMO_AT` - Allow demo time overrides
- `ENABLE_SYNC_CREDIT` - Use synchronous wallet credits
- `EVENTS_DRIVER` - Event driver (inproc/redis)

## Health Checks

### Endpoints
- `GET /healthz` - Basic health check
- `GET /readyz` - Readiness check (includes dependencies)
- `GET /metrics` - Prometheus metrics

### Health Check Script
```bash
#!/bin/bash
# health-check.sh

API_URL="http://localhost:8000"

# Check health
curl -f "$API_URL/healthz" || exit 1

# Check readiness
curl -f "$API_URL/readyz" || exit 1

# Check metrics
curl -f "$API_URL/metrics" | grep -q "http_requests_total" || exit 1

echo "All health checks passed"
```

## Troubleshooting

### Common Issues

#### High Memory Usage
- Check for memory leaks in async wallet processor
- Monitor Redis memory usage
- Review database connection pool settings

#### Slow Response Times
- Check database query performance
- Verify Redis connectivity
- Review rate limiting settings
- Check for circuit breaker activations

#### Wallet Credit Failures
- Verify wallet service connectivity
- Check circuit breaker status
- Review async queue processing
- Monitor error logs

### Log Analysis

#### Key Log Patterns
```bash
# High error rate
grep "ERROR" /var/log/nerava/app.log | tail -100

# Slow requests
grep "duration_ms.*[5-9][0-9][0-9]" /var/log/nerava/app.log

# Circuit breaker activations
grep "Circuit breaker is OPEN" /var/log/nerava/app.log

# Rate limiting
grep "Rate limit exceeded" /var/log/nerava/app.log
```

## Rollback Procedures

### Application Rollback
```bash
# Kubernetes
kubectl rollout undo deployment/nerava-api

# Docker
docker stop nerava-api
docker run -d --name nerava-api -p 8000:8000 nerava-backend:previous-tag
```

### Database Rollback
```bash
# Restore from backup
pg_restore -d nerava backup.sql

# Or use point-in-time recovery
# (Depends on database provider)
```

## Scaling

### Horizontal Scaling
- Use Kubernetes HPA for automatic scaling
- Monitor CPU and memory usage
- Set appropriate resource limits

### Vertical Scaling
- Increase CPU/memory limits
- Optimize database queries
- Review caching strategies

## Security

### Network Security
- Use TLS for all communications
- Implement proper firewall rules
- Use service mesh for internal communication

### Application Security
- Regular security updates
- Monitor for vulnerabilities
- Use secrets management
- Implement proper authentication

## Backup and Recovery

### Database Backups
```bash
# Daily backup
pg_dump nerava > backup-$(date +%Y%m%d).sql

# Automated backup script
#!/bin/bash
pg_dump nerava | gzip > backup-$(date +%Y%m%d).sql.gz
aws s3 cp backup-$(date +%Y%m%d).sql.gz s3://nerava-backups/
```

### Configuration Backups
- Store configuration in version control
- Use infrastructure as code
- Document all changes

## Performance Optimization

### Database Optimization
- Use appropriate indexes
- Monitor slow queries
- Regular VACUUM and ANALYZE
- Connection pooling

### Caching Strategy
- Cache frequently accessed data
- Use appropriate TTL values
- Monitor cache hit rates
- Implement cache warming

### Application Optimization
- Profile application performance
- Optimize database queries
- Use async processing
- Implement proper error handling
