# Multi-Cloud Resource Equivalents

## Contents

1. [Compute](#compute)
2. [Storage](#storage)
3. [Database](#database)
4. [Networking](#networking)
5. [Containers](#containers)
6. [Serverless](#serverless)
7. [Security and IAM](#security-and-iam)
8. [Monitoring](#monitoring)

---

## Compute

| Category | AWS | GCP | Azure |
|----------|-----|-----|-------|
| Virtual machine | EC2 | Compute Engine | Virtual Machines |
| Auto scaling group | ASG | MIG (Managed Instance Group) | VMSS (VM Scale Sets) |
| Spot/preemptible | Spot Instances | Spot VMs | Spot VMs |
| Dedicated host | Dedicated Hosts | Sole-tenant Nodes | Dedicated Hosts |
| Bare metal | Bare Metal (i3.metal) | Bare Metal Solution | Bare Metal |

### Instance family mapping

| Purpose | AWS | GCP | Azure |
|---------|-----|-----|-------|
| General purpose | m6i, m7g | e2, n2 | D-series |
| Compute optimized | c6i, c7g | c2, c3 | F-series |
| Memory optimized | r6i, r7g | m2, m3 | E-series |
| GPU | p4, g5 | a2, g2 | NC, ND-series |
| ARM | m7g, c7g | t2a | Dps-series |

---

## Storage

| Category | AWS | GCP | Azure |
|----------|-----|-----|-------|
| Object storage | S3 | Cloud Storage | Blob Storage |
| Block storage | EBS | Persistent Disk | Managed Disks |
| File storage (NFS) | EFS | Filestore | Azure Files |
| Archive | S3 Glacier | Archive Storage | Archive Storage |
| CDN | CloudFront | Cloud CDN | Azure CDN / Front Door |

### Storage tier mapping

| Tier | AWS S3 | GCP Cloud Storage | Azure Blob |
|------|--------|-------------------|------------|
| Hot (frequent) | Standard | Standard | Hot |
| Warm (infrequent) | S3-IA | Nearline | Cool |
| Cold (rare) | S3 Glacier IR | Coldline | Cold |
| Archive | Glacier Deep | Archive | Archive |

---

## Database

| Category | AWS | GCP | Azure |
|----------|-----|-----|-------|
| Relational (managed) | RDS | Cloud SQL | Azure SQL / Flexible Server |
| Relational (serverless) | Aurora Serverless | AlloyDB | Azure SQL Serverless |
| NoSQL document | DynamoDB | Firestore | Cosmos DB |
| NoSQL key-value | ElastiCache (Redis) | Memorystore | Azure Cache for Redis |
| Graph | Neptune | -- | Cosmos DB (Gremlin) |
| Time series | Timestream | Bigtable | Azure Data Explorer |
| Data warehouse | Redshift | BigQuery | Synapse Analytics |

---

## Networking

| Category | AWS | GCP | Azure |
|----------|-----|-----|-------|
| Virtual network | VPC | VPC | VNet |
| Subnet | Subnet | Subnet | Subnet |
| Load balancer (L7) | ALB | Cloud Load Balancing (HTTP) | Application Gateway |
| Load balancer (L4) | NLB | Cloud Load Balancing (TCP) | Azure Load Balancer |
| DNS | Route 53 | Cloud DNS | Azure DNS |
| VPN | Site-to-Site VPN | Cloud VPN | VPN Gateway |
| Private link | PrivateLink | Private Service Connect | Private Link |
| Firewall | Security Groups + NACLs | Firewall Rules | NSG + Azure Firewall |
| Transit/hub | Transit Gateway | Network Connectivity Center | Virtual WAN |

---

## Containers

| Category | AWS | GCP | Azure |
|----------|-----|-----|-------|
| Managed Kubernetes | EKS | GKE | AKS |
| Container registry | ECR | Artifact Registry | ACR |
| Serverless containers | Fargate | Cloud Run | Container Apps |
| Container orchestration | ECS | -- | Container Instances |

---

## Serverless

| Category | AWS | GCP | Azure |
|----------|-----|-----|-------|
| Functions | Lambda | Cloud Functions | Azure Functions |
| API Gateway | API Gateway | API Gateway | API Management |
| Event bus | EventBridge | Eventarc | Event Grid |
| Message queue | SQS | Pub/Sub | Service Bus |
| Workflow | Step Functions | Workflows | Logic Apps |

---

## Security and IAM

| Category | AWS | GCP | Azure |
|----------|-----|-----|-------|
| IAM | IAM (users, roles, policies) | IAM (members, roles, bindings) | Entra ID + RBAC |
| Secret manager | Secrets Manager | Secret Manager | Key Vault |
| Key management | KMS | Cloud KMS | Key Vault |
| Certificate manager | ACM | Certificate Manager | App Service Certificates |
| Web application firewall | WAF | Cloud Armor | WAF |
| Identity federation | IAM Identity Center (SSO) | Workforce Identity | Entra External ID |
| Workload identity | IRSA / Pod Identity | Workload Identity | Workload Identity |

---

## Monitoring

| Category | AWS | GCP | Azure |
|----------|-----|-----|-------|
| Metrics | CloudWatch | Cloud Monitoring | Azure Monitor |
| Logs | CloudWatch Logs | Cloud Logging | Log Analytics |
| Traces | X-Ray | Cloud Trace | Application Insights |
| Alerting | CloudWatch Alarms | Alerting Policies | Azure Alerts |
| Dashboard | CloudWatch Dashboards | Custom Dashboards | Azure Dashboards |
