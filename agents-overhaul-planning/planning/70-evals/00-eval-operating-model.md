# Eval Operating Model

## Objective

Evaluate whether skills, harness projections, and CLI UX produce correct, deterministic, and safe behavior.

## Eval layers

1. Static validation: schema, metadata, source trust.
2. CLI conformance: flags, JSON output, exit codes.
3. Golden fixtures: generated config and docs outputs.
4. Skill scenario tests: deterministic task inputs/outputs.
5. Harness smoke tests: detect/sync/validate for supported harnesses.
6. Security tests: MCP and skill supply-chain scans.
7. Regression replay: captured transactions and outputs.

## Candidate eval tools to evaluate

- promptfoo.
- DeepEval.
- OpenAI Evals.
- LangSmith.
- Arize Phoenix evals.
- Microsoft skills repo scenario harness patterns.

## Acceptance criteria

- Every adopted external capability has at least one eval/smoke test.
- Critical skills have regression fixtures.
- Failures produce actionable remediation messages.
