# Dockerfile Optimization Guide

## Contents

1. [Multi-Stage Builds](#multi-stage-builds)
2. [Layer Optimization](#layer-optimization)
3. [Base Image Selection](#base-image-selection)
4. [Security Hardening](#security-hardening)
5. [Language-Specific Patterns](#language-specific-patterns)

---

## Multi-Stage Builds

### Pattern: build + runtime separation

```dockerfile
# Stage 1: Build
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci --production=false
COPY . .
RUN npm run build

# Stage 2: Runtime
FROM node:20-alpine AS runtime
WORKDIR /app
RUN addgroup -g 1001 appgroup && adduser -u 1001 -G appgroup -s /bin/sh -D appuser
COPY --from=build --chown=appuser:appgroup /app/dist ./dist
COPY --from=build --chown=appuser:appgroup /app/node_modules ./node_modules
COPY --from=build --chown=appuser:appgroup /app/package.json ./
USER appuser
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

### Pattern: distroless runtime

```dockerfile
FROM golang:1.22 AS build
WORKDIR /app
COPY go.* ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /server

FROM gcr.io/distroless/static-debian12
COPY --from=build /server /server
USER nonroot:nonroot
ENTRYPOINT ["/server"]
```

---

## Layer Optimization

### Order by change frequency

```dockerfile
# Least likely to change (cached longest)
FROM python:3.12-slim
WORKDIR /app

# System dependencies (rare changes)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies (moderate changes)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Application code (frequent changes)
COPY . .

CMD ["python", "app.py"]
```

### Combine RUN commands

```dockerfile
# Bad: multiple layers
RUN apt-get update
RUN apt-get install -y curl
RUN rm -rf /var/lib/apt/lists/*

# Good: single layer, clean up in same layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*
```

### Use .dockerignore

```
.git
node_modules
*.md
.env*
docker-compose*.yml
Dockerfile*
.dockerignore
__pycache__
.pytest_cache
dist
build
```

---

## Base Image Selection

| Use case | Image | Size | Notes |
|----------|-------|------|-------|
| Go/Rust (static binary) | `gcr.io/distroless/static` | ~2MB | No shell, minimal attack surface |
| Node.js | `node:20-alpine` | ~130MB | Good balance of size and compatibility |
| Python | `python:3.12-slim` | ~150MB | Avoid full image (~1GB) |
| Java | `eclipse-temurin:21-jre-alpine` | ~150MB | JRE only, not JDK |
| General minimal | `alpine:3.19` | ~7MB | Requires manual dependency management |
| Debugging | `busybox` or `ubuntu:24.04` | varies | Development only |

### Tag rules

- Always use specific version tags: `node:20.11.0-alpine3.19`
- Never use `latest` — unpredictable builds
- Pin to digest for maximum reproducibility: `node@sha256:abc...`
- Use `.0` minor versions for stability, `.x` for latest patches

---

## Security Hardening

### Non-root user

```dockerfile
RUN addgroup -g 1001 appgroup && \
    adduser -u 1001 -G appgroup -s /bin/sh -D appuser
USER appuser
```

### Read-only filesystem

```dockerfile
# Application writes to /tmp only
RUN mkdir -p /tmp/app-cache && chown appuser:appgroup /tmp/app-cache
VOLUME ["/tmp/app-cache"]
```

### No secrets in layers

```dockerfile
# Bad: secret visible in layer history
COPY .env /app/.env

# Good: use build args for build-time secrets
ARG NPM_TOKEN
RUN echo "//registry.npmjs.org/:_authToken=${NPM_TOKEN}" > .npmrc && \
    npm ci && \
    rm .npmrc

# Better: use Docker BuildKit secrets
RUN --mount=type=secret,id=npm_token \
    NPM_TOKEN=$(cat /run/secrets/npm_token) npm ci
```

### Scan for vulnerabilities

```bash
# Trivy
trivy image myapp:latest

# Grype
grype myapp:latest

# Docker Scout
docker scout cves myapp:latest
```

---

## Language-Specific Patterns

### Python

```dockerfile
FROM python:3.12-slim AS build
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .

FROM python:3.12-slim
WORKDIR /app
RUN adduser --system --group appuser
COPY --from=build /app/.venv /app/.venv
COPY --from=build /app .
ENV PATH="/app/.venv/bin:$PATH"
USER appuser
CMD ["python", "-m", "app"]
```

### Go

```dockerfile
FROM golang:1.22-alpine AS build
WORKDIR /app
COPY go.* ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /server ./cmd/server

FROM gcr.io/distroless/static-debian12
COPY --from=build /server /server
USER nonroot:nonroot
EXPOSE 8080
ENTRYPOINT ["/server"]
```

### Node.js

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build && npm prune --production

FROM node:20-alpine
WORKDIR /app
RUN addgroup -g 1001 appgroup && adduser -u 1001 -G appgroup -s /bin/sh -D appuser
COPY --from=build --chown=appuser:appgroup /app/dist ./dist
COPY --from=build --chown=appuser:appgroup /app/node_modules ./node_modules
COPY --from=build --chown=appuser:appgroup /app/package.json ./
USER appuser
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

### Java

```dockerfile
FROM eclipse-temurin:21-jdk-alpine AS build
WORKDIR /app
COPY gradle* ./
COPY build.gradle* settings.gradle* ./
RUN gradle dependencies --no-daemon
COPY src ./src
RUN gradle bootJar --no-daemon

FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
RUN addgroup -g 1001 appgroup && adduser -u 1001 -G appgroup -s /bin/sh -D appuser
COPY --from=build /app/build/libs/*.jar app.jar
USER appuser
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```
