# Subagent Task Definitions — Expanded

Generated: `2026-05-01T07:19:13Z`

Total tasks: 482

## New clusters

- `C10` — Progressive Docs Architecture
- `C11` — Agent Skills Intake and Lifecycle
- `C12` — MCP Audit and Replacement
- `C13` — Harness Idiosyncratic Ecosystem Projections
- `C14` — Plugin and Extension Packaging
- `C15` — UI/UX Automation Productization
- `C16` — Docs and AI Instructions Truth
- `C17` — Security, Provenance, and Policy-as-Code
- `C18` — Observability, Evals, and Run Graphs
- `C19` — OpenSpec Finalization and Migration

## Expanded task nodes

### C10-001: Implement progressive-disclosure-map planning artifact
- Cluster: `C10`
- Owner team: `docs-architecture`
- Risk: `low`; complexity: `S`; merge risk: `1`
- Required inputs: uploaded planning bundle, latest repo inventory
- Produced artifacts: planning/artifacts/progressive-disclosure-map.md
- Blocking dependencies: none
- CI gates: docs-truth, linkcheck
- Review: owner team review, standard review

### C10-002: Implement assumption-and-drift-ledger planning artifact
- Cluster: `C10`
- Owner team: `docs-architecture`
- Risk: `low`; complexity: `S`; merge risk: `1`
- Required inputs: uploaded planning bundle, latest repo inventory
- Produced artifacts: planning/artifacts/assumption-and-drift-ledger.md
- Blocking dependencies: none
- CI gates: docs-truth, linkcheck
- Review: owner team review, standard review

### C10-003: Implement change-portfolio planning artifact
- Cluster: `C10`
- Owner team: `docs-architecture`
- Risk: `low`; complexity: `S`; merge risk: `1`
- Required inputs: uploaded planning bundle, latest repo inventory
- Produced artifacts: planning/artifacts/change-portfolio.md
- Blocking dependencies: none
- CI gates: docs-truth, linkcheck
- Review: owner team review, standard review

### C10-004: Implement directory-readmes planning artifact
- Cluster: `C10`
- Owner team: `docs-architecture`
- Risk: `low`; complexity: `S`; merge risk: `1`
- Required inputs: uploaded planning bundle, latest repo inventory
- Produced artifacts: planning/artifacts/directory-readmes.md
- Blocking dependencies: none
- CI gates: docs-truth, linkcheck
- Review: owner team review, standard review

### C10-005: Implement docs-artifact-manifest planning artifact
- Cluster: `C10`
- Owner team: `docs-architecture`
- Risk: `low`; complexity: `S`; merge risk: `1`
- Required inputs: uploaded planning bundle, latest repo inventory
- Produced artifacts: planning/artifacts/docs-artifact-manifest.md
- Blocking dependencies: none
- CI gates: docs-truth, linkcheck
- Review: owner team review, standard review

### C10-006: Implement source-ledger-refresh planning artifact
- Cluster: `C10`
- Owner team: `docs-architecture`
- Risk: `low`; complexity: `S`; merge risk: `1`
- Required inputs: uploaded planning bundle, latest repo inventory
- Produced artifacts: planning/artifacts/source-ledger-refresh.md
- Blocking dependencies: none
- CI gates: docs-truth, linkcheck
- Review: owner team review, standard review

### C10-007: Implement repo-sync-inventory planning artifact
- Cluster: `C10`
- Owner team: `docs-architecture`
- Risk: `low`; complexity: `S`; merge risk: `1`
- Required inputs: uploaded planning bundle, latest repo inventory
- Produced artifacts: planning/artifacts/repo-sync-inventory.md
- Blocking dependencies: none
- CI gates: docs-truth, linkcheck
- Review: owner team review, standard review

### C10-008: Implement support-tier-policy-refresh planning artifact
- Cluster: `C10`
- Owner team: `docs-architecture`
- Risk: `low`; complexity: `S`; merge risk: `1`
- Required inputs: uploaded planning bundle, latest repo inventory
- Produced artifacts: planning/artifacts/support-tier-policy-refresh.md
- Blocking dependencies: none
- CI gates: docs-truth, linkcheck
- Review: owner team review, standard review

### C10-009: Implement terminology-glossary planning artifact
- Cluster: `C10`
- Owner team: `docs-architecture`
- Risk: `low`; complexity: `S`; merge risk: `1`
- Required inputs: uploaded planning bundle, latest repo inventory
- Produced artifacts: planning/artifacts/terminology-glossary.md
- Blocking dependencies: none
- CI gates: docs-truth, linkcheck
- Review: owner team review, standard review

### C10-010: Implement planning-doc-link-check planning artifact
- Cluster: `C10`
- Owner team: `docs-architecture`
- Risk: `low`; complexity: `S`; merge risk: `1`
- Required inputs: uploaded planning bundle, latest repo inventory
- Produced artifacts: planning/artifacts/planning-doc-link-check.md
- Blocking dependencies: none
- CI gates: docs-truth, linkcheck
- Review: owner team review, standard review

### C10-011: Implement generated-vs-source-classifier planning artifact
- Cluster: `C10`
- Owner team: `docs-architecture`
- Risk: `low`; complexity: `S`; merge risk: `1`
- Required inputs: uploaded planning bundle, latest repo inventory
- Produced artifacts: planning/artifacts/generated-vs-source-classifier.md
- Blocking dependencies: none
- CI gates: docs-truth, linkcheck
- Review: owner team review, standard review

### C10-012: Implement planning-doc-ownership-map planning artifact
- Cluster: `C10`
- Owner team: `docs-architecture`
- Risk: `low`; complexity: `S`; merge risk: `1`
- Required inputs: uploaded planning bundle, latest repo inventory
- Produced artifacts: planning/artifacts/planning-doc-ownership-map.md
- Blocking dependencies: none
- CI gates: docs-truth, linkcheck
- Review: owner team review, standard review

### C11-001: Validate all local skill.md frontmatter
- Cluster: `C11`
- Owner team: `skills-platform`
- Risk: `low`; complexity: `M`; merge risk: `2`
- Required inputs: skills/, agentskills.io spec, skills.sh docs, GitHub gh skill docs
- Produced artifacts: planning/artifacts/skills/001-validate-all-local-SKILL.md-frontmatter.md
- Blocking dependencies: none
- CI gates: skill-spec, script-contract, docs-truth
- Review: owner team review, standard review

### C11-002: Score local skills for progressive disclosure
- Cluster: `C11`
- Owner team: `skills-platform`
- Risk: `low`; complexity: `M`; merge risk: `2`
- Required inputs: skills/, agentskills.io spec, skills.sh docs, GitHub gh skill docs
- Produced artifacts: planning/artifacts/skills/002-score-local-skills-for-progressive-disclosure.md
- Blocking dependencies: C10-001
- CI gates: skill-spec, script-contract, docs-truth
- Review: owner team review, standard review

### C11-003: Extract skill script cli contracts
- Cluster: `C11`
- Owner team: `skills-platform`
- Risk: `low`; complexity: `M`; merge risk: `2`
- Required inputs: skills/, agentskills.io spec, skills.sh docs, GitHub gh skill docs
- Produced artifacts: planning/artifacts/skills/003-extract-skill-script-CLI-contracts.md
- Blocking dependencies: C10-001
- CI gates: skill-spec, script-contract, docs-truth
- Review: owner team review, standard review

### C11-004: Add json/dry-run/exit-code tests for scripts
- Cluster: `C11`
- Owner team: `skills-platform`
- Risk: `low`; complexity: `M`; merge risk: `2`
- Required inputs: skills/, agentskills.io spec, skills.sh docs, GitHub gh skill docs
- Produced artifacts: planning/artifacts/skills/004-add-JSON/dry-run/exit-code-tests-for-scripts.md
- Blocking dependencies: C10-001
- CI gates: skill-spec, script-contract, docs-truth
- Review: owner team review, standard review

### C11-005: Build external skill intake manifest
- Cluster: `C11`
- Owner team: `skills-platform`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: skills/, agentskills.io spec, skills.sh docs, GitHub gh skill docs
- Produced artifacts: planning/artifacts/skills/005-build-external-skill-intake-manifest.md
- Blocking dependencies: C10-001
- CI gates: skill-spec, script-contract, docs-truth
- Review: owner team review, standard review

### C11-006: Implement npx skills wrapper plan
- Cluster: `C11`
- Owner team: `skills-platform`
- Risk: `low`; complexity: `M`; merge risk: `2`
- Required inputs: skills/, agentskills.io spec, skills.sh docs, GitHub gh skill docs
- Produced artifacts: planning/artifacts/skills/006-implement-npx-skills-wrapper-plan.md
- Blocking dependencies: C10-001
- CI gates: skill-spec, script-contract, docs-truth
- Review: owner team review, standard review

### C11-007: Implement gh skill preview/install audit lane
- Cluster: `C11`
- Owner team: `skills-platform`
- Risk: `low`; complexity: `M`; merge risk: `2`
- Required inputs: skills/, agentskills.io spec, skills.sh docs, GitHub gh skill docs
- Produced artifacts: planning/artifacts/skills/007-implement-gh-skill-preview/install-audit-lane.md
- Blocking dependencies: C10-001
- CI gates: skill-spec, script-contract, docs-truth
- Review: owner team review, standard review

