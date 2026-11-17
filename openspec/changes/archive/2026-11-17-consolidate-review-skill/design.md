## Architecture

`review` is a compact router plus a set of on-demand references and helper scripts. `SKILL.md` owns the portable public contract, dispatch table, output contract, safety gates, and resource index. Detailed protocols stay in `references/` and deterministic helpers stay in `scripts/`.

## Portable Skill Contract

`skills/review/SKILL.md` uses only broadly accepted skill metadata plus Claude-compatible UI hints:

| Field | Decision |
| --- | --- |
| `name` | `review` |
| `description` | One concise dispatch-focused sentence covering session/scoped/PR/audit/simplify/source review |
| `argument-hint` | Exposes common invocation forms without making harness-specific assumptions |
| `license` | `MIT` |
| `user-invocable` | `true` |
| `metadata.version` | `"1.0.0"` |
| root `model` | omitted; model selection remains harness-owned |
| root `hooks` | omitted; hook behavior is handled by harness-specific config/projection only after validation |

## Dispatch Model

| Input | Mode |
| --- | --- |
| empty + changed files | session review |
| empty + no changed files | mode menu; no implicit full audit |
| file or directory | scoped review |
| `audit` | full repository audit |
| PR number/URL or git range | PR/range review |
| `simplify analyze|apply|explain <target>` | behavior-preserving simplification lens |
| `source triage|inspect|commands|provenance|decision|scan <source-or-path>` | source/provenance lens |
| `--lens <name>` | specialist lens overlay |
| `history`, `diff`, `delta`, `learnings` | review state and false-positive memory modes |
| `--format sarif`, `--format conventional` | output format modifiers |
| `fix|apply approved findings` | approval-gated post-review edit pass |

## Harness Optimization

Harness-specific optimization is evidence, not frontmatter bloat.

| Harness | Policy |
| --- | --- |
| Claude Code | Portable `SKILL.md` plus validated package/eval/hook checks. Skill-scoped hooks are allowed only when `validate_hooks.py` and package dry-run prove them. |
| Codex | Discover through repo/plugin skill packaging and sync. Cross-session hook behavior belongs in `config/hook-registry.json` and Codex rendering, not skill frontmatter. |
| OpenCode | Discover from repo `opencode.json` `skills.paths`. Runtime models, plugins, and overlays stay in OpenCode config. |
| Grok Build CLI | Treat as Claude-compatible skill discovery plus `.grok/skills` mirroring. Validate with sync dry-run and `wagents grok doctor` when available. |
| Other Skills CLI targets | Keep prompt portable and verify additive sync dry-runs per target. |

## Migration Model

`honest-review`, `simplify`, and `external-skill-auditor` are removed as first-party skill directories and catalog entries. Historical mentions may remain only as migration or research evidence; active routing, install commands, generated catalog rows, README tables, and invocable skill surfaces point to `/review`, `/review simplify`, or `/review source`.

`code-reviewer` and `security-auditor` stay read-only agents. Their prompts instruct the agent to use the `/review` protocol and appropriate lens while preserving their no-edit boundary.

## Research And Trust Model

The external research artifact records query evidence, source owners, candidate skills, classification, duplicate clusters, trust risks, and synthesis outcomes. Third-party review skills remain external catalog evidence and are not copied into `skills/`.

## Safety Model

Read-only review is the default. File edits are allowed only after the user explicitly approves selected findings or invokes `simplify apply` on a target that passes the behavior-preservation gate. The skill must reject feature work, broad rewrites, unbounded simplification, source installs, and unapproved fix requests.
