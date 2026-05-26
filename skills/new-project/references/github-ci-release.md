# GitHub CI And Releases

Generated GitHub Actions must default to least privilege:

```yaml
permissions:
  contents: read
```

Add only narrow permissions such as `id-token: write` for OIDC. Avoid `pull_request_target` workflows with secrets unless a security review approves them.

Start with CI only. Release workflows, GitHub Releases, and Changesets require an explicit versioning strategy.
