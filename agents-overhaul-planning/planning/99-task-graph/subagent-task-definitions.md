# Granular Subagent Task Definitions

Total tasks: 305

## Clusters

- `C00`: Repo Sync and OpenSpec Reconciliation
- `C01`: Canonical Registry Core
- `C02`: Skills-First Packaging and Lifecycle
- `C03`: MCP Curation and Live-Systems Layer
- `C04`: Harness-Specific Projections
- `C05`: CLI/UI Automation
- `C06`: Config Safety and Supply Chain
- `C07`: CI/CD, Evals, and Observability
- `C08`: Docs and AI Instructions
- `C09`: Migration and Release

## Critical Path

C00-001 -> C00-009 -> C00-010 -> C01-001 -> C01-002 -> C01-003 -> C01-009 -> C02-001 -> C03-005 -> C04-001 -> C05-006 -> C06-001 -> C07-008 -> C08-001 -> C09-001

## Task Nodes

### C00-001: Inventory latest repository tree and classify source/generated files

- Cluster: `C00`
- Owner team: `platform-core`
- Blocking dependencies: none
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `2`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C00-001.md
- CI gates: schema, docs-truth
- Review requirements: owner team review, standard review

### C00-002: Parse pyproject, package metadata, Makefile, uv.lock, and CLI entrypoints

- Cluster: `C00`
- Owner team: `platform-core`
- Blocking dependencies: none
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `2`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C00-002.md
- CI gates: schema, docs-truth
- Review requirements: owner team review, standard review

### C00-003: Inventory skills directory and validate every SKILL.md candidate

- Cluster: `C00`
- Owner team: `platform-core`
- Blocking dependencies: none
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `2`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C00-003.md
- CI gates: schema, docs-truth
- Review requirements: owner team review, standard review

### C00-004: Inventory MCP configs and normalize current MCP server records

- Cluster: `C00`
- Owner team: `platform-core`
- Blocking dependencies: none
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `2`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C00-004.md
- CI gates: schema, docs-truth
- Review requirements: owner team review, standard review

### C00-005: Inventory harness-specific directories and claim support tiers

- Cluster: `C00`
- Owner team: `platform-core`
- Blocking dependencies: none
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `2`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C00-005.md
- CI gates: schema, docs-truth
- Review requirements: owner team review, standard review

### C00-006: Detect README/raw-rendered quickstart drift and command inconsistencies

- Cluster: `C00`
- Owner team: `platform-core`
- Blocking dependencies: none
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `2`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C00-006.md
- CI gates: schema, docs-truth
- Review requirements: owner team review, standard review

### C00-007: Inventory docs and AI instruction files

- Cluster: `C00`
- Owner team: `platform-core`
- Blocking dependencies: none
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `2`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C00-007.md
- CI gates: schema, docs-truth
- Review requirements: owner team review, standard review

### C00-008: Inventory tests/CI workflows/pre-commit quality gates

- Cluster: `C00`
- Owner team: `platform-core`
- Blocking dependencies: none
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `2`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C00-008.md
- CI gates: schema, docs-truth
- Review requirements: owner team review, standard review

### C00-009: Inventory existing OpenSpec assets without overwriting them

- Cluster: `C00`
- Owner team: `openspec-governance`
- Blocking dependencies: none
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `2`
- Required expertise: OpenSpec reconciliation and spec/task alignment.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C00-009.md
- CI gates: schema, docs-truth
- Review requirements: owner team review, standard review

### C00-010: Generate repo-sync inventory JSON

- Cluster: `C00`
- Owner team: `platform-core`
- Blocking dependencies: none
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `2`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C00-010.md
- CI gates: schema, docs-truth
- Review requirements: owner team review, standard review

### C00-011: Generate initial drift report between planning bundle and live repo

- Cluster: `C00`
- Owner team: `platform-core`
- Blocking dependencies: none
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `2`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C00-011.md
- CI gates: schema, docs-truth
- Review requirements: owner team review, standard review

### C00-012: Reconcile OpenSpec active changes with planning docs

- Cluster: `C00`
- Owner team: `openspec-governance`
- Blocking dependencies: none
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `2`
- Required expertise: OpenSpec reconciliation and spec/task alignment.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C00-012.md
- CI gates: schema, docs-truth
- Review requirements: owner team review, standard review

### C00-013: Create OpenSpec-to-task-graph mapping table

- Cluster: `C00`
- Owner team: `openspec-governance`
- Blocking dependencies: none
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `2`
- Required expertise: OpenSpec reconciliation and spec/task alignment.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C00-013.md
- CI gates: schema, docs-truth
- Review requirements: owner team review, standard review

### C00-014: Freeze support-tier vocabulary

- Cluster: `C00`
- Owner team: `platform-core`
- Blocking dependencies: none
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `2`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C00-014.md
- CI gates: schema, docs-truth
- Review requirements: owner team review, standard review

### C00-015: Publish repo-sync analysis doc

- Cluster: `C00`
- Owner team: `platform-core`
- Blocking dependencies: none
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `2`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C00-015.md
- CI gates: schema, docs-truth
- Review requirements: owner team review, standard review

### C00-016: Define branch/PR naming convention for overhaul work

- Cluster: `C00`
- Owner team: `platform-core`
- Blocking dependencies: none
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `2`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C00-016.md
- CI gates: schema, docs-truth
- Review requirements: owner team review, standard review

### C00-017: Create conflict-surface map for generated docs and harness configs

- Cluster: `C00`
- Owner team: `platform-core`
- Blocking dependencies: none
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `2`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C00-017.md
- CI gates: schema, docs-truth
- Review requirements: owner team review, standard review

### C00-018: Add repo-sync CI smoke test fixture

- Cluster: `C00`
- Owner team: `platform-core`
- Blocking dependencies: none
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `2`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C00-018.md
- CI gates: schema, docs-truth
- Review requirements: owner team review, standard review

### C01-001: Define canonical harness registry JSON/YAML schema

- Cluster: `C01`
- Owner team: `platform-core`
- Blocking dependencies: C00-010
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C01-001.md
- CI gates: schema, golden-fixtures
- Review requirements: owner team review, standard review

### C01-002: Define canonical skill registry schema

- Cluster: `C01`
- Owner team: `platform-core`
- Blocking dependencies: C00-010
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C01-002.md
- CI gates: schema, golden-fixtures
- Review requirements: owner team review, standard review

### C01-003: Define canonical MCP registry schema

- Cluster: `C01`
- Owner team: `platform-core`
- Blocking dependencies: C00-010
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C01-003.md
- CI gates: schema, golden-fixtures
- Review requirements: owner team review, standard review

### C01-004: Define plugin/extension registry schema

- Cluster: `C01`
- Owner team: `platform-core`
- Blocking dependencies: C00-010
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C01-004.md
- CI gates: schema, golden-fixtures
- Review requirements: owner team review, standard review

### C01-005: Define docs artifact registry schema

- Cluster: `C01`
- Owner team: `platform-core`
- Blocking dependencies: C00-010
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C01-005.md
- CI gates: schema, golden-fixtures
- Review requirements: owner team review, standard review

### C01-006: Define external capability catalog schema

- Cluster: `C01`
- Owner team: `platform-core`
- Blocking dependencies: C00-010
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C01-006.md
- CI gates: schema, golden-fixtures
- Review requirements: owner team review, standard review

### C01-007: Define support-tier validation rules

- Cluster: `C01`
- Owner team: `platform-core`
- Blocking dependencies: C00-010
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C01-007.md
- CI gates: schema, golden-fixtures
- Review requirements: owner team review, standard review

### C01-008: Define capability graph model and edges

- Cluster: `C01`
- Owner team: `platform-core`
- Blocking dependencies: C00-010
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C01-008.md
- CI gates: schema, golden-fixtures
- Review requirements: owner team review, standard review

### C01-009: Implement registry loader and resolver interface design

- Cluster: `C01`
- Owner team: `platform-core`
- Blocking dependencies: C00-010
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C01-009.md
- CI gates: schema, golden-fixtures
- Review requirements: owner team review, standard review

### C01-010: Create generated harness support matrix

- Cluster: `C01`
- Owner team: `platform-core`
- Blocking dependencies: C00-010
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C01-010.md
- CI gates: schema, golden-fixtures
- Review requirements: owner team review, standard review

### C01-011: Create generated skill support matrix

- Cluster: `C01`
- Owner team: `platform-core`
- Blocking dependencies: C00-010
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C01-011.md
- CI gates: schema, golden-fixtures
- Review requirements: owner team review, standard review

### C01-012: Create generated MCP risk matrix

- Cluster: `C01`
- Owner team: `platform-core`
- Blocking dependencies: C00-010
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C01-012.md
- CI gates: schema, golden-fixtures
- Review requirements: owner team review, standard review

### C01-013: Create registry schema tests

- Cluster: `C01`
- Owner team: `platform-core`
- Blocking dependencies: C00-010
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C01-013.md
- CI gates: schema, golden-fixtures
- Review requirements: owner team review, standard review

### C01-014: Create registry golden fixture set

- Cluster: `C01`
- Owner team: `platform-core`
- Blocking dependencies: C00-010
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C01-014.md
- CI gates: schema, golden-fixtures
- Review requirements: owner team review, standard review

### C01-015: Add registry docs generation plan

- Cluster: `C01`
- Owner team: `platform-core`
- Blocking dependencies: C00-010
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C01-015.md
- CI gates: schema, golden-fixtures
- Review requirements: owner team review, standard review

### C01-016: Add registry drift-detection plan

- Cluster: `C01`
- Owner team: `platform-core`
- Blocking dependencies: C00-010
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C01-016.md
- CI gates: schema, golden-fixtures
- Review requirements: owner team review, standard review

### C01-017: Add registry diff report UX spec

- Cluster: `C01`
- Owner team: `platform-core`
- Blocking dependencies: C00-010
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C01-017.md
- CI gates: schema, golden-fixtures
- Review requirements: owner team review, standard review

### C01-018: Lock registry schema version v1

- Cluster: `C01`
- Owner team: `platform-core`
- Blocking dependencies: C00-010
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Registry schemas, adapters, transaction engine, repo inventory.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C01-018.md
- CI gates: schema, golden-fixtures
- Review requirements: owner team review, standard review

### C02-001: Normalize all local skills to Agent Skills package model

- Cluster: `C02`
- Owner team: `skills-team`
- Blocking dependencies: C01-002
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Skill packaging, registry, lifecycle, external skills.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C02-001.md
- CI gates: skill-validation, cli-conformance
- Review requirements: owner team review, standard review

### C02-002: Validate required SKILL.md frontmatter fields

- Cluster: `C02`
- Owner team: `skills-team`
- Blocking dependencies: C01-002
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Skill packaging, registry, lifecycle, external skills.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C02-002.md
- CI gates: skill-validation, cli-conformance
- Review requirements: owner team review, standard review

### C02-003: Move heavy reference content into references/assets for progressive disclosure

