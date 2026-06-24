# Wave 2 Cross-Cutting Report

Generated: 2026-06-15

## Scope
- **W2-SEC** (15): security, MCP bearer, quarantine, hooks, CI
- **W2-DX** (12): fresh-clone onboarding simulation
- **W2-OS** (14): OpenSpec governance and spec drift
- **W2-COMP** (9): competitive benchmark vs agentskills.io, npx skills, plugins, MCP patterns

## Executive summary

1. **Policy vs artifacts gap (security)**: `instructions/global.md` and `SECURITY.md` articulate strong trust boundaries, but committed configs (`mcp.json`, `sync-manifest.json`, `tooling-policy.json`, `opencode.json`) embed maintainer paths and permissive MCP defaults (`tools: ["*"]`).
2. **MCPHUB_BEARER_TOKEN** is a high-value central secret with tunnel/public URL exposure risk; quarantine register exists but is not runtime-enforced in sync or CI.
3. **Fresh-clone DX**: `uv sync` + `validate` succeed quickly; full stranger flow (docs dev + skills sync preview + MCPHub) takes >30 minutes and fails on path leaks before fixes.
4. **OpenSpec governance debt**: 21 active changes, many missing `design.md` / `affected-surfaces.md` / `validation-matrix.md`; durable specs lag in-flight deltas for docs-instructions and agent-assets.
5. **Competitive position is strong** on bundle coherence, skill quality (NOT-for, evals), and conservative tiering — but complexity (MCPHub, OpenSpec, sync monolith) hurts stranger adoption.

## Finding counts
| Lane | Count | P0 | P1 |
|------|-------|----|----|
| SEC | 15 | 4 | 8 |
| DX | 12 | 1 | 6 |
| OS | 14 | 0 | 8 |
| COMP | 9 | 0 | 2 |
| **Total** | **50** | **5** | **24** |

## Top 5 cross-cutting actions
1. Path-neutral sync manifest + CI grep gate (unblocks SEC-01, DX-01, P0-001)
2. MCP default-deny tool policy + env-only bearer placeholders
3. 30-minute stranger onboarding page (DX-03, DX-12, ASSETS-DOCS-005)
4. OpenSpec artifact completeness validate step (OS-002, OS-009–011)
5. Publish harness tier honesty matrix publicly (P0-002, COMP-003)

## Registers
- Expanded v1: `findings/merged/register-v1.json` (138 findings)
- Post-critique v2: `findings/merged/register-v2.json` (138 findings)
- Coverage: `findings/merged/coverage-matrix.csv` (12×8)
