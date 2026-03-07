# Artifact Management Patterns

## Passing Artifacts Between Jobs

### GitHub Actions

```yaml
jobs:
  build:
    steps:
      - run: npm run build
      - uses: actions/upload-artifact@<sha>
        with:
          name: dist-${{ github.sha }}
          path: dist/
          retention-days: 1
  test:
    needs: build
    steps:
      - uses: actions/download-artifact@<sha>
        with:
          name: dist-${{ github.sha }}
      - run: npm test
```

### GitLab CI

```yaml
build:
  artifacts:
    paths: [dist/]
    expire_in: 1 hour
test:
  needs:
    - job: build
      artifacts: true
```

Best practices: upload once / download many; name uniquely in matrix jobs (`dist-${{ matrix.os }}`); exclude source maps and type declarations; use `compression-level: 9` for large artifacts.

## Retention Policies

| Context | Retention | Rationale |
|---------|-----------|-----------|
| PR check artifacts | 1 day | Only needed during review |
| Main branch builds | 7 days | Debug window for recent deploys |
| Release artifacts / SBOMs | 90+ days | Rollback and audit trail |
| Test reports (JUnit, coverage) | 14 days | Trend analysis |
| Failure diagnostics | 7 days | Investigation window |

**Keep long-term:** release binaries, signed packages, compliance artifacts. **Expire quickly:** intermediate build outputs, PR previews, lint reports.

## Environment Promotion

Build once, deploy the same artifact everywhere. Configuration differences come from environment variables, not separate builds.

```yaml
jobs:
  build:
    outputs:
      image-tag: ${{ steps.meta.outputs.tag }}
    steps:
      - id: meta
        run: echo "tag=sha-${GITHUB_SHA::8}" >> $GITHUB_OUTPUT
      - run: |
          docker build -t registry.example.com/app:${{ steps.meta.outputs.tag }} .
          docker push registry.example.com/app:${{ steps.meta.outputs.tag }}
  deploy-staging:
    needs: build
    environment: staging
    steps:
      - run: kubectl set image deploy/app app=registry.example.com/app:${{ needs.build.outputs.image-tag }}
  deploy-production:
    needs: deploy-staging
    environment: production
    steps:
      - run: kubectl set image deploy/app app=registry.example.com/app:${{ needs.build.outputs.image-tag }}
```

Use environment-scoped secrets (not branch-scoped). Store config in Kubernetes ConfigMaps, AWS SSM Parameter Store, or HashiCorp Vault. Never bake environment config into the artifact.

## Docker Image Tagging Strategies

| Tag Format | Example | Mutable | Purpose |
|------------|---------|---------|---------|
| Git SHA | `sha-a1b2c3d` | No | Exact commit traceability |
| Semver | `v1.2.3` | No | Release versioning |
| Branch | `main` | Yes | Latest from branch |
| `latest` | `latest` | Yes | Most recent release |
| PR-based | `pr-42` | Yes | Preview environments |

```yaml
- uses: docker/metadata-action@<sha>
  id: meta
  with:
    images: registry.example.com/app
    tags: |
      type=sha,prefix=sha-
      type=ref,event=branch
      type=semver,pattern=v{{version}}
```

Clean up PR images after merge by deleting versions matching `pr-<number>` via `gh api`.

## Package Registry Patterns

**npm (GitHub Packages):** Publish with `--registry=https://npm.pkg.github.com` using `GITHUB_TOKEN`.

**PyPI (Trusted Publishers):** Use `pypa/gh-action-pypi-publish@<sha>` with `id-token: write` permission -- no token needed via OIDC.

**Container (GHCR):** Login with `docker/login-action@<sha>` to `ghcr.io`, push with `docker/build-push-action@<sha>`.

**Multi-registry:** Tag and push the same image to both private and public registries in a single step to ensure consistency.
