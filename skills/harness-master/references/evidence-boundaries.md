# Evidence Boundaries

## Evidence Classes

Use exactly one of these tags on every finding:

- `verified-file` — directly supported by a local file or directory that was actually read
- `verified-doc` — directly supported by current first-party docs or canonical vendor docs
- `repo-observed` — inferred from the current repository's actual harness wiring or generation logic
- `blind-spot` — relevant surface or behavior exists, but cannot be directly observed from the current session

## Blind-Spot Rules

- Blind spots must be reported explicitly.
- Blind spots lower confidence.
- Blind spots never justify invented behavior.
- If a recommendation depends on a blind spot, either ask a focused follow-up question or keep the recommendation provisional.
- Web, cloud, and desktop-app UI settings are blind spots unless the current session has a verified export or local config file.
- Repo-observed filesystem conventions, such as `.perplexity/skills`, must not be upgraded to `verified-doc` without current first-party evidence.

## Alias And Facet Rules

- Alias normalization must preserve evidence boundaries. For example, `cursor-cli` and `cursor-cloud` normalize to `cursor`, but CLI and cloud blind spots still need explicit reporting.
- Aggregate aliases must expand deterministically. `github-copilot` expands to `github-copilot-web` and `github-copilot-cli`; do not collapse their findings into one mixed section.
- Desktop-app harnesses such as `claude-desktop`, `chatgpt`, `perplexity-desktop`, and `cherry-studio` can have no install agent name. Report them as config/app surfaces, not Skills CLI targets.

## Confidence Guidance

- `high confidence` — recommendation is supported by direct file evidence and current official docs
- `medium confidence` — recommendation is supported by either direct file evidence or current official docs, plus reasonable synthesis
- `low confidence` — recommendation depends on a blind spot, stale docs access, or repo-observed behavior without direct first-party confirmation

If confidence is `low`, prefer patch previews only when the edit is directly justified by file evidence.

## Contradiction Policy

If official docs and the observable repo disagree:

1. report both
2. tag the codebase fact as `verified-file`
3. tag the docs fact as `verified-doc`
4. explain the contradiction plainly
5. recommend the least risky path to reconcile them

If the contradiction blocks safe apply behavior, stop after the dry-run report and ask the user to confirm the intended authority before editing.

## Generated And Merged Files

Use `repo-observed` when the repository's generation or sync logic explains how a surface should be managed.

Examples:

- generated project instructions derived from a canonical source
- merged global config files with managed and unmanaged sections
- symlinked entrypoints or skill directories

When a generated or merged surface is wrong, recommend changing the canonical source first if the evidence supports that conclusion.

## Apply-Phase Boundary

`Apply Approved` is allowed only when:

- the user explicitly approves the reviewed batch
- the reviewed scope still matches the requested scope
- no unresolved blind spot makes the change unsafe

If those conditions are not met, rerun audit first.

## Usage Privacy Classes

Use these classes when collecting or reporting usage evidence:

- `aggregate-safe` — totals, counts, rates, status, or score summaries that cannot expose prompts, secrets, or raw traces
- `metadata-safe` — file presence, top-level keys, command availability, plugin names, timestamps, sizes, and non-secret identifiers
- `sanitized-export` — exported data explicitly sanitized by the source tool before the agent sees it
- `credential-presence` — boolean presence or absence of required environment variables or auth files; never print values
- `raw-sensitive` — raw prompts, raw completions, traces, reasoning parts, session bodies, database message rows, or unsanitized logs
- `secret-file` — `.env*`, auth databases, keys, tokens, credential JSON, WakaTime keys, Langfuse keys, provider credentials, and similar secrets
- `manual-only` — UI/cloud/dashboard evidence that the user must inspect or export manually before it is usable

Usage Review can collect `aggregate-safe`, `metadata-safe`, `sanitized-export`, and `credential-presence` evidence. `raw-sensitive` and `secret-file` sources are out of scope. `manual-only` sources may be listed as blocked evidence but must not be invented.

## Usage Evidence Boundaries

- Absence of telemetry is an `observability-gap`, not proof of low usage.
- Aggregate token or cost spikes can justify `instrument`, `tune-workflow`, or a later dry-run Audit, but not immediate edits.
- Tool, MCP, skill, and plugin recommendations must identify whether evidence came from actual usage, configuration presence, or only command availability.
- Never include raw transcript snippets, raw prompts, raw tool inputs, raw traces, or credential values in Usage Review output.
- Direct database reads are allowed only for schema or path discovery. Raw message, prompt, completion, trace, or reasoning rows are not allowed.
