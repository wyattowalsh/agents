# Output Format

## Per-Harness Report

Use this section order exactly:

1. `Harness`
2. `Level`
3. `Files Reviewed`
4. `Docs Checked`
5. `Project Context Summary`
6. `Blind Spots`
7. `Scorecard`
8. `Findings`
9. `Recommended Changes`
10. `Proposed Patch Preview`
11. `Confidence`

## Finding Shape

Every finding must include:

- severity: `high`, `medium`, or `low`
- affected surface
- evidence tag
- problem statement
- why it matters for this project
- recommended fix
- correct home for the fix

## Scorecard

Use these dimensions:

- `official-correctness`
- `scope-correctness`
- `project-fit`
- `instruction-layering`
- `mcp-hygiene`
- `permission-safety`
- `dryness`
- `generated-file-integrity`
- `portability`
- `maintainability`

Score each `0-3`, then summarize with one verdict:

- `strongly-aligned`
- `mostly-aligned`
- `needs-tuning`
- `materially-misaligned`

## Patch Preview Rules

- Show a diff-style patch preview when the correct edit is obvious.
- Show replacement snippets when a diff would be noisy.
- Do not show patch previews for blind-spot-dependent fixes.

## Cross-Harness Synthesis

When 2+ harnesses are reviewed, add:

1. `Shared Issues`
2. `Conflicting Conventions`
3. `Duplicated Instructions`
4. `DRY Opportunities`
5. `Suggested Cleanup Order`

Keep cross-harness synthesis separate from the per-harness sections.

## Facet Reporting

- If an alias expands to multiple canonical harnesses, such as `github-copilot`, produce separate per-harness reports for each expanded target.
- If a facet alias normalizes to one harness, such as `cursor-cli` or `cursor-cloud`, keep one `cursor` report and call out facet-specific files and blind spots inside that report.
- Desktop or web UI-only harnesses may have empty file-reviewed lists for a scope; in that case, list the blind spots instead of inventing local surfaces.
