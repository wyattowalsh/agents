# Current MCP Inventory

Source artifact: latest public `mcp.json` from `wyattowalsh/agents`.

## Inventory

| MCP | Domain | Install style | Auth | Dynamic-state rationale | Decision |
|---|---|---|---|---|---|
| brave-search | search | npx | env:BRAVE_API_KEY | live web search | keep-mcp |
| cascade-thinking | reasoning | npx | none | structured reasoning | replace-with-skill |
| chrome-devtools | browser | npx | browser local | live browser/runtime debugging | keep-mcp |
| context7 | docs | npx | env:CONTEXT7_API_KEY | current docs lookup | keep-mcp |
| deepwiki | docs/repo knowledge | npx mcp-remote | remote http | live repo docs | keep-mcp |
| docling | documents | uvx | none | document processing | hybrid-skill-wrapper |
| fetch | web | npx | none | live URL fetch | keep-mcp |
| fetcher | web | npx | none | live URL fetch overlap | dedupe-review |
| package-version | package metadata | absolute local path | local binary | package version lookup | replace-or-portable-uvx |
| repomix | repo packaging | npx | none | repo context packing | hybrid-skill-wrapper |
| sequential-thinking | reasoning | npx | none | sequential reasoning | replace-with-skill |
| structured-thinking | reasoning | npx | none | structured thinking | replace-with-skill |
| tavily | search | npx | env:TAVILY_API_KEY | live web search | keep-mcp |
| trafilatura | web extraction | absolute local path | local source path | article extraction | replace-with-uvx-or-skill |
| arxiv | research | uvx | none | live paper lookup | keep-mcp |
| atom-of-thoughts | reasoning | absolute local path | local source path | reasoning | replace-with-skill |
| crash | debugging | npx | env vars | debug/reasoning | review |
| creative-thinking | reasoning | absolute local path | local source path | creative reasoning | replace-with-skill |
| deep-lucid-3d | 3d/generation | absolute local path | local source path | specialized dynamic generation | review |
| duckduckgo-search | search | uvx | none | live web search | keep-mcp |
| exa | search | npx | env:EXA_API_KEY | live neural search | keep-mcp |
| ffmpeg | media | absolute local path | local source path | media manipulation | hybrid-skill-wrapper |
| g-search | search | npx | unknown | live search | dedupe-review |
| gmail | email | npx | oauth/local auth | authenticated SaaS | keep-mcp |
| linkedin | web/social | uvx | browser/no-headless | live SaaS/browser | keep-mcp-high-risk |
| lotus-wisdom-mcp | reasoning | npx | none | reasoning/wisdom | replace-with-skill |
| shannon-thinking | reasoning | npx | none | reasoning | replace-with-skill |
| think-strategies | reasoning | npx github | none | strategy reasoning | replace-with-skill |
| wayback | web archive | npx | none | live archive lookup | keep-mcp |
| wikipedia | knowledge | npx | none | live encyclopedia lookup | keep-mcp-or-skill-index |

## Immediate portability issues

- Absolute local paths appear in several MCP definitions (`package-version`, `trafilatura`, `atom-of-thoughts`, `creative-thinking`, `deep-lucid-3d`, `ffmpeg`). These must be converted to `uvx`, `npx`, Git source refs, or developer-private overlays before validated release.
- Multiple reasoning MCPs appear to provide static reasoning scaffolds and should be replaced by Agent Skills unless they provide unique runtime behavior.
- Multiple web/search MCPs overlap. Keep coverage diversity only when each has a distinct API/source-quality role.

## Required next artifact

Generate `planning/manifests/mcp-registry.yaml` from the actual repo inventory and attach scan results, install portability status, and skill-replacement classification.
