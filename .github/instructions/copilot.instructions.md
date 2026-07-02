---
applyTo: "**/*"
---

<!-- Managed by scripts/sync_agent_stack.py. Do not edit directly. -->
# GitHub Copilot

Copilot-specific extension only. Keep shared cross-platform instructions in `global.md`.

## Fleet Planning

- All plans must be `/fleet`-optimized per `/orchestrator` for maximum efficiency and robustness.
- Default to the highest applicable `/orchestrator` tier; do not collapse parallelizable work into a single-session plan.
- Maximize independent subagent dispatch, preserve clear file ownership, and keep synthesis gated on all dispatched work completing.

## Fleet Model Policy

- Default to the globally managed profile: `gpt-5.4`, high reasoning effort, `continueOnAutoMode=false`, and no explicit `COPILOT_SUBAGENT_MAX_CONCURRENT` or `COPILOT_SUBAGENT_MAX_DEPTH` caps.
- Use heavier or lighter models only when explicitly requested or when a bounded plan identifies a concrete need.
- Keep `/fleet` dispatch accountable. Do not invent artificial fan-out limits in instructions unless the user asks for them.

<!-- rtk-instructions v2 -->
# RTK — Token-Optimized CLI

**rtk** is a CLI proxy that filters and compresses command outputs, saving 60-90% tokens.

## Rule

Always prefix shell commands with `rtk`:

```bash
# Instead of:              Use:
git status                 rtk git status
git log -10                rtk git log -10
cargo test                 rtk cargo test
docker ps                  rtk docker ps
kubectl get pods           rtk kubectl pods
```

## Meta commands (use directly)

```bash
rtk gain              # Token savings dashboard
rtk gain --history    # Per-command savings history
rtk discover          # Find missed rtk opportunities
rtk proxy <cmd>       # Run raw (no filtering) but track usage
```
<!-- /rtk-instructions -->
