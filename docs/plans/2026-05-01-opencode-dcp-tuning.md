# OpenCode DCP Tuning Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Tune OpenCode Dynamic Context Pruning so long sessions compress before OpenAI rejects oversized requests.

**Architecture:** Keep `config/opencode-dcp.jsonc` as the repo-owned source of truth and sync it to `~/.config/opencode/dcp.jsonc` through existing OpenCode sync paths. Make the first change conservative and model-neutral: lower proactive compression thresholds and nudge cadence, then validate with tests, config drift checks, and new log evidence before considering fallback compaction changes.

**Tech Stack:** OpenCode, `@tarquinen/opencode-dcp@latest`, JSONC config, Python sync code, `uv`, pytest, `wagents`.

---

## Context

Observed evidence from recent OpenCode logs:

- `/Users/ww/.local/share/opencode/log/2026-05-01T021520.log:1781` showed `context_length_exceeded` for `providerID=openai modelID=gpt-5.5`.
- `/Users/ww/.local/share/opencode/log/2026-05-01T021520.log:1798` showed native OpenCode compaction immediately afterward: `service=session.compaction budget=8000 size=118260 total=0 tail fallback`.
- `/Users/ww/.local/share/opencode/log/2026-04-30T224019.log:60701-60715` showed native pruning can work, but only after context has already grown large.
- DCP is loading and registering tools; the root issue is that current proactive thresholds are too late/soft for the session shape.

Current DCP tuning in `config/opencode-dcp.jsonc:46-64`:

```jsonc
"compress": {
  "mode": "range",
  "permission": "allow",
  "showCompression": false,
  "summaryBuffer": true,
  "maxContextLimit": "85%",
  "minContextLimit": "55%",
  "nudgeFrequency": 4,
  "iterationNudgeThreshold": 12,
  "nudgeForce": "soft",
  "protectedTools": [
    "task",
    "skill",
    "todowrite",
    "todoread",
    "compress"
  ],
  "protectUserMessages": false
}
```

Target first-pass tuning:

```jsonc
"maxContextLimit": "75%",
"minContextLimit": "45%",
"nudgeFrequency": 2,
"iterationNudgeThreshold": 8,
"nudgeForce": "soft"
```

Rationale:

- `maxContextLimit: "75%"` starts compression earlier than the current `85%`, leaving more room for tool-result bursts and provider accounting differences.
- `minContextLimit: "45%"` gives compression a larger reduction target so the next request is less likely to immediately cross the limit again.
- `nudgeFrequency: 2` and `iterationNudgeThreshold: 8` prompt more regular proactive compression in long orchestration sessions.
- Keep `nudgeForce: "soft"` for the first pass to avoid over-aggressive interruption; only move to forceful behavior if logs still show oversized requests.
- Keep config model-neutral and do not add `compress.modelMaxLimits` or `compress.modelMinLimits`.

Second-pass update after runtime evaluation:

- `/Users/ww/.local/share/opencode/log/2026-05-01T111557.log:42745-42755` showed a fresh `agent=plan` request sent to `openai/gpt-5.5` and rejected with `context_length_exceeded` after the first-pass config was active.
- `/Users/ww/.local/share/opencode/log/2026-05-01T111557.log:42771-42778` showed native compaction only retried after the provider rejection, confirming DCP nudges were still too late/soft.
- Installed `@tarquinen/opencode-dcp@3.1.9` source confirms `nudgeForce` accepts only `"soft"` or `"strong"`; `"strong"` injects the turn nudge on a user message rather than an assistant message.
- Second pass keeps the config model-neutral while lowering thresholds to `70%`/`40%` and switching `nudgeForce` to `"strong"`.

Current target tuning after second pass:

```jsonc
"maxContextLimit": "70%",
"minContextLimit": "40%",
"nudgeFrequency": 2,
"iterationNudgeThreshold": 8,
"nudgeForce": "strong"
```

## Acceptance Criteria

- `config/opencode-dcp.jsonc` uses the new conservative threshold values.
- `~/.config/opencode/dcp.jsonc` matches `config/opencode-dcp.jsonc` exactly after sync.
- Existing model-neutral safeguards still pass: no OpenCode `model`, `small_model`, `mode`, or `agent` keys in DCP config; no DCP per-model limit maps.
- OpenCode sync tests pass for DCP behavior.
- General repo validation still passes, or any unrelated existing failures are documented with evidence.
- New OpenCode logs after a long-session smoke run show proactive DCP compression before any new `context_length_exceeded` entry.

## Non-Goals

