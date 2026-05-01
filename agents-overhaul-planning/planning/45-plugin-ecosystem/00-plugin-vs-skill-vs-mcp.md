# Plugin vs Skill vs MCP

## Decision table

| Need | Prefer | Why |
|---|---|---|
| Reusable procedural knowledge | Skill | portable, progressive disclosure, low runtime complexity |
| Bundled skill + hooks + agents + MCP for one harness | Plugin | native packaging/update/discovery |
| Live external state or authenticated tool calls | MCP | standardized live connector |
| Public API action in Custom GPT | OpenAPI Action | ChatGPT-native API integration |
| Interactive UI in ChatGPT | Apps SDK | MCP-backed app UI, preview |
| Always-on short guidance | Instruction/rule | low friction and always loaded |
| Spec-governed change | OpenSpec | proposal/design/tasks/spec delta |

## Anti-patterns

- MCP server that only stores a prompt.
- Plugin that creates a divergent copy of a skill.
- Always-on instruction that contains a long procedure better loaded as a skill.
- `@latest` plugin version in a validated support profile.
