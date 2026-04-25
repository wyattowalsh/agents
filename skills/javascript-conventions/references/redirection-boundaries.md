# Redirection Boundaries

Use this reference when JS/TS is present but may not be the dominant
workstream.

## Route Away When

| Situation | Better Fit |
|-----------|------------|
| Python files, `pyproject.toml`, or Python tooling are primary | `python-conventions` |
| Shell scripts, Makefiles, or portable shell behavior are primary | `shell-conventions` |
| CI workflow architecture or deployment pipelines are primary | `devops-engineer` |
| Frontend UX, visual polish, or component design is primary | `frontend-designer` |
| Docs framework structure or generated docs artifacts are primary | `docs-steward` |
| JS/TS is incidental inside a larger domain-specific task | The domain skill plus JS/TS conventions only for the JS/TS-owned seam |

## Mixed-Language Handling

1. If JS/TS files are primary and Python or shell is incidental, keep this skill active for the JS/TS-owned surface only.
2. If JS/TS is incidental and another language or pipeline surface dominates, do not force JS/TS conventions onto the entire task.
3. When multiple surfaces matter, apply each conventions skill only to its owned files and commands.
4. For tasks that edit both generated docs and the docs app, let `docs-steward` own docs generation and keep this skill limited to `docs/package.json`, TS, ESLint, or package commands.

## Auto-Invocation Boundaries

Trigger for:

- `.js`, `.jsx`, `.ts`, `.tsx`, `.mjs`, `.cjs`, `.mts`, or `.cts` work when that work is primary.
- `package.json`, `pnpm-lock.yaml`, `pnpm-workspace.yaml`, `tsconfig.json`, `eslint.config.*`, or Prettier config work.
- Node package commands, dependency changes, TypeScript type checks, ESLint, or Prettier.

Do not trigger for:

- Backend-only Python work that happens to mention a web client.
- Shell snippets embedded in a README unless shell conventions are the actual task.
- CI workflow design where package commands are only one step.
- Framework architecture decisions that require a framework-specific skill.

## Empty / Help Routing

If the user asks for general project-tooling help in a polyglot repo:

- summarize JS/TS hard requirements briefly,
- say when `python-conventions`, `shell-conventions`, or `devops-engineer` should take over,
- avoid presenting JS/TS defaults as repo-wide law for every language.
