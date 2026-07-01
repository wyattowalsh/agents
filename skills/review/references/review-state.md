# Review State

Use this reference for `/review history`, `/review delta`, and `/review learnings` modes. State is user-local and harness-specific; it is not repo-tracked.

## Base Paths

`review-store.py` and `learnings-store.py` resolve the active harness home via `get_agent_dir("reviews")`:

| Harness signal | State root |
| --- | --- |
| Default (Claude Code) | `~/.claude/reviews/` |
| `CODEX_CLI=1` or agent name contains `codex` | `~/.codex/reviews/` |
| `COPILOT_CLI=1` or agent name contains `copilot` | `~/.copilot/reviews/` |
| `GEMINI_CLI=1` or agent name contains `gemini` | `~/.gemini/reviews/` |

Learnings live under `{reviews}/learnings/{project-slug}.json`.

## Project Slugs

`slugify()` lowercases the project name, replaces non-alphanumeric runs with hyphens, and uses `unnamed` when the result is empty. Use the same project string across save, history, delta, and learnings commands.

## Review Filenames

Saved reviews use:

```text
{YYYY-MM-DD}-{project-slug}-{mode}[-{run_id}].json
```

- **mode:** `session`, `audit`, `pr`, `range`, `source`, `simplify`, or `scoped`
- **run_id:** optional disambiguator; `cmd_save` defaults to `HHMMSS-microseconds` when omitted

Same-day reruns therefore get distinct files when `run_id` differs. There is no automatic overwrite of an existing review file.

## Save Envelope (schema 2)

`review-store.py save` writes JSON with:

| Field | Meaning |
| --- | --- |
| `schema` | `2` for current saves (`1` still readable on load) |
| `date` | ISO date (`YYYY-MM-DD`) |
| `project` | slugified project name |
| `mode` | review mode that produced the findings |
| `commit` | optional git commit anchor |
| `run_id` | optional run disambiguator |
| `scope` | optional scope summary string |
| `findings` | JSON array of finding objects |
| `statistics` | derived counts (`reported`, `discarded`, `strengths`, severity buckets) |

Pipe a findings array to stdin or pass `--input <file>`.

## Load and List

- **load:** `review-store.py load --project <name> [--date latest|previous|YYYY-MM-DD]`
- **list:** `review-store.py list [--project <name>] [--limit N]`

`resolve_review_path` treats `latest` as newest file, `previous` as second newest, and `YYYY-MM-DD` as first file whose name starts with that date prefix.

## Delta Semantics

`review-store.py diff --project <name> --old <spec> --new <spec>` compares two saved reviews. Finding identity prefers location/category/description fingerprints over display IDs, because `RV-*` IDs may change between runs.

## Learnings

`learnings-store.py` manages false-positive suppressions per project:

| Subcommand | Purpose |
| --- | --- |
| `add` | Record a dismissed pattern with reason |
| `check` | Filter findings against stored learnings (stdin JSON array) |
| `list` | Show learnings for a project |
| `clear` | Remove learnings for a project |

Learning IDs use `L-NNN` sequential format within each project file.

## Cleanup and Retention

- State directories are created on first save; nothing is auto-pruned.
- Users own deletion; use `learnings clear` or remove files under the harness reviews directory manually.
- Do not commit review JSON or learnings into the repository during review workflows.

## Read-Only Modes

`history`, `delta`, and `learnings list` are read-only. `learnings add` and `learnings clear` mutate only learnings files, not reviewed source code.
