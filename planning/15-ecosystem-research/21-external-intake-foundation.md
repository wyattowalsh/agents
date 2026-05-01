# External Intake Foundation

## Source Manifest

Use `agents-overhaul-planning/planning/manifests/external-repo-evaluation-final.json` as the initial discovery ledger. It contains 93 external repository records and must remain discovery input until promotion gates pass.

## Rules

- Do not install external repositories by default.
- Do not vendor code or content from external repositories during foundation work.
- Do not promote any external capability without pinned source, license review, maintainer/activity review, security/provenance review, conformance fixtures, rollback plan, OpenSpec mapping, and docs/instruction sync plan.
- Treat awesome lists, MCP indexes, and community catalogs as discovery sources, not authority.

## Required Intake Findings

- Source URL and immutable revision.
- License compatibility.
- Maintainer and activity posture.
- Dependency and installer risk.
- Secrets, network, filesystem, and execution behavior.
- Skill-vs-MCP fit.
- Required fixtures and validation commands.
- Quarantine decision if applicable.

## Coverage Outputs

- `planning/15-ecosystem-research/22-feature-domain-coverage.md` maps the full external repository set into feature/domain requirements and integration principles.
- `planning/15-ecosystem-research/23-external-repo-coverage-backlog.md` records the per-repo coverage queue and priority waves.

These are research artifacts, not promotion artifacts. They can inform child lanes, but every repo still needs pinned source, license, security, provenance, and fixture review before adoption.

## Quarantine Cohorts

Auth-bridging, proxying, credential-sharing, and offensive-security repositories must be handled by `agents-c15-security-quarantine` before any other lane can reference them as more than research input.
