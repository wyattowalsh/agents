# Ultimate Repo Cleanup v7 — BLOCKER

**Status:** STOPPED — hooks fail-closed (retry exhausted)  
**Timestamp:** 2026-07-29T12:41:00-04:00 (approx)  
**Orchestrator:** resume Ultimate Repo Cleanup v7 end-to-end  
**Plan SSOT:** `/Users/ww/.cursor/plans/cleanup_agents_skills_0cf70953.plan.md`

## Exact errors

### Shell (`cursor-before-shell-execution-guard`)

```
Rejected: Command execution was blocked by a hook: Tool blocked because this hook is
configured to fail closed (block when it fails). Hook
""$CURSOR_PROJECT_DIR/hooks/run-wagents-hook" cursor-before-shell-execution-guard --harness cursor"
failed with exit code 1
```

- Attempt 1: `ls` / `find` inventory of `planning/tmp/cleanup-v7/` — **blocked**
- Attempt 2 (retry): same inventory command — **blocked**

### Read (`cursor-before-read-file-guard`)

```
Error: File read was blocked by a hook: Tool blocked because this hook is configured
to fail closed (block when it fails). Hook
""$CURSOR_PROJECT_DIR/hooks/run-wagents-hook" cursor-before-read-file-guard --harness cursor"
failed with exit code 1
```

- Attempt 1: Read plan SSOT `cleanup_agents_skills_0cf70953.plan.md` — **blocked**
- Attempt 2 (retry): same Read — **blocked**

## What landed this session

**Nothing.** No inventory completed, no waves executed, no file edits, no Task subagents launched.

Could not verify on-disk prior state (W0 / W1a / packets / accounting / validate logs) because shell and read were both fail-closed.

## Per-wave status (this session)

| Wave | Status | Notes |
|------|--------|-------|
| W0 | UNKNOWN | Could not inventory |
| W1a | UNKNOWN | Could not inventory |
| W1b–W7 | UNKNOWN | Not started; blocked before resume |

## Resume instructions

1. **Unblock hooks** (pick one):
   - Fix `hooks/run-wagents-hook` / `cursor-before-shell-execution-guard` and `cursor-before-read-file-guard` so they exit 0 for repo paths under `/Users/ww/dev/projects/agents` and plan path `/Users/ww/.cursor/plans/`.
   - Or temporarily disable fail-closed for those guards while cleanup runs (restore after).
   - Or run inventory + waves outside Cursor hook path if an alternate harness is approved.

2. **Re-inventory** (required before any wave work):

   ```bash
   ls -la planning/tmp/cleanup-v7/
   find planning/tmp/cleanup-v7 -type f | sort
   # Inspect: wave-*-account.json, packets/, BLOCKER.md, validate logs
   ```

3. **Skip completed waves; resume from first incomplete** per plan Accounting Rule.

4. **Hard constraints** (unchanged):
   - Keep Crush/OC auth/gemini-api/candidates
   - Claude 8-subset unchanged
   - No invent MDX
   - No home sync
   - NO commits (stop for approval at W7)
   - Nested Task model ALWAYS `cursor-grok-4.5-high`
   - Exclusive file ownership; peak ≤8/wave

5. **Re-run** this resume prompt after hooks allow shell + read.

## Ask

Approve hook fix / temporary disable before cleanup resume. Do not commit until W7 gate.
