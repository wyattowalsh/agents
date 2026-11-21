# Add Frontier Radar recurring automation

## Why

The Frontier Radar design defines recurring ChatGPT, Codex, human-review, and deterministic repository lanes, but the schedule needs a canonical machine-readable registry, a persistent review queue, and a DST-safe repository-side execution substrate.

## What changes

- Add `config/frontier-radar-schedules.json` as the schedule source of truth.
- Add a recurring automation runbook with authority, rollout, handoff, noise, and kill-switch rules.
- Add a GitHub Actions workflow for deterministic W0, freshness, and control-plane checks.
- Anchor research outputs and incidents to GitHub issue `#5`.
- Keep external research and candidate activation outside GitHub Actions.

## Safety

The workflow receives only `contents: read` and `issues: write`. It performs read-only scans and validation, writes only ephemeral runner evidence, and comments only when an executed recurring lane fails. It never installs or activates candidates, accesses secrets, pushes, merges, releases, deploys, or mutates canonical repository state.

## Rollout

Use a seven-day shadow period for the official delta, weekly synthesis, curator, and human promotion gate. Start broader ecosystem and paradigm monitoring after the shadow period. Keep the optional paid API lane disabled.
