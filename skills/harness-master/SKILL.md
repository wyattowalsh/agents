---
name: harness-master
description: >-
  Audit harness configs and apply fixes. Use when tuning Claude Code, Codex,
  Cursor, Gemini CLI, Antigravity, Copilot, or OpenCode. NOT for agents
  (agent-conventions) or MCP servers (mcp-creator).
argument-hint: "[project|global|both] [claude-code|codex|cursor|gemini-cli|antigravity|github-copilot|opencode|cherry-studio|all ...]"
model: opus
license: MIT
compatibility: >-
  Dry-run analysis first. Web access recommended for latest-doc checks. Optional
  Python 3.12+ for the surface discovery script.
metadata:
  author: wyattowalsh
  version: "1.0.0"
---

# Harness Master

Audit AI harness configuration quality, then apply approved fixes in the same session.

**NOT for:** creating agents (agent-conventions), building MCP servers (mcp-creator), or generic code review without harness/config focus (honest-review).

**Input:** the argument string after the skill name — harness names, level selection, `apply approved`, `install`, or natural-language harness requests.

## Dispatch

| `$ARGUMENTS` | Mode | First move |
|--------------|------|------------|
| `Empty` | Intake | Ask for harnesses or `all`, then ask for `project`, `global`, or `both` |
| `all` | Intake | Ask only for level |
| `all <level>` / `<level> all` | Audit | Dry-run all 8 harnesses in deterministic order |
| `<harness...>` | Intake | Resolve one or more harnesses, then ask only for missing level |
| `<level>` | Intake | Resolve level, then ask only for missing harnesses |
| `<harness...> <level>` / `<level> <harness...>` | Audit | Run dry-run review for the selected harnesses and level |
| `apply approved` | Apply Approved | Apply the last matching dry-run batch only if the user already approved it in this session |
| `apply <harness...> <level>` / `apply <level> <harness...>` | Apply Approved | Apply only if the same scope was already reviewed and approved in this session; otherwise rerun audit first |
| `install <harness...>` | Install Guidance | Show exact `npx skills add ...` commands only; do not edit configs |
| Natural language: "review/audit/check/tune <harness> config" | Audit | Normalize harnesses + level, then run dry-run review |
| Natural language approval like "approved", "do it", "apply those changes" | Apply Approved | Continue only if the immediately preceding `harness-master` review matches the scope and is still current |
| Requests to create agents or MCP servers | Refuse + redirect | Redirect to the correct specialized skill |
| Unsupported harness names | Refuse + clarify | List supported harnesses and ask the user to choose from that set |

### Empty-Args Handler

If the user invokes `/harness-master` with no arguments:

1. Ask which harnesses to review or whether to use `all`.
2. Ask for `project`, `global`, or `both`.
3. Explain that the first pass is always dry-run only.

## Input Normalization

- Supported harnesses: `claude-code`, `codex`, `cursor`, `gemini-cli`, `antigravity`, `github-copilot`, `opencode`, `cherry-studio`
- Supported levels: `project`, `global`, `both`
- Harness aliases:
  - `claude`, `claude-code` -> `claude-code`
  - `codex` -> `codex`
  - `cursor` -> `cursor`
  - `gemini`, `gemini-cli` -> `gemini-cli`
  - `antigravity`, `google-antigravity` -> `antigravity`
  - `copilot`, `gh-copilot`, `github-copilot` -> `github-copilot`
  - `opencode`, `open-code` -> `opencode`
  - `cherry`, `cherry-studio` -> `cherry-studio`
- Level aliases:
  - `project`, `repo`, `local` -> `project`
  - `global`, `user` -> `global`
  - `both`, `all-levels` -> `both`
- Split multiple harnesses on commas and whitespace.
- If the user supplies both `all` and named harnesses, ask which form they want.
- Deterministic `all` order: `claude-code`, `codex`, `cursor`, `gemini-cli`, `antigravity`, `github-copilot`, `opencode`, `cherry-studio`
- Unknown tokens are never guessed. Ask one focused clarification question.

## Classification Gate

