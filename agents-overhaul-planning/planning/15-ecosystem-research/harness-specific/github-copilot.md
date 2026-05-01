# GitHub Copilot Web/CLI Ecosystem Surface

## Sources

- Agent skills: https://docs.github.com/en/copilot/concepts/agents/about-agent-skills
- Add skills: https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/create-skills
- Copilot CLI skills: https://docs.github.com/copilot/how-tos/copilot-cli/customize-copilot/create-skills
- Custom agents: https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-custom-agents
- Custom agents config: https://docs.github.com/en/copilot/reference/custom-agents-configuration
- MCP for cloud agent: https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/extend-coding-agent-with-mcp

## Extension surfaces

- Project/personal agent skills.
- `gh skill` discovery/install/update/publish.
- Repository-wide and path-specific custom instructions.
- `AGENTS.md` hierarchy.
- Custom agents under `.github/agents/*.md` or org/enterprise `.github-private`.
- Repository MCP configuration and Copilot environment secrets.
- Copilot Extensions/skillsets where still supported.

## Planning implications

- Add `.github/skills` projection only if repo wants GitHub-native location; otherwise `.agents/skills` can remain portable.
- Use `gh skill preview` as audit gate for external GitHub skills.
- Treat custom agents as agent-profile projections, distinct from Agent Skills.
- Mark Copilot custom agents public preview where docs do.
