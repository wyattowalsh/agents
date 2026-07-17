# Affected Surfaces

## Source Of Truth

- `planning/manifests/candidate-corpus-jul2026/raw-urls.txt`
- `scripts/generate_candidate_corpus_shards.py`
- `scripts/promote_candidate_corpus.py`
- `scripts/apply_candidate_corpus_promotions.py`
- `scripts/record_candidate_non_skill_assurance.py`
- `tests/test_candidate_corpus.py`
- `config/mcp-registry.json`
- `config/plugin-extension-registry.json`
- `scripts/mcphub/bind-loopback.cjs`
- `scripts/mcphub/start-server.sh`
- `scripts/mcphub/common.sh`
- `scripts/mcphub/doctor.sh`
- `tests/test_mcphub_loopback_bind.py`
- `docs/src/authoring/skills/*.mdx` stable source-level and selector rows
- `docs/ai-tools/mcphub.md`
- `mcp/mcphub/README.md`
- `docs/src/content/docs/mcp/index.mdx`
- `docs/src/content/docs/harness-config/mcp-registry.mdx`
- `docs/src/content/docs/harness-config/plugin-skill-ownership.mdx`
- Generated `docs/src/content/docs/surfaces/tools.mdx` and `install.mdx`
- `planning/manifests/security-quarantine-register.json`
- `openspec/changes/integrate-candidate-corpus-jul2026/*`

## Generated Or Derived Manifest Outputs

- `planning/manifests/candidate-corpus-jul2026/normalized-urls.json`
- `planning/manifests/candidate-corpus-jul2026/records/*.json`
- `planning/manifests/candidate-corpus-jul2026/*-matrix.json`
- `planning/manifests/candidate-corpus-jul2026/research-task-graph.json`
- `planning/manifests/candidate-corpus-jul2026/research-packet-schema.json`
- `planning/manifests/candidate-corpus-jul2026/raw-research-packets.json`
- `planning/manifests/candidate-corpus-jul2026/unique-target-research-packets.json`
- `planning/manifests/candidate-corpus-jul2026/subagent-wave-queue.json`
- `planning/manifests/candidate-corpus-jul2026/promotion-readiness-queue.json`
- `planning/manifests/candidate-corpus-jul2026/promotion-gate-matrix.json`
- `planning/manifests/candidate-corpus-jul2026/live-install-command-preview.json`
- `planning/manifests/candidate-corpus-jul2026/promotion-wave-plan.json`
- `planning/manifests/candidate-corpus-jul2026/promotion-wave-plan.md`
- `planning/manifests/candidate-corpus-jul2026/full-integration-progress.json`
- `planning/manifests/candidate-corpus-jul2026/full-integration-state.md`
- `planning/manifests/candidate-corpus-jul2026/non-skill-install-assurance.json`
- `planning/manifests/candidate-corpus-jul2026/existing-integration-coverage.json`
- `planning/manifests/candidate-corpus-jul2026/*report.md`
- `planning/manifests/candidate-corpus-jul2026/*decision*.md`
- `planning/manifests/candidate-corpus-jul2026/catalog-authoring-summary.json`
- `docs/public/generated-registries/skills-catalog-index.json`
- `docs/src/content/docs/skills/catalog/external/*.mdx` stable detail pages
- `docs/src/content/docs/skills/catalog/external/index.mdx`
- `docs/src/content/docs/skills/catalog/index.mdx`
- `README.md`

## Promotion Overlay Surfaces

- `docs/src/authoring/skills/*.mdx` includes promoted installable rows, 158
  stable non-syncing references, and 4 stable hard-quarantine references.
- `planning/manifests/candidate-corpus-jul2026/promotion-overrides.json`
  records reviewed install commands, selectors, attribution, and local install
  evidence.
- `planning/manifests/candidate-corpus-jul2026/applied-promotion-overrides.json`
  records the applied overlay rows.
- `planning/manifests/candidate-corpus-jul2026/catalog-authoring-summary.json`
  records the stable 121/6/158/4 target partition, 162 generated stable
  references, installable selector counts separately, and zero public
  `candidate-corpus-*` rows.
- `planning/manifests/security-quarantine-register.json` records the four
  hard-blocked source or tree targets with deny-by-default exception reviews.
- `config/mcp-registry.json` and `mcp/mcphub/mcp_settings.json` include
  disabled-by-default MCP/tool entries with placeholder-only auth. Root
  `mcp.json` intentionally omits disabled direct servers and projects only the
  managed MCPHub endpoint surface.
- The repo-owned MCPHub launcher pins upstream 1.0.24, injects a loopback-only
  HTTP bind shim, and makes doctor validation reject wildcard listeners.
- No third-party source trees were vendored into `skills/`.
- Default MCPHub groups remain credential-safe; credentialed services are not
  auto-enabled.
- Audited user-local CLI/library distributions are recorded separately from
  skill-harness installation. Native plugins record their exact enabled or
  disabled state; broad-hook plugins remain disabled.
- Every normalized target has exactly one runtime disposition, including
  explicit skill-only, collection, non-executable, and quarantine outcomes.
- Public authoring, catalog index, and generated detail pages contain zero
  `candidate-corpus-*` identities after reconciliation.