1. Parse `$ARGUMENTS` into harnesses, level, `all`, install intent, apply intent, and unresolved tokens.
2. If unresolved tokens remain, ask a single clarification question before continuing.
3. If the request is `install ...`, run Install Guidance only.
4. If the request is `apply ...` or an approval phrase, run Apply Approved only if the matching dry-run review already exists in this session. Otherwise rerun audit first.
5. If the request includes unsupported harnesses, refuse cleanly and list the supported set.
6. If harnesses are missing, ask only for harnesses or `all`.
7. If the level is missing, ask only for `project`, `global`, or `both`.
8. Otherwise run Audit in dry-run mode.

## Workflow

### Mode A: Audit (default, dry-run first)

1. **Gate 0 — Discover surfaces**
   - Run:
     ```bash
     uv run python skills/harness-master/scripts/discover_surfaces.py --repo-root . --level <level> --harness <canonical-harness> [--harness ...]
     ```
   - Parse the JSON output and classify each surface as `present`, `missing`, `generated`, `merged`, `repo-observed`, or `blind-spot`.
   - If the script cannot run, fall back to manual discovery with `Glob`, `Read`, and `Grep`.

2. **Gate 1 — Inspect project context before recommending fixes**
   - Read the repo's intent and operating model first: `README.md`, `AGENTS.md`, harness-facing project files, key manifests, CI/workflow signals, and repo-native orchestration logic when present.
   - In this repository, treat the repo-level harness sync script together with `config/tooling-policy.json` and `config/sync-manifest.json` as canonical context for managed/generated/merged harness surfaces.

3. **Gate 2 — Refresh latest official guidance**
   - Read `references/latest-doc-sources.md`.
   - Use `llms.txt` first when available, then first-party docs, then canonical vendor repo docs, then web fallback only if needed.
   - If official docs are unavailable, enter degraded mode and lower confidence.

4. **Gate 3 — Audit each selected harness independently**
   - Load `references/harness-surfaces.md`, `references/harness-checklists.md`, and `references/evidence-boundaries.md` selectively for the selected harnesses only.
   - For `both`, compare project/global precedence before recommending edits.
   - Mark generated surfaces explicitly. Prefer fixing the canonical source over directly editing generated output.
   - Treat missing native surfaces as evidence to assess, not automatic failure.

5. **Gate 4 — Report dry-run findings**
   - Use the structure in `references/output-format.md`.
   - Every finding must include severity, affected surface, evidence tag, why it matters for this project, and the correct home for the fix.
   - Show concrete patch previews when the correct change is clear.
   - Stop after the dry-run report and wait for explicit user approval.

### Mode B: Apply Approved

1. Apply only after an explicit approval gate.
2. Approval is valid only when the immediately preceding `harness-master` dry-run review in the same session already covered the same harness set and level.
3. If the reviewed scope is stale, missing, ambiguous, or contradicted by new evidence, rerun Audit before editing.
4. Restate the approved batch before making changes.
5. Apply the smallest approved batch only. Do not broaden scope silently.
6. If the approved remediation is an install step, use the exact `npx skills add ...` guidance from `references/install-guidance.md`.
7. After edits, rerun surface discovery and targeted dry-run checks for the touched harnesses, then summarize remaining gaps.

## Scaling Strategy

| Scope | Strategy |
|-------|----------|
| 1 harness, 1 level | Inline review with one per-harness report |
| 2-3 harnesses or `both` on 1 harness | Review each harness independently, then add a short synthesis |
| 4-7 harnesses or `all` | Keep per-harness sections strict, batch discovery/research where possible, then finish with a cross-harness synthesis and ranked cleanup order |

## Latest-Doc Lookup Policy

Use the most current authoritative guidance available:

1. `llms.txt` or equivalent official index
2. First-party docs pages for config, instructions, rules, MCP, and permissions
3. Canonical vendor repo docs if first-party product docs are incomplete
4. Web fallback only when the above are unavailable

Never claim `latest` without evidence from a current source.

## Per-Harness Review Contract

