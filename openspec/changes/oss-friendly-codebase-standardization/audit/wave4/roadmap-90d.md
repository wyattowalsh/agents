# 90-Day OSS Roadmap

Generated: 2026-06-15

## Phase 1 — Unblock strangers (Weeks 1–4)
| Item | Findings | Effort |
|------|----------|--------|
| Path-neutral sync-manifest + mcp.json template | P0-001, W1-005, W2-DX-01 | M |
| Relative instruction includes | W1-001, W1-HARNESS-B-001 | S |
| CI path-leak grep (exclude .example) | P0-003, W2-SEC-01 | S |
| Gitignore .claude/settings.local.json | W1-006 | S |
| Root START-HERE.md | W2-DX-03, W1-ASSETS-DOCS-005 | S |

## Phase 2 — Honest harness claims (Weeks 5–8)
| Item | Findings | Effort |
|------|----------|--------|
| Public harness tier matrix + fixture status | P0-002, W1-007 | M |
| Codex adapter MVP | W1-003, W1-T-02 | L |
| Copilot/Gemini adapter stubs → minimum | W1-HARNESS-B-004 | L |
| MCP default-deny tools policy | W1-T-20, W2-SEC-03 | L |
| --format json on install/update/readme | W1-T-03 | M |

## Phase 3 — Governance & polish (Weeks 9–12)
| Item | Findings | Effort |
|------|----------|--------|
| OpenSpec artifact completeness gate | W2-OS-002, 009–011 | M |
| Quarantine runtime enforcement | W2-SEC-04 | L |
| Catalog trust badges + custom-first IA | W1-ASSETS-DOCS-006, 011 | M |
| Security test suite (bearer, MCP policy) | W2-SEC-11 | L |
| Thin sync_agent_stack → platform adapters | W1-T-01 | L |

## Success metrics
- Path leak count in tracked config: **0** `/Users/ww/`
- Stranger onboarding time-to-first-PR path: **≤30 min** documented
- At least **3 harnesses** reach fixture-executable (not plan-only)
- register-v2 P0 findings addressed or accepted with documented exceptions