- Do not change OpenCode main or small model selection.
- Do not add model-specific DCP limits.
- Do not disable Anthropic provider discovery; usage is controlled by model selection.
- Do not tune native OpenCode `compaction.reserved` until after DCP threshold tuning is evaluated.
- Do not clean duplicate skill paths or MCP credential placeholders in this plan; those are separate follow-up batches.
- Do not commit unless the user explicitly asks for a commit.

---

### Task 1: Add a Regression Test for Canonical DCP Thresholds

**Files:**
- Modify: `tests/test_sync_agent_stack.py:1028-1085`
- Read: `config/opencode-dcp.jsonc:46-64`

**Step 1: Write the failing test**

Add this test near the existing OpenCode DCP tests in `tests/test_sync_agent_stack.py`:

```python
def test_repo_opencode_dcp_config_uses_proactive_thresholds():
    payload = json.loads(sync_agent_stack.OPENCODE_DCP_TEMPLATE_PATH.read_text(encoding="utf-8"))

    compress = payload["compress"]
    assert compress["mode"] == "range"
    assert compress["maxContextLimit"] == "70%"
    assert compress["minContextLimit"] == "40%"
    assert compress["nudgeFrequency"] == 2
    assert compress["iterationNudgeThreshold"] == 8
    assert compress["nudgeForce"] == "strong"
    assert "modelMaxLimits" not in compress
    assert "modelMinLimits" not in compress
```

**Step 2: Run test to verify it fails**

Run:

```bash
uv run pytest tests/test_sync_agent_stack.py::test_repo_opencode_dcp_config_uses_proactive_thresholds -v
```

Expected: FAIL because the current canonical config still has `85%`, `55%`, `4`, and `12`.

**Step 3: Do not commit**

Do not commit unless the user explicitly asks.

---

### Task 2: Tune Canonical DCP Thresholds

**Files:**
- Modify: `config/opencode-dcp.jsonc:51-54`
- Test: `tests/test_sync_agent_stack.py`

**Step 1: Change only DCP nudge aggressiveness values**

Patch `config/opencode-dcp.jsonc`:

```diff
@@
-    "maxContextLimit": "85%",
-    "minContextLimit": "55%",
-    "nudgeFrequency": 4,
-    "iterationNudgeThreshold": 12,
+    "maxContextLimit": "70%",
+    "minContextLimit": "40%",
+    "nudgeFrequency": 2,
+    "iterationNudgeThreshold": 8,
-    "nudgeForce": "soft",
+    "nudgeForce": "strong",
```

**Step 2: Run the targeted test**

Run:

```bash
uv run pytest tests/test_sync_agent_stack.py::test_repo_opencode_dcp_config_uses_proactive_thresholds -v
```

Expected: PASS.

**Step 3: Run existing OpenCode sync tests**

Run:

```bash
uv run pytest tests/test_sync_agent_stack.py -k opencode
```

Expected: PASS. If a test still expects `85%`, update only that assertion if it is reading the canonical template value rather than constructing a local fixture.

**Step 4: Do not commit**

Do not commit unless the user explicitly asks.

---

### Task 3: Sync the Live DCP Config

**Files:**
- Source: `config/opencode-dcp.jsonc`
- Generated/merged live target: `/Users/ww/.config/opencode/dcp.jsonc`
- Code path: `wagents/platforms/opencode.py:216-222`
- Legacy code path: `scripts/sync_agent_stack.py` DCP merge helpers

**Step 1: Run the repo sync path that manages OpenCode home config**

Use the existing repo workflow rather than hand-editing the live file. Prefer the modern `wagents` path if available in this repo session:

```bash
uv run wagents install -a opencode -y
```

If that command is not the repo-supported path in the current checkout, use the established stack sync command that already manages OpenCode DCP:

```bash
uv run python scripts/sync_agent_stack.py --apply
```

Expected: `/Users/ww/.config/opencode/dcp.jsonc` is rewritten from the canonical config while preserving safe existing DCP overrides and stripping model-specific keys.

**Step 2: Confirm canonical/live DCP drift is gone**

Run:

```bash
cmp -s config/opencode-dcp.jsonc ~/.config/opencode/dcp.jsonc
```

Expected: exit code `0`.

**Step 3: Validate live DCP has no model-specific keys**

Run:

```bash
uv run python - <<'PY'
import json
from pathlib import Path

payload = json.loads(Path.home().joinpath('.config/opencode/dcp.jsonc').read_text())
compress = payload.get('compress', {})
for key in ('model', 'small_model', 'mode', 'agent'):
    assert key not in payload, key
for key in ('modelMaxLimits', 'modelMinLimits'):
    assert key not in compress, key
assert compress['maxContextLimit'] == '70%'
assert compress['minContextLimit'] == '40%'
assert compress['nudgeFrequency'] == 2
assert compress['iterationNudgeThreshold'] == 8
assert compress['nudgeForce'] == 'strong'
print('live DCP config is model-neutral and tuned')
PY
```

