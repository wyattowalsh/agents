# Design

## Pipeline

1. Detect local image paths from tool payload keys such as `image_path`, `images`, `attachments`, and normal file path fields.
2. Skip write and shell tools so the policy does not rewrite files being edited or created.
3. Resolve only existing local files under the current workspace, repo root, common user image/download directories, or the system temp directory.
4. Run `wagents.image_inputs` in a subprocess so the hook runner does not import Pillow on every startup.
5. Optimize into `~/.cache/wagents/image-inputs/<hash-prefix>/<hash>.<ext>` using source bytes plus profile config as the cache key.
6. Return no output when the source already fits the selected profile.
7. For Codex and Claude Code, return `updatedInput` with optimized cache paths.
8. For Cursor, Gemini CLI, and GitHub Copilot CLI, deny with an optimized retry path because safe input mutation is not proven.

## Profiles

- `general`: photos and mixed media; 2000px long edge, 4M pixels, 4.5MB.
- `screenshot-text`: UI, screenshots, documents, charts, OCR, code, and terminal captures; 3000px long edge, 8M pixels, 4.5MB.
- `transparent`: alpha-bearing assets; 3000px long edge, 8M pixels, 4.5MB, PNG output.
- `thumbnail`: low-risk previews; 1024px long edge, 1M pixels, 1.5MB.

## Harness Tiers

- Native transform: OpenCode via `opencode-large-image-optimizer@latest`.
- Hook rewrite: Codex and Claude Code.
- Hook block with optimized retry: Cursor, Gemini CLI, GitHub Copilot CLI.
- Specified only: Grok Build until generic hook projection is proven beyond Plannotator hooks.
- Instruction only: web, desktop, MCP-only, and unproven cloud surfaces.

## Safety Properties

- Source images are never overwritten.
- Cache files are created under a user-local cache directory with private permissions.
- Remote URLs and URI schemes are ignored by the hook policy.
- If optimization fails for a detected image input, the hook fails closed rather than letting oversized input proceed.
