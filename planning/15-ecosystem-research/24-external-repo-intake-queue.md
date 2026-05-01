# External Repo Intake Queue

## Boundary

This lane converts the external repository evaluation set into review work only. It does not install, vendor, execute, or promote any upstream repository.

Promotion remains blocked until every repository has source, license, maintainer/activity, executable-surface, security/provenance, conformance-fixture, rollback, OpenSpec, and docs/instruction evidence.

## Generated Manifests

| manifest | purpose |
|---|---|
| `planning/manifests/external-repo-intake-ledger.json` | Normalized 93-record ledger with gates and target lanes. |
| `planning/manifests/external-repo-intake-queue.json` | Per-repo intake queue for downstream lane ownership. |
| `planning/manifests/external-repo-review-tasks.json` | Seven pending review tasks per repo, 651 tasks total. |
| `planning/manifests/external-repo-quarantine-handoff.json` | C15 handoff records for denied-by-default repos. |
| `planning/manifests/external-repo-url-reconciliation.json` | URL, ID, duplicate, additions, and removals reconciliation. |

## Intake Summary

| dimension | values |
|---|---|
| total repos | 93 |
| review tasks | 651 |
| quarantine handoffs | 4 |
| source manifest | `planning/manifests/external-repo-evaluation-final.json` |

## Queue By Lane

| lane | count |
|---|---:|
| `docs-instructions` | 2 |
| `external-intake` | 18 |
| `harness-adapters` | 9 |
| `knowledge-graph-context` | 9 |
| `mcp-audit` | 2 |
| `multiagent-ui-patterns` | 14 |
| `security-quarantine` | 4 |
| `session-telemetry` | 2 |
| `skills-lifecycle` | 33 |

## Required Review Categories

- `source-verification`: Pin source, canonical URL, release or commit, and dedupe evidence.
- `license-review`: Record SPDX compatibility and attribution obligations.
- `maintainer-activity-review`: Check maintainer identity, activity, release cadence, issues, and bus factor.
- `executable-surface-review`: Identify installers, hooks, CLIs, network, filesystem, secrets, and dependency behavior.
- `security-provenance-review`: Threat-model credential, telemetry, remote execution, provenance, and sandbox risk.
- `conformance-fixture-review`: Define fixture or smoke test before any support-tier promotion.
- `rollback-docs-sync-review`: Record rollback plan, OpenSpec mapping, and docs/instruction sync impact.

## Downstream Use

- C02 consumes skill candidates only after source, license, provenance, and fixture evidence exist.
- C03 consumes MCP or wrapper candidates only after live-server value and sandbox behavior are proven.
- C11, C12, and C14 consume patterns as clean-room requirements, not copied upstream code.
- C15 consumes quarantine handoff records and remains the owner of denied-by-default decisions.
