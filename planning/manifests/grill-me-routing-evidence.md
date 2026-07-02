# Grill-Me Routing — Baseline Evidence (W0)

## Gaps before change

- `instructions/global.md` Clarification Gate: batched MCQ only; no `/grill-me` routing.
- `grill-me` curated external: weak description; explicit "grill me" trigger only.
- Agents (`planner`, `orchestrator`, `researcher`): clarify/open questions without depth routing.
- `plannotator-setup-goal`: best precedent — optional grill with embedded protocol.

## Skill clarification patterns (sample)

Skills with local ask/clarify rules: `research`, `harness-master`, `wargame`, `new-project`, `openspec-workflow`, `api-designer`, `things-manager`, `nerdbot`, `docling-graph`.

Harmonization: reference `instructions/global.md` Depth routing instead of duplicating protocol.

## Harness mirrors (sync targets)

- `.claude/rules/global.md`
- `.cursor/rules/global.mdc`
- `.github/instructions/global.instructions.md`
- `.apm/instructions/global.instructions.md`

## Grok overlay

- Generalize `sync_grok_skill_overlays` to symlink all `.grok/skills/*` with `SKILL.md`.
- Add `.grok/skills/grill-me/SKILL.md` repo overlay for discovery.