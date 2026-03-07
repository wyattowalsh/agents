# Pipeline Optimization Techniques

## Contents

1. [Caching Strategies](#caching-strategies)
2. [Parallelization](#parallelization)
3. [Selective Runs](#selective-runs)
4. [Matrix Optimization](#matrix-optimization)
5. [Docker Build Optimization](#docker-build-optimization)
6. [Runner Selection](#runner-selection)
7. [Artifact Management](#artifact-management)

---

## Caching Strategies

### Dependency caching

| Tool | Cache Path | Key Source |
|------|-----------|-----------|
| npm | `~/.npm` | `package-lock.json` |
| yarn | `~/.yarn/cache` | `yarn.lock` |
| pnpm | `~/.pnpm-store` | `pnpm-lock.yaml` |
| pip | `~/.cache/pip` | `requirements*.txt` |
| uv | `~/.cache/uv` | `uv.lock` |
| cargo | `~/.cargo/registry`, `target/` | `Cargo.lock` |
| go | `~/go/pkg/mod` | `go.sum` |
| gradle | `~/.gradle/caches` | `*.gradle*`, `gradle-wrapper.properties` |
| maven | `~/.m2/repository` | `pom.xml` |

### Build artifact caching

Cache compiled outputs between runs:
- TypeScript: `tsconfig.tsbuildinfo`
- Turbo: `.turbo/`
- Nx: `.nx/cache`
- Next.js: `.next/cache`
- Webpack: `node_modules/.cache`

### Cache key strategy

```yaml
key: ${{ runner.os }}-${{ hashFiles('lockfile') }}
restore-keys: |
  ${{ runner.os }}-    # Fallback to any OS cache
```

Use `restore-keys` for partial cache hits. Better to restore a stale cache and update than start fresh.

### Expected savings

| Cache type | Typical savings |
|-----------|----------------|
| Dependency (npm, pip) | 30-60% of install step |
| Build artifact | 40-70% of build step |
| Docker layers | 50-80% of Docker build |
| Test fixtures | 10-20% of test setup |

---

## Parallelization

### Job-level parallelism

Split independent work into separate jobs:

```yaml
jobs:
  lint:     # ~1min
    steps: [checkout, setup, lint]
  typecheck: # ~2min
    steps: [checkout, setup, tsc]
  test:      # ~5min
    steps: [checkout, setup, test]
  # All run in parallel: wall time = max(1, 2, 5) = 5min
```

### Test sharding

Split test suites across parallel runners:

```yaml
# GitHub Actions
test:
  strategy:
    matrix:
      shard: [1, 2, 3, 4]
  steps:
    - run: npm test -- --shard=${{ matrix.shard }}/4

# GitLab CI
test:
  parallel: 4
  script:
    - npm test -- --shard=$CI_NODE_INDEX/$CI_NODE_TOTAL
```

### Monorepo workspace parallelism

Detect changed packages and only build/test affected:

```yaml
- uses: dorny/paths-filter@<sha>
  id: changes
  with:
    filters: |
      api: ['packages/api/**']
      web: ['packages/web/**']
      shared: ['packages/shared/**']

# Rebuild shared + dependents
- if: steps.changes.outputs.shared == 'true'
  run: npm run build --workspace=shared && npm run build --workspaces
```

---

## Selective Runs

### Path filters

Skip unnecessary CI when only docs or config changed:

```yaml
on:
  push:
    paths-ignore:
      - '**.md'
      - 'docs/**'
      - '.github/ISSUE_TEMPLATE/**'
      - 'LICENSE'
      - '.editorconfig'
```

### Skip CI

Respect conventional skip markers:

```yaml
jobs:
  build:
    if: |
      !contains(github.event.head_commit.message, '[skip ci]') &&
      !contains(github.event.head_commit.message, '[ci skip]')
```

### Changed-file-based test selection

```yaml
- id: changed
  run: |
    FILES=$(git diff --name-only HEAD~1)
    echo "files=$FILES" >> $GITHUB_OUTPUT

- if: contains(steps.changed.outputs.files, 'src/')
  run: npm run test:unit

- if: contains(steps.changed.outputs.files, 'e2e/')
  run: npm run test:e2e
```

---

## Matrix Optimization

### Minimize matrix size

```yaml
strategy:
  matrix:
    # Only test OS variants on the primary Node version
    include:
      - os: ubuntu-latest
        node: 18
      - os: ubuntu-latest
        node: 20
      - os: ubuntu-latest
        node: 22
      - os: macos-latest
        node: 20   # Only latest on macOS
      - os: windows-latest
        node: 20   # Only latest on Windows
  fail-fast: false
```

### Separate fast and slow matrix jobs

```yaml
# Fast: lint + typecheck (no matrix needed)
lint:
  runs-on: ubuntu-latest
  steps: [checkout, setup, lint, typecheck]

# Slow: test across versions (matrix)
test:
  needs: lint  # Only if lint passes
  strategy:
    matrix:
      node: [18, 20, 22]
```

---

## Docker Build Optimization

### Multi-stage builds

```dockerfile
# Stage 1: Dependencies only (cached until lockfile changes)
FROM node:20-slim AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --production

# Stage 2: Build (cached until source changes)
FROM node:20-slim AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Stage 3: Runtime (minimal image)
FROM gcr.io/distroless/nodejs20
COPY --from=build /app/dist /app/dist
COPY --from=deps /app/node_modules /app/node_modules
CMD ["app/dist/index.js"]
```

### BuildKit cache mounts

```dockerfile
RUN --mount=type=cache,target=/root/.npm \
    npm ci --production
```

### GitHub Actions Docker caching

```yaml
- uses: docker/build-push-action@<sha>
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

---

## Runner Selection

| Workload | Recommended Runner | Rationale |
|----------|-------------------|-----------|
| Lint, format check | `ubuntu-latest` (default) | Low resource needs |
| Unit tests | `ubuntu-latest` | Sufficient for most test suites |
| Large build (monorepo) | `ubuntu-latest-4-core` | More CPU for parallel compilation |
| Docker build | `ubuntu-latest` + BuildKit | Layer caching offsets build time |
| iOS build | `macos-latest` | Required by Xcode |
| E2E tests | `ubuntu-latest-4-core` | Browser automation needs more resources |
| Security scanning | `ubuntu-latest` | Standard resource needs |

### Cost considerations

- macOS runners cost ~10x Linux runners
- Larger runners cost proportionally more but often save total minutes
- Self-hosted runners: zero GitHub billing but operational overhead

---

## Artifact Management

### Retention policies

```yaml
- uses: actions/upload-artifact@<sha>
  with:
    name: build-output
    path: dist/
    retention-days: 1   # Intermediate: keep 1 day
    # retention-days: 90  # Release: keep 90 days
```

### Minimize artifact size

```yaml
- uses: actions/upload-artifact@<sha>
  with:
    path: |
      dist/
      !dist/**/*.map    # Exclude source maps
      !dist/**/*.d.ts   # Exclude type declarations
    compression-level: 9  # Max compression
```

### Avoid unnecessary artifact uploads

Only upload when downstream jobs need the output. If all steps run in one job, artifacts are unnecessary overhead.
