# Skill-First External Ingredients

## Objective

Collect external capabilities that should influence the repo's skills-first architecture.

## Primary skill contract

The Agent Skills specification defines a skill package as a directory with `SKILL.md` and optional `scripts/`, `references/`, and `assets/`. Required frontmatter includes `name` and `description`; optional metadata includes `license`, `compatibility`, `metadata`, and `allowed-tools`. The spec's progressive disclosure model supports context efficiency by loading metadata first, SKILL.md body on activation, and additional resources only when needed.

## Preferred lifecycle pattern

Use no-install lifecycle commands where feasible:

```bash
npx skills add <source>
npx skills find <query>
npx skills validate <path>   # exact validator command must be confirmed before CI hard-coding
```

## External skill/capability sources to evaluate

| Source | Type | Why it matters | Integration posture | Required validation |
|---|---|---|---|---|
| skills.sh / Vercel Labs skills CLI | registry + CLI | Primary discovery/lifecycle lane for open agent skills | Prefer npx install and pinned refs | CLI flags, telemetry opt-out, lockfile, source trust |
| microsoft/skills | repo/reference corpus | Large curated skill/plugin/prompt/agent collection with test-harness patterns | Mine patterns, do not vendor blindly | License, compatibility, test scenarios, skill naming |
| GitHub Awesome Copilot skills/agents | curated ecosystem | Native Copilot skill/agent examples and conventions | Use as examples for Copilot-specific projection | Maintenance, overlap, docs accuracy |
| CrewAI skills | skill pack | Shows framework-specific skill packaging for Claude/Cursor/Codex | Candidate external skill references | Dependency/security review |
| tech-leads-club/agent-skills | registry implementation | Lockfiles, content hashing, symlink guards, audit trail | Borrow architecture ideas | Maintainability and compatibility review |
| Pinecone Gemini extension | extension + skills + MCP | Example of CLI extension combining skills/scripts and MCP | Pattern for Gemini projection | Verify manifest and uv dependency behavior |

## CLI robustness criteria

Every skill with scripts must define or be tested for:

- explicit arguments;
- JSON output mode where possible;
- stable exit codes;
- idempotent behavior;
- no hidden network unless declared;
- deterministic fixture mode;
- timeout and cancellation behavior;
- safe temp-file handling;
- no secret leakage in stdout/stderr;
- pinned dependencies or lockfile coverage.

## Skill adoption statuses

- `adopt`: package can be used with little adaptation.
- `adapt`: source is useful but must be wrapped or normalized.
- `reference`: use for patterns only.
- `watch`: promising but insufficient stability.
- `reject`: unsafe, unmaintained, or redundant.
- `replace-mcp`: should replace an MCP with skill-based implementation.

## Required docs updates

- `instructions/external-skills.md`: trust model and install policy.
- `docs/skills.md`: skill package schema and lifecycle.
- `README.md`: canonical install/update commands.
- `AGENTS.md`: how agents should choose skills vs MCP.