- Cluster: `C02`
- Owner team: `skills-team`
- Blocking dependencies: C01-002
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Skill packaging, registry, lifecycle, external skills.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C02-003.md
- CI gates: skill-validation, cli-conformance
- Review requirements: owner team review, standard review

### C02-004: Inventory scripts and classify execution risk

- Cluster: `C02`
- Owner team: `skills-team`
- Blocking dependencies: C01-002
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Skill packaging, registry, lifecycle, external skills.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C02-004.md
- CI gates: skill-validation, cli-conformance
- Review requirements: owner team review, standard review

### C02-005: Add CLI conformance fixture for each script-backed skill

- Cluster: `C02`
- Owner team: `skills-team`
- Blocking dependencies: C01-002
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Skill packaging, registry, lifecycle, external skills.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C02-005.md
- CI gates: skill-validation, cli-conformance
- Review requirements: owner team review, standard review

### C02-006: Define skill lockfile schema with source/ref/checksum

- Cluster: `C02`
- Owner team: `skills-team`
- Blocking dependencies: C01-002
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Skill packaging, registry, lifecycle, external skills.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C02-006.md
- CI gates: skill-validation, cli-conformance
- Review requirements: owner team review, standard review

### C02-007: Design npx skills lifecycle wrapper commands

- Cluster: `C02`
- Owner team: `skills-team`
- Blocking dependencies: C01-002
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Skill packaging, registry, lifecycle, external skills.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C02-007.md
- CI gates: skill-validation, cli-conformance
- Review requirements: owner team review, standard review

### C02-008: Evaluate skills.sh registry metadata and trust fields

- Cluster: `C02`
- Owner team: `skills-team`
- Blocking dependencies: C01-002
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Skill packaging, registry, lifecycle, external skills.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C02-008.md
- CI gates: skill-validation, cli-conformance
- Review requirements: owner team review, standard review

### C02-009: Evaluate Microsoft skills repo for reusable patterns

- Cluster: `C02`
- Owner team: `skills-team`
- Blocking dependencies: C01-002
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Skill packaging, registry, lifecycle, external skills.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C02-009.md
- CI gates: skill-validation, cli-conformance
- Review requirements: owner team review, standard review

### C02-010: Evaluate GitHub Awesome Copilot skills and agents

- Cluster: `C02`
- Owner team: `skills-team`
- Blocking dependencies: C01-002
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Skill packaging, registry, lifecycle, external skills.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C02-010.md
- CI gates: skill-validation, cli-conformance
- Review requirements: owner team review, standard review

### C02-011: Evaluate CrewAI skills pack

- Cluster: `C02`
- Owner team: `skills-team`
- Blocking dependencies: C01-002
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Skill packaging, registry, lifecycle, external skills.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C02-011.md
- CI gates: skill-validation, cli-conformance
- Review requirements: owner team review, standard review

### C02-012: Evaluate tech-leads agent-skills lockfile/hash patterns

- Cluster: `C02`
- Owner team: `skills-team`
- Blocking dependencies: C01-002
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Skill packaging, registry, lifecycle, external skills.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C02-012.md
- CI gates: skill-validation, cli-conformance
- Review requirements: owner team review, standard review

### C02-013: Create external skill adoption rubric

- Cluster: `C02`
- Owner team: `skills-team`
- Blocking dependencies: C01-002
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Skill packaging, registry, lifecycle, external skills.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C02-013.md
- CI gates: skill-validation, cli-conformance
- Review requirements: owner team review, standard review

### C02-014: Create skill signing/provenance plan

- Cluster: `C02`
- Owner team: `skills-team`
- Blocking dependencies: C01-002
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Skill packaging, registry, lifecycle, external skills.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C02-014.md
- CI gates: skill-validation, cli-conformance
- Review requirements: owner team review, security review if tools/config/secrets touched

### C02-015: Create skill update/rollback semantics

- Cluster: `C02`
- Owner team: `skills-team`
- Blocking dependencies: C01-002
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Skill packaging, registry, lifecycle, external skills.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C02-015.md
- CI gates: skill-validation, cli-conformance
- Review requirements: owner team review, standard review

### C02-016: Add skill install preview UX

- Cluster: `C02`
- Owner team: `skills-team`
- Blocking dependencies: C01-002
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Skill packaging, registry, lifecycle, external skills.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C02-016.md
- CI gates: skill-validation, cli-conformance
- Review requirements: owner team review, standard review

### C02-017: Add skill audit command spec

- Cluster: `C02`
- Owner team: `skills-team`
- Blocking dependencies: C01-002
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Skill packaging, registry, lifecycle, external skills.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C02-017.md
- CI gates: skill-validation, cli-conformance
- Review requirements: owner team review, standard review

### C02-018: Add skill docs generation spec

- Cluster: `C02`
- Owner team: `skills-team`
- Blocking dependencies: C01-002
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Skill packaging, registry, lifecycle, external skills.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C02-018.md
- CI gates: skill-validation, cli-conformance
- Review requirements: owner team review, standard review

### C02-019: Add skill security policy to AGENTS.md draft

- Cluster: `C02`
- Owner team: `skills-team`
- Blocking dependencies: C01-002
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Skill packaging, registry, lifecycle, external skills.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C02-019.md
- CI gates: skill-validation, cli-conformance
- Review requirements: owner team review, security review if tools/config/secrets touched

### C02-020: Add skill-vs-MCP replacement report

- Cluster: `C02`
- Owner team: `skills-team`
- Blocking dependencies: C01-002
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Skill packaging, registry, lifecycle, external skills.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C02-020.md
- CI gates: skill-validation, cli-conformance
- Review requirements: owner team review, standard review

### C02-021: Add skill fixture mode guidance

- Cluster: `C02`
- Owner team: `skills-team`
- Blocking dependencies: C01-002
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Skill packaging, registry, lifecycle, external skills.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C02-021.md
- CI gates: skill-validation, cli-conformance
- Review requirements: owner team review, standard review

### C02-022: Add skill telemetry/redaction guidance

- Cluster: `C02`
- Owner team: `skills-team`
- Blocking dependencies: C01-002
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Skill packaging, registry, lifecycle, external skills.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C02-022.md
- CI gates: skill-validation, cli-conformance
- Review requirements: owner team review, standard review

### C02-023: Create skill inventory JSON generator task

- Cluster: `C02`
- Owner team: `skills-team`
- Blocking dependencies: C01-002
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Skill packaging, registry, lifecycle, external skills.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C02-023.md
- CI gates: skill-validation, cli-conformance
- Review requirements: owner team review, standard review

### C02-024: Create first cohort of high-value adopted/adapted skills

- Cluster: `C02`
- Owner team: `skills-team`
- Blocking dependencies: C01-002
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Skill packaging, registry, lifecycle, external skills.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C02-024.md
- CI gates: skill-validation, cli-conformance
- Review requirements: owner team review, standard review

### C03-001: Scan Glama MCP index for candidate live-systems servers

- Cluster: `C03`
- Owner team: `mcp-team`
- Blocking dependencies: C01-003
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: MCP inventory, curation, security, smoke tests.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C03-001.md
- CI gates: mcp-schema, mcp-smoke, security-scan
- Review requirements: owner team review, standard review

### C03-002: Scan PulseMCP index for candidate live-systems servers

- Cluster: `C03`
- Owner team: `mcp-team`
- Blocking dependencies: C01-003
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: MCP inventory, curation, security, smoke tests.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C03-002.md
- CI gates: mcp-schema, mcp-smoke, security-scan
- Review requirements: owner team review, standard review

### C03-003: Scan MCP.so for candidate live-systems servers

- Cluster: `C03`
- Owner team: `mcp-team`
- Blocking dependencies: C01-003
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: MCP inventory, curation, security, smoke tests.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C03-003.md
- CI gates: mcp-schema, mcp-smoke, security-scan
- Review requirements: owner team review, standard review

### C03-004: Scan Awesome MCP lists and extract high-signal upstream repos

- Cluster: `C03`
- Owner team: `mcp-team`
- Blocking dependencies: C01-003
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: MCP inventory, curation, security, smoke tests.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C03-004.md
- CI gates: mcp-schema, mcp-smoke, security-scan
- Review requirements: owner team review, standard review

### C03-005: Normalize current repo MCP inventory into MCP registry

- Cluster: `C03`
- Owner team: `mcp-team`
- Blocking dependencies: C01-003
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: MCP inventory, curation, security, smoke tests.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C03-005.md
- CI gates: mcp-schema, mcp-smoke, security-scan
- Review requirements: owner team review, standard review

### C03-006: Classify every MCP by domain and live-state necessity

- Cluster: `C03`
- Owner team: `mcp-team`
- Blocking dependencies: C01-003
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: MCP inventory, curation, security, smoke tests.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C03-006.md
- CI gates: mcp-schema, mcp-smoke, security-scan
- Review requirements: owner team review, standard review

### C03-007: Classify transport: stdio, Streamable HTTP, deprecated SSE, other

- Cluster: `C03`
- Owner team: `mcp-team`
- Blocking dependencies: C01-003
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: MCP inventory, curation, security, smoke tests.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C03-007.md
- CI gates: mcp-schema, mcp-smoke, security-scan
- Review requirements: owner team review, standard review

### C03-008: Classify auth model and secret requirements

- Cluster: `C03`
- Owner team: `mcp-team`
- Blocking dependencies: C01-003
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: MCP inventory, curation, security, smoke tests.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C03-008.md
- CI gates: mcp-schema, mcp-smoke, security-scan
- Review requirements: owner team review, security review if tools/config/secrets touched

### C03-009: Mark static/redundant MCPs for skill replacement

- Cluster: `C03`
- Owner team: `mcp-team`
- Blocking dependencies: C01-003
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: MCP inventory, curation, security, smoke tests.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C03-009.md
- CI gates: mcp-schema, mcp-smoke, security-scan
- Review requirements: owner team review, standard review

### C03-010: Promote browser automation MCP candidates for review

- Cluster: `C03`
- Owner team: `mcp-team`
- Blocking dependencies: C01-003
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: MCP inventory, curation, security, smoke tests.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C03-010.md
- CI gates: mcp-schema, mcp-smoke, security-scan
- Review requirements: owner team review, standard review

### C03-011: Promote docs/search MCP candidates for review

- Cluster: `C03`
- Owner team: `mcp-team`
- Blocking dependencies: C01-003
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: MCP inventory, curation, security, smoke tests.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C03-011.md
- CI gates: mcp-schema, mcp-smoke, security-scan
- Review requirements: owner team review, standard review

### C03-012: Promote GitHub/CI/cloud MCP candidates for review

- Cluster: `C03`
- Owner team: `mcp-team`
- Blocking dependencies: C01-003
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: MCP inventory, curation, security, smoke tests.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C03-012.md
- CI gates: mcp-schema, mcp-smoke, security-scan
- Review requirements: owner team review, standard review

### C03-013: Reject or quarantine broad filesystem MCPs unless narrowly justified

