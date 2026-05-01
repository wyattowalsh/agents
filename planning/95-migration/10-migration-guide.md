# Migration Guide

## Audience

Maintainers migrating from the current ad hoc agent asset workflow to the planned agents platform control plane.

## Migration Shape

This readiness pass defines migration contracts only. It does not perform live config writes, generated documentation refreshes, external skill installs, or archive moves.

## Steps

1. Confirm all child OpenSpec changes are complete.
2. Run `uv run wagents openspec validate`.
3. Review lane-owned planning docs for current contracts:
   - `planning/10-skills-lifecycle/`
   - `planning/20-mcp-audit/`
   - `planning/30-harnesses/`
   - `planning/40-knowledge-context/`
   - `planning/50-config-safety/`
   - `planning/60-ci-cd/`
   - `planning/70-evals/`
   - `planning/80-security/`
   - `planning/90-ui-ux/`
   - `planning/95-migration/`
4. Decide whether derived docs and instruction mirrors will be regenerated in the same release or a follow-up release.
5. If regenerating derived docs, run the existing documented docs workflow in a clean follow-up commit and review generated diffs separately.
6. If applying harness config changes, use the C06 transaction contract with preview, backup, redaction, approval, apply, and rollback.
7. If promoting external skills, use the C10 intake allowlist and C15 quarantine contracts before install or vendoring.

## Surface Mapping

| Existing Surface | Migration Action |
| --- | --- |
| Skill lifecycle docs and scripts | Use C02 inventory, drift, packaging, and deprecation contracts before implementation edits. |
| MCP registry and installs | Use C03 audit contracts before adding or changing server definitions. |
| Harness configs | Use C04 per-harness contracts and C06 transaction safety before writes. |
| Generated docs | Treat as derived output; regenerate only with explicit release decision. |
| OpenSpec changes | Archive only after validation and post-merge checks pass. |

## Compatibility Notes

No backwards-compatibility code is introduced by this pass. Any future implementation that changes persisted files, public CLI output, archive layout, or external installer behavior must carry its own migration notes and tests.
