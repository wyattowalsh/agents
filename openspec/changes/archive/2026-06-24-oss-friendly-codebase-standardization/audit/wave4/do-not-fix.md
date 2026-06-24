# Do Not Fix (audit exclusions)

Generated: 2026-06-15

Items intentionally **out of scope** for oss-friendly standardization unless explicitly requested.

## Maintainer-local operational surfaces
- **Live `~/.config/opencode/opencode.json`** — user-owned; repo `opencode.json` is managed source but machine-tuned blocks may remain in local overlay only after split.
- **`.env.mcphub` secrets** — correctly gitignored; do not commit tokens.
- **MCPHub tunnel `https://mcp.w4w.dev/mcp`** — maintainer infra; document opt-in, do not remove maintainer capability.

## Experimental / planned harnesses
- **perplexity-desktop**, **cursor-agent-web/cli** — remain planned-research-backed; do not promote to repo-present without fixtures.
- **Cherry Studio** — experimental; keep out of default stranger sync group.

## Architectural choices (not bugs)
- **Grok skills via claude-code alias** — documented pattern; fix fixtures/docs, do not invent native Grok Skills CLI adapter prematurely.
- **OpenSpec as governance** — complexity is intentional; add stranger-lite path, do not remove OpenSpec.
- **MCPHub control plane** — valuable for maintainer; stranger docs should default to direct MCP or no-MCP path.
- **389 installed skills in catalog** — maintainer inventory signal; hide from default public view, do not delete local installs.

## Strengths to preserve
- NOT-for scoping on all repo skills
- agent-bundle.json single root
- Conservative harness tier registry
- external-skills.md narrative trust notes
- wagents validate + skill audit pipeline
