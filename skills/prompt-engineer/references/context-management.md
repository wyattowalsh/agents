# Context Management

Strategies for managing context windows, preventing context rot, and optimizing
token usage. Applies to any system using long contexts or multi-turn conversations.

## Evidence Discipline

Context and caching claims are provider-sensitive. When using this reference in
output, include the active provider/API surface and whether the recommendation is
`official-doc`, `provider-guide`, `research`, `community-heuristic`, or
`local-practice`. Re-check provider docs before quoting exact thresholds,
discounts, TTLs, or model-specific compaction features.

---

## Context Rot

Context rot is non-linear performance degradation as context window usage
increases. Chroma Research (July 2025) tested 18 LLMs and found that performance
degrades not just from exceeding the context window, but from filling it — models
perform worse at 80% capacity than at 40%, even though the content fits.

**Key findings:**
- Performance degradation is non-linear — it accelerates as context fills
- "Lost in the middle" effect: models attend more strongly to content at the
  beginning and end of the context window, weakly to content in the middle
- Stale information (old tool results, resolved errors, superseded plans)
  actively degrades performance even though it is technically "context"
- The degradation is model-dependent but universal — all 18 tested models
  exhibited it

**Mitigation strategies:**
- Monitor context utilization as a first-class metric
- Compact proactively before the window fills, not after performance degrades
- Place critical information at the beginning or end of the context
- Remove information that has served its purpose (resolved errors, completed
  tasks, superseded plans)
- For multi-turn agents: summarize completed work rather than keeping full
  history
- Treat context as a resource with a carrying cost, not free storage

---

## Compaction Stack

Three-tier compaction strategy, from least to most aggressive. Apply tiers
in order — escalate only when the current tier is insufficient.

### Tier 1: Tool Result Clearing

After a tool result has been processed and its information incorporated into
the conversation, replace the full result with a summary.

- Example: A 500-line file read becomes `"Read file.py (500 lines): contains
  UserAuth class with login(), logout(), refresh_token() methods"`
- Preserves: what was learned. Removes: raw data
- Risk: Very low — information is preserved in summary form
- Trigger: After every tool result is processed
- Cost savings: Typically 60-90% of tool result tokens

### Tier 2: Reversible Compaction

Compress prior conversation turns into structured summaries while keeping
the full content available for expansion.

- Implementation: Maintain a "compacted" flag on turns. Compacted turns show
  summaries. If the model needs details, it can request expansion of specific
  turns
- Preserves: ability to recall details on demand. Removes: default verbosity
- Risk: Low — full content is recoverable
- Trigger: When context reaches 50-60% capacity
- Format summaries as: `[Turn N] <action>: <key outcome>` for quick scanning

### Tier 3: LLM Summarization

Use a separate LLM call to summarize the conversation history. This is lossy
and irreversible — use only when Tiers 1-2 are insufficient.

- GPT-5's compaction endpoint automates this
- For other models: make an explicit summarization call with instructions to
  preserve: key decisions, current state, active goals, unresolved issues
- Preserves: essential state. Removes: conversational detail permanently
- Risk: Medium — summarization is lossy, and important details may be lost
- Trigger: When context reaches 70-80% capacity, or when Tier 2 is insufficient
- Always verify that the summary captures all active tasks and blocking issues
  before discarding the original context

---

## Prompt Caching Strategies

**General Principle:** Arrange prompt content so that the longest stable prefix
is cached. Static content early, dynamic content late. Exact savings, minimum
tokens, and TTLs are provider-specific; report current provider terms rather than
using a universal discount claim.

### Provider Cache Matrix

Last verified: 2026-04-23.

| Provider | Mechanism | Design implication | Evidence class |
|----------|-----------|--------------------|----------------|
| Anthropic | Explicit `cache_control` breakpoints | Place stable system/tool/examples before breakpoints; keep dynamic user and retrieved content after them | `official-doc` |
| OpenAI | Automatic prompt caching for stable prefixes | Keep prefix byte-identical across calls; use prompt objects/versioning when available | `official-doc` |
| Google Gemini API | Explicit cached content API | Best for large reusable context; minimums and TTL are API-surface-specific | `official-doc` |
| Vertex AI Gemini | Context cache resource | Verify Vertex-specific token thresholds, model support, and TTL pricing | `official-doc` |
| Self-hosted | Runtime KV/prefix cache | Depends on serving stack such as vLLM, llama.cpp, or provider wrapper | `community-heuristic` |

