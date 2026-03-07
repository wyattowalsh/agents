# GitHub Actions Patterns

## Contents

1. [Workflow Structure](#workflow-structure)
2. [Reusable Workflows](#reusable-workflows)
3. [Composite Actions](#composite-actions)
4. [Caching Patterns](#caching-patterns)
5. [Security Hardening](#security-hardening)
6. [Common Triggers](#common-triggers)
7. [Environment and Secrets](#environment-and-secrets)
8. [Artifact Patterns](#artifact-patterns)
9. [Conditional Execution](#conditional-execution)

---

## Workflow Structure

Standard CI workflow skeleton:

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions: {}  # Start with no permissions

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@<sha>
      - uses: actions/setup-node@<sha>
        with:
          node-version-file: '.node-version'
          cache: 'npm'
      - run: npm ci
      - run: npm test
      - run: npm run build
```

Key elements:
- Explicit `permissions: {}` at top level, grant per-job
- `concurrency` prevents redundant runs
- `timeout-minutes` on every job
- SHA-pinned actions
- `node-version-file` over hardcoded version

---

## Reusable Workflows

Caller workflow:

```yaml
jobs:
  deploy:
    uses: ./.github/workflows/deploy-template.yml
    with:
      environment: staging
    secrets: inherit  # Or pass explicitly
```

Called workflow (template):

```yaml
on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string
    secrets:
      DEPLOY_KEY:
        required: true

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    steps:
      - uses: actions/checkout@<sha>
      - run: ./deploy.sh
        env:
          DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
```

When to use:
- Same deployment logic across multiple environments
- Shared CI steps across multiple repositories (via repo reference)
- Standardized release process

---

## Composite Actions

`.github/actions/setup/action.yml`:

```yaml
name: Setup
description: Install dependencies with caching
inputs:
  node-version:
    default: '20'
runs:
  using: composite
  steps:
    - uses: actions/setup-node@<sha>
      with:
        node-version: ${{ inputs.node-version }}
        cache: 'npm'
    - run: npm ci
      shell: bash
```

Usage: `uses: ./.github/actions/setup`

When to use:
- 3+ workflows share the same setup steps
- Complex setup that should be tested independently

---

## Caching Patterns

### Dependency cache (built-in)

```yaml
- uses: actions/setup-node@<sha>
  with:
    cache: 'npm'  # Also: yarn, pnpm
```

### Custom cache

```yaml
- uses: actions/cache@<sha>
  with:
    path: |
      ~/.cache/pip
      .venv
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

### Docker layer cache

```yaml
- uses: docker/build-push-action@<sha>
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

### Turbo/Nx cache

```yaml
- uses: actions/cache@<sha>
  with:
    path: .turbo
    key: ${{ runner.os }}-turbo-${{ github.sha }}
    restore-keys: |
      ${{ runner.os }}-turbo-
```

---

## Security Hardening

### Pin actions to SHA

```yaml
# Bad: uses: actions/checkout@v4
# Good:
uses: actions/checkout@<full-40-char-sha>
```

### Minimal permissions

```yaml
permissions:
  contents: read
  pull-requests: write  # Only if needed
```

### Prevent script injection

```yaml
# Bad: run: echo "${{ github.event.pull_request.title }}"
# Good:
- run: echo "$TITLE"
  env:
    TITLE: ${{ github.event.pull_request.title }}
```

### OIDC for cloud auth (no long-lived secrets)

```yaml
permissions:
  id-token: write
  contents: read

- uses: aws-actions/configure-aws-credentials@<sha>
  with:
    role-to-assume: arn:aws:iam::123456789:role/deploy
    aws-region: us-east-1
```

---

## Common Triggers

### Path-filtered builds

```yaml
on:
  push:
    paths:
      - 'src/**'
      - 'package.json'
      - '.github/workflows/ci.yml'
    paths-ignore:
      - '**.md'
      - 'docs/**'
```

### Schedule

```yaml
on:
  schedule:
    - cron: '0 6 * * 1'  # Monday 6am UTC
```

### Manual dispatch

```yaml
on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        type: choice
        options: [staging, production]
```

---

## Environment and Secrets

### Environment protection rules

```yaml
jobs:
  deploy:
    environment:
      name: production
      url: https://example.com
    # Requires manual approval configured in repo settings
```

### Secret scoping

- Repository secrets: available to all workflows
- Environment secrets: available only to jobs targeting that environment
- Organization secrets: shared across repos with policy

### Dynamic secrets

```yaml
- uses: hashicorp/vault-action@<sha>
  with:
    url: ${{ secrets.VAULT_URL }}
    method: jwt
    role: deploy
    secrets: |
      secret/data/deploy api_key | API_KEY
```

---

## Artifact Patterns

### Pass artifacts between jobs

```yaml
jobs:
  build:
    steps:
      - run: npm run build
      - uses: actions/upload-artifact@<sha>
        with:
          name: dist
          path: dist/
          retention-days: 1  # Short for intermediate artifacts

  deploy:
    needs: build
    steps:
      - uses: actions/download-artifact@<sha>
        with:
          name: dist
          path: dist/
```

### Release artifacts

```yaml
- uses: actions/upload-artifact@<sha>
  with:
    name: release-${{ github.sha }}
    path: dist/
    retention-days: 90  # Longer for release artifacts
```

---

## Conditional Execution

### Skip on certain conditions

```yaml
jobs:
  deploy:
    if: github.ref == 'refs/heads/main' && !contains(github.event.head_commit.message, '[skip ci]')
```

### Matrix with exclude/include

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest]
    node: [18, 20, 22]
    exclude:
      - os: macos-latest
        node: 18
    include:
      - os: ubuntu-latest
        node: 22
        experimental: true
  fail-fast: false  # Don't cancel other jobs on failure
```

### Changed files detection

```yaml
- uses: dorny/paths-filter@<sha>
  id: changes
  with:
    filters: |
      backend:
        - 'backend/**'
      frontend:
        - 'frontend/**'

- if: steps.changes.outputs.backend == 'true'
  run: npm run test:backend
```
