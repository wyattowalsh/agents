# Dashboard Schema

JSON data contract for the HTML research dashboard. The dashboard template reads data from `<script id="data" type="application/json">`. Read when handling the `export` command.

## Schema

```json
{
  "metadata": {
    "query": "string — the original research question",
    "tier": "quick|standard|deep|exhaustive",
    "mode": "investigate|factcheck|compare|survey|track",
    "date": "YYYY-MM-DD",
    "sources_count": 0,
    "findings_count": 0,
    "mean_confidence": 0.0,
    "waves_completed": 0,
    "tools_used": ["brave-search", "context7"]
  },
  "findings": [
    {
      "id": "RR-001",
      "claim": "string — the discrete assertion",
      "confidence": 0.0,
      "evidence": [
        {
          "tool": "string — MCP tool or search engine used",
          "url": "string — source URL",
          "timestamp": "string — ISO 8601 access timestamp",
          "excerpt": "string — verbatim excerpt, max 100 words"
        }
      ],
      "cross_validation": "agrees|contradicts|partial|unverified",
      "bias_markers": ["recency", "authority"],
      "gaps": ["what additional evidence would strengthen this"]
    }
  ],
  "contradictions": [
    {
      "id": "C-01",
      "topic": "string — what the contradiction is about",
      "type": "factual|methodological|temporal|scope",
      "side_a": {
        "claim": "string",
        "source": "string — URL",
        "confidence": 0.0
      },
      "side_b": {
        "claim": "string",
        "source": "string — URL",
        "confidence": 0.0
      },
      "assessment": "string — analysis of which side is more credible and why"
    }
  ],
  "sources": [
    {
      "url": "string",
      "tool": "string — MCP tool used to access this source",
      "timestamp": "string — ISO 8601 access timestamp",
      "title": "string — page or document title",
      "referenced_by": ["RR-001", "RR-003"]
    }
  ],
  "confidence_distribution": {
    "high": 0,
    "medium": 0,
    "low": 0,
    "uncertain": 0
  },
  "gaps": ["string — identified knowledge gap"],
  "sub_questions": [
    {
      "question": "string — the sub-question",
      "status": "answered|partial|unanswered",
      "answer_summary": "string — brief answer or reason for unanswered status"
    }
  ]
}
```

## Field Definitions

| Field | Required | Description |
|-------|----------|-------------|
| `metadata.query` | Yes | Original research question verbatim |
| `metadata.tier` | Yes | Complexity tier from Wave 0 classification |
| `metadata.mode` | Yes | Research mode from dispatch |
| `metadata.date` | Yes | Date research was conducted |
| `metadata.sources_count` | Yes | Total unique sources consulted |
| `metadata.findings_count` | Yes | Total findings produced |
| `metadata.mean_confidence` | Yes | Arithmetic mean of all finding confidence scores |
| `metadata.waves_completed` | No | Number of waves executed (0-4) (recommended) |
| `metadata.tools_used` | No | List of MCP tools and search engines used (recommended) |
| `findings[].id` | Yes | Sequential ID: `RR-001`, `RR-002`, ... |
| `findings[].claim` | Yes | Discrete assertion statement |
| `findings[].confidence` | Yes | Score 0.0-1.0 per confidence rubric |
| `findings[].evidence` | Yes | Array of evidence items with provenance |
| `findings[].cross_validation` | Yes | Cross-source agreement status |
| `findings[].bias_markers` | No | Empty array if none detected |
| `findings[].gaps` | No | Empty array if none identified |
| `contradictions[].type` | Yes | One of: factual, methodological, temporal, scope |
| `sources[].referenced_by` | Yes | Finding IDs that cite this source |
| `sub_questions[].status` | Yes | One of: answered, partial, unanswered |

## Confidence Distribution Bands

| Band | Range | Key |
|------|-------|-----|
| High | 0.8-1.0 | `high` |
| Medium | 0.5-0.7 | `medium` |
| Low | 0.3-0.4 | `low` |
| Uncertain | < 0.3 | `uncertain` |

## Export Path

Write the rendered dashboard to: `~/.claude/research/exports/{journal-slug}.html`

The `journal-slug` matches the journal filename without date prefix and extension. Example: journal `2026-02-27-tech-llm-agent-patterns.md` exports to `llm-agent-patterns.html`.
