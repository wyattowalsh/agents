# Cost-Relative Comparison Guide

Approximate relative comparisons only. Never state dollar amounts.

## Cross-Cloud Resource Equivalents by Cost Tier

| Resource Type | AWS (relative) | GCP (relative) | Azure (relative) |
|---------------|---------------|-----------------|-------------------|
| General compute | EC2 m6i (1x) | n2 (~0.95x) | D-series (~1.05x) |
| Managed K8s | EKS (~1x) | GKE (~0.9x, free control plane) | AKS (~0.9x, free control plane) |
| Object storage | S3 (1x) | Cloud Storage (~0.95x) | Blob (~1x) |
| Managed DB (Postgres) | RDS (~1x) | Cloud SQL (~0.9x) | Flexible Server (~0.95x) |
| Serverless functions | Lambda (1x) | Cloud Functions (~1x) | Azure Functions (~1x) |
| Serverless containers | Fargate (~1x) | Cloud Run (~0.7x) | Container Apps (~0.8x) |
| Egress (internet) | ~1x | ~1x | ~0.95x |

## Compute Instance Families

| Family | Relative Cost | Workload Fit |
|--------|--------------|--------------|
| Burstable (t3/e2/B-series) | ~0.5x general | Dev, low-traffic, microservices |
| General purpose (m6i/n2/D-series) | 1x baseline | Web servers, APIs, standard apps |
| Compute optimized (c6i/c3/F-series) | ~1.2x general | CPU-bound, ML inference, encoding |
| Memory optimized (r6i/m3/E-series) | ~1.3x general | Databases, caches, analytics |
| ARM-based (m7g/t2a/Dps-series) | ~0.8x x86 equiv | Compatible workloads (20% savings) |
| GPU (p4/a2/NC-series) | ~5-20x general | ML training, rendering, HPC |

## Storage Tiers: Hot/Warm/Cold Cost Ratios

| Tier | Storage Cost | Retrieval Cost | Best For |
|------|-------------|----------------|----------|
| Hot (Standard/Standard/Hot) | 1x baseline | Free | Frequently accessed data |
| Warm (S3-IA/Nearline/Cool) | ~0.5x | Low per-GB | Monthly access patterns |
| Cold (Glacier IR/Coldline/Cold) | ~0.25x | Medium per-GB | Quarterly access |
| Archive (Glacier Deep/Archive/Archive) | ~0.1x | High + hours delay | Compliance, yearly access |

Block storage follows similar tiering: HDD (~0.3x) < General SSD (1x) < Provisioned IOPS (~3-5x).

## Cost Optimization Patterns

| Strategy | Savings | Commitment | Risk |
|----------|---------|------------|------|
| Right-sizing | 20-40% | None | Underprovisioning |
| Spot/Preemptible | 60-90% | None | 2-min interruption notice |
| Reserved (1yr) | ~35% | 1 year, specific instance | Inflexible |
| Reserved (3yr) | ~55% | 3 years, specific instance | Very inflexible |
| Savings Plans (1yr) | ~30% | 1 year, $/hr commit | Underutilization |
| Auto-scaling | 20-50% | Engineering effort | Cold start latency |
| ARM migration | ~20% | Compatibility testing | Application support |
| Storage lifecycle policies | 40-80% | Policy management | Retrieval latency |

## Serverless vs Containers vs VMs: Cost Decision Matrix

| Axis | Serverless (Lambda/Cloud Run) | Containers (EKS/GKE/AKS) | VMs (EC2/GCE) |
|------|-------------------------------|---------------------------|----------------|
| Idle cost | Near-zero (pay per invoke) | Control plane + min nodes | Full instance cost |
| At scale (steady) | Most expensive per-request | ~0.5-0.7x VM cost | 1x baseline |
| At scale (reserved) | No discount available | Node reservations apply | Best RI/SP savings |
| Burst cost | Linear with requests | Node autoscale lag | Manual/ASG lag |
| Ops overhead | Minimal | Medium (cluster mgmt) | High (OS patching) |

**When to choose:**
- **Serverless**: < 1M requests/month, spiky traffic, event-driven, prototype/MVP
- **Containers**: Steady traffic, microservices, need control over runtime, team knows K8s
- **VMs**: Legacy apps, license-bound software, bare-metal performance needs, stable predictable load with reservations

## Presentation Rules

- Always set a baseline row at 1x; express others as multipliers (~0.6x, ~2x)
- Include a trade-offs column explaining what changes with each option
- Add a recommendation summarizing decision factors
- State that these are approximate relative comparisons, not quotes
