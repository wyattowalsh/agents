# Google Antigravity Ecosystem Surface

## Sources

- Google Developers Blog: https://developers.googleblog.com/en/build-with-google-antigravity-our-new-agentic-development-platform/
- Gemini 3 launch: https://blog.google/products-and-platforms/products/gemini/gemini-3/

## Extension surfaces verified from public official sources

- Editor View: familiar IDE surface with tab completions and inline commands.
- Manager surface: agent-first orchestration of tasks.
- Agents operate across editor, terminal, and browser.
- Artifacts communicate plans, screenshots, browser recordings, and verification results.

## Unknowns

- Stable public plugin/config schema was not verified from official docs in this pass.
- MCP and Agent Skills support details should remain `experimental` or `repo-present-validation-required` unless validated against product docs and local install.

## Planning implications

- Project `.antigravity/` assets should be inventoried and documented, but support claims must stay conservative.
- Reuse Antigravity artifact UX as inspiration for `wagents` dashboard/run reports.
- Because agents can operate across terminal/browser/editor, transaction/rollback/sandbox docs should explicitly cover destructive-command risk.
