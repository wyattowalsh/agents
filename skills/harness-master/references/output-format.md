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

## Ecosystem Research Report

Use this section order exactly for `research`, `candidate`, and `compare` modes:

1. `Research Scope`
2. `Source Plan`
3. `Programmatic Access Status`
4. `Candidate Table`
5. `Per-Candidate Evidence Dossier`
6. `Compatibility Matrix By Harness`
7. `Security And Credential Review`
8. `Recommended Canonical Home`
9. `Validation And Rollback Plan`
10. `Confidence And Blocked Evidence`
11. `Apply Boundary`

## Candidate Table

Each candidate row must include:

- candidate name or URL
- category: `config`, `plugin`, `extension`, `mcp`, `skill`, or `all`
- target harnesses
- top evidence sources
- score verdict: `adopt`, `inspect`, `global-only`, `docs-only`, `quarantine`, or `avoid`
- support-tier recommendation
- highest unresolved risk
- next validation step

## Evidence Dossier

Each dossier must separate:

- official or `llms.txt` evidence
- local repo registry evidence
- GitHub REST/search discovery evidence
- GitHub GraphQL enrichment evidence
- package registry evidence
- MCP registry evidence
- Agent Skill registry or `npx skills add --list` evidence
- security and vulnerability evidence
- issue, release, changelog, discussion, or community evidence

Never merge community sentiment into authority or validation evidence. Community-only positive evidence can justify `inspect` at most.

## Programmatic Access Status

For each source used or skipped, report:

- source id
- access method
- auth environment variables, if any
- dry-run URL or command shape
- expected evidence fields
- status: `ready`, `missing-env`, `rate-limited`, `unavailable`, `manual-only`, or `skipped`
- confidence impact

## Research Scorecard

Use these dimensions:

- `authority`
- `programmatic-evidence`
- `harness-fit`
- `overlap-dry`
- `install-friction`
- `maintenance`
- `popularity`
- `security`
- `permissions-auth-risk`
- `validation-path`
- `rollback-path`

Score each `0-3`. The final recommendation must map to one verdict:

- `adopt`: strong evidence, low risk, clear validation and rollback.
- `inspect`: promising but missing evidence, validation, or local fit.
- `global-only`: useful but belongs only in user/global config, not repo source.
- `docs-only`: useful as documentation or watchlist context, not an implementation candidate.
- `quarantine`: possible value but must be isolated because of credential, auth, proxy, offensive, destructive, or broad-permission risk.
- `avoid`: weak, stale, duplicative, unmaintained, unsafe, or community-only evidence.

## Support Tier Mapping

- `validated`: local fixture evidence and rollback coverage exist.
- `repo-present-validation-required`: repo source exists but fixtures still need to prove behavior.
- `planned-research-backed`: external evidence is good but no local support exists.
- `experimental`: UI/cloud/desktop behavior remains mostly blind or hard to validate.
- `quarantine`: credentials, auth bridging, proxying, offensive tooling, broad destructive tools, or broad permission risk.

## Apply Boundary

Every ecosystem research report must state:

- no files were edited
- no tools were installed
- no generated docs were updated
- research findings cannot be applied without a matching dry-run audit and explicit approval

## Usage Review Report

Use this section order exactly for `usage` mode:

1. `Usage Scope`
2. `Source Plan`
3. `Privacy And Redaction Boundary`
4. `Collected Aggregate Signals`
5. `Usage Scorecard`
6. `Findings`
7. `Recommendation Lanes`
8. `Instrumentation Gaps`
9. `Confidence And Blocked Evidence`
10. `Apply Boundary`

## Usage Signal Shape

Each signal must include:

- `category`: `token-cost`, `tool-friction`, `mcp-usage`, `skill-usage`, `plugin-usage`, `subagent-usage`, `context-health`, `approval-safety`, `observability-gap`, or `workflow-fit`
- `source_id`
- `privacy_class`
- `harness`
- `level`
- `window_days`
- sanitized aggregate value or presence state
- confidence: `high`, `medium`, or `low`
- blocked evidence, if any

## Usage Scorecard

Use these dimensions:

- `source-coverage`
- `privacy-safety`
- `cost-token-posture`
- `tool-efficiency`
- `mcp-hygiene`
- `skill-fit`
- `plugin-fit`
- `context-health`
- `approval-safety`
- `recommendation-actionability`

Score each `0-3`, then summarize with one verdict:

- `well-instrumented`
- `usable-with-gaps`
- `under-instrumented`
- `unsafe-to-review`

## Usage Recommendation Lanes

Each recommendation must map to exactly one lane:

- `keep`: current posture is supported by evidence
- `tune-config`: needs a config change, but only after matching dry-run Audit approval
- `tune-skill`: improve or route Agent Skill usage
- `tune-mcp`: adjust MCP ownership, overlap, or validation
- `tune-plugin`: adjust plugin choice or placement
- `tune-workflow`: change how the harness is used without config edits
- `instrument`: add or enable safer aggregate telemetry before changing behavior
- `defer`: evidence is too incomplete for action
- `do-not-change`: risk outweighs benefit

## Usage Apply Boundary

Every Usage Review report must state:

- no files were edited
- no tools were installed
- no raw session bodies, raw prompts, raw traces, secret files, or credential values were collected or printed
- usage findings cannot be applied without a matching dry-run Audit and explicit approval