- Cluster: `C03`
- Owner team: `mcp-team`
- Blocking dependencies: C01-003
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: MCP inventory, curation, security, smoke tests.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C03-013.md
- CI gates: mcp-schema, mcp-smoke, security-scan
- Review requirements: owner team review, security review if tools/config/secrets touched

### C03-014: Run mcp-scan or equivalent scanner on current MCP configs

- Cluster: `C03`
- Owner team: `mcp-team`
- Blocking dependencies: C01-003
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: MCP inventory, curation, security, smoke tests.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C03-014.md
- CI gates: mcp-schema, mcp-smoke, security-scan
- Review requirements: owner team review, security review if tools/config/secrets touched

### C03-015: Define MCP sandbox policy

- Cluster: `C03`
- Owner team: `mcp-team`
- Blocking dependencies: C01-003
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: MCP inventory, curation, security, smoke tests.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C03-015.md
- CI gates: mcp-schema, mcp-smoke, security-scan
- Review requirements: owner team review, security review if tools/config/secrets touched

### C03-016: Define MCP pinning and tool-description diff policy

- Cluster: `C03`
- Owner team: `mcp-team`
- Blocking dependencies: C01-003
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: MCP inventory, curation, security, smoke tests.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C03-016.md
- CI gates: mcp-schema, mcp-smoke, security-scan
- Review requirements: owner team review, security review if tools/config/secrets touched

### C03-017: Create MCP smoke test harness

- Cluster: `C03`
- Owner team: `mcp-team`
- Blocking dependencies: C01-003
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: MCP inventory, curation, security, smoke tests.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C03-017.md
- CI gates: mcp-schema, mcp-smoke, security-scan
- Review requirements: owner team review, standard review

### C03-018: Create MCP risk matrix docs

- Cluster: `C03`
- Owner team: `mcp-team`
- Blocking dependencies: C01-003
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: MCP inventory, curation, security, smoke tests.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C03-018.md
- CI gates: mcp-schema, mcp-smoke, security-scan
- Review requirements: owner team review, standard review

### C03-019: Create MCP deprecation/rollback plan

- Cluster: `C03`
- Owner team: `mcp-team`
- Blocking dependencies: C01-003
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: MCP inventory, curation, security, smoke tests.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C03-019.md
- CI gates: mcp-schema, mcp-smoke, security-scan
- Review requirements: owner team review, standard review

### C03-020: Create MCP index refresh job spec

- Cluster: `C03`
- Owner team: `mcp-team`
- Blocking dependencies: C01-003
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: MCP inventory, curation, security, smoke tests.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C03-020.md
- CI gates: mcp-schema, mcp-smoke, security-scan
- Review requirements: owner team review, security review if tools/config/secrets touched

### C03-021: Create MCP security exception template

- Cluster: `C03`
- Owner team: `mcp-team`
- Blocking dependencies: C01-003
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: MCP inventory, curation, security, smoke tests.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C03-021.md
- CI gates: mcp-schema, mcp-smoke, security-scan
- Review requirements: owner team review, security review if tools/config/secrets touched

### C03-022: Create per-harness MCP projection fixtures

- Cluster: `C03`
- Owner team: `mcp-team`
- Blocking dependencies: C01-003
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: MCP inventory, curation, security, smoke tests.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C03-022.md
- CI gates: mcp-schema, mcp-smoke, security-scan
- Review requirements: owner team review, standard review

### C03-023: Add MCP audit docs to README/docs plan

- Cluster: `C03`
- Owner team: `mcp-team`
- Blocking dependencies: C01-003
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: MCP inventory, curation, security, smoke tests.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C03-023.md
- CI gates: mcp-schema, mcp-smoke, security-scan
- Review requirements: owner team review, standard review

### C03-024: Define uvx/npx install normalization for MCP servers

- Cluster: `C03`
- Owner team: `mcp-team`
- Blocking dependencies: C01-003
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: MCP inventory, curation, security, smoke tests.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C03-024.md
- CI gates: mcp-schema, mcp-smoke, security-scan
- Review requirements: owner team review, standard review

### C04-001: Claude Code: Validate repo artifacts and support tier

- Cluster: `C04`
- Owner team: `harness-claude`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Claude Desktop/Code adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/claude-code.md, tests/fixtures/harnesses/claude-code/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-002: Claude Code: Map official extension/plugin/config surfaces

- Cluster: `C04`
- Owner team: `harness-claude`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Claude Desktop/Code adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/claude-code.md, tests/fixtures/harnesses/claude-code/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-003: Claude Code: Define skill projection behavior

- Cluster: `C04`
- Owner team: `harness-claude`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Claude Desktop/Code adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/claude-code.md, tests/fixtures/harnesses/claude-code/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-004: Claude Code: Define MCP projection behavior and constraints

- Cluster: `C04`
- Owner team: `harness-claude`
- Blocking dependencies: C01-001, C02-001, C03-005
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Claude Desktop/Code adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/claude-code.md, tests/fixtures/harnesses/claude-code/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-005: Claude Code: Define instruction/rules/doc projection behavior

- Cluster: `C04`
- Owner team: `harness-claude`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Claude Desktop/Code adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/claude-code.md, tests/fixtures/harnesses/claude-code/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-006: Claude Code: Create golden config fixtures

- Cluster: `C04`
- Owner team: `harness-claude`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Claude Desktop/Code adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/claude-code.md, tests/fixtures/harnesses/claude-code/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-007: Claude Code: Create harness-specific setup docs

- Cluster: `C04`
- Owner team: `harness-claude`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Claude Desktop/Code adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/claude-code.md, tests/fixtures/harnesses/claude-code/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-008: Claude Code: Create drift detection and repair behavior

- Cluster: `C04`
- Owner team: `harness-claude`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Claude Desktop/Code adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/claude-code.md, tests/fixtures/harnesses/claude-code/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-009: Claude Code: Create rollback validation fixture

- Cluster: `C04`
- Owner team: `harness-claude`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Claude Desktop/Code adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/claude-code.md, tests/fixtures/harnesses/claude-code/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-010: Claude Desktop: Validate repo artifacts and support tier

- Cluster: `C04`
- Owner team: `harness-claude`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Claude Desktop/Code adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/claude-desktop.md, tests/fixtures/harnesses/claude-desktop/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-011: Claude Desktop: Map official extension/plugin/config surfaces

- Cluster: `C04`
- Owner team: `harness-claude`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Claude Desktop/Code adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/claude-desktop.md, tests/fixtures/harnesses/claude-desktop/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-012: Claude Desktop: Define skill projection behavior

- Cluster: `C04`
- Owner team: `harness-claude`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Claude Desktop/Code adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/claude-desktop.md, tests/fixtures/harnesses/claude-desktop/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-013: Claude Desktop: Define MCP projection behavior and constraints

- Cluster: `C04`
- Owner team: `harness-claude`
- Blocking dependencies: C01-001, C02-001, C03-005
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Claude Desktop/Code adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/claude-desktop.md, tests/fixtures/harnesses/claude-desktop/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-014: Claude Desktop: Define instruction/rules/doc projection behavior

- Cluster: `C04`
- Owner team: `harness-claude`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Claude Desktop/Code adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/claude-desktop.md, tests/fixtures/harnesses/claude-desktop/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-015: Claude Desktop: Create golden config fixtures

- Cluster: `C04`
- Owner team: `harness-claude`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Claude Desktop/Code adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/claude-desktop.md, tests/fixtures/harnesses/claude-desktop/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-016: Claude Desktop: Create harness-specific setup docs

- Cluster: `C04`
- Owner team: `harness-claude`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Claude Desktop/Code adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/claude-desktop.md, tests/fixtures/harnesses/claude-desktop/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-017: Claude Desktop: Create drift detection and repair behavior

- Cluster: `C04`
- Owner team: `harness-claude`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Claude Desktop/Code adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/claude-desktop.md, tests/fixtures/harnesses/claude-desktop/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-018: Claude Desktop: Create rollback validation fixture

- Cluster: `C04`
- Owner team: `harness-claude`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Claude Desktop/Code adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/claude-desktop.md, tests/fixtures/harnesses/claude-desktop/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-019: ChatGPT: Validate repo artifacts and support tier

- Cluster: `C04`
- Owner team: `harness-openai`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: ChatGPT and Codex adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/chatgpt.md, tests/fixtures/harnesses/chatgpt/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-020: ChatGPT: Map official extension/plugin/config surfaces

- Cluster: `C04`
- Owner team: `harness-openai`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: ChatGPT and Codex adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/chatgpt.md, tests/fixtures/harnesses/chatgpt/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-021: ChatGPT: Define skill projection behavior

- Cluster: `C04`
- Owner team: `harness-openai`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: ChatGPT and Codex adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/chatgpt.md, tests/fixtures/harnesses/chatgpt/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-022: ChatGPT: Define MCP projection behavior and constraints

- Cluster: `C04`
- Owner team: `harness-openai`
- Blocking dependencies: C01-001, C02-001, C03-005
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: ChatGPT and Codex adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/chatgpt.md, tests/fixtures/harnesses/chatgpt/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-023: ChatGPT: Define instruction/rules/doc projection behavior

- Cluster: `C04`
- Owner team: `harness-openai`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: ChatGPT and Codex adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/chatgpt.md, tests/fixtures/harnesses/chatgpt/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-024: ChatGPT: Create golden config fixtures

- Cluster: `C04`
- Owner team: `harness-openai`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: ChatGPT and Codex adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/chatgpt.md, tests/fixtures/harnesses/chatgpt/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-025: ChatGPT: Create harness-specific setup docs

- Cluster: `C04`
- Owner team: `harness-openai`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: ChatGPT and Codex adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/chatgpt.md, tests/fixtures/harnesses/chatgpt/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-026: ChatGPT: Create drift detection and repair behavior

- Cluster: `C04`
- Owner team: `harness-openai`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: ChatGPT and Codex adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/chatgpt.md, tests/fixtures/harnesses/chatgpt/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-027: ChatGPT: Create rollback validation fixture

- Cluster: `C04`
- Owner team: `harness-openai`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: ChatGPT and Codex adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/chatgpt.md, tests/fixtures/harnesses/chatgpt/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-028: OpenAI Codex: Validate repo artifacts and support tier

- Cluster: `C04`
- Owner team: `harness-openai`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: ChatGPT and Codex adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/codex.md, tests/fixtures/harnesses/codex/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-029: OpenAI Codex: Map official extension/plugin/config surfaces

- Cluster: `C04`
- Owner team: `harness-openai`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: ChatGPT and Codex adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/codex.md, tests/fixtures/harnesses/codex/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-030: OpenAI Codex: Define skill projection behavior

- Cluster: `C04`
- Owner team: `harness-openai`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: ChatGPT and Codex adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/codex.md, tests/fixtures/harnesses/codex/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-031: OpenAI Codex: Define MCP projection behavior and constraints

