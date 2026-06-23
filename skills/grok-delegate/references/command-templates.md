# Native command templates

Always include `--no-auto-update`. Use absolute `--cwd`.

## Wave 0 — scout

```bash
grok --no-auto-update \
  -p "Scout only (read-only): <question>. Return paths, risks, and recommended wave-1 slices." \
  --cwd "<repo>" \
  --output-format json \
  --max-turns 8 \
  --agent researcher \
  --permission-mode plan
```

Parallel scouts: add `-w w0-scout-<n>` per independent slice.

## Wave 1 — build

```bash
grok --no-auto-update \
  -p "<self-contained implementation task with file paths and done criteria>" \
  --cwd "<repo>" \
  --output-format json \
  --max-turns 25 \
  --agent "<agent-name>" \
  -w "w1-<role>-<n>"
```

## Wave 2 — verify

```bash
grok --no-auto-update \
  -p "Verify only: run relevant tests and report pass/fail with evidence." \
  --cwd "<repo>" \
  --output-format json \
  --max-turns 10 \
  --agent code-reviewer \
  --check
```

## Hypothesis (Pattern C)

Option A — native best-of-n:

```bash
grok --no-auto-update -p "<question>" --cwd "<repo>" \
  --output-format json --best-of-n 3
```

Option B — parallel worktrees with distinct prompts per theory.

## Plan-then-swarm (Pattern D)

Plan node:

```bash
grok --no-auto-update -p "Plan only: <task>" --cwd "<repo>" \
  --output-format json --permission-mode plan --agent planner
```

After parent approval, build nodes as wave 1.

## Observability between waves

```bash
grok sessions list -n 20
grok export <sessionId>   # when transcript needed
```