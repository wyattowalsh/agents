# Terraform Patterns

## Contents

1. [Module Structure](#module-structure)
2. [Variable Design](#variable-design)
3. [Resource Patterns](#resource-patterns)
4. [State Management](#state-management)
5. [Provider Configuration](#provider-configuration)
6. [Naming Conventions](#naming-conventions)

---

## Module Structure

Standard module layout:

```
modules/<name>/
  main.tf          # Resource definitions
  variables.tf     # Input variables
  outputs.tf       # Output values
  versions.tf      # Provider requirements
  locals.tf        # Computed values (optional)
  data.tf          # Data sources (optional)
```

Root module layout:

```
environments/
  dev/
    main.tf        # Module calls + env-specific config
    backend.tf     # State backend config
    terraform.tfvars
  staging/
  production/
modules/           # Reusable modules
```

---

## Variable Design

### Typed variables with validation

```hcl
variable "environment" {
  description = "Deployment environment"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production."
  }
}

variable "instance_config" {
  description = "EC2 instance configuration"
  type = object({
    instance_type = string
    volume_size   = number
    encrypted     = optional(bool, true)
  })
}
```

### Variable naming conventions

- Boolean: `enable_*`, `is_*` prefix
- Count/sizing: `*_count`, `*_size`
- Names/IDs: `*_name`, `*_id`
- Lists: plural noun (`subnet_ids`, `security_group_ids`)

---

## Resource Patterns

### for_each over count

```hcl
# Prefer: addressable by name
resource "aws_subnet" "private" {
  for_each          = toset(var.availability_zones)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, index(var.availability_zones, each.value))
  availability_zone = each.value

  tags = merge(local.common_tags, {
    Name = "${var.project}-private-${each.value}"
    Tier = "private"
  })
}

# Avoid: indexed, fragile on reorder
resource "aws_subnet" "private" {
  count             = length(var.availability_zones)
  availability_zone = var.availability_zones[count.index]
}
```

### Common tags via locals

```hcl
locals {
  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
    Team        = var.team
  }
}
```

### Dynamic blocks

```hcl
resource "aws_security_group" "main" {
  name   = "${var.project}-sg"
  vpc_id = aws_vpc.main.id

  dynamic "ingress" {
    for_each = var.ingress_rules
    content {
      from_port   = ingress.value.port
      to_port     = ingress.value.port
      protocol    = ingress.value.protocol
      cidr_blocks = ingress.value.cidr_blocks
      description = ingress.value.description
    }
  }
}
```

### Lifecycle rules

```hcl
resource "aws_instance" "main" {
  # ...
  lifecycle {
    create_before_destroy = true        # Zero-downtime replacement
    prevent_destroy       = true        # Protect critical resources
    ignore_changes        = [tags["UpdatedAt"]]  # External tag management
  }
}
```

---

## State Management

### Remote backend (S3)

```hcl
terraform {
  backend "s3" {
    bucket         = "company-terraform-state"
    key            = "project/environment/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

### State management rules

- One state file per environment per service
- Enable encryption and locking
- Never commit `.tfstate` files
- Use `terraform state mv` for refactoring, never manual edits
- Import existing resources with `terraform import`

---

## Provider Configuration

### Version pinning

```hcl
terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.25"
    }
  }
}
```

### Multi-region / multi-account

```hcl
provider "aws" {
  region = var.region
  alias  = "primary"
}

provider "aws" {
  region = var.dr_region
  alias  = "dr"
}

resource "aws_s3_bucket" "replica" {
  provider = aws.dr
  bucket   = "${var.project}-replica"
}
```

---

## Naming Conventions

| Resource | Pattern | Example |
|----------|---------|---------|
| S3 bucket | `{project}-{purpose}-{env}` | `myapp-assets-prod` |
| IAM role | `{project}-{service}-{purpose}` | `myapp-lambda-executor` |
| Security group | `{project}-{tier}-sg` | `myapp-web-sg` |
| Subnet | `{project}-{tier}-{az}` | `myapp-private-us-east-1a` |
| Lambda | `{project}-{function}` | `myapp-process-orders` |
| RDS | `{project}-{purpose}-{env}` | `myapp-primary-prod` |

All names lowercase, hyphen-separated. No underscores in resource names that appear in URLs or DNS.
