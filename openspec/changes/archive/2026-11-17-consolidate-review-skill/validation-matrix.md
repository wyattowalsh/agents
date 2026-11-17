## Validation Matrix

| Area | Command | Expected Result |
| --- | --- | --- |
| OpenSpec | `uv run wagents openspec validate` | change package validates |
| OpenSpec status | `uv run wagents openspec status --change consolidate-review-skill --format json` | change is discoverable |
| skill check | `uv run python skills/review/scripts/check.py` | skill, eval, package, and audit checks pass |
| skill audit | `uv run python skills/skill-creator/scripts/audit.py skills/review` | review skill scores as production-ready or acceptable |
| package | `uv run wagents package review --dry-run` | package dry-run succeeds |
| hooks | `uv run python skills/skill-creator/scripts/asset_toolkit/validate_hooks.py` | hook validation succeeds without relying on review skill hooks |
| eval schema | `uv run python skills/skill-creator/scripts/asset_toolkit/validate_evals.py skills/review` | review eval manifest validates |
| eval suite | `uv run wagents eval validate` | repo eval manifests validate |
| repo skills | `uv run wagents validate` | all skill/agent metadata validates |
| research docs | `uv run wagents docs research --validate-artifacts` | research artifact validates |
| authoring sync | `uv run wagents catalog sync-authoring --dry-run` then `uv run wagents catalog sync-authoring` | custom authoring rows can refresh |
| docs generate | `uv run wagents docs generate` | generated catalog/index/pages refresh |
| readme | `uv run wagents readme` | README refreshes from repo contents |
| docs build | `uv run wagents docs build` | static docs build succeeds |
| Claude Code | `uv run wagents skills sync --dry-run -a claude-code --format json` | additive sync can project review skill |
| Codex | `uv run wagents skills sync --dry-run -a codex --format json` | additive sync can project review skill |
| OpenCode | `uv run wagents skills sync --dry-run -a opencode --format json` | additive sync can project review skill |
| Grok | `uv run wagents skills sync --dry-run -a grok --format json` | additive sync can project review skill and mirror plan |
| Cursor | `uv run wagents skills sync --dry-run -a cursor --format json` | additive sync can project review skill |
| Gemini CLI | `uv run wagents skills sync --dry-run -a gemini-cli --format json` | additive sync can project review skill |
| Grok doctor | `uv run wagents grok doctor` | run when available and report exact blocker if unavailable |
| stale refs | `rg -n "/honest-review|/simplify|/external-skill-auditor|honest-review|simplify|external-skill-auditor" README.md instructions docs/src/authoring docs/src/skill-research agents skills config` | remaining hits are wrappers, migration notes, research evidence, or adjacent-skill boundaries |
| hygiene | `git diff --check`; `git status --short --branch` | no whitespace errors; dirty state understood |
