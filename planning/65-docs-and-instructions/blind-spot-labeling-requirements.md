# Blind-Spot Labeling Requirements

## Requirement

Unsupported, experimental, unverified, and quarantine harnesses or assets must be visible in docs with an explicit blind-spot label. Missing evidence is not a reason to omit a surface.

## Label Meanings

| label | meaning |
|---|---|
| `unsupported` | The repo explicitly does not support this surface. |
| `unverified` | The surface is known but lacks source, fixture, or install evidence. |
| `experimental` | The surface exists or is planned but lacks stable validation. |
| `quarantine` | The asset is denied by default due auth, proxy, credential, offensive, or supply-chain risk. |
| `planned-research-backed` | Planning evidence exists, but implementation or validation does not. |

## Rendering Rules

- Include the owner lane and next validation step where available.
- Link to the registry or manifest source when possible.
- Prefer plain caveats over optimistic language.
- Never hide risk behind “coming soon” or “supported soon” wording.

## Examples

- `quarantine`: Offensive security skill source, denied by default pending C15 review.
- `experimental`: Desktop app import path exists but lacks fixture-backed rollback.
- `unverified`: Harness appears in ecosystem research but has no local projection fixture.
