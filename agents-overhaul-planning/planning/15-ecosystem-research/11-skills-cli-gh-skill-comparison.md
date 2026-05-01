# Skills CLI and gh skill Comparison

## Objective

Decide when to use `npx skills`, `gh skill`, manual clone, or native harness install flows.

## npx skills

Source: https://skills.sh/docs

Strengths:

- Simple cross-agent install command.
- Supports `npx skills add <source>` style flows.
- Aligns with repo README quickstart.
- Good default for multi-harness installs.

Risks:

- skills.sh explicitly cannot guarantee quality/security of every listed skill.
- Need repo-local audit before promotion.
- Need pin/checksum/provenance wrapper in `wagents`.

## gh skill

Source: https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/create-skills

Strengths:

- Supports search, preview, install, update, publish.
- Supports version install via `@TAG` or `@SHA`.
- Supports `--pin` for update safety.
- Writes provenance metadata into `SKILL.md` frontmatter.
- Integrates with GitHub CLI and Copilot skill locations.

Risks:

- Public preview; subject to change.
- Copilot-oriented; not necessarily canonical for all harnesses.

## Recommended policy

- Use `npx skills` for user-facing cross-harness bootstrap.
- Use `gh skill preview` as an audit ingredient for GitHub-hosted external skills.
- Use `gh skill install --pin` for Copilot-specific managed installs.
- Use `wagents skills install` as repo wrapper that can call either backend and always emits manifest updates.
