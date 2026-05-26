# Security And Supply Chain

## Secrets

Never request, print, read, or commit real secrets. Generate `.env.example` only.

`scripts/validate_plan.py` rejects blueprint commands categorized as `secret_read`, including direct secret-reader commands such as `cat .env.local`, credential extractors such as `gh auth token`, and unsafe credential file paths. `.env.example`, `.env.sample`, `.env.template`, and `.env.test` are allowed placeholder paths.

## Command Categories

Command categories come from `data/command-groups.json` and `scripts/catalog_utils.py`. File mutations require `mutate-files`, package installs require `package-install`, and cloud/deploy/account side effects require `external-side-effect`. Destructive command categories are blocked rather than approved.

## Package Generators

Prefer `pnpm dlx` for one-off Node generators. Inspect generated package files and scripts before running installs or builds.

## Docker Compose

Flag privileged mode, host networking, Docker socket mounts, broad host mounts, root services, public DB binds, and volume deletion commands.

Safe read-only Compose checks may use placeholder env files, for example `docker compose --env-file .env.example config`. Compose lifecycle commands such as `docker compose up` still require mutation/package approval, and `docker compose down -v` is blocked because it deletes volumes.

## CI

Default GitHub Actions permissions to `contents: read`. Use pinned actions when practical and avoid secrets in fork PR contexts.