### C11-008: Add skill provenance lockfile
- Cluster: `C11`
- Owner team: `skills-platform`
- Risk: `low`; complexity: `M`; merge risk: `2`
- Required inputs: skills/, agentskills.io spec, skills.sh docs, GitHub gh skill docs
- Produced artifacts: planning/artifacts/skills/008-add-skill-provenance-lockfile.md
- Blocking dependencies: C10-001
- CI gates: skill-spec, script-contract, docs-truth
- Review: owner team review, standard review

### C11-009: Add skill signing/checksum plan
- Cluster: `C11`
- Owner team: `skills-platform`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: skills/, agentskills.io spec, skills.sh docs, GitHub gh skill docs
- Produced artifacts: planning/artifacts/skills/009-add-skill-signing/checksum-plan.md
- Blocking dependencies: C10-001
- CI gates: skill-spec, script-contract, docs-truth
- Review: owner team review, standard review

### C11-010: Add skill activation fixtures
- Cluster: `C11`
- Owner team: `skills-platform`
- Risk: `low`; complexity: `M`; merge risk: `2`
- Required inputs: skills/, agentskills.io spec, skills.sh docs, GitHub gh skill docs
- Produced artifacts: planning/artifacts/skills/010-add-skill-activation-fixtures.md
- Blocking dependencies: C10-001
- CI gates: skill-spec, script-contract, docs-truth
- Review: owner team review, standard review

### C11-011: Add skill non-activation fixtures
- Cluster: `C11`
- Owner team: `skills-platform`
- Risk: `low`; complexity: `M`; merge risk: `2`
- Required inputs: skills/, agentskills.io spec, skills.sh docs, GitHub gh skill docs
- Produced artifacts: planning/artifacts/skills/011-add-skill-non-activation-fixtures.md
- Blocking dependencies: C10-001
- CI gates: skill-spec, script-contract, docs-truth
- Review: owner team review, standard review

### C11-012: Generate skill docs from registry
- Cluster: `C11`
- Owner team: `skills-platform`
- Risk: `low`; complexity: `M`; merge risk: `2`
- Required inputs: skills/, agentskills.io spec, skills.sh docs, GitHub gh skill docs
- Produced artifacts: planning/artifacts/skills/012-generate-skill-docs-from-registry.md
- Blocking dependencies: C10-001
- CI gates: skill-spec, script-contract, docs-truth
- Review: owner team review, standard review

### C11-013: Audit skills.sh candidates
- Cluster: `C11`
- Owner team: `skills-platform`
- Risk: `low`; complexity: `M`; merge risk: `2`
- Required inputs: skills/, agentskills.io spec, skills.sh docs, GitHub gh skill docs
- Produced artifacts: planning/artifacts/skills/013-audit-skills.sh-candidates.md
- Blocking dependencies: C10-001
- CI gates: skill-spec, script-contract, docs-truth
- Review: owner team review, standard review

### C11-014: Audit awesome-copilot candidates
- Cluster: `C11`
- Owner team: `skills-platform`
- Risk: `low`; complexity: `M`; merge risk: `2`
- Required inputs: skills/, agentskills.io spec, skills.sh docs, GitHub gh skill docs
- Produced artifacts: planning/artifacts/skills/014-audit-awesome-copilot-candidates.md
- Blocking dependencies: C10-001
- CI gates: skill-spec, script-contract, docs-truth
- Review: owner team review, standard review

### C11-015: Audit crewai skill pack as pattern
- Cluster: `C11`
- Owner team: `skills-platform`
- Risk: `low`; complexity: `M`; merge risk: `2`
- Required inputs: skills/, agentskills.io spec, skills.sh docs, GitHub gh skill docs
- Produced artifacts: planning/artifacts/skills/015-audit-CrewAI-skill-pack-as-pattern.md
- Blocking dependencies: C10-001
- CI gates: skill-spec, script-contract, docs-truth
- Review: owner team review, standard review

### C11-016: Classify framework-specific skill packs
- Cluster: `C11`
- Owner team: `skills-platform`
- Risk: `low`; complexity: `M`; merge risk: `2`
- Required inputs: skills/, agentskills.io spec, skills.sh docs, GitHub gh skill docs
- Produced artifacts: planning/artifacts/skills/016-classify-framework-specific-skill-packs.md
- Blocking dependencies: C10-001
- CI gates: skill-spec, script-contract, docs-truth
- Review: owner team review, standard review

### C11-017: Add skill replacement plan for reasoning mcps
- Cluster: `C11`
- Owner team: `skills-platform`
- Risk: `low`; complexity: `M`; merge risk: `2`
- Required inputs: skills/, agentskills.io spec, skills.sh docs, GitHub gh skill docs
- Produced artifacts: planning/artifacts/skills/017-add-skill-replacement-plan-for-reasoning-MCPs.md
- Blocking dependencies: C10-001
- CI gates: skill-spec, script-contract, docs-truth
- Review: owner team review, standard review

### C11-018: Draft external-skills instruction doc
- Cluster: `C11`
- Owner team: `skills-platform`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: skills/, agentskills.io spec, skills.sh docs, GitHub gh skill docs
- Produced artifacts: planning/artifacts/skills/018-draft-external-skills-instruction-doc.md
- Blocking dependencies: C10-001
- CI gates: skill-spec, script-contract, docs-truth
- Review: owner team review, standard review

### C11-019: Create skill install rollback tests
- Cluster: `C11`
- Owner team: `skills-platform`
- Risk: `low`; complexity: `M`; merge risk: `2`
- Required inputs: skills/, agentskills.io spec, skills.sh docs, GitHub gh skill docs
- Produced artifacts: planning/artifacts/skills/019-create-skill-install-rollback-tests.md
- Blocking dependencies: C10-001
- CI gates: skill-spec, script-contract, docs-truth
- Review: owner team review, standard review

### C11-020: Add skill version drift detector
- Cluster: `C11`
- Owner team: `skills-platform`
- Risk: `low`; complexity: `M`; merge risk: `2`
- Required inputs: skills/, agentskills.io spec, skills.sh docs, GitHub gh skill docs
- Produced artifacts: planning/artifacts/skills/020-add-skill-version-drift-detector.md
- Blocking dependencies: C10-001
- CI gates: skill-spec, script-contract, docs-truth
- Review: owner team review, standard review

### C12-001: Audit MCP `brave-search`
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: mcp.json, MCP spec, mcp-scan docs, MCP indexes
- Produced artifacts: planning/artifacts/mcp/brave-search.md
- Blocking dependencies: C10-002
- CI gates: mcp-schema, mcp-scan, docs-truth
- Review: owner team review, standard review

### C12-002: Audit MCP `cascade-thinking`
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: mcp.json, MCP spec, mcp-scan docs, MCP indexes
- Produced artifacts: planning/artifacts/mcp/cascade-thinking.md
- Blocking dependencies: C10-002
- CI gates: mcp-schema, mcp-scan, docs-truth
- Review: owner team review, standard review

### C12-003: Audit MCP `chrome-devtools`
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: mcp.json, MCP spec, mcp-scan docs, MCP indexes
- Produced artifacts: planning/artifacts/mcp/chrome-devtools.md
- Blocking dependencies: C10-002
- CI gates: mcp-schema, mcp-scan, docs-truth
- Review: owner team review, standard review

### C12-004: Audit MCP `context7`
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: mcp.json, MCP spec, mcp-scan docs, MCP indexes
- Produced artifacts: planning/artifacts/mcp/context7.md
- Blocking dependencies: C10-002
- CI gates: mcp-schema, mcp-scan, docs-truth
- Review: owner team review, standard review

### C12-005: Audit MCP `deepwiki`
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: mcp.json, MCP spec, mcp-scan docs, MCP indexes
- Produced artifacts: planning/artifacts/mcp/deepwiki.md
- Blocking dependencies: C10-002
- CI gates: mcp-schema, mcp-scan, docs-truth
- Review: owner team review, standard review

### C12-006: Audit MCP `docling`
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: mcp.json, MCP spec, mcp-scan docs, MCP indexes
- Produced artifacts: planning/artifacts/mcp/docling.md
- Blocking dependencies: C10-002
- CI gates: mcp-schema, mcp-scan, docs-truth
- Review: owner team review, standard review

### C12-007: Audit MCP `fetch`
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: mcp.json, MCP spec, mcp-scan docs, MCP indexes
- Produced artifacts: planning/artifacts/mcp/fetch.md
- Blocking dependencies: C10-002
- CI gates: mcp-schema, mcp-scan, docs-truth
- Review: owner team review, standard review

### C12-008: Audit MCP `fetcher`
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: mcp.json, MCP spec, mcp-scan docs, MCP indexes
- Produced artifacts: planning/artifacts/mcp/fetcher.md
- Blocking dependencies: C10-002
- CI gates: mcp-schema, mcp-scan, docs-truth
- Review: owner team review, standard review

### C12-009: Audit MCP `package-version`
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `high`; complexity: `S`; merge risk: `1`
- Required inputs: mcp.json, MCP spec, mcp-scan docs, MCP indexes
- Produced artifacts: planning/artifacts/mcp/package-version.md
- Blocking dependencies: C10-002
- CI gates: mcp-schema, mcp-scan, docs-truth
- Review: owner team review, standard review

