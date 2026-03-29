---
name: javascript-conventions
description: >-
  JS/TS tooling conventions. Enforce pnpm. Use when working on JS/TS files
  or package.json. NOT for Python, backend-only, or shell scripts.
user-invocable: false
disable-model-invocation: false
license: MIT
metadata:
  author: wyattowalsh
  version: "1.0.0"
---

# JavaScript/Node.js Conventions

Apply these conventions when working on JavaScript or Node.js files or projects.

## Dispatch

| $ARGUMENTS | Action |
|------------|--------|
| Active (auto-invoked when working on JS/TS files) | Apply all conventions below |
| Empty | Display convention summary |
| `check` | Verify package manager compliance only |

## References

| File | Purpose |
|------|---------|
| `references/edge-cases.md` | Repo-specific exceptions and edge cases |
| `references/typescript-patterns.md` | Discriminated unions, type guards, utility types |

## Package Management

- Use `pnpm` for all Node.js package management
- Do not use `npm` or `yarn` unless the project explicitly requires them
- Commands: `pnpm install`, `pnpm add <pkg>`, `pnpm run <script>`, `pnpm exec <cmd>`
- Always commit `pnpm-lock.yaml` -- never `.gitignore` it
- Run `pnpm install --frozen-lockfile` in CI environments

### Monorepo Conventions

- Use `pnpm` workspaces for multi-package repositories
- Define workspaces in `pnpm-workspace.yaml` at the repo root
- Use `pnpm -r` or `pnpm --filter <pkg>` for targeted operations
- Hoist shared dependencies to the root where possible

### Lockfile Handling

- Commit lockfiles to version control
- Use `--frozen-lockfile` in CI to prevent drift
- When migrating from npm/yarn, delete the old lockfile and run `pnpm import` or `pnpm install`

## Tooling Preferences

| Purpose | Tool |
|---------|------|
| Package manager | `pnpm` |
| Bundler | `vite` or `esbuild` |
| Linting | `eslint` |
| Formatting | `prettier` |
| Testing | `vitest` or framework-native runner |
| Type checking | `tsc --noEmit` |

## TypeScript Type Safety

1. Prefer `unknown` over `any`; enforce via `noImplicitAny` in `tsconfig.json`
2. Prefer `interface` for object shapes; use `type` for unions and intersections
3. Use discriminated unions for state machines and tagged types
4. Use `as const` assertions to preserve literal types
5. Avoid type assertions (`as`); prefer type guards and `satisfies`
6. Enable all `strict` compiler options in `tsconfig.json`
7. Test types with `@ts-expect-error` or `tsd`
8. See `references/typescript-patterns.md` for discriminated union and utility type patterns

## Critical Rules

1. Always use `pnpm` unless an existing lockfile or CI config mandates otherwise
2. Never mix package managers in the same project (no `npm install` alongside `pnpm`)
3. Commit `pnpm-lock.yaml` to version control in every project
4. Run `pnpm install --frozen-lockfile` in CI — never allow lockfile mutation
5. Check `references/edge-cases.md` before breaking any convention
6. Use `pnpm exec` instead of `npx` for running local binaries

**Canonical terms** (use these exactly):
- `pnpm` -- the required package manager (not npm, not yarn)
- `lockfile` -- `pnpm-lock.yaml` specifically
- `workspace` -- pnpm workspace for monorepo packages
- `frozen-lockfile` -- CI mode that prevents lockfile changes
