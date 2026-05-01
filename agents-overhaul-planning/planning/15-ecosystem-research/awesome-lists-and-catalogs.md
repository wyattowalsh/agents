# Awesome Lists and Curated Catalogs

## Objective

Use curated lists to discover tools, not to approve tools.

## Categories to track

- Awesome AI Agents.
- Awesome MCP.
- Awesome LLM.
- Awesome AI IDEs.
- Awesome Agent Frameworks.
- Awesome LLM Security.
- Awesome Policy-as-Code.
- Awesome OpenTelemetry.
- Awesome Prompt Engineering.
- Awesome DevTools AI.
- Awesome GitHub Copilot.

## Extraction fields

For each candidate extracted from a list:

- source list URL;
- upstream repository URL;
- maintainer organization;
- license;
- stars/forks if available;
- last commit / release recency;
- documentation URL;
- integration lane: skill, plugin, MCP, CLI, OpenAPI, rules, eval, security, observability;
- maturity tier;
- security posture;
- supply-chain notes;
- overlap with existing repo capabilities;
- action: adopt, adapt, reference, watch, reject.

## High-signal candidates already worth tracking

| Candidate | Category | Why useful | Preferred lane |
|---|---|---|---|
| OpenAI Agents SDK | framework | Tool orchestration and eval/reference patterns | reference/skill wrappers |
| LangGraph | framework | graph-based agent orchestration patterns | reference/evals |
| LlamaIndex agents | framework | RAG/tooling patterns | reference/evals |
| Microsoft AutoGen | framework | multi-agent orchestration patterns | reference/evals |
| Semantic Kernel | framework | plugin/function abstraction patterns | reference |
| Promptfoo | eval | CLI-friendly eval harness | skill wrapper / CI |
| DeepEval | eval | LLM eval patterns | skill wrapper / CI |
| Langfuse | observability | tracing/cost/LLM run observability | observability adapter |
| Arize Phoenix | observability | open-source LLM tracing/evals | observability adapter |
| OpenTelemetry | observability | standard telemetry substrate | core telemetry |
| OPA / Conftest | policy | policy-as-code for config validation | skill/CI wrapper |
| Cosign / Sigstore | supply chain | signing/provenance | CI/security |
| Syft / Grype | SBOM/scanning | artifact inventory and vulnerability scanning | CI/security |
| mcp-scan | MCP security | prompt-injection/tool-poisoning scanning | CI/security |

## Governance rule

No candidate becomes a default dependency until it has:

1. source verification;
2. license check;
3. maintenance check;
4. security review;
5. conformance test;
6. docs entry;
7. rollback path.