### C12-010: Audit MCP `repomix`
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: mcp.json, MCP spec, mcp-scan docs, MCP indexes
- Produced artifacts: planning/artifacts/mcp/repomix.md
- Blocking dependencies: C10-002
- CI gates: mcp-schema, mcp-scan, docs-truth
- Review: owner team review, standard review

### C12-011: Audit MCP `sequential-thinking`
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: mcp.json, MCP spec, mcp-scan docs, MCP indexes
- Produced artifacts: planning/artifacts/mcp/sequential-thinking.md
- Blocking dependencies: C10-002
- CI gates: mcp-schema, mcp-scan, docs-truth
- Review: owner team review, standard review

### C12-012: Audit MCP `structured-thinking`
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: mcp.json, MCP spec, mcp-scan docs, MCP indexes
- Produced artifacts: planning/artifacts/mcp/structured-thinking.md
- Blocking dependencies: C10-002
- CI gates: mcp-schema, mcp-scan, docs-truth
- Review: owner team review, standard review

### C12-013: Audit MCP `tavily`
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: mcp.json, MCP spec, mcp-scan docs, MCP indexes
- Produced artifacts: planning/artifacts/mcp/tavily.md
- Blocking dependencies: C10-002
- CI gates: mcp-schema, mcp-scan, docs-truth
- Review: owner team review, standard review

### C12-014: Audit MCP `trafilatura`
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `high`; complexity: `S`; merge risk: `1`
- Required inputs: mcp.json, MCP spec, mcp-scan docs, MCP indexes
- Produced artifacts: planning/artifacts/mcp/trafilatura.md
- Blocking dependencies: C10-002
- CI gates: mcp-schema, mcp-scan, docs-truth
- Review: owner team review, standard review

### C12-015: Audit MCP `arxiv`
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: mcp.json, MCP spec, mcp-scan docs, MCP indexes
- Produced artifacts: planning/artifacts/mcp/arxiv.md
- Blocking dependencies: C10-002
- CI gates: mcp-schema, mcp-scan, docs-truth
- Review: owner team review, standard review

### C12-016: Audit MCP `atom-of-thoughts`
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `high`; complexity: `S`; merge risk: `1`
- Required inputs: mcp.json, MCP spec, mcp-scan docs, MCP indexes
- Produced artifacts: planning/artifacts/mcp/atom-of-thoughts.md
- Blocking dependencies: C10-002
- CI gates: mcp-schema, mcp-scan, docs-truth
- Review: owner team review, standard review

### C12-017: Audit MCP `crash`
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: mcp.json, MCP spec, mcp-scan docs, MCP indexes
- Produced artifacts: planning/artifacts/mcp/crash.md
- Blocking dependencies: C10-002
- CI gates: mcp-schema, mcp-scan, docs-truth
- Review: owner team review, standard review

### C12-018: Audit MCP `creative-thinking`
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `high`; complexity: `S`; merge risk: `1`
- Required inputs: mcp.json, MCP spec, mcp-scan docs, MCP indexes
- Produced artifacts: planning/artifacts/mcp/creative-thinking.md
- Blocking dependencies: C10-002
- CI gates: mcp-schema, mcp-scan, docs-truth
- Review: owner team review, standard review

### C12-019: Audit MCP `deep-lucid-3d`
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `high`; complexity: `S`; merge risk: `1`
- Required inputs: mcp.json, MCP spec, mcp-scan docs, MCP indexes
- Produced artifacts: planning/artifacts/mcp/deep-lucid-3d.md
- Blocking dependencies: C10-002
- CI gates: mcp-schema, mcp-scan, docs-truth
- Review: owner team review, standard review

### C12-020: Audit MCP `duckduckgo-search`
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: mcp.json, MCP spec, mcp-scan docs, MCP indexes
- Produced artifacts: planning/artifacts/mcp/duckduckgo-search.md
- Blocking dependencies: C10-002
- CI gates: mcp-schema, mcp-scan, docs-truth
- Review: owner team review, standard review

### C12-021: Audit MCP `exa`
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: mcp.json, MCP spec, mcp-scan docs, MCP indexes
- Produced artifacts: planning/artifacts/mcp/exa.md
- Blocking dependencies: C10-002
- CI gates: mcp-schema, mcp-scan, docs-truth
- Review: owner team review, standard review

### C12-022: Audit MCP `ffmpeg`
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `high`; complexity: `S`; merge risk: `1`
- Required inputs: mcp.json, MCP spec, mcp-scan docs, MCP indexes
- Produced artifacts: planning/artifacts/mcp/ffmpeg.md
- Blocking dependencies: C10-002
- CI gates: mcp-schema, mcp-scan, docs-truth
- Review: owner team review, standard review

### C12-023: Audit MCP `g-search`
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: mcp.json, MCP spec, mcp-scan docs, MCP indexes
- Produced artifacts: planning/artifacts/mcp/g-search.md
- Blocking dependencies: C10-002
- CI gates: mcp-schema, mcp-scan, docs-truth
- Review: owner team review, standard review

### C12-024: Audit MCP `gmail`
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `high`; complexity: `S`; merge risk: `1`
- Required inputs: mcp.json, MCP spec, mcp-scan docs, MCP indexes
- Produced artifacts: planning/artifacts/mcp/gmail.md
- Blocking dependencies: C10-002
- CI gates: mcp-schema, mcp-scan, docs-truth
- Review: owner team review, standard review

### C12-025: Audit MCP `linkedin`
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `high`; complexity: `S`; merge risk: `1`
- Required inputs: mcp.json, MCP spec, mcp-scan docs, MCP indexes
- Produced artifacts: planning/artifacts/mcp/linkedin.md
- Blocking dependencies: C10-002
- CI gates: mcp-schema, mcp-scan, docs-truth
- Review: owner team review, standard review

### C12-026: Audit MCP `lotus-wisdom-mcp`
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: mcp.json, MCP spec, mcp-scan docs, MCP indexes
- Produced artifacts: planning/artifacts/mcp/lotus-wisdom-mcp.md
- Blocking dependencies: C10-002
- CI gates: mcp-schema, mcp-scan, docs-truth
- Review: owner team review, standard review

### C12-027: Audit MCP `shannon-thinking`
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: mcp.json, MCP spec, mcp-scan docs, MCP indexes
- Produced artifacts: planning/artifacts/mcp/shannon-thinking.md
- Blocking dependencies: C10-002
- CI gates: mcp-schema, mcp-scan, docs-truth
- Review: owner team review, standard review

### C12-028: Audit MCP `think-strategies`
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: mcp.json, MCP spec, mcp-scan docs, MCP indexes
- Produced artifacts: planning/artifacts/mcp/think-strategies.md
- Blocking dependencies: C10-002
- CI gates: mcp-schema, mcp-scan, docs-truth
- Review: owner team review, standard review

### C12-029: Audit MCP `wayback`
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: mcp.json, MCP spec, mcp-scan docs, MCP indexes
- Produced artifacts: planning/artifacts/mcp/wayback.md
- Blocking dependencies: C10-002
- CI gates: mcp-schema, mcp-scan, docs-truth
- Review: owner team review, standard review

### C12-030: Audit MCP `wikipedia`
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: mcp.json, MCP spec, mcp-scan docs, MCP indexes
- Produced artifacts: planning/artifacts/mcp/wikipedia.md
- Blocking dependencies: C10-002
- CI gates: mcp-schema, mcp-scan, docs-truth
- Review: owner team review, standard review

### C12-100: Harvest official-mcp-registry candidates
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `medium`; complexity: `M`; merge risk: `1`
- Required inputs: source ledger, MCP promotion gates
- Produced artifacts: planning/artifacts/mcp-indexes/official-mcp-registry.md
- Blocking dependencies: C12-001
- CI gates: source-ledger, mcp-schema
- Review: owner team review, standard review

### C12-101: Harvest glama-mcp-list candidates
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `medium`; complexity: `M`; merge risk: `1`
- Required inputs: source ledger, MCP promotion gates
- Produced artifacts: planning/artifacts/mcp-indexes/glama-mcp-list.md
- Blocking dependencies: C12-001
- CI gates: source-ledger, mcp-schema
- Review: owner team review, standard review

### C12-102: Harvest mcp-so candidates
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `medium`; complexity: `M`; merge risk: `1`
- Required inputs: source ledger, MCP promotion gates
- Produced artifacts: planning/artifacts/mcp-indexes/mcp-so.md
- Blocking dependencies: C12-001
- CI gates: source-ledger, mcp-schema
- Review: owner team review, standard review

### C12-103: Harvest pulsemcp candidates
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `medium`; complexity: `M`; merge risk: `1`
- Required inputs: source ledger, MCP promotion gates
- Produced artifacts: planning/artifacts/mcp-indexes/pulsemcp.md
- Blocking dependencies: C12-001
- CI gates: source-ledger, mcp-schema
- Review: owner team review, standard review

### C12-104: Harvest mcp-directory candidates
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `medium`; complexity: `M`; merge risk: `1`
- Required inputs: source ledger, MCP promotion gates
- Produced artifacts: planning/artifacts/mcp-indexes/mcp-directory.md
- Blocking dependencies: C12-001
- CI gates: source-ledger, mcp-schema
- Review: owner team review, standard review

