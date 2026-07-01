# Tasks

## Hyperfine Task Graph

### Lane A: Repository State And Existing Ownership

- [x] A1. Confirm current branch and dirty worktree.
- [x] A2. Inspect root AGENTS instructions and relevant hook/CLI surfaces.
- [x] A3. Verify existing OpenCode native image optimizer plugin/config ownership.
- [x] A4. Identify harnesses with hook rewrite, hook block, native plugin, or instruction-only posture.

### Lane B: Optimizer Core

- [x] B1. Add repo-owned image optimizer config.
- [x] B2. Add JSON schema for config profiles and harness tiers.
- [x] B3. Add cache-keyed optimizer module.
- [x] B4. Preserve source files and write optimized derivatives to user cache only.
- [x] B5. Implement profile detection for screenshot/text and transparent assets.
- [x] B6. Add CLI entry point `wagents media optimize-image`.
- [x] B7. Declare Pillow dependency.

### Lane C: Hook Enforcement

- [x] C1. Extend hook path detection to image-specific payload keys.
- [x] C2. Add image consumer gating so write/shell tools are skipped.
- [x] C3. Add safe local path resolution and image file detection.
- [x] C4. Invoke optimizer subprocess from the hook policy.
- [x] C5. Add Codex/Claude updated-input response.
- [x] C6. Add Cursor/Gemini/Copilot block-with-retry response.
- [x] C7. Register `image-input-optimizer-guard` in the hook registry.

### Lane D: Specs, Instructions, And Registry Metadata

- [x] D1. Add OpenSpec proposal, design, tasks, and spec deltas.
- [x] D2. Add instruction-only harness guidance without overclaiming assurance.
- [x] D3. Add sync-manifest entry for the canonical optimizer config.
- [ ] D4. Regenerate broad generated docs only after the existing generated-docs worktree is reconciled.

### Lane E: Tests And Validation

- [x] E1. Add optimizer unit tests with real Pillow images.
- [x] E2. Add hook rewrite/block tests with mocked optimizer subprocess.
- [x] E3. Add config/schema metadata test.
- [x] E4. Run `uv lock`.
- [x] E5. Run focused pytest for optimizer and hook behavior.
- [x] E6. Run hook registry/config validation.
- [x] E7. Run OpenSpec validation.

### Lane F: Review Finding Hardening

- [x] F1. Project the optimizer hook into every declared repo-local harness surface.
- [x] F2. Materialize Codex and Gemini APM hook bundles.
- [x] F3. Replace the image hook's ambient `python3` command with the repo hook runner placeholder.
- [x] F4. Tighten trusted `uv` lookup and remove inherited `UV_CACHE_DIR`.
- [x] F5. Pass source identity from hook inspection to optimizer consumption.
- [x] F6. Reject symlink source paths and validate source/cache state across reads and writes.
- [x] F7. Align Codex with block-with-retry semantics rather than in-place rewrite.

## Stop Rules

- Do not run live harness installs or `wagents skills sync --apply`.
- Do not touch unrelated generated docs while the existing generated-docs tree is dirty.
- Do not claim hard assurance for harnesses listed as instruction-only or specified-only.