- Cluster: `C04`
- Owner team: `harness-openai`
- Blocking dependencies: C01-001, C02-001, C03-005
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: ChatGPT and Codex adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/codex.md, tests/fixtures/harnesses/codex/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-032: OpenAI Codex: Define instruction/rules/doc projection behavior

- Cluster: `C04`
- Owner team: `harness-openai`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: ChatGPT and Codex adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/codex.md, tests/fixtures/harnesses/codex/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-033: OpenAI Codex: Create golden config fixtures

- Cluster: `C04`
- Owner team: `harness-openai`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: ChatGPT and Codex adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/codex.md, tests/fixtures/harnesses/codex/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-034: OpenAI Codex: Create harness-specific setup docs

- Cluster: `C04`
- Owner team: `harness-openai`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: ChatGPT and Codex adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/codex.md, tests/fixtures/harnesses/codex/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-035: OpenAI Codex: Create drift detection and repair behavior

- Cluster: `C04`
- Owner team: `harness-openai`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: ChatGPT and Codex adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/codex.md, tests/fixtures/harnesses/codex/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-036: OpenAI Codex: Create rollback validation fixture

- Cluster: `C04`
- Owner team: `harness-openai`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: ChatGPT and Codex adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/codex.md, tests/fixtures/harnesses/codex/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-037: GitHub Copilot Web: Validate repo artifacts and support tier

- Cluster: `C04`
- Owner team: `harness-copilot`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: GitHub Copilot Web/CLI adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/github-copilot-web.md, tests/fixtures/harnesses/github-copilot-web/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-038: GitHub Copilot Web: Map official extension/plugin/config surfaces

- Cluster: `C04`
- Owner team: `harness-copilot`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: GitHub Copilot Web/CLI adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/github-copilot-web.md, tests/fixtures/harnesses/github-copilot-web/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-039: GitHub Copilot Web: Define skill projection behavior

- Cluster: `C04`
- Owner team: `harness-copilot`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: GitHub Copilot Web/CLI adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/github-copilot-web.md, tests/fixtures/harnesses/github-copilot-web/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-040: GitHub Copilot Web: Define MCP projection behavior and constraints

- Cluster: `C04`
- Owner team: `harness-copilot`
- Blocking dependencies: C01-001, C02-001, C03-005
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: GitHub Copilot Web/CLI adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/github-copilot-web.md, tests/fixtures/harnesses/github-copilot-web/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-041: GitHub Copilot Web: Define instruction/rules/doc projection behavior

- Cluster: `C04`
- Owner team: `harness-copilot`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: GitHub Copilot Web/CLI adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/github-copilot-web.md, tests/fixtures/harnesses/github-copilot-web/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-042: GitHub Copilot Web: Create golden config fixtures

- Cluster: `C04`
- Owner team: `harness-copilot`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: GitHub Copilot Web/CLI adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/github-copilot-web.md, tests/fixtures/harnesses/github-copilot-web/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-043: GitHub Copilot Web: Create harness-specific setup docs

- Cluster: `C04`
- Owner team: `harness-copilot`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: GitHub Copilot Web/CLI adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/github-copilot-web.md, tests/fixtures/harnesses/github-copilot-web/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-044: GitHub Copilot Web: Create drift detection and repair behavior

- Cluster: `C04`
- Owner team: `harness-copilot`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: GitHub Copilot Web/CLI adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/github-copilot-web.md, tests/fixtures/harnesses/github-copilot-web/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-045: GitHub Copilot Web: Create rollback validation fixture

- Cluster: `C04`
- Owner team: `harness-copilot`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: GitHub Copilot Web/CLI adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/github-copilot-web.md, tests/fixtures/harnesses/github-copilot-web/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-046: GitHub Copilot CLI: Validate repo artifacts and support tier

- Cluster: `C04`
- Owner team: `harness-copilot`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: GitHub Copilot Web/CLI adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/github-copilot-cli.md, tests/fixtures/harnesses/github-copilot-cli/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-047: GitHub Copilot CLI: Map official extension/plugin/config surfaces

- Cluster: `C04`
- Owner team: `harness-copilot`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: GitHub Copilot Web/CLI adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/github-copilot-cli.md, tests/fixtures/harnesses/github-copilot-cli/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-048: GitHub Copilot CLI: Define skill projection behavior

- Cluster: `C04`
- Owner team: `harness-copilot`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: GitHub Copilot Web/CLI adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/github-copilot-cli.md, tests/fixtures/harnesses/github-copilot-cli/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-049: GitHub Copilot CLI: Define MCP projection behavior and constraints

- Cluster: `C04`
- Owner team: `harness-copilot`
- Blocking dependencies: C01-001, C02-001, C03-005
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: GitHub Copilot Web/CLI adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/github-copilot-cli.md, tests/fixtures/harnesses/github-copilot-cli/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-050: GitHub Copilot CLI: Define instruction/rules/doc projection behavior

- Cluster: `C04`
- Owner team: `harness-copilot`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: GitHub Copilot Web/CLI adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/github-copilot-cli.md, tests/fixtures/harnesses/github-copilot-cli/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-051: GitHub Copilot CLI: Create golden config fixtures

- Cluster: `C04`
- Owner team: `harness-copilot`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: GitHub Copilot Web/CLI adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/github-copilot-cli.md, tests/fixtures/harnesses/github-copilot-cli/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-052: GitHub Copilot CLI: Create harness-specific setup docs

- Cluster: `C04`
- Owner team: `harness-copilot`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: GitHub Copilot Web/CLI adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/github-copilot-cli.md, tests/fixtures/harnesses/github-copilot-cli/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-053: GitHub Copilot CLI: Create drift detection and repair behavior

- Cluster: `C04`
- Owner team: `harness-copilot`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: GitHub Copilot Web/CLI adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/github-copilot-cli.md, tests/fixtures/harnesses/github-copilot-cli/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-054: GitHub Copilot CLI: Create rollback validation fixture

- Cluster: `C04`
- Owner team: `harness-copilot`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: GitHub Copilot Web/CLI adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/github-copilot-cli.md, tests/fixtures/harnesses/github-copilot-cli/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-055: OpenCode: Validate repo artifacts and support tier

- Cluster: `C04`
- Owner team: `harness-opencode`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: OpenCode adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/opencode.md, tests/fixtures/harnesses/opencode/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-056: OpenCode: Map official extension/plugin/config surfaces

- Cluster: `C04`
- Owner team: `harness-opencode`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: OpenCode adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/opencode.md, tests/fixtures/harnesses/opencode/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-057: OpenCode: Define skill projection behavior

- Cluster: `C04`
- Owner team: `harness-opencode`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: OpenCode adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/opencode.md, tests/fixtures/harnesses/opencode/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-058: OpenCode: Define MCP projection behavior and constraints

- Cluster: `C04`
- Owner team: `harness-opencode`
- Blocking dependencies: C01-001, C02-001, C03-005
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: OpenCode adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/opencode.md, tests/fixtures/harnesses/opencode/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-059: OpenCode: Define instruction/rules/doc projection behavior

- Cluster: `C04`
- Owner team: `harness-opencode`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: OpenCode adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/opencode.md, tests/fixtures/harnesses/opencode/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-060: OpenCode: Create golden config fixtures

- Cluster: `C04`
- Owner team: `harness-opencode`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: OpenCode adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/opencode.md, tests/fixtures/harnesses/opencode/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-061: OpenCode: Create harness-specific setup docs

- Cluster: `C04`
- Owner team: `harness-opencode`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: OpenCode adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/opencode.md, tests/fixtures/harnesses/opencode/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-062: OpenCode: Create drift detection and repair behavior

- Cluster: `C04`
- Owner team: `harness-opencode`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: OpenCode adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/opencode.md, tests/fixtures/harnesses/opencode/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-063: OpenCode: Create rollback validation fixture

- Cluster: `C04`
- Owner team: `harness-opencode`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: OpenCode adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/opencode.md, tests/fixtures/harnesses/opencode/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-064: Gemini CLI: Validate repo artifacts and support tier

- Cluster: `C04`
- Owner team: `harness-gemini`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Gemini CLI adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/gemini-cli.md, tests/fixtures/harnesses/gemini-cli/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-065: Gemini CLI: Map official extension/plugin/config surfaces

- Cluster: `C04`
- Owner team: `harness-gemini`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Gemini CLI adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/gemini-cli.md, tests/fixtures/harnesses/gemini-cli/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-066: Gemini CLI: Define skill projection behavior

- Cluster: `C04`
- Owner team: `harness-gemini`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Gemini CLI adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/gemini-cli.md, tests/fixtures/harnesses/gemini-cli/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-067: Gemini CLI: Define MCP projection behavior and constraints

- Cluster: `C04`
- Owner team: `harness-gemini`
- Blocking dependencies: C01-001, C02-001, C03-005
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Gemini CLI adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/gemini-cli.md, tests/fixtures/harnesses/gemini-cli/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-068: Gemini CLI: Define instruction/rules/doc projection behavior

- Cluster: `C04`
- Owner team: `harness-gemini`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Gemini CLI adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/gemini-cli.md, tests/fixtures/harnesses/gemini-cli/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-069: Gemini CLI: Create golden config fixtures

- Cluster: `C04`
- Owner team: `harness-gemini`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Gemini CLI adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/gemini-cli.md, tests/fixtures/harnesses/gemini-cli/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-070: Gemini CLI: Create harness-specific setup docs

- Cluster: `C04`
- Owner team: `harness-gemini`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Gemini CLI adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/gemini-cli.md, tests/fixtures/harnesses/gemini-cli/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-071: Gemini CLI: Create drift detection and repair behavior

- Cluster: `C04`
- Owner team: `harness-gemini`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Gemini CLI adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/gemini-cli.md, tests/fixtures/harnesses/gemini-cli/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-072: Gemini CLI: Create rollback validation fixture

- Cluster: `C04`
- Owner team: `harness-gemini`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Gemini CLI adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/gemini-cli.md, tests/fixtures/harnesses/gemini-cli/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-073: Cursor Editor: Validate repo artifacts and support tier

- Cluster: `C04`
- Owner team: `harness-cursor`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Cursor editor/agent adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/cursor-editor.md, tests/fixtures/harnesses/cursor-editor/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-074: Cursor Editor: Map official extension/plugin/config surfaces

- Cluster: `C04`
- Owner team: `harness-cursor`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Cursor editor/agent adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/cursor-editor.md, tests/fixtures/harnesses/cursor-editor/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-075: Cursor Editor: Define skill projection behavior

- Cluster: `C04`
- Owner team: `harness-cursor`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Cursor editor/agent adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/cursor-editor.md, tests/fixtures/harnesses/cursor-editor/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-076: Cursor Editor: Define MCP projection behavior and constraints

- Cluster: `C04`
- Owner team: `harness-cursor`
- Blocking dependencies: C01-001, C02-001, C03-005
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Cursor editor/agent adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/cursor-editor.md, tests/fixtures/harnesses/cursor-editor/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-077: Cursor Editor: Define instruction/rules/doc projection behavior

