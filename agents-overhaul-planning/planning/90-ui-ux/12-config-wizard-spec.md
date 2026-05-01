# Config Wizard Spec

## Objective

Guide users through safe multi-harness setup without requiring them to understand every config file.

## Wizard steps

1. Detect installed harnesses.
2. Detect existing repo/user config files.
3. Ask desired scope: repo-local, user-global, or both.
4. Recommend skill-first defaults.
5. Recommend MCP profile only for live-state needs.
6. Show support tiers and risks.
7. Render diff preview.
8. Apply transaction.
9. Validate install.
10. Offer rollback.

## Questions to avoid

Do not ask users to choose between protocol internals unless required. Translate choices into use cases:

- “I need current web/docs lookup.” → docs/search MCP profile.
- “I need codebase playbooks.” → skills.
- “I need browser testing.” → browser MCP profile.
- “I need project rules.” → instructions/rules projection.
