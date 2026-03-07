# IaC Security Hardening Reference

## Terraform Security

- **State**: Encrypted remote backend (S3+DynamoDB, GCS, azurerm) with state locking. Never local state in prod
- **Sensitive vars**: Mark `sensitive = true`. Never log or output them. Use env vars or OIDC for provider creds

```hcl
terraform {
  backend "s3" {
    bucket = "tfstate-prod"
    key    = "infra/terraform.tfstate"
    encrypt = true
    dynamodb_table = "tfstate-lock"
  }
}
variable "db_password" { type = string; sensitive = true }
```

## Kubernetes Security

**Pod Security**: Enforce `restricted` profile via namespace labels. **RBAC**: Scope roles to specific namespaces/verbs, never `cluster-admin` for workloads. **Network Policies**: Default deny all, then allow specific traffic. **Secrets**: External Secrets Operator or Sealed Secrets, not plain K8s Secrets in git. Set `automountServiceAccountToken: false` unless needed.

```yaml
# Namespace-level enforcement
metadata:
  labels: { pod-security.kubernetes.io/enforce: restricted }
---
# Default deny all traffic
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: default-deny-all }
spec: { podSelector: {}, policyTypes: ["Ingress", "Egress"] }
---
# Least-privilege RBAC
rules:
  - apiGroups: [""]
    resources: ["pods", "services"]
    verbs: ["get", "list", "watch"]
```

## Docker Security

Use distroless or minimal bases. Always set non-root USER. Pin image tags (or digests for prod).

```dockerfile
FROM python:3.12-slim AS runtime
RUN groupadd -r app && useradd -r -g app app
COPY --from=builder /app /app
USER app:app
```

Essential container `securityContext` in K8s manifests:

```yaml
securityContext:
  runAsNonRoot: true
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities: { drop: ["ALL"] }
  seccompProfile: { type: RuntimeDefault }
```

## Cloud IAM Best Practices

- **Least privilege**: Start with zero permissions, add only what is needed
- **Service accounts**: One per workload, never shared. Use workload identity (IRSA/Workload Identity/Managed Identity) over static keys
- **No wildcards**: Never `"Action": "*"` on `"Resource": "*"` in production
- **Role boundaries**: Permission boundaries (AWS) or deny policies (GCP) to cap delegated roles
- **Conditions**: Restrict by source IP, VPC, MFA, or principal tags

```json
{ "Effect": "Allow", "Action": ["s3:GetObject"], "Resource": "arn:aws:s3:::bucket/data/*",
  "Condition": {"StringEquals": {"aws:PrincipalTag/team": "backend"}} }
```

## Common Misconfigurations by Severity

| Severity | Misconfiguration | Impact |
|----------|-----------------|--------|
| **Critical** | `0.0.0.0/0` on SSH/RDP ports | Direct remote exploitation |
| **Critical** | Plaintext secrets in IaC | Credential exposure in VCS |
| **Critical** | `privileged: true` containers | Full host access, escape |
| **Critical** | Wildcard IAM (`*`/`*`) | Unrestricted account control |
| **High** | Unencrypted storage at rest | Data exposure |
| **High** | No K8s resource limits | Node exhaustion, DoS |
| **High** | `latest` image tag in prod | Supply chain risk |
| **High** | Root user in Dockerfile | Elevated escape privileges |
| **Medium** | Missing network policies | Unrestricted pod traffic |
| **Medium** | Shared service accounts | Blast radius, audit gaps |
| **Medium** | No audit logging | Undetectable security events |
| **Low** | Missing resource tags | Cost/ownership tracking gaps |
| **Low** | No pod disruption budgets | Availability risk on upgrades |
