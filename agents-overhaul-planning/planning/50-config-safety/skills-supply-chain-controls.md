# Skill Supply-Chain Controls

## Objective

Treat external skills as installable software artifacts.

## Required controls

- exact source/ref pinning;
- checksum capture;
- optional signature/provenance verification;
- license capture;
- maintainer/trust metadata;
- script inventory;
- script execution policy;
- SBOM for packaged dependencies where feasible;
- audit trail for installs/updates/removals;
- rollback to previous pinned version.

## Recommended tooling to evaluate

- Sigstore/cosign for signing and verification.
- SLSA provenance patterns for build/source integrity.
- Syft/Grype for SBOM and vulnerability scanning.
- OPA/Conftest for policy-as-code validation.

## Acceptance criteria

- External skills cannot be silently upgraded.
- Skill updates produce a diff and validation report.
- Script-backed skills cannot run without policy approval.
