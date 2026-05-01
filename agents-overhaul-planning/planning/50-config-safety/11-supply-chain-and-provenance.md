# Supply Chain and Provenance

## Objective

Prevent external skills, plugins, MCPs, and generated configs from becoming untracked supply-chain risk.

## Controls

| Control | Skills | MCP | Plugins |
|---|---|---|---|
| Source repo/ref | required | required | required |
| License | required | required | required |
| Checksum/tree SHA | required for external | required for validated | required |
| Pinning | recommended/required external | required validated | required validated |
| SBOM | required for package release | required for packaged server | required plugin release |
| Signature/provenance | target via Sigstore/cosign/SLSA | target | target |
| Security scan | skill audit | mcp-scan | manifest audit |
| Secret scan | scripts/assets | env/args/config | hooks/scripts |

## Implementation tasks

- Add provenance metadata fields to registries.
- Add `wagents audit provenance` command.
- Generate SBOM for release bundles.
- Add checksum lockfile for external skills/MCPs.
- Add CI gate that blocks unpinned external runtime components in validated profiles.
