# Design: Cursor Grok 4.5 High pin layers

## Pin contract

| Constant | Value |
| --- | --- |
| Canonical slug | `cursor-grok-4.5-high` |
| Forbidden (soft rule / Task) | `inherit`, `*-fast`, `composer-*`, Claude/GPT/Terra/Sol, omitting Task `model` |
| Phase B omit | Allowed (inherit High parent); deny only explicit non-High |

## Layer matrix (SSOT)

| Layer | Mechanism | Omit `model` | Wrong/fast model | Hook crash |
| --- | --- | --- | --- | --- |
| Soft rule | `.cursor/rules/cursor-models.mdc` | Agents must not omit | Agents must not pass | N/A |
| Phase A | `preToolUse` Task rewrite | Pins to High via `updated_input` | Rewrites + clears alts | **fail-open** (Task proceeds) |
| Phase B | `subagentStart` allowlist | Allow (inherit High parent) | Deny if explicit non-High | **fail-open** |
| Validate/CI | `validate_hooks` + pytest | N/A | N/A | Compensatory: projection **must** exist |

Security Enforce guards stay **fail-closed** (RV-004). Pin hooks stay **fail-open**.

## Layers

1. **Overlay (hard SSOT)** — `config/cursor-agents.json` + schema const; renders `.cursor/agents/*.md`.
2. **Rule (soft)** — `.cursor/rules/cursor-models.mdc` (`alwaysApply: true`): always pass High; ban omit/fast/inherit/other slugs; quotes layer matrix; Explore inherits High parent via operator SHOULD CLI inherit.
3. **Hooks**
   - **Phase A:** `cursor-task-model-pin-rewrite` on `preToolUse` matcher `Task` — rewrite `updated_input.model` to High; fail-open.
   - **Phase B:** `cursor-subagent-model-allowlist` on `subagentStart` — deny explicit models outside `{cursor-grok-4.5-high}` after smoke; omit allowed.
4. **Sync allowlist** — `CURSOR_HOME_RULES_ALLOWLIST` copies at least `cursor-models.mdc` to `~/.cursor/rules/`; never delete home-only orphans. Cursor-only home path must still run this before early return.
5. **Home agents** — managed-marker projection into `~/.cursor/agents/`; preserve unmarked user agents; remove only stale managed files.
6. **Local CLI/IDE (operator SHOULD)** — Operators SHOULD set `~/.cursor/cli-config.json` `exploreSubagentModel: "inherit"` and IDE picker = Grok 4.5 High. Sync SHALL NOT write `cli-config` or live `state.vscdb`; RO-verify keys only. W2-L1 is operator-owned residual (same ownership class as W2-L2).

## Out of hard lock

Parent IDE picker and CLI `exploreSubagentModel` remain user-owned until manually set. Cloud/dashboard/team admin, Bugbot, and ACP stay out of scope.
