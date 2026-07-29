# Delta: Proof-Only Downstream Regression Gates

## ADDED Requirements

### Requirement: AITK preserves the Crush flat MCP projection

Review closure SHALL retain RV-007 as a proof-only regression that verifies
AITK uses `render_flat_mcp(..., harness="crush")`, emits a flat MCP map with
`type: stdio`, and does not route through `render_client_mcp`.

#### Scenario: AITK and Crush sync tests run

- **WHEN** `uv run pytest -q tests/test_sync_agent_stack.py -k 'crush or aitk'`
  executes
- **THEN** every asserted AITK MCP entry SHALL be selected by the Crush filter
- **AND** each entry SHALL use `type: stdio`
- **AND** no removed harness mapping SHALL be reintroduced.

### Requirement: Reddit MCP Buddy retains an exact tool allowlist

Review closure SHALL retain RV-011 as a proof-only regression for the Reddit
MCP Buddy registry. Its allowed tools SHALL be exactly `browse_subreddit`,
`search_reddit`, `get_post_details`, `user_analysis`, and `reddit_explain`.

#### Scenario: Reddit MCP Buddy registry test runs

- **WHEN** `uv run pytest -q tests/test_reddit_mcp_buddy_registry.py` executes
- **THEN** the exact five tools SHALL be enabled
- **AND** no additional or missing tool SHALL pass
- **AND** wildcard or `tools_allow_all` behavior SHALL be rejected.

### Requirement: Retired harness cleanup remains semantically bounded

Review closure SHALL retain RV-013 as a proof-only regression over the
harness-retirement source and generated surfaces. Active endorsements of the
retired managed IDs and `https://github.com/google/gemini-cli` SHALL fail while
explicit historical/change-control evidence and unrelated source-name keep-set
content remain classified rather than blanket-deleted.

#### Scenario: Retirement proof runs

- **WHEN** `uv run pytest -q tests/test_retire_harness_targets.py`,
  `uv run python scripts/retire_harness_targets.py --check`, and the bounded
  generated-surface semantic scan execute
- **THEN** active source/generated endorsement of retired managed IDs and the
  retired Gemini CLI repository URL SHALL be absent
- **AND** the explicit keep-set SHALL remain intact.
