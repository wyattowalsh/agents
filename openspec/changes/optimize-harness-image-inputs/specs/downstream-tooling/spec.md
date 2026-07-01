## ADDED Requirements

### Requirement: Model-bound image inputs are optimized before consumption where harnesses can enforce it

The repository SHALL provide a source-preserving image optimizer and hook policy for local image paths passed to model-bound image-consuming tools.

#### Scenario: Hook-rewrite harness consumes an oversized local image

- **GIVEN** a Claude Code PreToolUse payload contains a local image path that exceeds the selected optimizer profile
- **WHEN** the `image-input-optimizer-guard` hook runs
- **THEN** it SHALL write an optimized derivative under the wagents image input cache
- **AND** it SHALL return updated tool input pointing at the optimized derivative
- **AND** it SHALL NOT mutate the source image.

#### Scenario: Hook-block harness consumes an oversized local image

- **GIVEN** a Codex, Cursor, Gemini CLI, or GitHub Copilot CLI hook payload contains a local image path that exceeds the selected optimizer profile
- **WHEN** the `image-input-optimizer-guard` hook runs
- **THEN** it SHALL write an optimized derivative under the wagents image input cache
- **AND** it SHALL block the original tool call with the optimized retry path.

#### Scenario: Source image path is unsafe or changes during optimization

- **GIVEN** a local image input path contains a symlink component or its stat identity changes between hook inspection and optimizer consumption
- **WHEN** the `image-input-optimizer-guard` hook runs
- **THEN** it SHALL block the tool call
- **AND** it SHALL NOT consume or cache the unsafe source path.

#### Scenario: Source image already fits the selected profile

- **GIVEN** a local image input already fits its selected profile
- **WHEN** the optimizer hook runs
- **THEN** it SHALL allow the tool call without rewriting or blocking.

### Requirement: Image optimization policy declares per-harness assurance tiers

The repository SHALL maintain a machine-readable image input optimizer config that distinguishes native transform, hook rewrite, hook block, specified-only, and instruction-only harnesses.

#### Scenario: OpenCode image inputs are handled by native plugin ownership

- **WHEN** image input assurance is inspected for OpenCode
- **THEN** the config SHALL identify `opencode-large-image-optimizer@latest` as the native transform owner
- **AND** generic hook projection SHALL NOT duplicate OpenCode image optimization ownership.

#### Scenario: Unsupported or unproven surfaces are documented without hard assurance

- **WHEN** image input assurance is inspected for web, desktop, MCP-only, or unproven cloud harnesses
- **THEN** the config SHALL list those surfaces as instruction-only or specified-only
- **AND** docs or instructions SHALL NOT claim hard pre-consumption enforcement for those surfaces.
