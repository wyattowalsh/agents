# Soft policy: never-sign / no agent attribution

- Instruction SSOT: `instructions/global.md` — "Never sign or add self-attribution."
- Hard gate: `wagents/hooks/policies/git_commit_push_guard.py` denies Cursor Co-authored-by / Made-with / Generated-by trailers on `git commit`.
- Registry: `git-commit-push-guard` FAIL_CLOSED in `config/hook-registry.json`.
- Cursor cli-config: `attributeCommitsToAgent` and `attributePRsToAgent` must remain false.
