# OSS Shareability Scorecard

Generated: 2026-06-15  
Change: `oss-friendly-codebase-standardization`  
Audit root: `openspec/changes/oss-friendly-codebase-standardization/audit/`

## Bottom line

The **wyattowalsh/agents** repo is a **mature, differentiated multi-harness asset bundle** with strong skill conventions, `agent-bundle.json`, OpenSpec governance, and MCPHub control plane. It is **not yet stranger-OSS-ready**: maintainer path leakage (`/Users/ww/`, 5824+ occurrences), zero validated harness fixtures, stub platform adapters, and fragmented onboarding block clean contribution from foreign machines.

## Scorecard (1–10)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Skill asset quality | 8 | NOT-for on 58/58; evals; validation tooling |
| Bundle portability | 6 | agent-bundle.json clean; sync-manifest dirty |
| Path portability | 3 | P0 blocker across configs/instructions/MCP |
| Harness tier honesty | 4 | Good registry; poor public framing |
| Security posture | 5 | Strong policy; weak MCP defaults + enforcement |
| Contributor DX | 5 | uv/validate fast; no 30-min path |
| Docs stranger UX | 5 | Generator strong; catalog overwhelms with installed |
| OpenSpec governance | 6 | Functional; incomplete active changes |
| Test/CI coverage | 7 | 76+ sync tests; thin security tests |
| Competitive differentiation | 8 | Bundle + tiers + quality vs npx-only repos |

**Overall OSS shareability: 5.5/10** — fix path neutrality + onboarding to reach 7+.

## Finding volume
- Phase 0 + Waves 1–2: **138** detailed findings
- Post-critique register: **138** accepted
- P0 count: **27**

## Top 5 stranger-first ships (90 days)
1. **Path-neutral sync** — `REPO_ROOT` placeholders in sync-manifest, mcp-registry, instruction shims; CI grep gate
2. **30-minute onboarding** — root START-HERE + docs start-here unified flow
3. **Tier honesty in public docs** — fixture-plan-only badges per harness
4. **Codex adapter minimum** — exit stub; thin sync monolith
5. **MCP contributor defaults** — opt-in MCPHub; default-deny tools; env bearer only

## Artifacts index
- Phase 0: `audit/phase0/`
- Wave 1: `audit/wave1/report-*.md`
- Wave 2: `audit/wave2/report-crosscutting.md`
- Wave 3: `audit/wave3/critique-rebuttal.md`
- Registers: `audit/findings/merged/register-v(1, 2).json`, `coverage-matrix.csv`
- Synthesis: `audit/wave4/` (this folder)