### C12-105: Harvest abordage-awesome-mcp candidates
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `medium`; complexity: `M`; merge risk: `1`
- Required inputs: source ledger, MCP promotion gates
- Produced artifacts: planning/artifacts/mcp-indexes/abordage-awesome-mcp.md
- Blocking dependencies: C12-001
- CI gates: source-ledger, mcp-schema
- Review: owner team review, standard review

### C12-106: Harvest ever-works-awesome-mcp candidates
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `medium`; complexity: `M`; merge risk: `1`
- Required inputs: source ledger, MCP promotion gates
- Produced artifacts: planning/artifacts/mcp-indexes/ever-works-awesome-mcp.md
- Blocking dependencies: C12-001
- CI gates: source-ledger, mcp-schema
- Review: owner team review, standard review

### C12-107: Harvest mcp-awesome candidates
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `medium`; complexity: `M`; merge risk: `1`
- Required inputs: source ledger, MCP promotion gates
- Produced artifacts: planning/artifacts/mcp-indexes/mcp-awesome.md
- Blocking dependencies: C12-001
- CI gates: source-ledger, mcp-schema
- Review: owner team review, standard review

### C12-108: Harvest context-awesome candidates
- Cluster: `C12`
- Owner team: `mcp-curation`
- Risk: `medium`; complexity: `M`; merge risk: `1`
- Required inputs: source ledger, MCP promotion gates
- Produced artifacts: planning/artifacts/mcp-indexes/context-awesome.md
- Blocking dependencies: C12-001
- CI gates: source-ledger, mcp-schema
- Review: owner team review, standard review

### C13-001: Refine Claude Desktop harness projection
- Cluster: `C13`
- Owner team: `harness-projection`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: harness official docs, repo inventory, harness registry
- Produced artifacts: planning/20-harness-registry/claude-desktop.md, planning/artifacts/harness/claude-desktop.md
- Blocking dependencies: C10-002
- CI gates: harness-fixture, docs-truth, support-tier-check
- Review: owner team review, standard review

### C13-002: Refine Claude Code harness projection
- Cluster: `C13`
- Owner team: `harness-projection`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: harness official docs, repo inventory, harness registry
- Produced artifacts: planning/20-harness-registry/claude-code.md, planning/artifacts/harness/claude-code.md
- Blocking dependencies: C01-001
- CI gates: harness-fixture, docs-truth, support-tier-check
- Review: owner team review, standard review

### C13-003: Refine ChatGPT harness projection
- Cluster: `C13`
- Owner team: `harness-projection`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: harness official docs, repo inventory, harness registry
- Produced artifacts: planning/20-harness-registry/chatgpt.md, planning/artifacts/harness/chatgpt.md
- Blocking dependencies: C01-001
- CI gates: harness-fixture, docs-truth, support-tier-check
- Review: owner team review, standard review

### C13-004: Refine Codex harness projection
- Cluster: `C13`
- Owner team: `harness-projection`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: harness official docs, repo inventory, harness registry
- Produced artifacts: planning/20-harness-registry/codex.md, planning/artifacts/harness/codex.md
- Blocking dependencies: C01-001
- CI gates: harness-fixture, docs-truth, support-tier-check
- Review: owner team review, standard review

### C13-005: Refine GitHub Copilot Web / Cloud Agent harness projection
- Cluster: `C13`
- Owner team: `harness-projection`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: harness official docs, repo inventory, harness registry
- Produced artifacts: planning/20-harness-registry/github-copilot-web.md, planning/artifacts/harness/github-copilot-web.md
- Blocking dependencies: C01-001
- CI gates: harness-fixture, docs-truth, support-tier-check
- Review: owner team review, standard review

### C13-006: Refine GitHub Copilot CLI harness projection
- Cluster: `C13`
- Owner team: `harness-projection`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: harness official docs, repo inventory, harness registry
- Produced artifacts: planning/20-harness-registry/github-copilot-cli.md, planning/artifacts/harness/github-copilot-cli.md
- Blocking dependencies: C01-001
- CI gates: harness-fixture, docs-truth, support-tier-check
- Review: owner team review, standard review

### C13-007: Refine OpenCode harness projection
- Cluster: `C13`
- Owner team: `harness-projection`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: harness official docs, repo inventory, harness registry
- Produced artifacts: planning/20-harness-registry/opencode.md, planning/artifacts/harness/opencode.md
- Blocking dependencies: C01-001
- CI gates: harness-fixture, docs-truth, support-tier-check
- Review: owner team review, standard review

### C13-008: Refine Gemini CLI harness projection
- Cluster: `C13`
- Owner team: `harness-projection`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: harness official docs, repo inventory, harness registry
- Produced artifacts: planning/20-harness-registry/gemini-cli.md, planning/artifacts/harness/gemini-cli.md
- Blocking dependencies: C01-001
- CI gates: harness-fixture, docs-truth, support-tier-check
- Review: owner team review, standard review

### C13-009: Refine Google Antigravity harness projection
- Cluster: `C13`
- Owner team: `harness-projection`
- Risk: `high`; complexity: `M`; merge risk: `2`
- Required inputs: harness official docs, repo inventory, harness registry
- Produced artifacts: planning/20-harness-registry/antigravity.md, planning/artifacts/harness/antigravity.md
- Blocking dependencies: C01-001
- CI gates: harness-fixture, docs-truth, support-tier-check
- Review: owner team review, standard review

### C13-010: Refine Perplexity Desktop / Mac harness projection
- Cluster: `C13`
- Owner team: `harness-projection`
- Risk: `high`; complexity: `M`; merge risk: `2`
- Required inputs: harness official docs, repo inventory, harness registry
- Produced artifacts: planning/20-harness-registry/perplexity-desktop.md, planning/artifacts/harness/perplexity-desktop.md
- Blocking dependencies: C01-001
- CI gates: harness-fixture, docs-truth, support-tier-check
- Review: owner team review, standard review

### C13-011: Refine Cherry Studio harness projection
- Cluster: `C13`
- Owner team: `harness-projection`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: harness official docs, repo inventory, harness registry
- Produced artifacts: planning/20-harness-registry/cherry-studio.md, planning/artifacts/harness/cherry-studio.md
- Blocking dependencies: C01-001
- CI gates: harness-fixture, docs-truth, support-tier-check
- Review: owner team review, standard review

### C13-012: Refine Cursor Editor harness projection
- Cluster: `C13`
- Owner team: `harness-projection`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: harness official docs, repo inventory, harness registry
- Produced artifacts: planning/20-harness-registry/cursor-editor.md, planning/artifacts/harness/cursor-editor.md
- Blocking dependencies: C01-001
- CI gates: harness-fixture, docs-truth, support-tier-check
- Review: owner team review, standard review

### C13-013: Refine Cursor Agent CLI/Web harness projection
- Cluster: `C13`
- Owner team: `harness-projection`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: harness official docs, repo inventory, harness registry
- Produced artifacts: planning/20-harness-registry/cursor-agent.md, planning/artifacts/harness/cursor-agent.md
- Blocking dependencies: C01-001
- CI gates: harness-fixture, docs-truth, support-tier-check
- Review: owner team review, standard review

### C14-001: Claude plugin manifest reconciliation
- Cluster: `C14`
- Owner team: `plugin-packaging`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: plugin docs, agent-bundle.json, repo plugin folders
- Produced artifacts: planning/artifacts/plugins/001-claude-plugin-manifest-reconciliation.md
- Blocking dependencies: C10-003
- CI gates: plugin-schema, harness-fixture, docs-truth
- Review: owner team review, standard review

### C14-002: Claude plugin marketplace doc
- Cluster: `C14`
- Owner team: `plugin-packaging`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: plugin docs, agent-bundle.json, repo plugin folders
- Produced artifacts: planning/artifacts/plugins/002-claude-plugin-marketplace-doc.md
- Blocking dependencies: C10-003
- CI gates: plugin-schema, harness-fixture, docs-truth
- Review: owner team review, standard review

### C14-003: Codex plugin manifest reconciliation
- Cluster: `C14`
- Owner team: `plugin-packaging`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: plugin docs, agent-bundle.json, repo plugin folders
- Produced artifacts: planning/artifacts/plugins/003-codex-plugin-manifest-reconciliation.md
- Blocking dependencies: C10-003
- CI gates: plugin-schema, harness-fixture, docs-truth
- Review: owner team review, standard review

### C14-004: Agents marketplace manifest validation
- Cluster: `C14`
- Owner team: `plugin-packaging`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: plugin docs, agent-bundle.json, repo plugin folders
- Produced artifacts: planning/artifacts/plugins/004-agents-marketplace-manifest-validation.md
- Blocking dependencies: C10-003
- CI gates: plugin-schema, harness-fixture, docs-truth
- Review: owner team review, standard review

### C14-005: Opencode plugin/package validation
- Cluster: `C14`
- Owner team: `plugin-packaging`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: plugin docs, agent-bundle.json, repo plugin folders
- Produced artifacts: planning/artifacts/plugins/005-opencode-plugin/package-validation.md
- Blocking dependencies: C10-003
- CI gates: plugin-schema, harness-fixture, docs-truth
- Review: owner team review, standard review

