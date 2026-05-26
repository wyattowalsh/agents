# Scaffold Profiles

## Common Artifacts

| Profile       | Artifacts                                                                               |
| ------------- | --------------------------------------------------------------------------------------- |
| `minimal`     | `README.md`, `.gitignore`, `.editorconfig`, `AGENTS.md`                                 |
| `recommended` | minimal plus `justfile`, `.pre-commit-config.yaml`, GitHub CI, OpenSpec, docs-lite plan |
| `python-*`    | `pyproject.toml`, `uv.lock`, source package, `tests/`                                   |
| `node-*`      | `package.json`, lockfile, `tsconfig.json`, app/package directories                      |
| `docs-*`      | dedicated docs root, framework config, starter docs content                             |
| `monorepo`    | `pnpm-workspace.yaml`, `apps/`, `packages/`, optional `nx.json`                         |

Always report existing files that were skipped.
