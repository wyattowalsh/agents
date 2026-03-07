# Kubernetes Patterns

## Contents

1. [Workload Patterns](#workload-patterns)
2. [Security Context](#security-context)
3. [Health Checks](#health-checks)
4. [Resource Management](#resource-management)
5. [Networking](#networking)
6. [Helm Conventions](#helm-conventions)
7. [Scaling](#scaling)

---

## Workload Patterns

### Deployment (stateless)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
  labels:
    app.kubernetes.io/name: app
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: infrastructure-coder
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: app
  template:
    metadata:
      labels:
        app.kubernetes.io/name: app
    spec:
      serviceAccountName: app
      securityContext:
        runAsNonRoot: true
        fsGroup: 1000
      containers:
        - name: app
          image: registry/app:1.0.0
          ports:
            - containerPort: 8080
              name: http
          # Resources, probes, securityContext below
```

### StatefulSet (stateful)

Use for: databases, message queues, anything needing stable network identity or persistent storage.

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: db
spec:
  serviceName: db
  replicas: 3
  podManagementPolicy: Parallel  # or OrderedReady
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: gp3
        resources:
          requests:
            storage: 50Gi
```

### CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: cleanup
spec:
  schedule: "0 2 * * *"
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      backoffLimit: 3
      activeDeadlineSeconds: 3600
```

---

## Security Context

### Pod level

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  fsGroup: 1000
  seccompProfile:
    type: RuntimeDefault
```

### Container level

```yaml
securityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop: ["ALL"]
```

### Service account

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app
  annotations:
    # AWS IRSA
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789:role/app
    # GCP Workload Identity
    iam.gke.io/gcp-service-account: app@project.iam.gserviceaccount.com
automountServiceAccountToken: false  # Only mount if needed
```

---

## Health Checks

### Standard probe set

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: http
  initialDelaySeconds: 15
  periodSeconds: 20
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /readyz
    port: http
  initialDelaySeconds: 5
  periodSeconds: 10
  failureThreshold: 3

startupProbe:
  httpGet:
    path: /healthz
    port: http
  failureThreshold: 30
  periodSeconds: 10
```

### Probe selection guide

| Probe | Purpose | When to use |
|-------|---------|-------------|
| `startupProbe` | Detect slow-starting containers | Apps needing >30s to start |
| `livenessProbe` | Restart unhealthy containers | Always — detects deadlocks |
| `readinessProbe` | Remove from service endpoints | Always — prevents traffic to unready pods |

---

## Resource Management

### Requests and limits

```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

### Sizing guidelines

| Workload type | CPU request:limit | Memory request:limit |
|---------------|-------------------|----------------------|
| Web server | 1:4 | 1:2 |
| Worker | 1:2 | 1:1.5 |
| Database | 1:1 | 1:1 |
| Batch job | 1:1 | 1:2 |

### Pod Disruption Budget

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: app
spec:
  minAvailable: 2  # or maxUnavailable: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: app
```

---

## Networking

### Service types

| Type | Use case |
|------|----------|
| ClusterIP | Internal service-to-service |
| NodePort | Development, direct access |
| LoadBalancer | External traffic (cloud LB) |
| Headless (clusterIP: None) | StatefulSet DNS discovery |

### NetworkPolicy (default deny + allowlist)

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
spec:
  podSelector: {}
  policyTypes: ["Ingress", "Egress"]

---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-app
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: app
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app.kubernetes.io/name: frontend
      ports:
        - port: 8080
  egress:
    - to:
        - podSelector:
            matchLabels:
              app.kubernetes.io/name: db
      ports:
        - port: 5432
```

---

## Helm Conventions

### values.yaml structure

```yaml
replicaCount: 3

image:
  repository: registry/app
  tag: "1.0.0"
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 80

resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi

autoscaling:
  enabled: false
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilization: 80
```

### Template helpers

```yaml
# _helpers.tpl
{{- define "app.fullname" -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "app.labels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}
```

---

## Scaling

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: app
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: app
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
```

### Vertical Pod Autoscaler (recommendations)

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: app
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: app
  updatePolicy:
    updateMode: "Off"  # Recommendation only
```
