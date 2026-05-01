# Tasks

## Foundation

- [x] Read required repo and planning context.
- [x] Run requested preflight commands where allowed.
- [x] Record preflight blockers and dirty worktree state.
- [x] Create parent OpenSpec Markdown artifacts in root OpenSpec.
- [x] Create non-Markdown repo-sync inventory and drift ledger.
- [x] Create non-Markdown registry schemas and support-tier manifest.
- [x] Copy/normalize external repo evaluation manifest into root `planning/manifests/`.
- [x] Validate root OpenSpec after non-Markdown artifacts are added.
- [ ] Commit foundation changes.

## Child Change Governance

- [x] Create child OpenSpec scaffolds for every child lane.
- [x] Create or update dispatch prompts with allowed files, forbidden shared files, dependencies, validation commands, expected artifacts, commit requirement, and final response format.
- [x] Ensure child teams do not edit `README.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, parent tasks, or generated support matrices directly.

## Registry And Policy

- [x] Freeze support-tier vocabulary: `validated`, `repo-present-validation-required`, `planned-research-backed`, `experimental`, `unverified`, `unsupported`, `quarantine`.
- [x] Encode skills-first decision tree across OpenSpec specs, planning docs, manifests, and dispatch prompts.
- [x] Require every MCP record to define secrets model, transport model, sandbox model, and smoke fixture.
- [x] Require every script-backed skill to define `--help`, `--json`, `--dry-run`, or a documented exception.

## Harness Surface Coverage

- [x] Add expanded harness surface map for Claude Desktop, Claude Code, ChatGPT, Codex, GitHub Copilot Web, GitHub Copilot CLI, OpenCode, Gemini CLI, Antigravity, Perplexity Desktop, Cherry Studio, Cursor Editor, Cursor Agent Web, and Cursor Agent CLI.
- [x] Add cross-harness projection contract for instructions, skills, agents, MCP, plugins/extensions, hooks/guards, UI/control plane, and telemetry/history.
- [x] Add harness gap closure waves and per-harness missing-plan details.
- [x] Update dispatch prompts for Claude, OpenAI/Codex, Copilot, Cursor, OpenCode/Gemini/Antigravity, experimental harnesses, config safety, and docs/instructions.
- [x] Convert expanded harness surface map into non-Markdown registry fragments after plan mode ends.
- [x] Add fixture-backed support tiers for each harness variant.

## External Intake

- [x] Use `planning/manifests/external-repo-evaluation-final.json` as discovery input.
- [x] Do not install, vendor, or promote external repositories by default.
- [x] Create child tasks for source, license, security, provenance, and conformance-fixture review.
- [x] Quarantine auth-bridging, proxying, credential-sharing, and offensive-security repositories.
- [x] Add feature/domain coverage map for the external repo set.
- [x] Add per-repo coverage backlog with integrate/wrap/borrow/reference/quarantine strategies.
