# Agent Skills Deep Audit Ingredients

## Objective

Capture source-backed ingredients for a skills-first overhaul.

## Authoritative facts

- Agent Skills are directories with a required `SKILL.md`; optional `scripts/`, `references/`, and `assets/` directories support executable helpers, detailed docs, and static resources.
- `SKILL.md` must contain YAML frontmatter followed by Markdown body.
- Required fields are `name` and `description`; optional fields include `license`, `compatibility`, `metadata`, and experimental `allowed-tools`.
- Progressive disclosure is a core design principle: metadata loads early, the full `SKILL.md` loads on activation, supporting resources load only when needed.

Source: https://agentskills.io/specification

## Repo application

Existing `skills/` should be audited for:

- directory name equals frontmatter `name`;
- description includes what + when to use;
- scripts declare dependencies and exit codes;
- references/assets are not deeply nested;
- allowed-tools usage is marked harness-specific/experimental;
- provenance metadata is present for imported skills;
- generated docs reflect installed/local/external status.

## CLI robustness criteria

A skill script earns `cli_robust=true` only when it has:

- deterministic arguments;
- documented exit codes;
- JSON output mode where machine use is expected;
- clear stderr vs stdout behavior;
- idempotence notes;
- dry-run/preview mode for mutations;
- no credential logging;
- reproducible dependency installation.

## Skills vs instructions

Use instructions for always-on, short, general norms. Use skills for detailed workflows, scripts, examples, templates, or task-specific knowledge that should load only when relevant.

## Skills vs MCP

Use skills when work can be performed from local files, bundled references, or deterministic CLI scripts. Use MCP only when live external state, streaming interaction, OAuth, browser runtime, or remote tool discovery is actually required.
