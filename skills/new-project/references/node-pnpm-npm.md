# Node, pnpm, npm, and Nx

Use `pnpm` for new Node projects unless the target already uses npm, yarn, or bun.

## Command Defaults

- One-off generators: prefer `pnpm dlx <tool>`.
- Project commands: prefer `pnpm exec <tool>`.
- Upstream npm-only docs: `npx` is acceptable when justified.
- After generators, inspect `package.json`, lockfiles, scripts, and postinstall hooks before continuing.

## Nx

Add Nx only when workspace orchestration, affected builds, caching, generators, or task graphs matter. Do not add Nx to single-package apps by default.

## Changesets

Use Changesets for libraries and monorepos that publish packages. Avoid it for simple deployed apps unless a versioned release process is needed.
