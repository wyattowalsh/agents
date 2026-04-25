# ESLint and Prettier

Use this reference when the task touches linting, typed linting, formatting,
or ESLint/Prettier configuration.

## ESLint Flat Config

- Prefer ESLint flat config for new setup.
- Use `eslint.config.js`, `eslint.config.mjs`, or `eslint.config.cjs` at the package root unless the repo already has a stronger convention.
- Include explicit `files` patterns for TypeScript files such as `**/*.ts`, `**/*.tsx`, `**/*.mts`, and `**/*.cts`.
- Keep ignores in config or ignore files consistent with generated output and build directories.
- Use package scripts for repeatable commands, for example `lint`, `lint:fix`, or framework-native equivalents.

## TypeScript ESLint

- Use `typescript-eslint` for TypeScript linting.
- For type-aware rules, use type-checked recommended configs and `parserOptions.projectService: true`.
- Treat typed linting as a stronger but slower lint mode; enable it when the repo can support the cost.
- If typed linting cannot find a TSConfig for config files or scripts, add an explicit lint TSConfig or exclude those files intentionally.
- Do not replace `tsc --noEmit` with ESLint; linting and type checking catch different failures.

## Prettier Separation

- Use Prettier for formatting.
- Use ESLint for code-quality and correctness rules.
- Add `eslint-config-prettier` when ESLint stylistic rules conflict with Prettier.
- Avoid running Prettier as an ESLint rule by default; it is slower and noisier than running Prettier directly.
- Prefer `prettier --check .` in CI and `prettier --write .` only when formatting is in scope.

## Completion Checks

When lint or format config changes, run the package's equivalent of:

```bash
pnpm exec eslint .
pnpm exec prettier --check .
pnpm exec tsc --noEmit
```

If a framework owns the commands, use its package scripts instead and report
the mapping.
