# Edge Cases

Use this reference only when a JS/TS task appears to require an exception to
the standard `pnpm` and tooling contract.

## Exception Gate

Allow a deviation only when the response names:

1. the existing evidence (`package-lock.json`, `yarn.lock`, CI config, vendor docs, or migration ticket),
2. the owner or reason for the exception,
3. the commands that are safe for this package root, and
4. the exit criteria if the exception is temporary.

## When npm Is Acceptable

- The package root has `package-lock.json`, no `pnpm-lock.yaml`, and no migration is planned.
- CI or deployment tooling explicitly requires `npm ci` and cannot be configured safely in the current task.
- A third-party generator or vendor command only supports npm; document the source and avoid mixing lockfiles.
- Corepack or pnpm is unavailable in a constrained environment and the task is read-only or diagnostic.

## When yarn Is Acceptable

- The package root has `yarn.lock`, no `pnpm-lock.yaml`, and no migration is planned.
- The monorepo already uses Yarn Berry or Plug'n'Play with significant committed configuration.
- CI, deployment, or workspace tooling is explicitly wired to yarn and changing it is outside scope.

## Corepack and pnpm Availability

- Do not assume `corepack` is present just because Node.js is installed.
- Node.js 25 and newer do not bundle Corepack; use the repo's documented install path or the standalone/userland Corepack path when needed.
- For Node.js versions that include Corepack, prefer a pinned `packageManager` field and `corepack enable pnpm` only when the environment supports it.
- If pnpm is unavailable and installation is out of scope, stop after reporting the exact missing executable and the command that would have been run.

## CI Lockfile Handling

- Use `pnpm install --frozen-lockfile` in CI when `pnpm-lock.yaml` is present.
- Do not run plain `pnpm install` in CI to "fix" a stale lockfile.
- If a lockfile needs updating, make that an explicit dependency-change or migration step.
- Do not delete `package-lock.json` or `yarn.lock` in a feature change unless the task is a package-manager migration.

## Package Root Ambiguity

- In nested repos, run package commands from the nearest owning `package.json`.
- If both root and nested `package.json` files exist, inspect `packageManager`, lockfiles, and workspace config before choosing a command root.
- For pnpm workspaces, prefer `pnpm --filter <pkg> run <script>` for targeted package scripts.
- Do not install dependencies at the repository root when the importing file belongs to a nested package.

## Docs Site (Starlight/Astro)

- This repo's docs app is under `docs/`, not the repository root.
- `docs/package.json` owns the docs app package commands.
- `docs/pnpm-workspace.yaml` marks the docs package root for pnpm workspace behavior.
- Run docs package commands from `docs/` or with an explicit working directory.
- Astro/Starlight integrations should be managed with `pnpm add` in the docs package root when dependency changes are in scope.

## Generated Apps and Scaffolds

- For one-off generators, use `pnpm dlx <generator>` unless the generator requires npm or yarn.
- After scaffolding, switch to the generated app's own package root and inspect its `package.json` and lockfile before running commands.
- Do not normalize a generated app's package manager during the same task unless the user asked for a migration.

## Global Tools and One-Off Commands

- Prefer local project binaries via `pnpm exec`.
- Prefer `pnpm dlx` for one-off registry tools that are not project dependencies.
- Avoid `pnpm add -g`; if a global tool is truly required, document why local or one-off execution is insufficient.
- Do not use `npx` as a default replacement for `pnpm exec` or `pnpm dlx`.

## Migration Rules

- Keep package-manager migrations as dedicated logical changes.
- Preserve the old lockfile until the migration step intentionally replaces it.
- Use `pnpm import` when converting from an existing lockfile if it preserves dependency resolution.
- Verify the new lockfile with `pnpm install --frozen-lockfile` after migration.
