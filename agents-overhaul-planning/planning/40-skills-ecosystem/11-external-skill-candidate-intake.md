# External Skill Candidate Intake

## Intake sources

- `skills.sh` leaderboard/registry.
- GitHub `gh skill search` results.
- Awesome GitHub Copilot skill catalog.
- Awesome Agent Skills lists.
- Framework-specific skill packs, such as CrewAI.
- High-quality vendor/team repositories.

## Intake workflow

1. Discover candidate.
2. Record source in `external-tool-catalog.json`.
3. Preview contents without installing.
4. Inspect `SKILL.md`, scripts, assets, references.
5. Score CLI robustness and security.
6. Classify as `adopt`, `adapt`, `watch`, `reject`, or `docs-only`.
7. If adopted, vendor or reference with pinned provenance.
8. Add eval and docs tasks.

## External candidate scoring

```text
score =
  3 * portability
+ 3 * safety
+ 2 * cli_robustness
+ 2 * maintenance_signal
+ 2 * overlap_gap_value
+ 1 * docs_quality
- 3 * credential_risk
- 2 * destructive_command_risk
- 2 * unsupported_harness_risk
```
