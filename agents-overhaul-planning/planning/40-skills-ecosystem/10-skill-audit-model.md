# Skill Audit Model

## Objective

Make every local or external Agent Skill auditable before install, sync, or docs promotion.

## Audit dimensions

| Dimension | Checks |
|---|---|
| Spec | `SKILL.md` exists; frontmatter valid; name matches dir; description within limit |
| Progressive disclosure | Main body concise; references/assets used for depth; no deeply nested chains |
| CLI/scripts | dependencies documented; JSON output; exit codes; dry-run; idempotence |
| Security | no hidden destructive commands; no secret exfiltration; network use declared |
| Provenance | source repo/ref/tree SHA/checksum/license recorded |
| Portability | works across target hosts or caveats documented |
| Docs | generated docs page and README table are current |
| Evals | skill has at least one activation and one non-activation fixture |

## Audit verdicts

- `pass`: eligible for validated registry tier.
- `warn`: can remain experimental/watch.
- `fail`: blocked from install/promotion.
- `manual-review`: requires human approval.
