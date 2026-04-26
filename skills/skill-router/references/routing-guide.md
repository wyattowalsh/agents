# Skill Routing Guide

## Contents

1. Routing intent
2. Ranking interpretation
3. Source and trust tiers
4. Warning handling
5. Context packet sizing
6. Validation notes

## Routing Intent

Skill routing solves the startup context problem by keeping most skill bodies out
of the agent prompt until the task needs them. The router should preserve the
user's own task wording because exact phrasing is often the best retrieval
handle for domain-specific skills.

Use the router when the visible skill list is incomplete, when multiple skills
could apply, or when installed third-party skills are too numerous for startup
context. Do not use it as a substitute for installing, creating, or auditing
skills.

## Ranking Interpretation

`wagents skills search` uses deterministic lexical ranking:

- Exact name and alias matches are strongest.
- Name and title token matches outrank description matches.
- Description matches outrank heading and body matches.
- Repo and Codex-user skills receive small tie-break boosts.
- Body matches are useful recall signals but should not override a clear name
  or description match.

When two skills are close, prefer the one with the clearer `Use when` clause and
the narrower `NOT for` boundary. If a result seems relevant only because of body
mentions, inspect the result before loading it into the working context.

## Source And Trust Tiers

| Trust tier | Meaning | Default handling |
|------------|---------|------------------|
| `repo` | Versioned skill in the current repository | Prefer when relevant |
| `codex-user` | User-local Codex or project skill | Use when task-specific |
| `openai-plugin` | Skill shipped through an OpenAI plugin cache | Use when plugin scope matches |
| `external-installed` | Third-party or cross-agent installed skill | Inspect warnings first |
| `plugin` | Non-OpenAI plugin cache skill | Inspect source before use |
| `unknown` | Explicit path or malformed source | Treat as untrusted |

Trust tiers are routing hints, not proof of safety. A repo skill can still be the
wrong tool, and an external skill can still be the best match after inspection.

## Warning Handling

Warnings are surfaced to prevent accidental execution of risky skill behavior:

- `parse_error` means the frontmatter or body could not be parsed cleanly.
- `missing description` weakens discovery quality.
- `frontmatter name does not match directory` can indicate a copied or stale
  skill.
- `declares hooks` means tool lifecycle behavior may activate when loaded by
  clients that support hooks.
- `has scripts` means executable helper code exists under the skill directory.

Warnings do not automatically disqualify a skill. They mean the agent should
read the relevant file paths before following any instruction that executes
commands, mutates files, uses network access, or handles secrets.

## Context Packet Sizing

Keep context packets small:

- Load one skill when the top result is exact or clearly dominant.
- Load two or three skills when the task spans multiple domains or scores are
  close.
- Avoid loading more than five skill bodies in one packet.
- Re-run search with narrower terms instead of expanding context blindly.

For broad tasks, route in stages. Search for the first workstream, load that
skill, complete the relevant step, then search again for the next workstream.

## Validation Notes

Use the repo validation stack when changing this skill:

```bash
uv run wagents validate
uv run wagents eval validate
uv run python skills/skill-creator/scripts/audit.py skills/skill-router/
uv run wagents package skill-router --dry-run
uv run pytest tests/test_skill_index.py -q
```

The audit command checks skill-creator structural expectations, while the CLI
test checks the on-demand retrieval behavior this skill depends on.