### C14-006: Gemini extension manifest generation
- Cluster: `C14`
- Owner team: `plugin-packaging`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: plugin docs, agent-bundle.json, repo plugin folders
- Produced artifacts: planning/artifacts/plugins/006-gemini-extension-manifest-generation.md
- Blocking dependencies: C10-003
- CI gates: plugin-schema, harness-fixture, docs-truth
- Review: owner team review, standard review

### C14-007: Cursor rules adapter fixtures
- Cluster: `C14`
- Owner team: `plugin-packaging`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: plugin docs, agent-bundle.json, repo plugin folders
- Produced artifacts: planning/artifacts/plugins/007-cursor-rules-adapter-fixtures.md
- Blocking dependencies: C10-003
- CI gates: plugin-schema, harness-fixture, docs-truth
- Review: owner team review, standard review

### C14-008: Chatgpt actions openapi adapter docs
- Cluster: `C14`
- Owner team: `plugin-packaging`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: plugin docs, agent-bundle.json, repo plugin folders
- Produced artifacts: planning/artifacts/plugins/008-chatgpt-actions-OpenAPI-adapter-docs.md
- Blocking dependencies: C10-003
- CI gates: plugin-schema, harness-fixture, docs-truth
- Review: owner team review, standard review

### C14-009: Apps sdk preview caveat docs
- Cluster: `C14`
- Owner team: `plugin-packaging`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: plugin docs, agent-bundle.json, repo plugin folders
- Produced artifacts: planning/artifacts/plugins/009-apps-SDK-preview-caveat-docs.md
- Blocking dependencies: C10-003
- CI gates: plugin-schema, harness-fixture, docs-truth
- Review: owner team review, standard review

### C14-010: Native plugin version pin policy
- Cluster: `C14`
- Owner team: `plugin-packaging`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: plugin docs, agent-bundle.json, repo plugin folders
- Produced artifacts: planning/artifacts/plugins/010-native-plugin-version-pin-policy.md
- Blocking dependencies: C10-003
- CI gates: plugin-schema, harness-fixture, docs-truth
- Review: owner team review, standard review

### C14-011: Plugin install smoke tests
- Cluster: `C14`
- Owner team: `plugin-packaging`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: plugin docs, agent-bundle.json, repo plugin folders
- Produced artifacts: planning/artifacts/plugins/011-plugin-install-smoke-tests.md
- Blocking dependencies: C10-003
- CI gates: plugin-schema, harness-fixture, docs-truth
- Review: owner team review, standard review

### C14-012: Plugin docs generation
- Cluster: `C14`
- Owner team: `plugin-packaging`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: plugin docs, agent-bundle.json, repo plugin folders
- Produced artifacts: planning/artifacts/plugins/012-plugin-docs-generation.md
- Blocking dependencies: C10-003
- CI gates: plugin-schema, harness-fixture, docs-truth
- Review: owner team review, standard review

### C15-001: Doctor command ux spec
- Cluster: `C15`
- Owner team: `ux-automation`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: CLI contract, transaction engine spec, harness registry
- Produced artifacts: planning/artifacts/ux/001-doctor-command-UX-spec.md
- Blocking dependencies: C10-001
- CI gates: cli-fixture, docs-truth
- Review: owner team review, standard review

### C15-002: Catalog browser cli spec
- Cluster: `C15`
- Owner team: `ux-automation`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: CLI contract, transaction engine spec, harness registry
- Produced artifacts: planning/artifacts/ux/002-catalog-browser-CLI-spec.md
- Blocking dependencies: C10-001
- CI gates: cli-fixture, docs-truth
- Review: owner team review, standard review

### C15-003: Skill search and preview flow
- Cluster: `C15`
- Owner team: `ux-automation`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: CLI contract, transaction engine spec, harness registry
- Produced artifacts: planning/artifacts/ux/003-skill-search-and-preview-flow.md
- Blocking dependencies: C10-001
- CI gates: cli-fixture, docs-truth
- Review: owner team review, standard review

### C15-004: Mcp inspector flow
- Cluster: `C15`
- Owner team: `ux-automation`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: CLI contract, transaction engine spec, harness registry
- Produced artifacts: planning/artifacts/ux/004-mcp-inspector-flow.md
- Blocking dependencies: C10-001
- CI gates: cli-fixture, docs-truth
- Review: owner team review, standard review

### C15-005: Sync preview diff flow
- Cluster: `C15`
- Owner team: `ux-automation`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: CLI contract, transaction engine spec, harness registry
- Produced artifacts: planning/artifacts/ux/005-sync-preview-diff-flow.md
- Blocking dependencies: C10-001
- CI gates: cli-fixture, docs-truth
- Review: owner team review, standard review

### C15-006: Sync apply transaction flow
- Cluster: `C15`
- Owner team: `ux-automation`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: CLI contract, transaction engine spec, harness registry
- Produced artifacts: planning/artifacts/ux/006-sync-apply-transaction-flow.md
- Blocking dependencies: C10-001, C05-001
- CI gates: cli-fixture, docs-truth
- Review: owner team review, standard review

### C15-007: Rollback ux flow
- Cluster: `C15`
- Owner team: `ux-automation`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: CLI contract, transaction engine spec, harness registry
- Produced artifacts: planning/artifacts/ux/007-rollback-UX-flow.md
- Blocking dependencies: C10-001, C05-001
- CI gates: cli-fixture, docs-truth
- Review: owner team review, standard review

### C15-008: Drift repair wizard
- Cluster: `C15`
- Owner team: `ux-automation`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: CLI contract, transaction engine spec, harness registry
- Produced artifacts: planning/artifacts/ux/008-drift-repair-wizard.md
- Blocking dependencies: C10-001, C05-001
- CI gates: cli-fixture, docs-truth
- Review: owner team review, standard review

### C15-009: Config wizard questions
- Cluster: `C15`
- Owner team: `ux-automation`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: CLI contract, transaction engine spec, harness registry
- Produced artifacts: planning/artifacts/ux/009-config-wizard-questions.md
- Blocking dependencies: C10-001, C05-001
- CI gates: cli-fixture, docs-truth
- Review: owner team review, standard review

### C15-010: Dashboard overview panel
- Cluster: `C15`
- Owner team: `ux-automation`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: CLI contract, transaction engine spec, harness registry
- Produced artifacts: planning/artifacts/ux/010-dashboard-overview-panel.md
- Blocking dependencies: C10-001, C05-001
- CI gates: cli-fixture, docs-truth
- Review: owner team review, standard review

### C15-011: Dashboard skill panel
- Cluster: `C15`
- Owner team: `ux-automation`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: CLI contract, transaction engine spec, harness registry
- Produced artifacts: planning/artifacts/ux/011-dashboard-skill-panel.md
- Blocking dependencies: C10-001, C05-001
- CI gates: cli-fixture, docs-truth
- Review: owner team review, standard review

### C15-012: Dashboard mcp panel
- Cluster: `C15`
- Owner team: `ux-automation`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: CLI contract, transaction engine spec, harness registry
- Produced artifacts: planning/artifacts/ux/012-dashboard-MCP-panel.md
- Blocking dependencies: C10-001, C05-001
- CI gates: cli-fixture, docs-truth
- Review: owner team review, standard review

### C15-013: Dashboard harness panel
- Cluster: `C15`
- Owner team: `ux-automation`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: CLI contract, transaction engine spec, harness registry
- Produced artifacts: planning/artifacts/ux/013-dashboard-harness-panel.md
- Blocking dependencies: C10-001, C05-001
- CI gates: cli-fixture, docs-truth
- Review: owner team review, standard review

### C15-014: Openspec status panel
- Cluster: `C15`
- Owner team: `ux-automation`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: CLI contract, transaction engine spec, harness registry
- Produced artifacts: planning/artifacts/ux/014-OpenSpec-status-panel.md
- Blocking dependencies: C10-001, C05-001
- CI gates: cli-fixture, docs-truth
- Review: owner team review, standard review

### C15-015: Machine-readable json output contract
- Cluster: `C15`
- Owner team: `ux-automation`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: CLI contract, transaction engine spec, harness registry
- Produced artifacts: planning/artifacts/ux/015-machine-readable-JSON-output-contract.md
- Blocking dependencies: C10-001, C05-001
- CI gates: cli-fixture, docs-truth
- Review: owner team review, standard review

### C15-016: Guided remediation messages
- Cluster: `C15`
- Owner team: `ux-automation`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: CLI contract, transaction engine spec, harness registry
- Produced artifacts: planning/artifacts/ux/016-guided-remediation-messages.md
- Blocking dependencies: C10-001, C05-001
- CI gates: cli-fixture, docs-truth
- Review: owner team review, standard review

### C15-017: One-command bootstrap script
- Cluster: `C15`
- Owner team: `ux-automation`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: CLI contract, transaction engine spec, harness registry
- Produced artifacts: planning/artifacts/ux/017-one-command-bootstrap-script.md
- Blocking dependencies: C10-001, C05-001
- CI gates: cli-fixture, docs-truth
- Review: owner team review, standard review

### C15-018: Interactive/noninteractive parity tests
- Cluster: `C15`
- Owner team: `ux-automation`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: CLI contract, transaction engine spec, harness registry
- Produced artifacts: planning/artifacts/ux/018-interactive/noninteractive-parity-tests.md
- Blocking dependencies: C10-001, C05-001
- CI gates: cli-fixture, docs-truth
- Review: owner team review, standard review

