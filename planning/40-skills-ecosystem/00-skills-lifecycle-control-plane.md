# Skills Lifecycle Control Plane

## Scope

This lane defines how local skills, script-backed capabilities, and external skill candidates move from discovery to safe promotion. It does not install, vendor, or modify skill bodies in this pass.

## Local Inventory Model

Every local skill record must capture:

- Skill path and frontmatter name.
- Whether the skill has reference files, scripts, hooks, or command substitutions.
- Whether the skill invokes external network, package manager, browser, shell, or filesystem operations.
- Validation commands required before packaging or promotion.
- Owning lane and support tier.

Script-backed capabilities require separate records for each executable entrypoint, including input files, output files, side effects, and dry-run behavior.

## Execution Risk Classes

| Class | Meaning | Required Gate |
| --- | --- | --- |
| `read-only` | Reads docs, repo files, or manifests without changing state. | Frontmatter validation and reference integrity. |
| `local-write` | Writes repo-local files or generated artifacts. | Dry-run, diff check, and rollback note. |
| `external-network` | Fetches web, package, or API content. | Source provenance, timeout, and cache/fixture plan. |
| `package-manager` | Runs npm, uv, pnpm, pip, cargo, go, or install commands. | Explicit user approval and no global install by default. |
| `secret-adjacent` | Touches auth, env, tokens, keychains, browser profiles, or credentials. | Security quarantine review before promotion. |
| `destructive` | Deletes, overwrites, force-pushes, resets, or mutates live configs. | Blocked unless a separate approved change defines safeguards. |

## CLI Conformance Requirements

Skill helper CLIs and scripts must provide:

- Stable JSON output when consumed by automation.
- Non-zero exit codes on validation failures.
- `--dry-run` or preview mode before write operations.
- Clear stderr messages that do not print secrets.
- Deterministic fixtures for success and failure paths.

## Provenance And Lockfile Requirements

External skill candidates require a source lock record before promotion:

- Source URL and canonical upstream repo.
- Pinned commit, tag, package version, or release digest.
- License and maintainer identity.
- Files copied, adapted, omitted, or rewritten.
- Executable surfaces, network behavior, and credential behavior.
- Rollback path and re-audit trigger.

## Adoption Rubric

External skills remain candidates until all gates pass:

1. Source verification succeeds against a pinned upstream.
2. License permits redistribution or adaptation.
3. Executable and secret-adjacent behavior is reviewed.
4. Frontmatter matches repo standards.
5. Package dry-run passes.
6. Docs generation and README checks remain clean or are explicitly scheduled.

Community catalogs are discovery inputs only. Official registries and first-party vendor skills can enter a higher trust review lane, but none install by default.

## Fixture Plan

Promotion fixtures must include:

- A valid minimal skill.
- A skill with references and no executable surface.
- A script-backed skill with dry-run output.
- A rejected skill with unsafe hooks or secrets behavior.
- A provenance lock record with pinned source data.
