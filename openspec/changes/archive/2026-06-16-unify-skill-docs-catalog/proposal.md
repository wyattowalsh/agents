# Proposal

## Problem

Skill docs used a dual catalog: JSON `SkillCatalog` hubs plus flat `skills/<name>/` MDX pages. Sync only surfaced curated skills already present in harness inventory, so Install Now gaps were invisible. Legacy `/skills/<name>/` URLs diverged from the canonical catalog path.

## Intent

Unify skill documentation under `skills/catalog/<name>/`, compile hub indexes from one node list, extend sync desired-set to repo-owned + Install Now curated entries, add optional cached per-skill research, and redirect legacy skill URLs.

## Scope

- `wagents/skill_docs.py`, `wagents/skill_research.py`, `wagents/docs.py`, `wagents/rendering.py`, `wagents/site_model.py`
- `wagents/external_skills.py`, `wagents/installed_inventory.py`, `wagents/cli.py` sync slice
- `docs/src/middleware.ts` legacy redirects
- Hand-maintained overlays under `docs/src/content/docs/skills/catalog/`
- Retire `SkillCatalog` hub component and bloated JSON skill indexes

## Out Of Scope

- Mandatory CI network research for every skill page
- Auto-editing `config/external-skills.md` from docs generate

## Affected Surfaces

- Docs site routes, sidebar autogenerate, install-scripts JSON
- `wagents skills sync` missing/already-present reporting
- OpenSpec docs-instructions spec promotion (follow-up)
