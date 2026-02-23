# JavaScript Convention Edge Cases

Repo-specific exceptions to the standard JavaScript conventions.

## When npm Is Acceptable

- Project has an existing `package-lock.json` and no migration is planned
- CI pipeline explicitly requires npm (e.g., Vercel, Netlify defaults)
- Third-party tooling that only supports npm (document the reason)

## When yarn Is Acceptable

- Project has an existing `yarn.lock` with yarn Berry (v3+) and Plug'n'Play
- Monorepo already uses yarn workspaces with significant configuration

## CI Lockfile Handling

- Always use `--frozen-lockfile` in CI environments
- If migrating lockfiles, do it in a dedicated PR (not alongside feature work)
- Run `pnpm install` locally after migration to verify the new lockfile

## Docs Site (Starlight/Astro)

- The `docs/` directory uses pnpm workspaces
- Run `pnpm install` from `docs/` before `pnpm dev`
- Astro config and integrations are managed via `pnpm add`

## Global Tools

- Use `pnpm add -g` for global CLI tools when needed
- Prefer `pnpm dlx` over `npx` for one-off command execution
- Document any required global installations in project README