- Review each harness independently before writing any synthesis.
- Tag every finding as `verified-file`, `verified-doc`, `repo-observed`, or `blind-spot`.
- Surface the authoritative, secondary, generated, and merged config surfaces for the selected level.
- For `both`, report project/global conflicts before recommending changes.
- If a harness-specific native surface is not observable from the current session, mark it as a blind spot instead of inventing behavior.
- Antigravity project-level advice must clearly separate first-party documented global behavior from repo-observed compatibility assumptions.

## Install Guidance Contract

- Load `references/install-guidance.md` only when the user asks how to install `harness-master`, or when missing skill availability is the actual root cause.
- Default surfaced form:
  ```bash
  npx skills add <source> --skill harness-master -y -g --agent <agent>
  ```
- Do not recommend install commands for native config problems.
- Do not suggest project-local install by default. Mention `wagents install --local` only if the user explicitly asks for project-local installation.

## Cross-Harness Synthesis Contract

After all per-harness reviews, synthesize:

- Shared issues across harnesses
- Conflicting conventions or precedence rules
- Duplicated instruction sources or MCP definitions
- Generated-vs-canonical drift patterns
- Highest-leverage cleanup order if the user wants a follow-up apply batch

## Output Contract

Every per-harness report must include:

1. Harness
2. Level
3. Files Reviewed
4. Docs Checked
5. Project Context Summary
6. Blind Spots
7. Scorecard
8. Findings
9. Recommended Changes
10. Proposed Patch Preview
11. Confidence

Then add a cross-harness synthesis section when 2+ harnesses were reviewed.

## Reference File Index

| File | Content | Read When |
|------|---------|-----------|
| `references/workflow.md` | Gate-by-gate audit/apply workflow, precedence rules, degraded mode, and approval gate details | Audit, Apply Approved |
| `references/latest-doc-sources.md` | Official `llms.txt` and docs URLs per harness, plus fallback order | Latest-doc refresh |
| `references/harness-surfaces.md` | Project/global surfaces, precedence, install agent names, generated/merged notes | Surface interpretation |
| `references/harness-checklists.md` | Per-harness audit checklist and edge cases | Per-harness review |
| `references/evidence-boundaries.md` | Evidence tags, blind-spot handling, and contradiction policy | Reporting findings |
| `references/install-guidance.md` | Exact `npx skills add ...` commands, when to surface them, and anti-patterns | Install Guidance |
| `references/output-format.md` | Per-harness and cross-harness report templates | Final output |

Read only the references needed for the active step. Do not preload all references.

## Canonical Vocabulary

Use these terms exactly throughout:

| Term | Meaning | NOT |
|------|---------|-----|
| `harness` | One supported agent/runtime target | `editor`, `toolchain` |
| `level` | `project`, `global`, or `both` scope for the review | `environment` |
| `project surface` | Repo-local file or generated artifact used by a harness | `global config` |
| `global surface` | User-level harness config outside the repo | `project file` |
| `dry-run` | Findings + patch preview only; no edits | `apply` |
| `approval gate` | Explicit user consent required before edits | `implied approval` |
| `blind-spot` | A surface or behavior that is not observable in the current session | `guess` |
| `repo-observed` | Behavior inferred from the current codebase's real harness wiring | `official-doc evidence` |
| `patch preview` | Proposed diff or snippet shown before edits | `applied change` |
| `canonical source` | The file or config that should be changed instead of a generated output | `generated surface` |

## Critical Rules

1. Every new `harness-master` run starts in dry-run audit mode.
2. Never edit before explicit user approval.
3. `Apply Approved` is valid only after a matching dry-run review in the current session.
4. Ask only for missing inputs. Never re-ask resolved harnesses or levels.
5. Always inspect project context before recommending harness changes.
6. Always refresh latest official guidance before claiming a configuration is current or stale.
7. Mark blind spots explicitly. Do not guess hidden or UI-only settings.
8. Prefer edits to canonical sources over generated or merged outputs when this is clear from evidence.
9. Every finding must carry an evidence tag: `verified-file`, `verified-doc`, `repo-observed`, or `blind-spot`.
10. Show concrete patch previews whenever the correct edit is clear.
11. Use `npx skills add ...` only when installation is genuinely the right next step.
12. Unsupported harnesses must be refused cleanly with the supported set listed.
