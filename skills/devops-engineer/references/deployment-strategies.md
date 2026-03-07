# Deployment Strategies

## Contents

1. [Strategy Comparison](#strategy-comparison)
2. [Blue/Green Deployment](#bluegreen-deployment)
3. [Canary Deployment](#canary-deployment)
4. [Rolling Deployment](#rolling-deployment)
5. [Selection Guide](#selection-guide)
6. [Rollback Procedures](#rollback-procedures)
7. [Health Checks](#health-checks)

---

## Strategy Comparison

| Factor | Blue/Green | Canary | Rolling |
|--------|-----------|--------|---------|
| **Rollback speed** | Instant (switch DNS/LB) | Fast (route to old) | Slow (redeploy all) |
| **Resource cost** | 2x during deploy | 1.1-1.5x during deploy | 1x (in-place) |
| **Risk exposure** | Zero (test before switch) | Gradual (% traffic) | Gradual (instance-by-instance) |
| **Complexity** | Medium | High | Low |
| **Downtime** | Zero | Zero | Near-zero |
| **Smoke test window** | Full (test green before switch) | Limited (% of real traffic) | None (immediate replacement) |
| **Database migration** | Requires backward-compatible schemas | Same | Same |
| **Best for** | Critical services, regulated industries | High-traffic APIs, feature validation | Cost-sensitive, internal services |

---

## Blue/Green Deployment

Two identical environments. Deploy to inactive (green), test, then switch traffic.

### GitHub Actions workflow pattern

```yaml
jobs:
  deploy-green:
    environment: production-green
    steps:
      - run: deploy_to_green
      - run: run_smoke_tests --target green
      - run: verify_health_checks --target green

  switch-traffic:
    needs: deploy-green
    environment: production
    steps:
      - run: switch_load_balancer --from blue --to green
      - run: verify_traffic --target green
      - run: tag_blue_as_rollback
```

### Key implementation details

- Both environments must be identical in configuration
- Database must support both versions simultaneously (backward-compatible migrations)
- DNS TTL should be low (30-60s) if using DNS-based switching
- Load balancer switching is preferred over DNS (instant)
- Keep blue environment running for rollback window (configurable, typically 1-4 hours)
- Cleanup: decommission old blue after rollback window expires

### Rollback

```bash
# Instant: switch load balancer back to blue
switch_load_balancer --from green --to blue
```

---

## Canary Deployment

Route a small percentage of traffic to the new version. Gradually increase if healthy.

### Traffic progression

```
Deploy canary -> 1% traffic -> monitor 10min
                -> 5% traffic -> monitor 15min
                -> 25% traffic -> monitor 15min
                -> 50% traffic -> monitor 10min
                -> 100% traffic -> complete
```

### GitHub Actions workflow pattern

```yaml
jobs:
  canary-deploy:
    steps:
      - run: deploy_canary --version ${{ github.sha }}
      - run: set_traffic_weight --canary 1
      - run: monitor_metrics --duration 10m --threshold error_rate<0.01
      - run: set_traffic_weight --canary 5
      - run: monitor_metrics --duration 15m --threshold error_rate<0.01
      - run: set_traffic_weight --canary 25
      - run: monitor_metrics --duration 15m --threshold p99_latency<500ms
      - run: promote_canary  # 100% traffic

  rollback:
    if: failure()
    steps:
      - run: set_traffic_weight --canary 0
      - run: delete_canary
```

### Key metrics to monitor

- Error rate (5xx responses)
- Latency (p50, p95, p99)
- CPU and memory usage
- Custom business metrics (conversion rate, API success rate)

### Rollback

```bash
# Fast: route all traffic away from canary
set_traffic_weight --canary 0
delete_canary
```

---

## Rolling Deployment

Replace instances one at a time (or in batches).

### Kubernetes rolling update

```yaml
apiVersion: apps/v1
kind: Deployment
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1      # At most 1 pod down during update
      maxSurge: 1             # At most 1 extra pod during update
  minReadySeconds: 30         # Wait before marking ready
```

### GitHub Actions pattern

```yaml
jobs:
  rolling-deploy:
    strategy:
      matrix:
        server: [server-1, server-2, server-3]
      max-parallel: 1  # One at a time
    steps:
      - run: drain_server ${{ matrix.server }}
      - run: deploy_to ${{ matrix.server }}
      - run: health_check ${{ matrix.server }}
      - run: undrain_server ${{ matrix.server }}
```

### Key configuration

- `maxUnavailable`: how many instances can be down simultaneously
- `maxSurge`: how many extra instances can exist during rollout
- `minReadySeconds`: stability window before proceeding
- Health checks must pass before next batch starts

### Rollback

```bash
# Kubernetes: automatic if health check fails
kubectl rollout undo deployment/app

# Manual: redeploy previous version
kubectl set image deployment/app app=registry/app:previous-sha
```

---

## Selection Guide

### Choose Blue/Green when:

- Zero-downtime is non-negotiable
- You need a full smoke test window before exposing users
- Regulatory requirements demand pre-production validation
- You can afford 2x infrastructure during deployment
- Database migrations are backward-compatible

### Choose Canary when:

- You need to validate with real production traffic
- Error detection requires production load patterns
- You have good observability (metrics, alerting)
- Traffic routing infrastructure exists (Istio, ALB, etc.)
- Gradual risk exposure is preferred

### Choose Rolling when:

- Cost is a primary concern (no extra infrastructure)
- Simple applications with quick startup
- Internal services with lower SLA requirements
- Kubernetes is the deployment platform (native support)
- You trust health checks to catch issues quickly

---

## Rollback Procedures

### Automated rollback triggers

| Metric | Threshold | Action |
|--------|-----------|--------|
| Error rate (5xx) | >1% for 5 min | Automatic rollback |
| Latency p99 | >2x baseline for 5 min | Automatic rollback |
| Health check | 3 consecutive failures | Automatic rollback |
| CPU usage | >90% for 10 min | Alert + manual review |
| Memory usage | >85% for 5 min | Alert + manual review |

### Rollback checklist

1. Verify the issue is deployment-related (not external dependency)
2. Execute rollback procedure (strategy-specific)
3. Verify old version is healthy
4. Preserve logs and metrics from failed deployment
5. Create incident report with root cause

---

## Health Checks

### Types

| Type | Purpose | Example |
|------|---------|---------|
| Startup | Application is initialized | TCP port check |
| Liveness | Application is running | GET /healthz returns 200 |
| Readiness | Application can serve traffic | GET /readyz checks DB connection |
| Deep | Full dependency check | GET /health/deep checks all backends |

### Implementation

```yaml
# Kubernetes probes
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 15
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /readyz
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
  failureThreshold: 2
```

### CI/CD health check step

```yaml
- name: Verify deployment health
  run: |
    for i in $(seq 1 30); do
      if curl -sf "$DEPLOY_URL/healthz"; then
        echo "Health check passed"
        exit 0
      fi
      sleep 10
    done
    echo "Health check failed after 5 minutes"
    exit 1
```