- Cluster: `C04`
- Owner team: `harness-cursor`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Cursor editor/agent adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/cursor-editor.md, tests/fixtures/harnesses/cursor-editor/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-078: Cursor Editor: Create golden config fixtures

- Cluster: `C04`
- Owner team: `harness-cursor`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Cursor editor/agent adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/cursor-editor.md, tests/fixtures/harnesses/cursor-editor/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-079: Cursor Editor: Create harness-specific setup docs

- Cluster: `C04`
- Owner team: `harness-cursor`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Cursor editor/agent adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/cursor-editor.md, tests/fixtures/harnesses/cursor-editor/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-080: Cursor Editor: Create drift detection and repair behavior

- Cluster: `C04`
- Owner team: `harness-cursor`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Cursor editor/agent adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/cursor-editor.md, tests/fixtures/harnesses/cursor-editor/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-081: Cursor Editor: Create rollback validation fixture

- Cluster: `C04`
- Owner team: `harness-cursor`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Cursor editor/agent adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/cursor-editor.md, tests/fixtures/harnesses/cursor-editor/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-082: Cursor Agent CLI/Web: Validate repo artifacts and support tier

- Cluster: `C04`
- Owner team: `harness-cursor`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Cursor editor/agent adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/cursor-agent.md, tests/fixtures/harnesses/cursor-agent/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-083: Cursor Agent CLI/Web: Map official extension/plugin/config surfaces

- Cluster: `C04`
- Owner team: `harness-cursor`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Cursor editor/agent adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/cursor-agent.md, tests/fixtures/harnesses/cursor-agent/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-084: Cursor Agent CLI/Web: Define skill projection behavior

- Cluster: `C04`
- Owner team: `harness-cursor`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Cursor editor/agent adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/cursor-agent.md, tests/fixtures/harnesses/cursor-agent/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-085: Cursor Agent CLI/Web: Define MCP projection behavior and constraints

- Cluster: `C04`
- Owner team: `harness-cursor`
- Blocking dependencies: C01-001, C02-001, C03-005
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Cursor editor/agent adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/cursor-agent.md, tests/fixtures/harnesses/cursor-agent/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-086: Cursor Agent CLI/Web: Define instruction/rules/doc projection behavior

- Cluster: `C04`
- Owner team: `harness-cursor`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Cursor editor/agent adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/cursor-agent.md, tests/fixtures/harnesses/cursor-agent/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-087: Cursor Agent CLI/Web: Create golden config fixtures

- Cluster: `C04`
- Owner team: `harness-cursor`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Cursor editor/agent adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/cursor-agent.md, tests/fixtures/harnesses/cursor-agent/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-088: Cursor Agent CLI/Web: Create harness-specific setup docs

- Cluster: `C04`
- Owner team: `harness-cursor`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Cursor editor/agent adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/cursor-agent.md, tests/fixtures/harnesses/cursor-agent/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-089: Cursor Agent CLI/Web: Create drift detection and repair behavior

- Cluster: `C04`
- Owner team: `harness-cursor`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Cursor editor/agent adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/cursor-agent.md, tests/fixtures/harnesses/cursor-agent/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-090: Cursor Agent CLI/Web: Create rollback validation fixture

- Cluster: `C04`
- Owner team: `harness-cursor`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Cursor editor/agent adapters and docs.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/cursor-agent.md, tests/fixtures/harnesses/cursor-agent/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-091: Antigravity: Validate repo artifacts and support tier

- Cluster: `C04`
- Owner team: `harness-experimental`
- Blocking dependencies: C01-001, C02-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Antigravity, Perplexity, Cherry Studio validation.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/antigravity.md, tests/fixtures/harnesses/antigravity/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, security review if tools/config/secrets touched

### C04-092: Antigravity: Map official extension/plugin/config surfaces

- Cluster: `C04`
- Owner team: `harness-experimental`
- Blocking dependencies: C01-001, C02-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Antigravity, Perplexity, Cherry Studio validation.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/antigravity.md, tests/fixtures/harnesses/antigravity/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, security review if tools/config/secrets touched

### C04-093: Antigravity: Define skill projection behavior

- Cluster: `C04`
- Owner team: `harness-experimental`
- Blocking dependencies: C01-001, C02-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Antigravity, Perplexity, Cherry Studio validation.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/antigravity.md, tests/fixtures/harnesses/antigravity/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, security review if tools/config/secrets touched

### C04-094: Antigravity: Define MCP projection behavior and constraints

- Cluster: `C04`
- Owner team: `harness-experimental`
- Blocking dependencies: C01-001, C02-001, C03-005
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Antigravity, Perplexity, Cherry Studio validation.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/antigravity.md, tests/fixtures/harnesses/antigravity/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, security review if tools/config/secrets touched

### C04-095: Antigravity: Define instruction/rules/doc projection behavior

- Cluster: `C04`
- Owner team: `harness-experimental`
- Blocking dependencies: C01-001, C02-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Antigravity, Perplexity, Cherry Studio validation.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/antigravity.md, tests/fixtures/harnesses/antigravity/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, security review if tools/config/secrets touched

### C04-096: Antigravity: Create golden config fixtures

- Cluster: `C04`
- Owner team: `harness-experimental`
- Blocking dependencies: C01-001, C02-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Antigravity, Perplexity, Cherry Studio validation.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/antigravity.md, tests/fixtures/harnesses/antigravity/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, security review if tools/config/secrets touched

### C04-097: Antigravity: Create harness-specific setup docs

- Cluster: `C04`
- Owner team: `harness-experimental`
- Blocking dependencies: C01-001, C02-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Antigravity, Perplexity, Cherry Studio validation.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/antigravity.md, tests/fixtures/harnesses/antigravity/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, security review if tools/config/secrets touched

### C04-098: Antigravity: Create drift detection and repair behavior

- Cluster: `C04`
- Owner team: `harness-experimental`
- Blocking dependencies: C01-001, C02-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Antigravity, Perplexity, Cherry Studio validation.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/antigravity.md, tests/fixtures/harnesses/antigravity/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, security review if tools/config/secrets touched

### C04-099: Antigravity: Create rollback validation fixture

- Cluster: `C04`
- Owner team: `harness-experimental`
- Blocking dependencies: C01-001, C02-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Antigravity, Perplexity, Cherry Studio validation.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/antigravity.md, tests/fixtures/harnesses/antigravity/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, security review if tools/config/secrets touched

### C04-100: Perplexity Desktop: Validate repo artifacts and support tier

- Cluster: `C04`
- Owner team: `harness-experimental`
- Blocking dependencies: C01-001, C02-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Antigravity, Perplexity, Cherry Studio validation.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/perplexity-desktop.md, tests/fixtures/harnesses/perplexity-desktop/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, security review if tools/config/secrets touched

### C04-101: Perplexity Desktop: Map official extension/plugin/config surfaces

- Cluster: `C04`
- Owner team: `harness-experimental`
- Blocking dependencies: C01-001, C02-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Antigravity, Perplexity, Cherry Studio validation.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/perplexity-desktop.md, tests/fixtures/harnesses/perplexity-desktop/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, security review if tools/config/secrets touched

### C04-102: Perplexity Desktop: Define skill projection behavior

- Cluster: `C04`
- Owner team: `harness-experimental`
- Blocking dependencies: C01-001, C02-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Antigravity, Perplexity, Cherry Studio validation.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/perplexity-desktop.md, tests/fixtures/harnesses/perplexity-desktop/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, security review if tools/config/secrets touched

### C04-103: Perplexity Desktop: Define MCP projection behavior and constraints

- Cluster: `C04`
- Owner team: `harness-experimental`
- Blocking dependencies: C01-001, C02-001, C03-005
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Antigravity, Perplexity, Cherry Studio validation.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/perplexity-desktop.md, tests/fixtures/harnesses/perplexity-desktop/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, security review if tools/config/secrets touched

### C04-104: Perplexity Desktop: Define instruction/rules/doc projection behavior

- Cluster: `C04`
- Owner team: `harness-experimental`
- Blocking dependencies: C01-001, C02-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Antigravity, Perplexity, Cherry Studio validation.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/perplexity-desktop.md, tests/fixtures/harnesses/perplexity-desktop/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, security review if tools/config/secrets touched

### C04-105: Perplexity Desktop: Create golden config fixtures

- Cluster: `C04`
- Owner team: `harness-experimental`
- Blocking dependencies: C01-001, C02-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Antigravity, Perplexity, Cherry Studio validation.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/perplexity-desktop.md, tests/fixtures/harnesses/perplexity-desktop/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, security review if tools/config/secrets touched

### C04-106: Perplexity Desktop: Create harness-specific setup docs

- Cluster: `C04`
- Owner team: `harness-experimental`
- Blocking dependencies: C01-001, C02-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Antigravity, Perplexity, Cherry Studio validation.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/perplexity-desktop.md, tests/fixtures/harnesses/perplexity-desktop/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, security review if tools/config/secrets touched

### C04-107: Perplexity Desktop: Create drift detection and repair behavior

- Cluster: `C04`
- Owner team: `harness-experimental`
- Blocking dependencies: C01-001, C02-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Antigravity, Perplexity, Cherry Studio validation.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/perplexity-desktop.md, tests/fixtures/harnesses/perplexity-desktop/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, security review if tools/config/secrets touched

### C04-108: Perplexity Desktop: Create rollback validation fixture

- Cluster: `C04`
- Owner team: `harness-experimental`
- Blocking dependencies: C01-001, C02-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Antigravity, Perplexity, Cherry Studio validation.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/perplexity-desktop.md, tests/fixtures/harnesses/perplexity-desktop/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, security review if tools/config/secrets touched

### C04-109: Cherry Studio: Validate repo artifacts and support tier

- Cluster: `C04`
- Owner team: `harness-experimental`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Antigravity, Perplexity, Cherry Studio validation.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/cherry-studio.md, tests/fixtures/harnesses/cherry-studio/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-110: Cherry Studio: Map official extension/plugin/config surfaces

- Cluster: `C04`
- Owner team: `harness-experimental`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Antigravity, Perplexity, Cherry Studio validation.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/cherry-studio.md, tests/fixtures/harnesses/cherry-studio/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-111: Cherry Studio: Define skill projection behavior

- Cluster: `C04`
- Owner team: `harness-experimental`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Antigravity, Perplexity, Cherry Studio validation.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/cherry-studio.md, tests/fixtures/harnesses/cherry-studio/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-112: Cherry Studio: Define MCP projection behavior and constraints

- Cluster: `C04`
- Owner team: `harness-experimental`
- Blocking dependencies: C01-001, C02-001, C03-005
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Antigravity, Perplexity, Cherry Studio validation.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/cherry-studio.md, tests/fixtures/harnesses/cherry-studio/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-113: Cherry Studio: Define instruction/rules/doc projection behavior

