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
