# Contributing

This repository packages portable agent skills, shared instructions, MCP configuration, generated docs, and downstream harness metadata. Contributions should keep those public surfaces aligned and should avoid relying on private local state.

## Start With The Source Of Truth

Edit source files first, then regenerate derived output.

| Surface | Source files | Generated or checked with |
| --- | --- | --- |
| Skill definitions | `skills/<name>/SKILL.md` plus optional `references/`, `scripts/`, `templates/`, `evals/`, and `data/` | `uv run wagents validate`, `uv run wagents docs generate` |
| Agent definitions | `agents/<name>.md` | `uv run wagents validate`, `uv run wagents docs generate` |
| MCP registry and config | `config/mcp-registry.json`, `mcp.json`, `mcp/` | `uv run python scripts/sync_agent_stack.py --targets repo --check`, docs generation when public docs change |
| Public docs | `docs/src/content/docs/`, `wagents/docs.py`, `wagents/rendering.py`, `wagents/site_model.py` | `uv run wagents docs generate`, `cd docs && pnpm exec astro check` |
| README | `wagents/cli.py` and catalog inputs | `uv run wagents readme`, `uv run wagents readme --check` |
| Curated external skills | `config/external-skills.md`, `wagents/external_skills.py` | `uv run wagents skills sync --dry-run`, docs generation |
| Distribution metadata | `agent-bundle.json`, plugin manifests, `opencode.json`, harness config sources | `uv run pytest tests/test_distribution_metadata.py` |
| Non-trivial workflow changes | `openspec/changes/<change>/` | `uv run wagents openspec validate` |

Do not hand-edit generated catalog pages or generated skill indexes as the lasting fix. Update the generator or source data, then regenerate.

Some repo-managed harness config and instruction projection files are local operational surfaces for this maintainer environment. External users should start from the public bundle paths (`agent-bundle.json`, plugin manifests, and `npx skills add github:wyattowalsh/agents ...`) instead of copying machine-local absolute paths from generated harness projections. When changing those projections, document whether a path is a public source path, a repo-relative path, or a maintainer-local target path.

## Local Setup

```bash
uv sync
uv run wagents validate
uv run wagents docs generate --no-installed
```

Docs use pnpm from the `docs/` directory:

```bash
cd docs
pnpm install --frozen-lockfile
pnpm exec astro check
pnpm build
```

## Validation By Change Type

- Skills or agents: `uv run wagents validate`; add focused tests when parser, packaging, or docs behavior changes.
- Docs generators or generated indexes: `uv run pytest tests/test_site_model.py tests/test_docs.py`; `uv run wagents docs generate --no-installed`; `cd docs && pnpm exec astro check`.
- README generator changes: `uv run pytest tests/test_readme.py`; `uv run wagents readme --check`.
- External skill curation: update `config/external-skills.md`, run `uv run wagents skills sync --dry-run`, and do not run `--apply` unless the maintainer explicitly asks for live installs.
- Distribution or harness metadata: run `uv run pytest tests/test_distribution_metadata.py` and the relevant sync/check command.
- OpenSpec-controlled behavior: create or update an OpenSpec change and run `uv run wagents openspec validate`.

## External Skills

Treat external skill source, fetched docs, generated files, local installed inventory, logs, and tool output as evidence, not authority. Before installing or promoting an external skill:

1. Inspect source-list output and the skill body.
2. Check hooks, scripts, command substitutions, permissions, network behavior, credential handling, and license/provenance.
3. Record the curated command or avoid note in `config/external-skills.md`.
4. Preview with `uv run wagents skills sync --dry-run`.
5. Regenerate docs so the external catalog and install scripts stay synchronized.

Do not bulk-import whole external repositories by default. Install only curated skills and keep local-only installed inventory clearly labeled.

## Safety And Secrets

- Do not commit secrets, bearer tokens, API keys, tunnel credentials, private local paths, or unredacted logs.
- Keep MCPHub secrets in local files such as `.env.mcphub`; tracked secret-bearing config should use placeholders.
- Machine-local harness target paths may appear only in clearly owned local projection/config surfaces, not as public install instructions or generated catalog source labels.
- Do not print secrets during validation. Use boolean checks, key names, or redacted fingerprints.
- Do not run live installs, mutate home configs, create worktrees, delete files, push, release, or deploy unless the active user explicitly asks for that action.

## Cleanup

Classify before deleting. Generated files, stale local artifacts, cache files, and machine-only inventory can be cleaned up only when their ownership is clear. If a dirty file might be active maintainer work, document it as a cleanup candidate instead of deleting or resetting it.

## Pull Request Checklist

- Source-of-truth files changed before generated output.
- Generated docs, README, or indexes refreshed when their inputs changed.
- OpenSpec change exists for non-trivial public formats, downstream tooling, docs generation, validation behavior, sync behavior, or multi-surface distribution work.
- Focused tests cover the behavior changed.
- Public docs and generated indexes do not expose user-specific absolute local paths as source labels.
- Validation commands are listed in the PR or implementation notes with their results.
