# Pipeline Review Checklist

## Contents

1. [Security](#security)
2. [Reliability](#reliability)
3. [Performance](#performance)
4. [Maintainability](#maintainability)
5. [Cost](#cost)

---

## Security

### Actions and Dependencies

- [ ] All third-party actions pinned to full SHA (not version tags)
- [ ] No `pull_request_target` with checkout of PR head (script injection)
- [ ] No inline expansion of user-controlled inputs in `run:` blocks
- [ ] No `actions/github-script` with untrusted PR data

### Permissions

- [ ] Explicit `permissions` block at top level (not relying on defaults)
- [ ] Per-job permissions granted (principle of least privilege)
- [ ] No `permissions: write-all`
- [ ] `id-token: write` only when OIDC auth is used

### Secrets

- [ ] No hardcoded secrets, tokens, or API keys
- [ ] Secrets passed via `${{ secrets.NAME }}`, not environment variables
- [ ] Environment-scoped secrets for deployment workflows
- [ ] No secrets logged (check for `echo $SECRET` patterns)

### Supply Chain

- [ ] Dependency lockfiles committed and verified
- [ ] `npm ci` (not `npm install`) for reproducible installs
- [ ] Container images use specific tags (not `latest`)
- [ ] Artifact provenance enabled for released packages

---

## Reliability

### Timeouts and Retries

- [ ] `timeout-minutes` set on every job
- [ ] Network-dependent steps have retry logic
- [ ] No unbounded wait/poll loops
- [ ] Reasonable timeout values (not excessively long or short)

### Concurrency

- [ ] `concurrency` group defined for PR and deployment workflows
- [ ] `cancel-in-progress: true` for PR workflows
- [ ] `cancel-in-progress: false` for deployment workflows (prevent half-deploys)
- [ ] No race conditions between parallel jobs writing to same resource

### Error Handling

- [ ] Deployment jobs have rollback steps on failure
- [ ] `continue-on-error` used intentionally (not to mask failures)
- [ ] `fail-fast: false` for matrix jobs where partial success is useful
- [ ] Critical post-deploy verification steps present

### Triggers

- [ ] Appropriate trigger events (not overly broad)
- [ ] Branch filters match protection rules
- [ ] Schedule cron expressions are correct (validated)
- [ ] `workflow_dispatch` available for manual runs

---

## Performance

### Caching

- [ ] Dependency caching enabled (setup-node cache, actions/cache, etc.)
- [ ] Cache keys use lockfile hashes for precise invalidation
- [ ] `restore-keys` provide fallback for partial cache hits
- [ ] Build artifact caching for incremental builds
- [ ] Docker layer caching for container builds

### Parallelization

- [ ] Independent jobs run in parallel (not unnecessarily sequential)
- [ ] Test suites sharded across parallel runners
- [ ] `needs` used for DAG execution instead of stage-only ordering
- [ ] No unnecessary dependencies between jobs

### Selective Execution

- [ ] Path filters skip CI for irrelevant changes (docs, config)
- [ ] Monorepo workflows only build affected packages
- [ ] Expensive jobs (E2E, integration) gated behind fast checks (lint, unit)
- [ ] Matrix strategy avoids unnecessary combinations

---

## Maintainability

### Structure

- [ ] Reusable workflows or composite actions for shared logic
- [ ] No copy-pasted steps across multiple workflow files
- [ ] Clear job and step naming (descriptive `name:` fields)
- [ ] Logical stage/job ordering matching the build pipeline

### Documentation

- [ ] Non-obvious configuration choices have inline comments
- [ ] Workflow purpose documented in file-level comments
- [ ] Required secrets and variables documented
- [ ] Manual dispatch inputs have descriptions

### Versioning

- [ ] Tool versions pinned (Node.js, Python, etc.)
- [ ] Version source is a single file (.node-version, .python-version, .tool-versions)
- [ ] Action versions tracked and updatable (Dependabot/Renovate configured)

---

## Cost

### Runner Usage

- [ ] Appropriate runner size for workload (not over-provisioned)
- [ ] macOS/Windows runners only used when necessary
- [ ] No idle wait times between steps
- [ ] Self-hosted runners justified by cost analysis

### Artifact Retention

- [ ] Intermediate artifacts expire quickly (1-3 days)
- [ ] Release artifacts have appropriate retention (30-90 days)
- [ ] No unnecessary artifacts uploaded
- [ ] Artifact compression enabled

### Matrix Efficiency

- [ ] Matrix combinations are justified (not testing every permutation)
- [ ] Expensive OS variants limited to minimum necessary versions
- [ ] `fail-fast` strategy appropriate for the use case
- [ ] Conditional matrix includes/excludes reduce waste
