# Docs Truth Surface Rules

## Truth Hierarchy

1. OpenSpec specs and stable child artifacts define intended behavior.
2. Registries and manifests define machine-readable support claims.
3. Planning fragments explain decisions, blockers, and handoffs.
4. Generated docs project the above sources for users.
5. Bridge instruction files mirror canonical instruction sources for specific harnesses.

## Required Labels

Docs must label claims as one of:

- validated
- repo-present-validation-required
- planned-research-backed
- experimental
- unverified
- unsupported
- quarantine

## Prohibited Claims

- Do not claim a skill is installed on a platform unless the installed-skill inventory or harness registry proves it.
- Do not claim MCP support for a harness when the registry marks it manual, experimental, suppressed, or unsupported.
- Do not merge desktop, web, CLI, and editor variants into one support row.
- Do not describe quarantine references as install candidates.

## C08 Consolidation Rule

C08 may consolidate docs only from stable source inputs. If inputs are dirty, untracked, or owned by another lane, C08 records the blocker and defers generated output.
