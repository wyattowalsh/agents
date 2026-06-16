# OpenSpec Change Drafts (extends oss-friendly)

Generated: 2026-06-15

These packages extend `oss-friendly-codebase-standardization` — do not duplicate its scope.

## 1. `path-neutral-sync-manifest`
**Goal**: Replace absolute paths in `config/sync-manifest.json`, generated projections, and instruction shims with `REPO_ROOT` / env placeholders.  
**Findings**: P0-001, W1-005, W1-HARNESS-B-001, W2-DX-01, W2-SEC-01  
**Surfaces**: config/, scripts/sync_agent_stack.py, mcp.json generation, CI validate  
**Validation**: grep gate + `tests/test_sync_agent_stack.py` foreign-path fixtures

## 2. `harness-fixture-executable-program`
**Goal**: Promote 3 harnesses from fixture-plan-only to executable fixtures.  
**Findings**: P0-002, W1-007, W1-HARNESS-B-003  
**Surfaces**: planning/manifests/harness-fixture-support.json, tests/fixtures/  
**Validation**: CI matrix per harness

## 3. `platform-adapter-completion`
**Goal**: Implement Codex/Copilot/Gemini minimum adapters; thin sync monolith.  
**Findings**: W1-003, W1-HARNESS-B-004, W1-T-01, W1-T-02  
**Surfaces**: wagents/platforms/, scripts/sync_agent_stack.py  
**Validation**: adapter unit tests + dry-run sync

## 4. `stranger-onboarding-30min`
**Goal**: Single onboarding path for fresh clone contributors.  
**Findings**: W1-ASSETS-DOCS-005, W2-DX-03, W2-DX-12  
**Surfaces**: START-HERE.md, docs/start-here.mdx, CONTRIBUTING.md  
**Validation**: manual dry-run checklist in change validation-matrix

## 5. `mcp-contributor-safe-defaults`
**Goal**: Default-deny MCP tools; env-only bearer; opt-in tunnel/MCPHub.  
**Findings**: W1-T-18, W1-T-20, W2-SEC-02, W2-SEC-03, W2-SEC-09  
**Surfaces**: config/mcp-registry.json, mcp.json, docs/mcp/  
**Validation**: policy tests + mcphub doctor docs

## 6. `openspec-change-hygiene`
**Goal**: Enforce design/affected-surfaces/validation-matrix on active changes.  
**Findings**: W2-OS-002, 009–011  
**Surfaces**: openspec/schemas/, wagents/openspec.py validate  
**Validation**: `wagents openspec validate` in CI

## 7. `public-catalog-trust-ux`
**Goal**: Custom+curated first; trust badges on LinkCards; machine-readable external trust.  
**Findings**: W1-ASSETS-DOCS-006, 007, 011, 017  
**Surfaces**: wagents/site_model.py, docs/skills/  
**Validation**: docs build + snapshot tests
