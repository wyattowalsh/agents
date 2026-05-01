---
status: planning
owner: ecosystem-research-team
last_updated: 2026-05-01
---

# External Tool Shortlist Ingredients

## Skills/plugins priority candidates

| Candidate class | Integration form | Why it is useful | Promotion risk |
|---|---|---|---|
| OpenAI skills | Agent Skill catalog | Codex/OpenAI-facing examples and conventions | Verify package layout and supported clients |
| Trail of Bits skills | Security skill catalog | High-value security review playbooks | License/provenance review required |
| Supabase agent skills | Domain skills | Useful DB/backend workflow examples | Domain-specific; do not over-import |
| HashiCorp/infrastructure skills | Domain skills | IaC and infra workflow patterns | Requires careful secret/cloud controls |
| Awesome Copilot skills/agents | Skill/agent templates | Useful Copilot-specific patterns | Community items need review |
| OpenCode plugin examples | Plugin | Event hooks and local automation | Plugin code execution risk |
| Gemini extensions | Extension package | Native packaging for Gemini CLI | Conflict/prefix and restart semantics |

## MCP priority candidates

| Candidate | Integration form | Why MCP remains appropriate | Notes |
|---|---|---|---|
| Context7 | MCP | live current docs retrieval | Pair with docs-lookup skill wrapper |
| Chrome DevTools MCP | MCP | live browser/runtime inspection | Strong UI/testing complement |
| Playwright MCP | MCP | browser automation | Use isolated profile and test creds |
| Perplexity MCP | MCP | search/ask/research API | API-key scoping and cost telemetry |
| Firecrawl MCP | MCP | extraction/deep web research | Treat output as untrusted web content |
| Notion MCP | MCP | live workspace state | OAuth and least privilege |
| Linear MCP | MCP | live issue state | Project scope controls |
| Atlassian Rovo MCP | MCP | Jira/Confluence/Compass | Enterprise admin controls |
| Sentry MCP/AI monitoring | MCP/observability | incident and trace state | Redaction and PII policy |

## Do-not-promote-yet classes

- MCPs without clear upstream repo or license.
- MCPs that require broad filesystem/cloud permissions without sandbox plan.
- Experimental harness surfaces without official docs.
- UI tools that cannot be exercised in CI or documented cleanly.
