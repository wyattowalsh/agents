# Cross-Agent Install Smoke Runbook

Three-phase rollout for validating curated skill install commands without flaking PR CI.

## Phase 1 — Dry-run JSON (default)

Runs on every maintainer check; no network installs.

```bash
uv run python skills/cross-agent-install-smoke/scripts/dry_run.py --format json
uv run python skills/cross-agent-install-smoke/scripts/check.py
```

**Pass criteria:** exit 0; JSON report includes `ok: true` and per-harness dry-run summaries from `wagents skills sync --dry-run`.

## Phase 2 — Local temp-home smoke

Opt-in on maintainer machines only. Uses an isolated `HOME` / XDG dirs — never mutates the developer's live harness config.

```bash
INSTALL_SMOKE=1 uv run python skills/cross-agent-install-smoke/scripts/local_smoke.py --harness cursor --format json
```

**Pass criteria:** exit 0; smoke log shows sync dry-run or sandboxed install preview completed without credential access.

## Phase 3 — Scheduled workflow matrix

`workflow_dispatch` only (see `.github/workflows/install-smoke-phase3.yml`). Not on every PR.

```bash
gh workflow run install-smoke-phase3.yml -f harness=cursor
```

## Troubleshooting

| Symptom | Action |
| ------- | ------ |
| Dry-run JSON missing harness | Add harness to `wagents skills sync --dry-run -a <harness>` manually and compare |
| Phase 2 skips | Confirm `INSTALL_SMOKE=1` is exported |
| Live install requested | Do **not** run `wagents skills sync --apply` in CI; use phase 3 dispatch with explicit maintainer approval |
| Apply exits 1 with partial installs | Re-run `wagents skills sync --apply --format json` and inspect `apply_failures` for failed `npx skills add` batches |

## Related

- Skill: `skills/cross-agent-install-smoke/SKILL.md`
- Flagship eval manifest: `planning/manifests/eval-ci-flagship-skills.json`
- IDEAS task: W6 T-560a-f, W13 T-680a-d