### C16-001: Sync documentation artifact `README.md`
- Cluster: `C16`
- Owner team: `docs-truth`
- Risk: `low`; complexity: `S`; merge risk: `3`
- Required inputs: docs artifact contract, repo inventory, harness registry, skill registry, mcp registry
- Produced artifacts: planning/artifacts/docs/READMEdotmd.md
- Blocking dependencies: C10-005
- CI gates: docs-truth, linkcheck, support-tier-check
- Review: owner team review, standard review

### C16-002: Sync documentation artifact `AGENTS.md`
- Cluster: `C16`
- Owner team: `docs-truth`
- Risk: `medium`; complexity: `S`; merge risk: `3`
- Required inputs: docs artifact contract, repo inventory, harness registry, skill registry, mcp registry
- Produced artifacts: planning/artifacts/docs/AGENTSdotmd.md
- Blocking dependencies: C10-005
- CI gates: docs-truth, linkcheck, support-tier-check
- Review: owner team review, standard review

### C16-003: Sync documentation artifact `CLAUDE.md`
- Cluster: `C16`
- Owner team: `docs-truth`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: docs artifact contract, repo inventory, harness registry, skill registry, mcp registry
- Produced artifacts: planning/artifacts/docs/CLAUDEdotmd.md
- Blocking dependencies: C10-005
- CI gates: docs-truth, linkcheck, support-tier-check
- Review: owner team review, standard review

### C16-004: Sync documentation artifact `GEMINI.md`
- Cluster: `C16`
- Owner team: `docs-truth`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: docs artifact contract, repo inventory, harness registry, skill registry, mcp registry
- Produced artifacts: planning/artifacts/docs/GEMINIdotmd.md
- Blocking dependencies: C10-005
- CI gates: docs-truth, linkcheck, support-tier-check
- Review: owner team review, standard review

### C16-005: Sync documentation artifact `.github/copilot-instructions.md`
- Cluster: `C16`
- Owner team: `docs-truth`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: docs artifact contract, repo inventory, harness registry, skill registry, mcp registry
- Produced artifacts: planning/artifacts/docs/dotgithub-copilot-instructionsdotmd.md
- Blocking dependencies: C10-005
- CI gates: docs-truth, linkcheck, support-tier-check
- Review: owner team review, standard review

### C16-006: Sync documentation artifact `.github/instructions/*.instructions.md`
- Cluster: `C16`
- Owner team: `docs-truth`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: docs artifact contract, repo inventory, harness registry, skill registry, mcp registry
- Produced artifacts: planning/artifacts/docs/dotgithub-instructions-stardotinstructionsdotmd.md
- Blocking dependencies: C10-005
- CI gates: docs-truth, linkcheck, support-tier-check
- Review: owner team review, standard review

### C16-007: Sync documentation artifact `.cursor/rules/**`
- Cluster: `C16`
- Owner team: `docs-truth`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: docs artifact contract, repo inventory, harness registry, skill registry, mcp registry
- Produced artifacts: planning/artifacts/docs/dotcursor-rules-starstar.md
- Blocking dependencies: C10-005
- CI gates: docs-truth, linkcheck, support-tier-check
- Review: owner team review, standard review

### C16-008: Sync documentation artifact `.claude/rules/**`
- Cluster: `C16`
- Owner team: `docs-truth`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: docs artifact contract, repo inventory, harness registry, skill registry, mcp registry
- Produced artifacts: planning/artifacts/docs/dotclaude-rules-starstar.md
- Blocking dependencies: C10-005
- CI gates: docs-truth, linkcheck, support-tier-check
- Review: owner team review, standard review

### C16-009: Sync documentation artifact `.antigravity/**`
- Cluster: `C16`
- Owner team: `docs-truth`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: docs artifact contract, repo inventory, harness registry, skill registry, mcp registry
- Produced artifacts: planning/artifacts/docs/dotantigravity-starstar.md
- Blocking dependencies: C10-005
- CI gates: docs-truth, linkcheck, support-tier-check
- Review: owner team review, standard review

### C16-010: Sync documentation artifact `.cherry/**`
- Cluster: `C16`
- Owner team: `docs-truth`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: docs artifact contract, repo inventory, harness registry, skill registry, mcp registry
- Produced artifacts: planning/artifacts/docs/dotcherry-starstar.md
- Blocking dependencies: C10-005
- CI gates: docs-truth, linkcheck, support-tier-check
- Review: owner team review, standard review

### C16-011: Sync documentation artifact `.perplexity/**`
- Cluster: `C16`
- Owner team: `docs-truth`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: docs artifact contract, repo inventory, harness registry, skill registry, mcp registry
- Produced artifacts: planning/artifacts/docs/dotperplexity-starstar.md
- Blocking dependencies: C10-005
- CI gates: docs-truth, linkcheck, support-tier-check
- Review: owner team review, standard review

### C16-012: Sync documentation artifact `docs/skills.md`
- Cluster: `C16`
- Owner team: `docs-truth`
- Risk: `low`; complexity: `S`; merge risk: `1`
- Required inputs: docs artifact contract, repo inventory, harness registry, skill registry, mcp registry
- Produced artifacts: planning/artifacts/docs/docs-skillsdotmd.md
- Blocking dependencies: C10-005
- CI gates: docs-truth, linkcheck, support-tier-check
- Review: owner team review, standard review

### C16-013: Sync documentation artifact `docs/mcp.md`
- Cluster: `C16`
- Owner team: `docs-truth`
- Risk: `low`; complexity: `S`; merge risk: `1`
- Required inputs: docs artifact contract, repo inventory, harness registry, skill registry, mcp registry
- Produced artifacts: planning/artifacts/docs/docs-mcpdotmd.md
- Blocking dependencies: C10-005
- CI gates: docs-truth, linkcheck, support-tier-check
- Review: owner team review, standard review

### C16-014: Sync documentation artifact `docs/harnesses.md`
- Cluster: `C16`
- Owner team: `docs-truth`
- Risk: `low`; complexity: `S`; merge risk: `1`
- Required inputs: docs artifact contract, repo inventory, harness registry, skill registry, mcp registry
- Produced artifacts: planning/artifacts/docs/docs-harnessesdotmd.md
- Blocking dependencies: C10-005
- CI gates: docs-truth, linkcheck, support-tier-check
- Review: owner team review, standard review

### C16-015: Sync documentation artifact `docs/openspec.md`
- Cluster: `C16`
- Owner team: `docs-truth`
- Risk: `low`; complexity: `S`; merge risk: `1`
- Required inputs: docs artifact contract, repo inventory, harness registry, skill registry, mcp registry
- Produced artifacts: planning/artifacts/docs/docs-openspecdotmd.md
- Blocking dependencies: C10-005
- CI gates: docs-truth, linkcheck, support-tier-check
- Review: owner team review, standard review

### C16-016: Sync documentation artifact `docs/security.md`
- Cluster: `C16`
- Owner team: `docs-truth`
- Risk: `low`; complexity: `S`; merge risk: `1`
- Required inputs: docs artifact contract, repo inventory, harness registry, skill registry, mcp registry
- Produced artifacts: planning/artifacts/docs/docs-securitydotmd.md
- Blocking dependencies: C10-005
- CI gates: docs-truth, linkcheck, support-tier-check
- Review: owner team review, standard review

### C16-017: Sync documentation artifact `docs/external-skills.md`
- Cluster: `C16`
- Owner team: `docs-truth`
- Risk: `low`; complexity: `S`; merge risk: `1`
- Required inputs: docs artifact contract, repo inventory, harness registry, skill registry, mcp registry
- Produced artifacts: planning/artifacts/docs/docs-external-skillsdotmd.md
- Blocking dependencies: C10-005
- CI gates: docs-truth, linkcheck, support-tier-check
- Review: owner team review, standard review

### C16-018: Sync documentation artifact `docs/version-matrix.md`
- Cluster: `C16`
- Owner team: `docs-truth`
- Risk: `low`; complexity: `S`; merge risk: `1`
- Required inputs: docs artifact contract, repo inventory, harness registry, skill registry, mcp registry
- Produced artifacts: planning/artifacts/docs/docs-version-matrixdotmd.md
- Blocking dependencies: C10-005
- CI gates: docs-truth, linkcheck, support-tier-check
- Review: owner team review, standard review

### C16-019: Sync documentation artifact `docs/support-tiers.md`
- Cluster: `C16`
- Owner team: `docs-truth`
- Risk: `low`; complexity: `S`; merge risk: `1`
- Required inputs: docs artifact contract, repo inventory, harness registry, skill registry, mcp registry
- Produced artifacts: planning/artifacts/docs/docs-support-tiersdotmd.md
- Blocking dependencies: C10-005
- CI gates: docs-truth, linkcheck, support-tier-check
- Review: owner team review, standard review

### C16-020: Sync documentation artifact `docs/quickstart.md`
- Cluster: `C16`
- Owner team: `docs-truth`
- Risk: `low`; complexity: `S`; merge risk: `1`
- Required inputs: docs artifact contract, repo inventory, harness registry, skill registry, mcp registry
- Produced artifacts: planning/artifacts/docs/docs-quickstartdotmd.md
- Blocking dependencies: C10-005
- CI gates: docs-truth, linkcheck, support-tier-check
- Review: owner team review, standard review

