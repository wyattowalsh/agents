# Full-audit remediation residual (updated 2026-07-13 — v10 waves)

## v10 session-review residual (executed)

| RV | Status | Evidence |
|----|--------|----------|
| **001** TLS/SNI on pin path | **Closed** | Single `client.request` path; Host + `sni_hostname`; TypeError fail-closed |
| **002** Unproven wrapper | **Closed** | `tests/test_pinned_httpx_client.py` records IP netloc + Host + SNI |
| **003** Commit hygiene | **Closed (tooling)** | Allowlist includes new tests; recipe below — **no commit until user asks** |
| **004** `pinned[0]` only | **Closed** | Multi-pin transport retry (`_MAX_PIN_TRIES=4`); 503 does not retry |

## Prior closed (summary)

E-GATE security spine, hop-safe SSRF, placeholders, secret SSOT, Bash deny, pin gate, quarantine install_command gate, hooks LinkCards, OpenCode bash deny — see git dirty tree / earlier ledger sections.

## Deferred (explicit)

| Item | Why |
|------|-----|
| Live home apply | User OK required |
| OpenSpec bulk archive | Maintainer-gated |
| Bulk MDX reclass | Policy gate; not required |
| Git commit | User must request |

## Commit recipe (when requested)

```bash
uv run python scripts/check_s0_allowlist.py
# Stage only S0 allowlist paths — never git add -A
```

## Assurance

```bash
uv run pytest tests/test_ssrf_policy.py tests/test_pinned_httpx_client.py \
  tests/mcp/test_source_url_health.py tests/test_skills_sync_pin_gate.py \
  tests/test_remediation_rg_gates.py -q
```
