# Proposal

## Why

Large image inputs waste context, trigger provider-side payload errors, and can degrade multimodal reasoning when screenshots or text-heavy images are naively downsampled by a harness or provider. The repo already manages OpenCode's native large-image optimizer, but other harnesses need a shared, auditable policy so local image inputs are resized intelligently before consumption where the harness can enforce that.

## What Changes

- Add `config/image-input-optimizer.json` plus schema coverage for image profiles, cache policy, and per-harness assurance tiers.
- Add `wagents.image_inputs` and `wagents media optimize-image` for source-preserving optimization into `~/.cache/wagents/image-inputs`.
- Add the `image-input-optimizer-guard` hook policy and project it through the existing hook registry for Codex, Claude Code, Cursor, GitHub Copilot CLI, and Gemini CLI.
- Keep OpenCode on the existing native `opencode-large-image-optimizer@latest` plugin and repo-managed plugin config.
- Distinguish hard-enforced harnesses from instruction-only or unproven surfaces such as ChatGPT, Claude Desktop, Copilot Web, Cursor cloud-only surfaces, Grok Build generic hooks, Antigravity, Cherry Studio, and Crush.
- Add instructions that tell non-hooked harnesses to optimize manually without claiming hard pre-consumption enforcement.

## Impact

- Hook-rewrite harnesses can consume cache-optimized derivatives without mutating user source images.
- Hook-block harnesses fail closed with explicit optimized retry paths when in-place input rewriting is not proven.
- The optimizer preserves extra detail for screenshots, UI, charts, documents, OCR/code captures, and alpha-bearing transparent assets.
- Maintainers get a single config surface for future harness-specific upgrades.

## Scope

- Core optimizer, CLI command, hook policy, registry entry, config/schema, focused tests, and docs/instruction notes.
- OpenSpec artifacts for downstream harness behavior and instruction posture.

## Out Of Scope

- Live harness install or `wagents skills sync --apply`.
- Generic Grok hook projection before Grok PreToolUse semantics are fixture-tested.
- Remote URL fetching, credentialed media downloads, or mutating original image files.
- Claiming hard enforcement for web, desktop, MCP-only, or cloud surfaces that do not expose local pre-consumption hooks.

## Risks

- Harness updated-input semantics can drift. Mitigate by using hook-block mode where rewrite is not proven and by keeping focused tests around response shapes.
- Pillow availability can lag in local environments. Mitigate with explicit dependency declaration and fail-closed hook messaging.
- Over-compression can hide UI or OCR detail. Mitigate with separate screenshot/text and transparent profiles.
