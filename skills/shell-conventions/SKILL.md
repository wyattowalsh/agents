---
name: shell-conventions
description: >-
  Shell tooling conventions. Enforce portable bash and sh practices, quoting,
  env usage, and Make or just patterns. Use when editing shell files. NOT for
  Python or CI/CD.
user-invocable: false
disable-model-invocation: false
license: MIT
metadata:
  author: wyattowalsh
  version: "1.0"
---

# Shell Conventions

Apply these conventions whenever working on shell scripts, shell snippets,
Makefiles, or justfiles.

## Dispatch

| $ARGUMENTS | Action |
|------------|--------|
| Active (auto-invoked when editing `.sh`, `.bash`, `.zsh`, `Makefile`, or `justfile`) | Apply the conventions below |
| Empty | Display the conventions summary |
| `check` | Verify conventions only |

## Scope

- Use this skill for style, portability, safety, and repo-wide shell habits.
- Use shell-scripter when the task is generating, converting, or deeply reviewing shell code.
- Use devops-engineer for CI workflow YAML and release automation.

## Tooling Preferences

- Prefer POSIX `sh` for simple automation that does not need arrays, `[[ ]]`, or process substitution.
- Use `bash` only when the script clearly benefits from bash-only features.
- Use env-based shebangs such as `#!/usr/bin/env bash` or `#!/usr/bin/env sh`.
- Prefer built-ins and standard utilities before adding dependencies.

## Script Baseline

- For `bash`, start with `set -euo pipefail` unless there is a clear reason not to.
- For portable `sh`, use `set -eu` and avoid `pipefail`.
- Quote variable expansions unless word splitting is intentionally required.
- Use `command -v tool >/dev/null 2>&1` before depending on a non-guaranteed tool.
- Prefer explicit long flags over obscure short-flag combinations in repository automation.
- Keep shell functions short and single-purpose.

## Make and Just Conventions

- Make targets must be task-oriented and documented through a `help` target when the file is substantial.
- Use `.PHONY` for non-file Make targets.
- Keep recipes idempotent where possible.
- In Makefiles, escape `$` as `$$` inside recipes.
- In justfiles, use parameters only when they materially simplify repeated tasks.
- Do not hide destructive behavior behind vague target names.

## Naming and Structure

- Use lowercase, descriptive function names.
- Prefer `project_root`, `target_path`, or `output_file` over one-letter names.
- Keep environment variable names uppercase.
- Favor early validation and explicit usage text over silent failure.

## Critical Rules

1. Always use env-based shebangs, not hardcoded interpreter paths.
2. Quote variable expansions unless intentional splitting is required.
3. Use `bash` only when you need bash; otherwise prefer portable `sh`.
4. Do not use `eval` unless there is no safer alternative and the risk is explained.
5. Validate required external commands before first use.
6. Make or just tasks that mutate state must be named clearly and predictably.
7. Route script generation and major refactors to shell-scripter; this skill is conventions only.
