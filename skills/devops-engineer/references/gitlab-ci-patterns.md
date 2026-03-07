# GitLab CI Patterns

## Contents

1. [Pipeline Structure](#pipeline-structure)
2. [Includes and Templates](#includes-and-templates)
3. [Rules and Conditions](#rules-and-conditions)
4. [Caching](#caching)
5. [Environments and Deployment](#environments-and-deployment)
6. [Artifacts](#artifacts)
7. [Security](#security)

---

## Pipeline Structure

Standard `.gitlab-ci.yml` skeleton:

```yaml
default:
  image: node:20-slim
  interruptible: true

stages:
  - build
  - test
  - deploy

variables:
  NODE_ENV: production
  FF_USE_FASTZIP: "true"  # Faster artifact handling

build:
  stage: build
  script:
    - npm ci --cache .npm
    - npm run build
  cache:
    key: $CI_COMMIT_REF_SLUG
    paths:
      - .npm/
      - node_modules/
  artifacts:
    paths:
      - dist/
    expire_in: 1 hour

test:
  stage: test
  needs: [build]
  parallel: 3
  script:
    - npm run test -- --shard=$CI_NODE_INDEX/$CI_NODE_TOTAL
  coverage: '/Statements\s*:\s*(\d+\.?\d*)%/'

deploy:staging:
  stage: deploy
  environment:
    name: staging
    url: https://staging.example.com
  script:
    - ./deploy.sh staging
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

Key elements:
- `interruptible: true` in defaults -- cancel stale pipelines
- `needs` for DAG-based execution (not just stage ordering)
- `parallel` for test sharding
- Short `expire_in` for intermediate artifacts
- `rules` over `only/except` (deprecated)

---

## Includes and Templates

### Local includes

```yaml
include:
  - local: .gitlab/ci/build.yml
  - local: .gitlab/ci/deploy.yml
```

### Remote templates

```yaml
include:
  - project: 'group/ci-templates'
    ref: v2.0.0
    file: '/templates/node.yml'
```

### Hidden jobs as templates

```yaml
.deploy_template:
  stage: deploy
  image: bitnami/kubectl:latest
  before_script:
    - kubectl config use-context $KUBE_CONTEXT
  script:
    - kubectl apply -f k8s/

deploy:staging:
  extends: .deploy_template
  environment:
    name: staging
  variables:
    KUBE_CONTEXT: staging-cluster

deploy:production:
  extends: .deploy_template
  environment:
    name: production
  variables:
    KUBE_CONTEXT: production-cluster
  when: manual
```

---

## Rules and Conditions

### Branch rules

```yaml
rules:
  - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
  - if: $CI_COMMIT_TAG
```

### Path-based rules

```yaml
rules:
  - changes:
      paths:
        - backend/**/*
        - shared/**/*
    when: always
  - when: never
```

### Manual gates

```yaml
deploy:production:
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: manual
      allow_failure: false  # Block pipeline until approved
```

---

## Caching

### Dependency cache

```yaml
cache:
  key:
    files:
      - package-lock.json  # Cache key from lockfile hash
  paths:
    - node_modules/
  policy: pull-push  # Default: read and write
```

### Cache per branch with fallback

```yaml
cache:
  key: $CI_COMMIT_REF_SLUG
  paths:
    - .cache/
  fallback_keys:
    - $CI_DEFAULT_BRANCH
    - default
```

### Read-only cache for test jobs

```yaml
test:
  cache:
    key: $CI_COMMIT_REF_SLUG
    paths:
      - node_modules/
    policy: pull  # Never writes -- faster
```

---

## Environments and Deployment

### Review apps

```yaml
deploy:review:
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    url: https://$CI_COMMIT_REF_SLUG.review.example.com
    on_stop: stop:review
    auto_stop_in: 1 week
  rules:
    - if: $CI_MERGE_REQUEST_IID

stop:review:
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    action: stop
  script:
    - ./teardown-review.sh
  when: manual
```

### Incremental rollout

```yaml
.rollout:
  stage: deploy
  script:
    - kubectl set image deployment/app app=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - kubectl rollout status deployment/app

deploy:10%:
  extends: .rollout
  environment:
    name: production
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: manual

deploy:50%:
  extends: .rollout
  needs: [deploy:10%]
  when: manual

deploy:100%:
  extends: .rollout
  needs: [deploy:50%]
  when: manual
```

---

## Artifacts

### Build artifacts

```yaml
artifacts:
  paths:
    - dist/
    - coverage/
  reports:
    junit: test-results.xml
    coverage_report:
      coverage_format: cobertura
      path: coverage/cobertura.xml
  expire_in: 7 days
```

### Passing between jobs

```yaml
build:
  artifacts:
    paths:
      - dist/

test:
  needs:
    - job: build
      artifacts: true
```

---

## Security

### Protected variables

- Use Settings > CI/CD > Variables with "Protected" flag
- Protected variables only available on protected branches/tags
- Mask variables to hide from logs

### Container scanning

```yaml
include:
  - template: Security/Container-Scanning.gitlab-ci.yml
  - template: Security/SAST.gitlab-ci.yml
  - template: Security/Dependency-Scanning.gitlab-ci.yml
```

### Restrict runner access

```yaml
deploy:production:
  tags:
    - production-runner  # Only runs on tagged runners
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: manual
```