- Cluster: `C04`
- Owner team: `harness-experimental`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Antigravity, Perplexity, Cherry Studio validation.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/cherry-studio.md, tests/fixtures/harnesses/cherry-studio/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-114: Cherry Studio: Create golden config fixtures

- Cluster: `C04`
- Owner team: `harness-experimental`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Antigravity, Perplexity, Cherry Studio validation.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/cherry-studio.md, tests/fixtures/harnesses/cherry-studio/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-115: Cherry Studio: Create harness-specific setup docs

- Cluster: `C04`
- Owner team: `harness-experimental`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Antigravity, Perplexity, Cherry Studio validation.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/cherry-studio.md, tests/fixtures/harnesses/cherry-studio/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-116: Cherry Studio: Create drift detection and repair behavior

- Cluster: `C04`
- Owner team: `harness-experimental`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Antigravity, Perplexity, Cherry Studio validation.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/cherry-studio.md, tests/fixtures/harnesses/cherry-studio/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C04-117: Cherry Studio: Create rollback validation fixture

- Cluster: `C04`
- Owner team: `harness-experimental`
- Blocking dependencies: C01-001, C02-001
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `4`
- Required expertise: Antigravity, Perplexity, Cherry Studio validation.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/20-harness-registry/cherry-studio.md, tests/fixtures/harnesses/cherry-studio/
- CI gates: harness-fixtures, docs-truth
- Review requirements: owner team review, standard review

### C05-001: Design wagents doctor output model

- Cluster: `C05`
- Owner team: `ux-cli`
- Blocking dependencies: C01-009
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CLI and dashboard user flows.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C05-001.md
- CI gates: cli-snapshots, docs-truth
- Review requirements: owner team review, standard review

### C05-002: Implement doctor prerequisites and harness detection spec

- Cluster: `C05`
- Owner team: `ux-cli`
- Blocking dependencies: C01-009
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CLI and dashboard user flows.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C05-002.md
- CI gates: cli-snapshots, docs-truth
- Review requirements: owner team review, standard review

### C05-003: Design catalog browse/explain UX

- Cluster: `C05`
- Owner team: `ux-cli`
- Blocking dependencies: C01-009
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CLI and dashboard user flows.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C05-003.md
- CI gates: cli-snapshots, docs-truth
- Review requirements: owner team review, standard review

### C05-004: Design skill add preview/apply UX

- Cluster: `C05`
- Owner team: `ux-cli`
- Blocking dependencies: C01-009
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CLI and dashboard user flows.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C05-004.md
- CI gates: cli-snapshots, docs-truth
- Review requirements: owner team review, standard review

### C05-005: Design MCP inspect/enable UX

- Cluster: `C05`
- Owner team: `ux-cli`
- Blocking dependencies: C01-009
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CLI and dashboard user flows.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C05-005.md
- CI gates: cli-snapshots, docs-truth
- Review requirements: owner team review, standard review

### C05-006: Design sync preview UX

- Cluster: `C05`
- Owner team: `ux-cli`
- Blocking dependencies: C01-009
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CLI and dashboard user flows.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C05-006.md
- CI gates: cli-snapshots, docs-truth
- Review requirements: owner team review, standard review

### C05-007: Design sync apply transaction UX

- Cluster: `C05`
- Owner team: `ux-cli`
- Blocking dependencies: C01-009
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CLI and dashboard user flows.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C05-007.md
- CI gates: cli-snapshots, docs-truth
- Review requirements: owner team review, standard review

### C05-008: Design rollback UX

- Cluster: `C05`
- Owner team: `ux-cli`
- Blocking dependencies: C01-009
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CLI and dashboard user flows.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C05-008.md
- CI gates: cli-snapshots, docs-truth
- Review requirements: owner team review, standard review

### C05-009: Design OpenSpec command group UX

- Cluster: `C05`
- Owner team: `ux-cli`
- Blocking dependencies: C01-009
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CLI and dashboard user flows.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C05-009.md
- CI gates: cli-snapshots, docs-truth
- Review requirements: owner team review, standard review

### C05-010: Define machine-readable JSON output formats for automation

- Cluster: `C05`
- Owner team: `ux-cli`
- Blocking dependencies: C01-009
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CLI and dashboard user flows.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C05-010.md
- CI gates: cli-snapshots, docs-truth
- Review requirements: owner team review, standard review

### C05-011: Define CLI error taxonomy and remediation hints

- Cluster: `C05`
- Owner team: `ux-cli`
- Blocking dependencies: C01-009
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CLI and dashboard user flows.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C05-011.md
- CI gates: cli-snapshots, docs-truth
- Review requirements: owner team review, standard review

### C05-012: Define dashboard information architecture

- Cluster: `C05`
- Owner team: `ux-cli`
- Blocking dependencies: C01-009
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CLI and dashboard user flows.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C05-012.md
- CI gates: cli-snapshots, docs-truth
- Review requirements: owner team review, standard review

### C05-013: Define skill catalog dashboard view

- Cluster: `C05`
- Owner team: `ux-cli`
- Blocking dependencies: C01-009
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CLI and dashboard user flows.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C05-013.md
- CI gates: cli-snapshots, docs-truth
- Review requirements: owner team review, standard review

### C05-014: Define MCP audit dashboard view

- Cluster: `C05`
- Owner team: `ux-cli`
- Blocking dependencies: C01-009
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CLI and dashboard user flows.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C05-014.md
- CI gates: cli-snapshots, docs-truth
- Review requirements: owner team review, standard review

### C05-015: Define config drift dashboard view

- Cluster: `C05`
- Owner team: `ux-cli`
- Blocking dependencies: C01-009
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CLI and dashboard user flows.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C05-015.md
- CI gates: cli-snapshots, docs-truth
- Review requirements: owner team review, standard review

### C05-016: Define transaction history dashboard view

- Cluster: `C05`
- Owner team: `ux-cli`
- Blocking dependencies: C01-009
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CLI and dashboard user flows.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C05-016.md
- CI gates: cli-snapshots, docs-truth
- Review requirements: owner team review, standard review

### C05-017: Define support matrix dashboard view

- Cluster: `C05`
- Owner team: `ux-cli`
- Blocking dependencies: C01-009
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CLI and dashboard user flows.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C05-017.md
- CI gates: cli-snapshots, docs-truth
- Review requirements: owner team review, standard review

### C05-018: Define guided onboarding wizard

- Cluster: `C05`
- Owner team: `ux-cli`
- Blocking dependencies: C01-009
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CLI and dashboard user flows.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C05-018.md
- CI gates: cli-snapshots, docs-truth
- Review requirements: owner team review, standard review

### C05-019: Create CLI golden snapshot tests

- Cluster: `C05`
- Owner team: `ux-cli`
- Blocking dependencies: C01-009
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CLI and dashboard user flows.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C05-019.md
- CI gates: cli-snapshots, docs-truth
- Review requirements: owner team review, standard review

### C05-020: Create dashboard wireframe docs

- Cluster: `C05`
- Owner team: `ux-cli`
- Blocking dependencies: C01-009
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CLI and dashboard user flows.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C05-020.md
- CI gates: cli-snapshots, docs-truth
- Review requirements: owner team review, standard review

### C06-001: Define transaction engine operation model

- Cluster: `C06`
- Owner team: `security`
- Blocking dependencies: C01-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Supply-chain, sandboxing, MCP/skill security.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C06-001.md
- CI gates: security-review, policy-tests
- Review requirements: owner team review, security review if tools/config/secrets touched

### C06-002: Define backup snapshot format

- Cluster: `C06`
- Owner team: `security`
- Blocking dependencies: C01-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Supply-chain, sandboxing, MCP/skill security.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C06-002.md
- CI gates: security-review, policy-tests
- Review requirements: owner team review, security review if tools/config/secrets touched

### C06-003: Define atomic file-write strategy

- Cluster: `C06`
- Owner team: `security`
- Blocking dependencies: C01-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Supply-chain, sandboxing, MCP/skill security.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C06-003.md
- CI gates: security-review, policy-tests
- Review requirements: owner team review, security review if tools/config/secrets touched

### C06-004: Define rollback verification strategy

- Cluster: `C06`
- Owner team: `security`
- Blocking dependencies: C01-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Supply-chain, sandboxing, MCP/skill security.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C06-004.md
- CI gates: security-review, policy-tests
- Review requirements: owner team review, security review if tools/config/secrets touched

### C06-005: Define secret redaction model

- Cluster: `C06`
- Owner team: `security`
- Blocking dependencies: C01-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Supply-chain, sandboxing, MCP/skill security.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C06-005.md
- CI gates: security-review, policy-tests
- Review requirements: owner team review, security review if tools/config/secrets touched

### C06-006: Define environment overlay policy

- Cluster: `C06`
- Owner team: `security`
- Blocking dependencies: C01-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Supply-chain, sandboxing, MCP/skill security.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C06-006.md
- CI gates: security-review, policy-tests
- Review requirements: owner team review, security review if tools/config/secrets touched

### C06-007: Define policy-as-code validation rules

- Cluster: `C06`
- Owner team: `security`
- Blocking dependencies: C01-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Supply-chain, sandboxing, MCP/skill security.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C06-007.md
- CI gates: security-review, policy-tests
- Review requirements: owner team review, security review if tools/config/secrets touched

### C06-008: Define external skill source trust policy

- Cluster: `C06`
- Owner team: `security`
- Blocking dependencies: C01-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Supply-chain, sandboxing, MCP/skill security.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C06-008.md
- CI gates: security-review, policy-tests
- Review requirements: owner team review, security review if tools/config/secrets touched

### C06-009: Define MCP source trust policy

- Cluster: `C06`
- Owner team: `security`
- Blocking dependencies: C01-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Supply-chain, sandboxing, MCP/skill security.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C06-009.md
- CI gates: security-review, policy-tests
- Review requirements: owner team review, security review if tools/config/secrets touched

### C06-010: Define signing/checksum/provenance strategy

- Cluster: `C06`
- Owner team: `security`
- Blocking dependencies: C01-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Supply-chain, sandboxing, MCP/skill security.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C06-010.md
- CI gates: security-review, policy-tests
- Review requirements: owner team review, security review if tools/config/secrets touched

### C06-011: Evaluate Sigstore/cosign for skill provenance

- Cluster: `C06`
- Owner team: `security`
- Blocking dependencies: C01-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Supply-chain, sandboxing, MCP/skill security.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C06-011.md
- CI gates: security-review, policy-tests
- Review requirements: owner team review, security review if tools/config/secrets touched

### C06-012: Evaluate SBOM tooling for skill dependencies

- Cluster: `C06`
- Owner team: `security`
- Blocking dependencies: C01-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Supply-chain, sandboxing, MCP/skill security.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C06-012.md
- CI gates: security-review, policy-tests
- Review requirements: owner team review, security review if tools/config/secrets touched

### C06-013: Evaluate OPA/Conftest for registry policy

- Cluster: `C06`
- Owner team: `security`
- Blocking dependencies: C01-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Supply-chain, sandboxing, MCP/skill security.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C06-013.md
- CI gates: security-review, policy-tests
- Review requirements: owner team review, security review if tools/config/secrets touched