### C16-021: Sync documentation artifact `raw README/rendered README drift`
- Cluster: `C16`
- Owner team: `docs-truth`
- Risk: `medium`; complexity: `S`; merge risk: `1`
- Required inputs: docs artifact contract, repo inventory, harness registry, skill registry, mcp registry
- Produced artifacts: planning/artifacts/docs/raw-README-rendered-README-drift.md
- Blocking dependencies: C10-005
- CI gates: docs-truth, linkcheck, support-tier-check
- Review: owner team review, standard review

### C17-001: Policy schema for validated support tier
- Cluster: `C17`
- Owner team: `security-supply-chain`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: security docs, source ledger, mcp-scan docs, skill audit model
- Produced artifacts: planning/artifacts/security/001-policy-schema-for-validated-support-tier.md
- Blocking dependencies: C10-002
- CI gates: policy, security-scan, docs-truth
- Review: owner team review, standard review

### C17-002: Deny latest for validated mcp/plugin
- Cluster: `C17`
- Owner team: `security-supply-chain`
- Risk: `high`; complexity: `M`; merge risk: `2`
- Required inputs: security docs, source ledger, mcp-scan docs, skill audit model
- Produced artifacts: planning/artifacts/security/002-deny-latest-for-validated-MCP/plugin.md
- Blocking dependencies: C10-002
- CI gates: policy, security-scan, docs-truth
- Review: owner team review, standard review

### C17-003: Deny absolute local path in portable profile
- Cluster: `C17`
- Owner team: `security-supply-chain`
- Risk: `high`; complexity: `M`; merge risk: `2`
- Required inputs: security docs, source ledger, mcp-scan docs, skill audit model
- Produced artifacts: planning/artifacts/security/003-deny-absolute-local-path-in-portable-profile.md
- Blocking dependencies: C10-002
- CI gates: policy, security-scan, docs-truth
- Review: owner team review, standard review

### C17-004: Deny external skill without provenance
- Cluster: `C17`
- Owner team: `security-supply-chain`
- Risk: `high`; complexity: `M`; merge risk: `2`
- Required inputs: security docs, source ledger, mcp-scan docs, skill audit model
- Produced artifacts: planning/artifacts/security/004-deny-external-skill-without-provenance.md
- Blocking dependencies: C10-002
- CI gates: policy, security-scan, docs-truth
- Review: owner team review, standard review

### C17-005: Secret reference scanner
- Cluster: `C17`
- Owner team: `security-supply-chain`
- Risk: `high`; complexity: `M`; merge risk: `2`
- Required inputs: security docs, source ledger, mcp-scan docs, skill audit model
- Produced artifacts: planning/artifacts/security/005-secret-reference-scanner.md
- Blocking dependencies: C10-002
- CI gates: policy, security-scan, docs-truth
- Review: owner team review, standard review

### C17-006: Mcp-scan ci integration
- Cluster: `C17`
- Owner team: `security-supply-chain`
- Risk: `high`; complexity: `M`; merge risk: `2`
- Required inputs: security docs, source ledger, mcp-scan docs, skill audit model
- Produced artifacts: planning/artifacts/security/006-mcp-scan-CI-integration.md
- Blocking dependencies: C10-002
- CI gates: policy, security-scan, docs-truth
- Review: owner team review, standard review

### C17-007: Skill script destructive command scanner
- Cluster: `C17`
- Owner team: `security-supply-chain`
- Risk: `high`; complexity: `M`; merge risk: `2`
- Required inputs: security docs, source ledger, mcp-scan docs, skill audit model
- Produced artifacts: planning/artifacts/security/007-skill-script-destructive-command-scanner.md
- Blocking dependencies: C10-002
- CI gates: policy, security-scan, docs-truth
- Review: owner team review, standard review

### C17-008: Sbom generation for release bundle
- Cluster: `C17`
- Owner team: `security-supply-chain`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: security docs, source ledger, mcp-scan docs, skill audit model
- Produced artifacts: planning/artifacts/security/008-SBOM-generation-for-release-bundle.md
- Blocking dependencies: C10-002
- CI gates: policy, security-scan, docs-truth
- Review: owner team review, standard review

### C17-009: Sigstore cosign plan
- Cluster: `C17`
- Owner team: `security-supply-chain`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: security docs, source ledger, mcp-scan docs, skill audit model
- Produced artifacts: planning/artifacts/security/009-Sigstore-cosign-plan.md
- Blocking dependencies: C10-002
- CI gates: policy, security-scan, docs-truth
- Review: owner team review, standard review

### C17-010: Slsa provenance plan
- Cluster: `C17`
- Owner team: `security-supply-chain`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: security docs, source ledger, mcp-scan docs, skill audit model
- Produced artifacts: planning/artifacts/security/010-SLSA-provenance-plan.md
- Blocking dependencies: C10-002
- CI gates: policy, security-scan, docs-truth
- Review: owner team review, standard review

### C17-011: Security exception registry
- Cluster: `C17`
- Owner team: `security-supply-chain`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: security docs, source ledger, mcp-scan docs, skill audit model
- Produced artifacts: planning/artifacts/security/011-security-exception-registry.md
- Blocking dependencies: C10-002
- CI gates: policy, security-scan, docs-truth
- Review: owner team review, standard review

### C17-012: Sandbox profile taxonomy
- Cluster: `C17`
- Owner team: `security-supply-chain`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: security docs, source ledger, mcp-scan docs, skill audit model
- Produced artifacts: planning/artifacts/security/012-sandbox-profile-taxonomy.md
- Blocking dependencies: C10-002
- CI gates: policy, security-scan, docs-truth
- Review: owner team review, standard review

### C17-013: Least-privilege secret docs
- Cluster: `C17`
- Owner team: `security-supply-chain`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: security docs, source ledger, mcp-scan docs, skill audit model
- Produced artifacts: planning/artifacts/security/013-least-privilege-secret-docs.md
- Blocking dependencies: C10-002
- CI gates: policy, security-scan, docs-truth
- Review: owner team review, standard review

### C17-014: Prompt injection guidance for skills
- Cluster: `C17`
- Owner team: `security-supply-chain`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: security docs, source ledger, mcp-scan docs, skill audit model
- Produced artifacts: planning/artifacts/security/014-prompt-injection-guidance-for-skills.md
- Blocking dependencies: C10-002
- CI gates: policy, security-scan, docs-truth
- Review: owner team review, standard review

### C17-015: Mcp tool poisoning playbook
- Cluster: `C17`
- Owner team: `security-supply-chain`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: security docs, source ledger, mcp-scan docs, skill audit model
- Produced artifacts: planning/artifacts/security/015-MCP-tool-poisoning-playbook.md
- Blocking dependencies: C10-002
- CI gates: policy, security-scan, docs-truth
- Review: owner team review, standard review

### C17-016: Supply-chain incident response runbook
- Cluster: `C17`
- Owner team: `security-supply-chain`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: security docs, source ledger, mcp-scan docs, skill audit model
- Produced artifacts: planning/artifacts/security/016-supply-chain-incident-response-runbook.md
- Blocking dependencies: C10-002
- CI gates: policy, security-scan, docs-truth
- Review: owner team review, standard review

### C18-001: Opentelemetry genai semconv watch task
- Cluster: `C18`
- Owner team: `evals-observability`
- Risk: `medium`; complexity: `M`; merge risk: `1`
- Required inputs: OpenTelemetry GenAI docs, Langfuse docs, Phoenix docs, task graph
- Produced artifacts: planning/artifacts/observability/001-OpenTelemetry-GenAI-semconv-watch-task.md
- Blocking dependencies: C10-001
- CI gates: schema, eval-fixture, docs-truth
- Review: owner team review, standard review

### C18-002: Langfuse integration feasibility note
- Cluster: `C18`
- Owner team: `evals-observability`
- Risk: `medium`; complexity: `M`; merge risk: `1`
- Required inputs: OpenTelemetry GenAI docs, Langfuse docs, Phoenix docs, task graph
- Produced artifacts: planning/artifacts/observability/002-Langfuse-integration-feasibility-note.md
- Blocking dependencies: C10-001
- CI gates: schema, eval-fixture, docs-truth
- Review: owner team review, standard review

### C18-003: Phoenix integration feasibility note
- Cluster: `C18`
- Owner team: `evals-observability`
- Risk: `medium`; complexity: `M`; merge risk: `1`
- Required inputs: OpenTelemetry GenAI docs, Langfuse docs, Phoenix docs, task graph
- Produced artifacts: planning/artifacts/observability/003-Phoenix-integration-feasibility-note.md
- Blocking dependencies: C10-001
- CI gates: schema, eval-fixture, docs-truth
- Review: owner team review, standard review

### C18-004: Run graph json schema
- Cluster: `C18`
- Owner team: `evals-observability`
- Risk: `medium`; complexity: `M`; merge risk: `1`
- Required inputs: OpenTelemetry GenAI docs, Langfuse docs, Phoenix docs, task graph
- Produced artifacts: planning/artifacts/observability/004-run-graph-JSON-schema.md
- Blocking dependencies: C10-001
- CI gates: schema, eval-fixture, docs-truth
- Review: owner team review, standard review

