# Downstream Tooling Delta

## MODIFIED Requirements

### Requirement: Supported Agent Mapping Is Stable

The repository SHALL maintain a deterministic mapping from repo-supported agent IDs to OpenSpec tool IDs and Skills CLI install targets, while documenting requested harness facets that do not have direct Skills CLI adapters.

#### Scenario: Installing curated external skills across supported harnesses

- **WHEN** a curated external skill command is added for global rollout
- **THEN** the command SHALL use only Skills CLI target IDs supported by the repo install/sync tooling
- **AND** desktop, cloud, or app UI harness facets without direct Skills CLI target IDs SHALL be reported as config or blind-spot surfaces rather than invented install adapters.

#### Scenario: Mapping split GitHub Copilot facets

- **WHEN** a user requests installation for GitHub Copilot web, CLI, or aggregate Copilot surfaces
- **THEN** the repository SHALL use the single `github-copilot` Skills CLI target for install/sync
- **AND** documentation or reports SHALL keep web and CLI audit facets separate when discussing observable surfaces and blind spots.
