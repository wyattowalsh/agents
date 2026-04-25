# Tooling Contract

Use this reference when the task touches JS/TS commands, dependencies,
lockfiles, workspaces, package roots, or CI install behavior.

## Package Root Resolution

Before running package commands:

1. Find the nearest owning `package.json` for the file or script.
2. Inspect `packageManager`, lockfiles, and `pnpm-workspace.yaml`.
3. Run the command from that package root or use an explicit working directory.
4. Use `pnpm --filter <pkg>` only after confirming the workspace package name.

Do not install dependencies at the repository root when the importing source
belongs to a nested package.

## Required Defaults

| Task | Required Command | Reject |
|------|------------------|--------|
| Install dependencies | `pnpm install` | `npm install`, `yarn install` without exception |
| CI install | `pnpm install --frozen-lockfile` | lockfile mutation in CI |
| Add dependency | `pnpm add <pkg>` | editing `package.json` by hand for normal dependencies |
| Add dev dependency | `pnpm add -D <pkg>` | global install for project tooling |
| Run script | `pnpm run <script>` | `npm run` in a pnpm package root |
| Target workspace | `pnpm --filter <pkg> run <script>` | running all packages when a target is known |
| Run local binary | `pnpm exec <cmd>` | `npx <cmd>` for installed project tools |
| One-off registry tool | `pnpm dlx <pkg>` | adding temporary tools as dependencies |
| Type check | `pnpm exec tsc --noEmit` or package script | skipping type checks after TS changes |
| Lint | `pnpm exec eslint .` or package script | ad hoc lint alternatives as repo default |
| Format check | `pnpm exec prettier --check .` or package script | ESLint as the formatter |

## `packageManager`

- Honor the owning package's `packageManager` field when present.
- Prefer adding or updating `packageManager` in a package-manager maintenance task, not as incidental churn.
- Pin pnpm through `packageManager` for reproducible contributor and CI behavior when the package root owns its own tooling.
- If Corepack is unavailable, report that separately from the package-manager choice; do not switch package managers silently.

## Workspaces

- A pnpm workspace is declared by `pnpm-workspace.yaml` at the workspace root.
- `pnpm install` at the workspace root installs dependencies for all workspace projects.
- Use `pnpm --filter <pkg>` for targeted scripts or dependency changes when the package name is known.
- Keep dependencies in the package that imports them; put shared tooling at the workspace root only when the repo already follows that pattern.

## Lockfiles

- Commit `pnpm-lock.yaml`.
- Do not `.gitignore` lockfiles for applications, docs apps, CLIs, or deployable packages.
- Do not mix `pnpm-lock.yaml`, `package-lock.json`, and `yarn.lock` in one package root.
- Use `pnpm import` during a dedicated migration when converting an existing npm or yarn lockfile.
- Use `pnpm install --frozen-lockfile` in CI and verification runs when a lockfile exists.

## Completion Sequence

For JS/TS code changes, adapt to the package's scripts but preserve this order:

1. Install or update dependencies with `pnpm add` when needed.
2. Run package scripts through `pnpm run` or `pnpm --filter`.
3. Run type checks for TypeScript changes.
4. Run ESLint for JS/TS quality checks.
5. Run Prettier check or formatting only when formatting is part of the task.
6. Run the relevant test script.

If the package lacks a script for one gate, report the missing script instead
of inventing a new project standard in the same task.
