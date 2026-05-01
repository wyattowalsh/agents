# Implementation Sequencing

## Ordering principle

Do not implement harness-specific writes before the canonical registry, support tiers, and transaction model are stable.

## Critical path

1. Repo inventory and OpenSpec reconciliation.
2. Canonical registry schemas.
3. Skill-vs-MCP decision tree.
4. Transaction-safe config engine.
5. Harness projection fixtures.
6. CI conformance gates.
7. Docs/AI-instruction truth generation.
8. External capability adoption.

## Parallel work after registry freeze

Once the registry schemas are frozen, these teams can run in parallel:

- Claude team.
- Copilot team.
- Cursor team.
- OpenCode team.
- Gemini team.
- ChatGPT/Codex team.
- Cherry/Perplexity/Antigravity experimental team.
- Skills packaging team.
- MCP audit team.
- Docs and AI instructions team.
- UI/UX CLI team.
- CI/evals/security team.

## Integration checkpoints

- Checkpoint A: registry schemas accepted.
- Checkpoint B: first three harnesses have golden fixtures.
- Checkpoint C: skill packages validate and CLI conformance tests pass.
- Checkpoint D: MCP audit produces promote/watch/reject decisions.
- Checkpoint E: docs generation proves no drift.
- Checkpoint F: transaction engine passes rollback tests.
