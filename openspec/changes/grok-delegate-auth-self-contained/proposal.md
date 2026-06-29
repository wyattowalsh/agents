## Summary

Make `grok-delegate` preflight self-contained with OAuth-primary auth checks, Tier-T trivial offload policy, and bundled `doctor.py` — decoupled from `wagents` for skill packaging.

## Why OpenSpec

Touches public skill contract, global instruction surfaces, downstream-tooling spec, generated docs, and validation behavior.

## Problem

Cross-harness Grok delegation fails when OAuth tokens are stale because preflight shells to `wagents grok doctor`, which does not validate `~/.grok/auth.json`. The skill is not portable outside the agents repo.

## Proposed Change

- Bundle `doctor.py`, `auth_lib.py`, `preflight.sh`, optional `auth_verify.sh` under `skills/grok-delegate/scripts/`
- OAuth-primary policy with explicit API-key opt-in (`GROK_DELEGATE_ALLOW_API_KEY`)
- Tier-T trivial offload in global instructions and orchestrator
- Contract tests including no-wagents guard

## Non-Goals

- Extending `wagents/grok_doctor.py` auth (harness diagnostics remain separate)
- Live `skills sync --apply`