# Affected Surfaces

## Source Of Truth

- `instructions/external-skills.md` — canonical curated external skill install set and target suffix guidance.
- `wagents/external_skills.py` — parser for curated external skill commands and selected skill names.
- `wagents/cli.py` — `wagents skills sync` command generation and target-agent behavior.
- `wagents/installed_inventory.py` — normalized installed/repo/curated inventory rows.
- `wagents/docs.py` — generated docs pages that include external skills.
- `wagents/site_model.py` — generated site data that includes curated external skills.
- `AGENTS.md` and `instructions/global.md` — repo policy for external skill trust gates and sync commands if target coverage wording changes.
- `openspec/changes/add-audited-external-skills/` — change-control artifacts for this work.

## Generated Outputs

- `README.md` from `uv run wagents readme`.
- `docs/src/generated-site-data.mjs` from `uv run wagents docs generate`.
- Generated docs content under `docs/src/content/docs/` when docs generation refreshes external skill or install coverage pages.

## Downstream Harness Artifacts

- Global/project skill installs written by `npx skills add ... -g -a <agent>` for supported adapters.
- Harness-specific skill/config locations discovered by `harness-master` for requested targets not directly supported by the Skills CLI.
- `~/.ctf-tools` and package-manager-installed tools created by the audited `ctf-skills` installer if dry-run permits execution.

## External Sources

- `https://github.com/ljagiello/ctf-skills` at audited HEAD `ed2a356db92b078d52b4590c2ebbbf2e6641a7ee`.
- `https://github.com/nextlevelbuilder/ui-ux-pro-max-skill` at audited HEAD `b7e3af80f6e331f6fb456667b82b12cade7c9d35`.
- `https://github.com/Leonxlnx/taste-skill` at audited HEAD `60c2de19766019297287bd26a260275e499789a9`.

## Validation Commands

- `uv run wagents docs generate`
- `uv run wagents readme`
- `uv run wagents skills sync --dry-run`
- `uv run wagents skills sync --apply` when dry-run reports only approved missing curated installs for supported harnesses.
- `uv run wagents validate`
- `uv run wagents openspec validate`
- `cd docs && pnpm build`

## Review

- Run a docs-steward subagent review after docs generation/build to check docs drift, generated site data, README consistency, external skill visibility, and harness coverage wording.
