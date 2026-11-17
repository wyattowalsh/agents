## Source Surfaces

| Surface | Change |
| --- | --- |
| `skills/review/` | New canonical first-party review skill, references, helper scripts, and eval manifest |
| `skills/honest-review/` | Deleted; behavior folded into `/review` |
| `skills/simplify/` | Deleted; behavior folded into `/review simplify` |
| `skills/external-skill-auditor/` | Deleted; behavior folded into `/review source` |
| `agents/code-reviewer.md` | Read-only agent delegates protocol to `/review` |
| `agents/security-auditor.md` | Read-only security agent delegates protocol to `/review --lens security` |
| `instructions/global.md`, `AGENTS.md`, harness overlays | References to old public review names should route to `/review` where appropriate |
| `docs/src/skill-research/review.md` | New research, trust, duplicate, and synthesis artifact |

## Generated Surfaces

| Surface | Refresh Command |
| --- | --- |
| `docs/src/authoring/skills/*.mdx` for custom skills | `uv run wagents catalog sync-authoring` |
| `docs/public/generated-registries/skills-catalog-index.json` | `uv run wagents docs generate` |
| generated docs catalog pages | `uv run wagents docs generate` |
| `README.md` | `uv run wagents readme` |
| docs build output | `uv run wagents docs build` |

## Validation Surfaces

| Surface | Command |
| --- | --- |
| skill frontmatter and package | `uv run wagents validate`; `uv run wagents package review --dry-run` |
| eval schemas | `uv run python skills/skill-creator/scripts/asset_toolkit/validate_evals.py skills/review`; `uv run wagents eval validate` |
| docs research | `uv run wagents docs research --validate-artifacts` |
| harness sync | `uv run wagents skills sync --dry-run -a <harness> --format json` |
| OpenSpec | `uv run wagents openspec validate`; `uv run wagents openspec status --change consolidate-review-skill --format json` |
