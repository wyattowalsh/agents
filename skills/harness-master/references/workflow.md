# Harness Master Workflow

## Contents

1. [Gate 0: Discover Surfaces](#gate-0-discover-surfaces)
2. [Gate 1: Project Context Audit](#gate-1-project-context-audit)
3. [Gate 2: Latest Guidance Refresh](#gate-2-latest-guidance-refresh)
4. [Gate 3: Per-Harness Audit](#gate-3-per-harness-audit)
5. [Gate 4: Dry-Run Report](#gate-4-dry-run-report)
6. [Gate 5: Apply Approved](#gate-5-apply-approved)
7. [Precedence And Conflict Rules](#precedence-and-conflict-rules)
8. [Degraded Mode](#degraded-mode)

## Gate 0: Discover Surfaces

Run the discovery script first when possible:

```bash
uv run python skills/harness-master/scripts/discover_surfaces.py --repo-root . --level <level> --harness <canonical-harness> [--harness ...]
```

Use the script output to:

- confirm the selected harness set and level
- identify observable files before reading them
- classify surfaces as `present`, `missing`, `generated`, `merged`, `repo-observed`, or `blind-spot`
- identify canonical sources in repos with generated harness artifacts

If the script cannot run:

1. Use `Glob` to discover the expected files and directories.
2. Use `Read` to inspect only the surfaces that exist.
3. Use `Grep` to discover project conventions or generated-file markers.
4. Note the fallback in the final report.

## Gate 1: Project Context Audit

Before recommending any harness change, inspect the repository itself.

Always read:

- `README.md`
- `AGENTS.md`
- the harness-facing project files present in the repo
- at least one package/build manifest when present (`pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`)

Read additional context when relevant:

- CI workflows
- docs or release tooling
- repo-native sync or generation scripts
- instruction-layering files such as `.claude/rules/**`, `.cursor/rules/**`, `.github/instructions/**`

In this repository, treat these as especially important:

- `scripts/sync_agent_stack.py`
- `config/tooling-policy.json`
- `config/sync-manifest.json`

They explain which harness surfaces are canonical, merged, generated, or symlinked.

## Gate 2: Latest Guidance Refresh

Load `references/latest-doc-sources.md`.

Use this order:

1. `llms.txt` or equivalent official index
2. first-party docs pages
3. canonical vendor repo docs
4. general web fallback only if the above are unavailable

Capture which docs were actually checked. Never claim `latest` without a current source.

## Gate 3: Per-Harness Audit

Audit each harness independently.

For each harness:

1. Load the relevant surface table from `references/harness-surfaces.md`.
2. Load the matching checklist from `references/harness-checklists.md`.
3. Compare the current observable config to latest official guidance.
4. Compare the config to the repository's actual workflow and constraints.
5. Check for duplicated or conflicting instructions.
6. Check for generated-vs-canonical drift.
7. Tag every finding with an evidence class.

Do not jump to cross-harness synthesis until every selected harness has a complete report.

## Gate 4: Dry-Run Report

Load `references/output-format.md`.

The dry-run report must:

- include the exact files reviewed
- list the docs checked
- call out blind spots
- classify findings by severity and evidence
- show patch previews when the edit is obvious
- stop and wait for explicit user approval before any write or install step

## Gate 5: Apply Approved

`Apply Approved` is only valid when the immediately preceding `harness-master` dry-run report in the same session already covered the same harness set and level.

Before editing:

1. Restate the approved scope.
2. Restate the approved batch.
3. Confirm whether the user approved all fixes or only a subset.

Apply rules:

- change the smallest approved batch only
- do not broaden scope silently
- prefer canonical sources over generated outputs
- if the user approved an install step, use the exact command from `references/install-guidance.md`

After edits:

1. rerun the discovery script for touched harnesses
2. rerun targeted dry-run checks
3. summarize what changed and what remains

## Precedence And Conflict Rules

Use these precedence rules when `level` is `both`:

- report project and global findings separately first
- identify the authoritative surface for the harness before recommending edits
- if the same policy appears in both project and global surfaces, prefer the narrowest scope that actually controls the behavior
- when a generated file conflicts with a canonical source, recommend changing the canonical source first
- if authoritative precedence is unclear from evidence, mark a blind spot instead of inventing a resolution

## Degraded Mode

Enter degraded mode when:

- official docs cannot be fetched
- the discovery script cannot run and manual discovery is incomplete
- the relevant global surfaces are inaccessible from the current session

Degraded mode rules:

- lower confidence explicitly
- keep findings grounded in observable files
- avoid “latest” claims without current evidence
- prefer patch previews only for issues directly supported by codebase evidence