### C06-014: Define sandbox profiles for script-backed skills

- Cluster: `C06`
- Owner team: `security`
- Blocking dependencies: C01-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Supply-chain, sandboxing, MCP/skill security.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C06-014.md
- CI gates: security-review, policy-tests
- Review requirements: owner team review, security review if tools/config/secrets touched

### C06-015: Define sandbox profiles for local MCP servers

- Cluster: `C06`
- Owner team: `security`
- Blocking dependencies: C01-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Supply-chain, sandboxing, MCP/skill security.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C06-015.md
- CI gates: security-review, policy-tests
- Review requirements: owner team review, security review if tools/config/secrets touched

### C06-016: Define network access declaration schema

- Cluster: `C06`
- Owner team: `security`
- Blocking dependencies: C01-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Supply-chain, sandboxing, MCP/skill security.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C06-016.md
- CI gates: security-review, policy-tests
- Review requirements: owner team review, security review if tools/config/secrets touched

### C06-017: Define prompt-injection and tool-poisoning mitigations

- Cluster: `C06`
- Owner team: `security`
- Blocking dependencies: C01-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Supply-chain, sandboxing, MCP/skill security.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C06-017.md
- CI gates: security-review, policy-tests
- Review requirements: owner team review, security review if tools/config/secrets touched

### C06-018: Define security review checklist

- Cluster: `C06`
- Owner team: `security`
- Blocking dependencies: C01-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Supply-chain, sandboxing, MCP/skill security.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C06-018.md
- CI gates: security-review, policy-tests
- Review requirements: owner team review, security review if tools/config/secrets touched

### C06-019: Create threat model docs

- Cluster: `C06`
- Owner team: `security`
- Blocking dependencies: C01-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Supply-chain, sandboxing, MCP/skill security.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C06-019.md
- CI gates: security-review, policy-tests
- Review requirements: owner team review, security review if tools/config/secrets touched

### C06-020: Create security exception workflow

- Cluster: `C06`
- Owner team: `security`
- Blocking dependencies: C01-001
- Risk: `high`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Supply-chain, sandboxing, MCP/skill security.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C06-020.md
- CI gates: security-review, policy-tests
- Review requirements: owner team review, security review if tools/config/secrets touched

### C07-001: Create registry schema validation CI gate

- Cluster: `C07`
- Owner team: `ci-evals`
- Blocking dependencies: C01-013
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CI gates, conformance, evals, fixtures.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C07-001.md
- CI gates: ci
- Review requirements: owner team review, standard review

### C07-002: Create skill validation CI gate

- Cluster: `C07`
- Owner team: `ci-evals`
- Blocking dependencies: C01-013
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CI gates, conformance, evals, fixtures.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C07-002.md
- CI gates: ci
- Review requirements: owner team review, standard review

### C07-003: Create skill CLI conformance CI gate

- Cluster: `C07`
- Owner team: `ci-evals`
- Blocking dependencies: C01-013
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CI gates, conformance, evals, fixtures.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C07-003.md
- CI gates: ci
- Review requirements: owner team review, standard review

### C07-004: Create MCP registry validation CI gate

- Cluster: `C07`
- Owner team: `ci-evals`
- Blocking dependencies: C01-013
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CI gates, conformance, evals, fixtures.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C07-004.md
- CI gates: ci
- Review requirements: owner team review, standard review

### C07-005: Create MCP smoke test CI gate

- Cluster: `C07`
- Owner team: `ci-evals`
- Blocking dependencies: C01-013
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CI gates, conformance, evals, fixtures.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C07-005.md
- CI gates: ci
- Review requirements: owner team review, standard review

### C07-006: Create MCP security scan CI gate

- Cluster: `C07`
- Owner team: `ci-evals`
- Blocking dependencies: C01-013
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CI gates, conformance, evals, fixtures.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C07-006.md
- CI gates: ci
- Review requirements: owner team review, standard review

### C07-007: Create adapter golden-fixture CI gate

- Cluster: `C07`
- Owner team: `ci-evals`
- Blocking dependencies: C01-013
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CI gates, conformance, evals, fixtures.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C07-007.md
- CI gates: ci
- Review requirements: owner team review, standard review

### C07-008: Create docs truth CI gate

- Cluster: `C07`
- Owner team: `ci-evals`
- Blocking dependencies: C01-013
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CI gates, conformance, evals, fixtures.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C07-008.md
- CI gates: ci
- Review requirements: owner team review, standard review

### C07-009: Create AI instruction truth CI gate

- Cluster: `C07`
- Owner team: `ci-evals`
- Blocking dependencies: C01-013
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CI gates, conformance, evals, fixtures.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C07-009.md
- CI gates: ci
- Review requirements: owner team review, standard review

### C07-010: Create OpenSpec validation CI gate

- Cluster: `C07`
- Owner team: `ci-evals`
- Blocking dependencies: C01-013
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CI gates, conformance, evals, fixtures.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C07-010.md
- CI gates: ci
- Review requirements: owner team review, standard review

### C07-011: Create transaction rollback CI gate

- Cluster: `C07`
- Owner team: `ci-evals`
- Blocking dependencies: C01-013
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CI gates, conformance, evals, fixtures.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C07-011.md
- CI gates: ci
- Review requirements: owner team review, standard review

### C07-012: Create repo-sync inventory CI gate

- Cluster: `C07`
- Owner team: `ci-evals`
- Blocking dependencies: C01-013
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CI gates, conformance, evals, fixtures.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C07-012.md
- CI gates: ci
- Review requirements: owner team review, standard review

### C07-013: Create eval scenario schema

- Cluster: `C07`
- Owner team: `ci-evals`
- Blocking dependencies: C01-013
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CI gates, conformance, evals, fixtures.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C07-013.md
- CI gates: ci
- Review requirements: owner team review, standard review

### C07-014: Create promptfoo/deepeval feasibility notes

- Cluster: `C07`
- Owner team: `ci-evals`
- Blocking dependencies: C01-013
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CI gates, conformance, evals, fixtures.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C07-014.md
- CI gates: ci
- Review requirements: owner team review, standard review

### C07-015: Create Microsoft skills scenario-harness adaptation note

- Cluster: `C07`
- Owner team: `ci-evals`
- Blocking dependencies: C01-013
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CI gates, conformance, evals, fixtures.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C07-015.md
- CI gates: ci
- Review requirements: owner team review, standard review

### C07-016: Create deterministic replay fixture design

- Cluster: `C07`
- Owner team: `ci-evals`
- Blocking dependencies: C01-013
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: CI gates, conformance, evals, fixtures.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C07-016.md
- CI gates: ci
- Review requirements: owner team review, standard review

### C07-017: Create local audit log schema

- Cluster: `C07`
- Owner team: `observability`
- Blocking dependencies: C01-013
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Telemetry, logs, run graph, cost accounting.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C07-017.md
- CI gates: ci
- Review requirements: owner team review, standard review

### C07-018: Create OpenTelemetry instrumentation plan

- Cluster: `C07`
- Owner team: `observability`
- Blocking dependencies: C01-013
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Telemetry, logs, run graph, cost accounting.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C07-018.md
- CI gates: ci
- Review requirements: owner team review, standard review

### C07-019: Create run graph visualization spec

- Cluster: `C07`
- Owner team: `observability`
- Blocking dependencies: C01-013
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Telemetry, logs, run graph, cost accounting.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C07-019.md
- CI gates: ci
- Review requirements: owner team review, standard review

### C07-020: Create cost telemetry design

- Cluster: `C07`
- Owner team: `observability`
- Blocking dependencies: C01-013
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Telemetry, logs, run graph, cost accounting.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C07-020.md
- CI gates: ci
- Review requirements: owner team review, standard review

### C07-021: Create CI report dashboard spec

- Cluster: `C07`
- Owner team: `observability`
- Blocking dependencies: C01-013
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Telemetry, logs, run graph, cost accounting.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C07-021.md
- CI gates: ci
- Review requirements: owner team review, standard review

### C07-022: Create failure remediation docs

- Cluster: `C07`
- Owner team: `observability`
- Blocking dependencies: C01-013
- Risk: `medium`
- Complexity: `M`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: Telemetry, logs, run graph, cost accounting.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C07-022.md
- CI gates: ci
- Review requirements: owner team review, standard review

### C08-001: Canonicalize README quickstart and supported agents section

- Cluster: `C08`
- Owner team: `docs-ai-instructions`
- Blocking dependencies: C01-005
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `5`
- Required expertise: README, docs, AI instructions, support matrices.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C08-001.md
- CI gates: docs-truth, ai-instructions-truth
- Review requirements: owner team review, standard review

### C08-002: Update README skill catalog section from skill inventory

- Cluster: `C08`
- Owner team: `docs-ai-instructions`
- Blocking dependencies: C01-005
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `5`
- Required expertise: README, docs, AI instructions, support matrices.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C08-002.md
- CI gates: docs-truth, ai-instructions-truth
- Review requirements: owner team review, standard review

### C08-003: Update README MCP policy section from MCP inventory

- Cluster: `C08`
- Owner team: `docs-ai-instructions`
- Blocking dependencies: C01-005
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `5`
- Required expertise: README, docs, AI instructions, support matrices.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C08-003.md
- CI gates: docs-truth, ai-instructions-truth
- Review requirements: owner team review, standard review

### C08-004: Update README OpenSpec governance section

- Cluster: `C08`
- Owner team: `docs-ai-instructions`
- Blocking dependencies: C01-005
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `5`
- Required expertise: README, docs, AI instructions, support matrices.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C08-004.md
- CI gates: docs-truth, ai-instructions-truth
- Review requirements: owner team review, standard review

### C08-005: Update AGENTS.md with skill-first decision tree

- Cluster: `C08`
- Owner team: `docs-ai-instructions`
- Blocking dependencies: C01-005
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `5`
- Required expertise: README, docs, AI instructions, support matrices.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C08-005.md
- CI gates: docs-truth, ai-instructions-truth
- Review requirements: owner team review, standard review

### C08-006: Update AGENTS.md with MCP safety policy

- Cluster: `C08`
- Owner team: `docs-ai-instructions`
- Blocking dependencies: C01-005
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: README, docs, AI instructions, support matrices.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C08-006.md
- CI gates: docs-truth, ai-instructions-truth
- Review requirements: owner team review, standard review

### C08-007: Update CLAUDE.md with Claude Code skills/plugins/hooks/subagents guidance

- Cluster: `C08`
- Owner team: `docs-ai-instructions`
- Blocking dependencies: C01-005
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: README, docs, AI instructions, support matrices.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C08-007.md
- CI gates: docs-truth, ai-instructions-truth
- Review requirements: owner team review, standard review

### C08-008: Update GEMINI.md with Gemini extension/MCP guidance

- Cluster: `C08`
- Owner team: `docs-ai-instructions`
- Blocking dependencies: C01-005
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: README, docs, AI instructions, support matrices.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C08-008.md
- CI gates: docs-truth, ai-instructions-truth
- Review requirements: owner team review, standard review