### Anthropic (Claude)

- Explicit cache breakpoints via `cache_control: {"type": "ephemeral"}`
- Up to 4 breakpoints per request
- Place breakpoints after: system prompt, tool definitions, few-shot examples
- Dynamic content (user query, retrieved docs) after the last breakpoint
- TTL and minimum-token thresholds vary by model/API version — verify current
  docs before quoting values

### OpenAI (GPT)

- Automatic prefix caching — no explicit breakpoints needed
- Any request sharing an exact token-for-token prefix gets cached
- Minimum 1024 tokens for eligibility
- Keep the shared prefix byte-identical across requests — any difference
  invalidates the cache from that point forward
- Provider docs describe latency and cost reductions for cached prompts; verify
  current pricing before quoting exact percentages

### Google (Gemini)

- Context caching API — create a named cache with specified TTL
- Gemini API and Vertex AI have different context-cache surfaces and thresholds.
  Verify the active surface before designing economics.
- Best for large, stable contexts (full codebases, document collections)
- Cache is explicitly managed (create, use, delete)
- Cost-effective only when the cached content is reused many times within TTL

### Self-Hosted (Llama, etc.)

- KV-cache is typically managed at the inference level
- vLLM and similar engines support automatic prefix caching
- Design prompts with shared prefixes for batch efficiency
- Prefix caching benefits scale with request volume — higher throughput means
  higher cache hit rates

---

## ACE Framework

**Adaptive Contextual Expertise (ACE)** — arXiv:2510.04618, ICLR 2026

A framework for self-improving agent playbooks. Agents maintain a persistent
knowledge base that improves with each task execution.

**Key components:**
- **Playbook**: Structured document of strategies, common patterns, and learned
  heuristics for a specific domain or task type
- **Evaluation**: After each task, assess outcome quality and identify what
  could improve — both in execution and in the playbook itself
- **Update**: Modify the playbook based on evaluation — add new strategies,
  refine existing ones, remove ineffective patterns
- **Selection**: Before each task, select relevant playbook entries based on
  task characteristics — not all entries apply to every task

**Reported results:** benchmark-specific improvement vs. static prompts; treat
as `research`, not a guaranteed production lift.

**Application to prompt engineering:**
- Maintain a "prompt playbook" for recurring prompt types (summarization,
  extraction, classification, agent instructions)
- Track which techniques work best for which tasks and models — build an
  empirical record, not intuition
- Version prompts and correlate versions with eval results to identify what
  actually drives improvements
- Build organizational knowledge of what works, not just individual prompt files
- Review and prune the playbook regularly — stale entries cause the same
  degradation as stale context

---

## Multi-Context-Window Workflows

### Two-Agent Harness (Anthropic Pattern)

Split processing across two agents with different context profiles:
- Agent 1: Large context window, processes full documents or codebases
- Agent 2: Small context window, receives summaries and makes decisions
- Benefits: Cost efficiency (only one agent pays for large context), decision
  quality (Agent 2 is not overwhelmed by irrelevant detail)
- Use when: Processing large inputs where the decision logic is separable from
  the raw data analysis

### Context Isolation

Separate concerns into different context windows to prevent cross-contamination:
- Research agent (reads documents) produces a summary. Decision agent (acts on
  summary) never sees the raw documents
- Each agent gets only the context relevant to its role
- Prevents one task's context from degrading performance on another task
- Especially valuable in multi-agent systems where agents have distinct roles

### Tool Result Isolation

Tool outputs, retrieved documents, emails, web pages, and MCP resources can carry
indirect prompt injection. Treat them as untrusted context unless the caller has
validated provenance and integrity.

- Wrap tool results in explicit data tags with source metadata.
- Separate privileged instructions from untrusted retrieved/tool content.
- Summarize or validate tool results before passing them into a higher-privilege
  decision prompt.
- For write-capable tools, keep read/reasoning context separate from execution
  context and require explicit action gates.

### Structured Note-Taking for Cross-Session Persistence

Bridge the gap between sessions with persistent structured notes:
- Agents write structured notes (markdown, JSON) to persistent storage between
  sessions
- Next session loads relevant notes into context — not the entire history
- Prevents "starting from scratch" on every session
- Implementation: scratchpad files, memory systems, or dedicated note-taking
  tools
- Keep notes concise — they consume context window in the next session, so
  apply the same economy as prompt design
