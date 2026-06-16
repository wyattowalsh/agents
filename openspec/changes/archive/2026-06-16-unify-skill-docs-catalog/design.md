# Design

## Catalog pipeline

- `collect_skill_doc_nodes()` merges repo `skills/`, optional installed inventory, and curated stubs from `config/external-skills.md` with priority custom > installed > curated-external.
- `wagents docs generate` writes detail pages to `docs/src/content/docs/skills/catalog/<id>.mdx` and hub indexes (`skills/index.mdx`, `skills/all.mdx`, `skills/install.mdx`) using LinkCard rows — no JSON `SkillCatalog` component.
- Starlight sidebar autogenerates `skills/catalog` detail pages.

## Research cache

- Cached artifacts live in `docs/src/skill-research/<name>.md` with YAML frontmatter.
- Phase A seeds repo-grounded Quick Answer briefs from `SKILL.md` via `wagents docs research --seed-from-repo`.
- Rendered pages embed research under an evidence disclaimer Aside; research is not authority.

## Sync desired set

- `collect_desired_sync_rows()` = repo-owned desired rows + Install Now curated entries.
- `merge_desired_with_installed()` overlays desired rows without replacing installed inventory rows.
- `_build_sync_report()` compares merged verified rows per harness target.

## URL migration

- Canonical detail URL: `/skills/catalog/<name>/`.
- `docs/src/middleware.ts` returns 308 from legacy `/skills/<name>/` excluding hub slugs (`all`, `install`, `installed`, `catalog`).
