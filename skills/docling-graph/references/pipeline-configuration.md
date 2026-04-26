# Pipeline Configuration

Docling Graph configuration should make the extraction contract, provider/model, structured-output behavior, and debug artifacts explicit. Avoid relying on hidden defaults for production or reviewable workflows.

## Core Decisions

| Decision | Options | Guidance |
| --- | --- | --- |
| Extraction contract | `direct`, `staged`, `delta` | Choose deliberately for every non-trivial template. |
| Provider/model | OpenAI, Mistral, Gemini, Watsonx, local Ollama/vLLM/LM Studio | Match privacy, cost, latency, context length, and structured-output support. |
| Structured output | schema-enforced, sparse-check, fallback parser | Prefer schema enforcement where supported; record fallback behavior. |
| Gleaning | disabled, one pass, bounded multi-pass | Use for recall-sensitive fields and relationship discovery. |
| Streaming | off/on | Enable for long runs that need progress, cancellation, or live logs. |
| Debug dumping | off/on | Enable for development, failures, and audit handoffs. |

## Extraction Contracts

### Direct

Use direct extraction when the schema is small enough to fit comfortably in one model call and the document-to-graph mapping is straightforward.

Checks:

- Required fields appear in the graph artifact.
- Relationship fields are populated and directionally correct.
- Sparse-check output does not show systematic omissions.
- No provider context or schema-size warning appears.

### Staged

Use staged extraction when the root graph can be decomposed into sections, entity groups, or document regions. Staged extraction reduces schema pressure but introduces merge risks.

Checks:

- Each stage has a clear root object and output artifact.
- Cross-stage relationships survive the merge.
- Stable IDs exist before merge, not only after export.
- Inspect artifacts show which stage produced each entity group.

### Delta

Use delta extraction when documents contain many observations that must be resolved into a graph, or when entity/relationship evidence is scattered across the source.

Checks:

- Entity-like models have stable `graph_id_fields`.
- Resolver configuration is documented.
- Duplicate entities and orphan relationships are counted.
- High-cardinality collections are sampled before export.

## Structured Output

Structured output should be enabled when the selected provider supports schema enforcement. Pair it with a sparse check when fields may be optional or partially observable.

Record:

- Whether schema enforcement was enabled.
- Whether a fallback parser was used.
- Which fields failed sparse checks.
- Whether fallback output changed graph shape or relationship counts.

## Gleaning

Gleaning is useful when the first pass may miss low-salience entities or relationships. Keep it bounded.

Recommended policy:

- Start with one additional pass for recall-sensitive runs.
- Cap passes and token budget.
- Compare entity and relationship deltas between passes.
- Do not use gleaning to compensate for vague field descriptions or missing stable IDs.

## Streaming

Enable LLM streaming for long documents or batch jobs where operators need live progress. Treat streaming as observability, not correctness.

Check that streamed events line up with final artifacts before claiming completion.

## Python API Shape

Use explicit config fields and `Path` objects where possible:

```python
from pathlib import Path

from docling_graph import run_pipeline
from docling_graph.pipeline import PipelineConfig

config = PipelineConfig(
    input_path=Path("input.pdf"),
    output_dir=Path("out/input"),
    template=RootGraph,
    provider_override="openai",
    model_override="gpt-4.1-mini",
    extraction_contract="direct",
    structured_output=True,
    structured_sparse_check=True,
    llm_streaming=True,
    gleaning_enabled=False,
    dump_to_disk=True,
    debug=True,
)

context = run_pipeline(config)
```

If the installed version uses different names, inspect the local package help and adapt the names while preserving the same decisions.

## Provider Environment

Use environment variables, not inline secrets. Common provider checks:

- OpenAI: `OPENAI_API_KEY`
- Mistral: `MISTRAL_API_KEY`
- Gemini: `GOOGLE_API_KEY` or `GEMINI_API_KEY`
- Watsonx: `WATSONX_APIKEY`, `WATSONX_URL`, `WATSONX_PROJECT_ID`
- Ollama: local server reachable, optional `OLLAMA_HOST`
- vLLM or LM Studio: OpenAI-compatible base URL and model name

## Debug Artifacts

For development and failures, enable disk/debug output and preserve:

- Final graph artifact.
- Intermediate extraction JSON.
- `debug/trace_data.json`.
- Inspect HTML output.
- Provider/model config actually used.
- Command or `PipelineConfig` snapshot with secrets redacted.