Expected: prints `live DCP config is model-neutral and tuned`.

**Step 4: Do not commit**

Do not commit unless the user explicitly asks.

---

### Task 4: Run Repository Validation

**Files:**
- Validate: `tests/test_sync_agent_stack.py`
- Validate: `config/opencode-dcp.jsonc`
- Validate: `/Users/ww/.config/opencode/dcp.jsonc`

**Step 1: Run targeted tests**

Run:

```bash
uv run pytest tests/test_sync_agent_stack.py -k opencode
```

Expected: PASS.

**Step 2: Run asset validation**

Run:

```bash
uv run wagents validate
```

Expected: PASS.

**Step 3: Check README freshness**

Run:

```bash
uv run wagents readme --check
```

Expected: PASS, unless the worktree already has unrelated README/doc drift. If it fails, inspect output and classify whether it is caused by this DCP config change.

**Step 4: Check whitespace in touched files only**

Run:

```bash
git diff --check -- config/opencode-dcp.jsonc tests/test_sync_agent_stack.py
```

Expected: no output.

**Step 5: Do not commit**

Do not commit unless the user explicitly asks.

---

### Task 5: Evaluate Runtime Effect in OpenCode Logs

**Files:**
- Inspect: `/Users/ww/.local/share/opencode/log/`
- Inspect: `/Users/ww/.config/opencode/dcp.jsonc`

**Step 1: Restart or reload OpenCode**

Restart the OpenCode session so the DCP plugin reads the tuned config.

Expected: a new log file appears under `/Users/ww/.local/share/opencode/log/`.

**Step 2: Run a long-session smoke test**

Use OpenCode normally through a task that performs multiple searches/reads and enough tool output to approach pruning thresholds.

Expected: DCP should nudge or compress before provider request failure.

**Step 3: Search the newest logs for context failures**

Run:

```bash
rg -n "context_length_exceeded|session\.compaction|service=dcp|compress" /Users/ww/.local/share/opencode/log
```

Expected:

- No new `context_length_exceeded` entry after the restart timestamp.
- DCP-related compression/nudge evidence should appear before any native tail fallback.
- If native `service=session.compaction` appears, it should not be preceded by a failed provider request.

**Step 4: Record evidence**

Add the exact newest log path and line numbers to the follow-up report.

**Step 5: Do not commit**

Do not commit unless the user explicitly asks.

---

### Task 6: Decide Whether a Second Tuning Pass Is Needed

**Files:**
- Potentially modify later: `config/opencode-dcp.jsonc:51-55`
- Potentially modify later: `/Users/ww/.config/opencode/opencode.json` native `compaction.reserved`

**Step 1: If no new provider failures occur, stop**

Expected: keep the first-pass thresholds and do not make native compaction changes.

**Step 2: If DCP compresses but still too late, tighten DCP only**

Patch preview for a second DCP-only pass:

```diff
@@
-    "maxContextLimit": "75%",
-    "minContextLimit": "45%",
+    "maxContextLimit": "70%",
+    "minContextLimit": "40%",
@@
-    "nudgeForce": "soft",
+    "nudgeForce": "strong",
```

Only apply this if fresh logs still show oversize failures after the first-pass tuning.

**Step 3: If native fallback still tail-prunes too little, tune OpenCode compaction separately**

Patch preview for live-only native fallback tuning in `/Users/ww/.config/opencode/opencode.json`:

```json
"compaction": {
  "auto": true,
  "prune": true,
  "reserved": 24000
}
```

Only apply this after DCP threshold tuning is evaluated, because native compaction is fallback behavior and live OpenCode config is user-owned.

**Step 4: Validate after any second pass**

Repeat Tasks 3, 4, and 5.

**Step 5: Do not commit**

Do not commit unless the user explicitly asks.

---

## Follow-Up Work Outside This Plan

- Duplicate skill discovery cleanup: inventory `skills.paths`, installed skill paths, and duplicate warning lines, then remove redundant paths from the correct canonical or live config surface.
- MCP credential cleanup: replace inline live OpenCode MCP secret values with env placeholders where supported, using secret-safe tools and without printing values.
- Optional temporary DCP debug mode: enable `debug: true` only during a short controlled evaluation, then restore `debug: false`.

## Execution Options

1. Subagent-Driven (this session): dispatch fresh subagent per task, review after each task, and keep commits disabled unless explicitly requested.
2. Parallel Session (separate): open a new session with `executing-plans` and run the tasks with checkpoints.