### C08-009: Create .github/copilot-instructions.md projection

- Cluster: `C08`
- Owner team: `docs-ai-instructions`
- Blocking dependencies: C01-005
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: README, docs, AI instructions, support matrices.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C08-009.md
- CI gates: docs-truth, ai-instructions-truth
- Review requirements: owner team review, standard review

### C08-010: Create .github/instructions scoped instruction docs

- Cluster: `C08`
- Owner team: `docs-ai-instructions`
- Blocking dependencies: C01-005
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: README, docs, AI instructions, support matrices.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C08-010.md
- CI gates: docs-truth, ai-instructions-truth
- Review requirements: owner team review, standard review

### C08-011: Update Cursor rules docs and deprecate .cursorrules assumptions

- Cluster: `C08`
- Owner team: `docs-ai-instructions`
- Blocking dependencies: C01-005
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: README, docs, AI instructions, support matrices.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C08-011.md
- CI gates: docs-truth, ai-instructions-truth
- Review requirements: owner team review, standard review

### C08-012: Update OpenCode setup docs

- Cluster: `C08`
- Owner team: `docs-ai-instructions`
- Blocking dependencies: C01-005
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: README, docs, AI instructions, support matrices.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C08-012.md
- CI gates: docs-truth, ai-instructions-truth
- Review requirements: owner team review, standard review

### C08-013: Update Cherry Studio preset/setup docs

- Cluster: `C08`
- Owner team: `docs-ai-instructions`
- Blocking dependencies: C01-005
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: README, docs, AI instructions, support matrices.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C08-013.md
- CI gates: docs-truth, ai-instructions-truth
- Review requirements: owner team review, standard review

### C08-014: Update Perplexity Desktop caveat docs

- Cluster: `C08`
- Owner team: `docs-ai-instructions`
- Blocking dependencies: C01-005
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: README, docs, AI instructions, support matrices.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C08-014.md
- CI gates: docs-truth, ai-instructions-truth
- Review requirements: owner team review, standard review

### C08-015: Update Antigravity experimental caveat docs

- Cluster: `C08`
- Owner team: `docs-ai-instructions`
- Blocking dependencies: C01-005
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: README, docs, AI instructions, support matrices.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C08-015.md
- CI gates: docs-truth, ai-instructions-truth
- Review requirements: owner team review, standard review

### C08-016: Create docs/skills.md from skill registry

- Cluster: `C08`
- Owner team: `docs-ai-instructions`
- Blocking dependencies: C01-005
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: README, docs, AI instructions, support matrices.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C08-016.md
- CI gates: docs-truth, ai-instructions-truth
- Review requirements: owner team review, standard review

### C08-017: Create docs/mcp.md from MCP registry

- Cluster: `C08`
- Owner team: `docs-ai-instructions`
- Blocking dependencies: C01-005
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: README, docs, AI instructions, support matrices.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C08-017.md
- CI gates: docs-truth, ai-instructions-truth
- Review requirements: owner team review, standard review

### C08-018: Create docs/harnesses index

- Cluster: `C08`
- Owner team: `docs-ai-instructions`
- Blocking dependencies: C01-005
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: README, docs, AI instructions, support matrices.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C08-018.md
- CI gates: docs-truth, ai-instructions-truth
- Review requirements: owner team review, standard review

### C08-019: Create docs/security.md

- Cluster: `C08`
- Owner team: `docs-ai-instructions`
- Blocking dependencies: C01-005
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: README, docs, AI instructions, support matrices.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C08-019.md
- CI gates: docs-truth, ai-instructions-truth
- Review requirements: owner team review, standard review

### C08-020: Create docs/config-transactions.md

- Cluster: `C08`
- Owner team: `docs-ai-instructions`
- Blocking dependencies: C01-005
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: README, docs, AI instructions, support matrices.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C08-020.md
- CI gates: docs-truth, ai-instructions-truth
- Review requirements: owner team review, standard review

### C08-021: Create docs/openspec.md

- Cluster: `C08`
- Owner team: `docs-ai-instructions`
- Blocking dependencies: C01-005
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: README, docs, AI instructions, support matrices.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C08-021.md
- CI gates: docs-truth, ai-instructions-truth
- Review requirements: owner team review, standard review

### C08-022: Create docs/external-capabilities.md

- Cluster: `C08`
- Owner team: `docs-ai-instructions`
- Blocking dependencies: C01-005
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: README, docs, AI instructions, support matrices.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C08-022.md
- CI gates: docs-truth, ai-instructions-truth
- Review requirements: owner team review, standard review

### C08-023: Create docs/ui-ux.md

- Cluster: `C08`
- Owner team: `docs-ai-instructions`
- Blocking dependencies: C01-005
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: README, docs, AI instructions, support matrices.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C08-023.md
- CI gates: docs-truth, ai-instructions-truth
- Review requirements: owner team review, standard review

### C08-024: Create docs/evals.md

- Cluster: `C08`
- Owner team: `docs-ai-instructions`
- Blocking dependencies: C01-005
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: README, docs, AI instructions, support matrices.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C08-024.md
- CI gates: docs-truth, ai-instructions-truth
- Review requirements: owner team review, standard review

### C08-025: Create docs/observability.md

- Cluster: `C08`
- Owner team: `docs-ai-instructions`
- Blocking dependencies: C01-005
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: README, docs, AI instructions, support matrices.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C08-025.md
- CI gates: docs-truth, ai-instructions-truth
- Review requirements: owner team review, standard review

### C08-026: Create docs/contributing.md overhaul section

- Cluster: `C08`
- Owner team: `docs-ai-instructions`
- Blocking dependencies: C01-005
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: README, docs, AI instructions, support matrices.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C08-026.md
- CI gates: docs-truth, ai-instructions-truth
- Review requirements: owner team review, standard review

### C08-027: Create version/support matrix doc

- Cluster: `C08`
- Owner team: `docs-ai-instructions`
- Blocking dependencies: C01-005
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: README, docs, AI instructions, support matrices.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C08-027.md
- CI gates: docs-truth, ai-instructions-truth
- Review requirements: owner team review, standard review

### C08-028: Create MCP audit report doc

- Cluster: `C08`
- Owner team: `docs-ai-instructions`
- Blocking dependencies: C01-005
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: README, docs, AI instructions, support matrices.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C08-028.md
- CI gates: docs-truth, ai-instructions-truth
- Review requirements: owner team review, standard review

### C08-029: Create external skill audit report doc

- Cluster: `C08`
- Owner team: `docs-ai-instructions`
- Blocking dependencies: C01-005
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: README, docs, AI instructions, support matrices.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C08-029.md
- CI gates: docs-truth, ai-instructions-truth
- Review requirements: owner team review, standard review

### C08-030: Create docs generation/check command docs

- Cluster: `C08`
- Owner team: `docs-ai-instructions`
- Blocking dependencies: C01-005
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `3`
- Required expertise: README, docs, AI instructions, support matrices.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C08-030.md
- CI gates: docs-truth, ai-instructions-truth
- Review requirements: owner team review, standard review

### C09-001: Create phased rollout plan

- Cluster: `C09`
- Owner team: `release`
- Blocking dependencies: C05-006, C07-008
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `2`
- Required expertise: Migration, rollout, rollback, changelog, archive.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C09-001.md
- CI gates: release-readiness
- Review requirements: owner team review, standard review

### C09-002: Create migration guide for existing users

- Cluster: `C09`
- Owner team: `release`
- Blocking dependencies: C05-006, C07-008
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `2`
- Required expertise: Migration, rollout, rollback, changelog, archive.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C09-002.md
- CI gates: release-readiness
- Review requirements: owner team review, standard review

### C09-003: Create branch/PR integration policy

- Cluster: `C09`
- Owner team: `release`
- Blocking dependencies: C05-006, C07-008
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `2`
- Required expertise: Migration, rollout, rollback, changelog, archive.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C09-003.md
- CI gates: release-readiness
- Review requirements: owner team review, standard review

### C09-004: Create support-tier changelog policy

- Cluster: `C09`
- Owner team: `release`
- Blocking dependencies: C05-006, C07-008
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `2`
- Required expertise: Migration, rollout, rollback, changelog, archive.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C09-004.md
- CI gates: release-readiness
- Review requirements: owner team review, standard review

### C09-005: Create feature flag/preview policy

- Cluster: `C09`
- Owner team: `release`
- Blocking dependencies: C05-006, C07-008
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `2`
- Required expertise: Migration, rollout, rollback, changelog, archive.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C09-005.md
- CI gates: release-readiness
- Review requirements: owner team review, standard review

### C09-006: Create backwards compatibility policy

- Cluster: `C09`
- Owner team: `release`
- Blocking dependencies: C05-006, C07-008
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `2`
- Required expertise: Migration, rollout, rollback, changelog, archive.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C09-006.md
- CI gates: release-readiness
- Review requirements: owner team review, standard review

### C09-007: Create rollback playbook

- Cluster: `C09`
- Owner team: `release`
- Blocking dependencies: C05-006, C07-008
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `2`
- Required expertise: Migration, rollout, rollback, changelog, archive.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C09-007.md
- CI gates: release-readiness
- Review requirements: owner team review, standard review

### C09-008: Create release checklist

- Cluster: `C09`
- Owner team: `release`
- Blocking dependencies: C05-006, C07-008
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `2`
- Required expertise: Migration, rollout, rollback, changelog, archive.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C09-008.md
- CI gates: release-readiness
- Review requirements: owner team review, standard review

### C09-009: Create post-merge validation checklist

- Cluster: `C09`
- Owner team: `release`
- Blocking dependencies: C05-006, C07-008
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `2`
- Required expertise: Migration, rollout, rollback, changelog, archive.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C09-009.md
- CI gates: release-readiness
- Review requirements: owner team review, standard review

### C09-010: Create OpenSpec archive checklist

- Cluster: `C09`
- Owner team: `release`
- Blocking dependencies: C05-006, C07-008
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `2`
- Required expertise: Migration, rollout, rollback, changelog, archive.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C09-010.md
- CI gates: release-readiness
- Review requirements: owner team review, standard review

### C09-011: Create external dependency update cadence

- Cluster: `C09`
- Owner team: `release`
- Blocking dependencies: C05-006, C07-008
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `2`
- Required expertise: Migration, rollout, rollback, changelog, archive.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C09-011.md
- CI gates: release-readiness
- Review requirements: owner team review, standard review

### C09-012: Create long-term maintenance backlog

- Cluster: `C09`
- Owner team: `release`
- Blocking dependencies: C05-006, C07-008
- Risk: `medium`
- Complexity: `S`
- PR scope: `small`
- Merge-risk score: `2`
- Required expertise: Migration, rollout, rollback, changelog, archive.
- Required inputs: latest repo checkout, source ledger
- Produced artifacts: planning/artifacts/C09-012.md
- CI gates: release-readiness
- Review requirements: owner team review, standard review