### C18-005: Transaction audit event schema
- Cluster: `C18`
- Owner team: `evals-observability`
- Risk: `medium`; complexity: `M`; merge risk: `1`
- Required inputs: OpenTelemetry GenAI docs, Langfuse docs, Phoenix docs, task graph
- Produced artifacts: planning/artifacts/observability/005-transaction-audit-event-schema.md
- Blocking dependencies: C10-001
- CI gates: schema, eval-fixture, docs-truth
- Review: owner team review, standard review

### C18-006: Skill activation eval fixtures
- Cluster: `C18`
- Owner team: `evals-observability`
- Risk: `medium`; complexity: `M`; merge risk: `1`
- Required inputs: OpenTelemetry GenAI docs, Langfuse docs, Phoenix docs, task graph
- Produced artifacts: planning/artifacts/observability/006-skill-activation-eval-fixtures.md
- Blocking dependencies: C10-001
- CI gates: schema, eval-fixture, docs-truth
- Review: owner team review, standard review

### C18-007: Mcp tool snapshot eval fixtures
- Cluster: `C18`
- Owner team: `evals-observability`
- Risk: `medium`; complexity: `M`; merge risk: `1`
- Required inputs: OpenTelemetry GenAI docs, Langfuse docs, Phoenix docs, task graph
- Produced artifacts: planning/artifacts/observability/007-MCP-tool-snapshot-eval-fixtures.md
- Blocking dependencies: C10-001
- CI gates: schema, eval-fixture, docs-truth
- Review: owner team review, standard review

### C18-008: Harness projection eval fixtures
- Cluster: `C18`
- Owner team: `evals-observability`
- Risk: `medium`; complexity: `M`; merge risk: `1`
- Required inputs: OpenTelemetry GenAI docs, Langfuse docs, Phoenix docs, task graph
- Produced artifacts: planning/artifacts/observability/008-harness-projection-eval-fixtures.md
- Blocking dependencies: C10-001
- CI gates: schema, eval-fixture, docs-truth
- Review: owner team review, standard review

### C18-009: Cost telemetry placeholder fields
- Cluster: `C18`
- Owner team: `evals-observability`
- Risk: `medium`; complexity: `M`; merge risk: `1`
- Required inputs: OpenTelemetry GenAI docs, Langfuse docs, Phoenix docs, task graph
- Produced artifacts: planning/artifacts/observability/009-cost-telemetry-placeholder-fields.md
- Blocking dependencies: C10-001
- CI gates: schema, eval-fixture, docs-truth
- Review: owner team review, standard review

### C18-010: Dashboard run graph visualization
- Cluster: `C18`
- Owner team: `evals-observability`
- Risk: `medium`; complexity: `M`; merge risk: `1`
- Required inputs: OpenTelemetry GenAI docs, Langfuse docs, Phoenix docs, task graph
- Produced artifacts: planning/artifacts/observability/010-dashboard-run-graph-visualization.md
- Blocking dependencies: C10-001
- CI gates: schema, eval-fixture, docs-truth
- Review: owner team review, standard review

### C18-011: Ci artifact retention plan
- Cluster: `C18`
- Owner team: `evals-observability`
- Risk: `medium`; complexity: `M`; merge risk: `1`
- Required inputs: OpenTelemetry GenAI docs, Langfuse docs, Phoenix docs, task graph
- Produced artifacts: planning/artifacts/observability/011-CI-artifact-retention-plan.md
- Blocking dependencies: C10-001
- CI gates: schema, eval-fixture, docs-truth
- Review: owner team review, standard review

### C18-012: Eval scorecard docs
- Cluster: `C18`
- Owner team: `evals-observability`
- Risk: `medium`; complexity: `M`; merge risk: `1`
- Required inputs: OpenTelemetry GenAI docs, Langfuse docs, Phoenix docs, task graph
- Produced artifacts: planning/artifacts/observability/012-eval-scorecard-docs.md
- Blocking dependencies: C10-001
- CI gates: schema, eval-fixture, docs-truth
- Review: owner team review, standard review

### C18-013: Deterministic replay fixture docs
- Cluster: `C18`
- Owner team: `evals-observability`
- Risk: `medium`; complexity: `M`; merge risk: `1`
- Required inputs: OpenTelemetry GenAI docs, Langfuse docs, Phoenix docs, task graph
- Produced artifacts: planning/artifacts/observability/013-deterministic-replay-fixture-docs.md
- Blocking dependencies: C10-001
- CI gates: schema, eval-fixture, docs-truth
- Review: owner team review, standard review

### C18-014: Agent task performance metrics
- Cluster: `C18`
- Owner team: `evals-observability`
- Risk: `medium`; complexity: `M`; merge risk: `1`
- Required inputs: OpenTelemetry GenAI docs, Langfuse docs, Phoenix docs, task graph
- Produced artifacts: planning/artifacts/observability/014-agent-task-performance-metrics.md
- Blocking dependencies: C10-001
- CI gates: schema, eval-fixture, docs-truth
- Review: owner team review, standard review

### C19-001: Inventory existing openspec tree
- Cluster: `C19`
- Owner team: `openspec-governance`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: openspec/, task graph, planning docs
- Produced artifacts: planning/artifacts/openspec/001-inventory-existing-openspec-tree.md
- Blocking dependencies: none
- CI gates: openspec-validate, docs-truth
- Review: owner team review, standard review

### C19-002: Preserve existing active changes
- Cluster: `C19`
- Owner team: `openspec-governance`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: openspec/, task graph, planning docs
- Produced artifacts: planning/artifacts/openspec/002-preserve-existing-active-changes.md
- Blocking dependencies: C10-002
- CI gates: openspec-validate, docs-truth
- Review: owner team review, standard review

### C19-003: Map task graph ids to openspec tasks
- Cluster: `C19`
- Owner team: `openspec-governance`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: openspec/, task graph, planning docs
- Produced artifacts: planning/artifacts/openspec/003-map-task-graph-IDs-to-OpenSpec-tasks.md
- Blocking dependencies: C10-002
- CI gates: openspec-validate, docs-truth
- Review: owner team review, standard review

### C19-004: Add skills-first spec deltas
- Cluster: `C19`
- Owner team: `openspec-governance`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: openspec/, task graph, planning docs
- Produced artifacts: planning/artifacts/openspec/004-add-skills-first-spec-deltas.md
- Blocking dependencies: C10-002
- CI gates: openspec-validate, docs-truth
- Review: owner team review, standard review

### C19-005: Add mcp live-systems spec deltas
- Cluster: `C19`
- Owner team: `openspec-governance`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: openspec/, task graph, planning docs
- Produced artifacts: planning/artifacts/openspec/005-add-MCP-live-systems-spec-deltas.md
- Blocking dependencies: C10-002
- CI gates: openspec-validate, docs-truth
- Review: owner team review, standard review

### C19-006: Add documentation-truth spec deltas
- Cluster: `C19`
- Owner team: `openspec-governance`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: openspec/, task graph, planning docs
- Produced artifacts: planning/artifacts/openspec/006-add-documentation-truth-spec-deltas.md
- Blocking dependencies: C10-002
- CI gates: openspec-validate, docs-truth
- Review: owner team review, standard review

### C19-007: Add config-transaction spec deltas
- Cluster: `C19`
- Owner team: `openspec-governance`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: openspec/, task graph, planning docs
- Produced artifacts: planning/artifacts/openspec/007-add-config-transaction-spec-deltas.md
- Blocking dependencies: C10-002
- CI gates: openspec-validate, docs-truth
- Review: owner team review, standard review

### C19-008: Add harness-registry spec deltas
- Cluster: `C19`
- Owner team: `openspec-governance`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: openspec/, task graph, planning docs
- Produced artifacts: planning/artifacts/openspec/008-add-harness-registry-spec-deltas.md
- Blocking dependencies: C10-002
- CI gates: openspec-validate, docs-truth
- Review: owner team review, standard review

### C19-009: Add ui/ux automation spec deltas
- Cluster: `C19`
- Owner team: `openspec-governance`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: openspec/, task graph, planning docs
- Produced artifacts: planning/artifacts/openspec/009-add-UI/UX-automation-spec-deltas.md
- Blocking dependencies: C10-002
- CI gates: openspec-validate, docs-truth
- Review: owner team review, standard review

### C19-010: Validate openspec in ci
- Cluster: `C19`
- Owner team: `openspec-governance`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: openspec/, task graph, planning docs
- Produced artifacts: planning/artifacts/openspec/010-validate-OpenSpec-in-CI.md
- Blocking dependencies: C10-002
- CI gates: openspec-validate, docs-truth
- Review: owner team review, standard review

### C19-011: Archive completed change protocol
- Cluster: `C19`
- Owner team: `openspec-governance`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: openspec/, task graph, planning docs
- Produced artifacts: planning/artifacts/openspec/011-archive-completed-change-protocol.md
- Blocking dependencies: C10-002
- CI gates: openspec-validate, docs-truth
- Review: owner team review, standard review

### C19-012: Openspec docs ux integration
- Cluster: `C19`
- Owner team: `openspec-governance`
- Risk: `medium`; complexity: `M`; merge risk: `2`
- Required inputs: openspec/, task graph, planning docs
- Produced artifacts: planning/artifacts/openspec/012-OpenSpec-docs-UX-integration.md
- Blocking dependencies: C10-002
- CI gates: openspec-validate, docs-truth
- Review: owner team review, standard review
