# Dashboard JSON Schema

Data contract for the composable HTML dashboard (`templates/dashboard.html`). The LLM generates only the JSON data block; the template JS renders it deterministically.

## Required Fields

| Field | Type | Values |
|-------|------|--------|
| `view` | string | Space-separated view names |
| `scenario_title` | string | Scenario title |

## Optional Top-Level Fields

| Field | Type | Values |
|-------|------|--------|
| `tier` | string | `clear` \| `complicated` \| `complex` \| `chaotic` |
| `turn` | integer | Current turn number |
| `total_turns` | integer | Total turns in wargame |
| `difficulty` | string | `optimistic` \| `realistic` \| `adversarial` \| `worst-case` |

## View Schemas

### `classification`

```json
{
  "classification": {
    "dimensions": [{"name": "", "score": 0, "reasoning": ""}],
    "total": 0,
    "tier_sensitivity": ""
  }
}
```

### `turn`

```json
{
  "situation_brief": "",
  "inject": {"active": false, "title": "", "dilemma": "", "deadline_turn": 0},
  "actors": [{
    "name": "", "archetype": "hawk|dove|pragmatist|ideologue|bureaucrat|opportunist|disruptor",
    "is_player": false, "stance": "", "loss_aversion": 0.0, "last_action": "",
    "resources": [{"name": "", "value": 0, "trend": []}],
    "beliefs": {"Target": {"key": 0.0}}
  }],
  "options": [{"letter": "", "description": "", "domain": "", "risk_pct": "", "impact": "", "criteria_alignment": ""}]
}
```

### `analysis`

```json
{
  "analysis": {
    "type": "ach",
    "hypotheses": [],
    "evidence": [{"name": "", "scores": []}],
    "options_table": [{"name": "", "upside": "", "downside": "", "feasibility": ""}],
    "stakeholders": [{"name": "", "interest": "", "power": "", "position": ""}]
  }
}
```

### `aar`

```json
{
  "aar": {
    "timeline": [{"turn": 0, "decision": "", "outcome": "", "surprise": false}],
    "worked": [],
    "failed": [],
    "biases": {"human": [], "llm": []},
    "paths_not_taken": [{"turn": 0, "option": "", "likely_outcome": ""}],
    "insights": [],
    "action_bridge": {
      "probe": {"action": "", "tests": "", "watch_for": ""},
      "position": {"action": "", "advances": "", "preserves": ""},
      "commit": {"action": "", "captures": "", "trigger": ""}
    },
    "actor_performance": [{"name": "", "accuracy": 0.0, "surprises": 0, "notes": ""}]
  }
}
```

### `sensitivity`

```json
{
  "sensitivity": {
    "baseline": "",
    "variables": [{"name": "", "low": 0, "high": 0, "unit": ""}]
  }
}
```

### `delphi`

```json
{
  "delphi": {
    "question": "",
    "experts": [{"role": "", "position": "", "confidence": 0.0, "reasoning": ""}],
    "consensus": ""
  }
}
```

### `forecast`

```json
{
  "forecast": {
    "reference_class": "",
    "base_rate": "",
    "adjustments": [{"factor": "", "direction": "up|down", "magnitude": ""}],
    "final_estimate": ""
  }
}
```

### `negotiate`

```json
{
  "negotiate": {
    "parties": [{"name": "", "batna": "", "reservation": "", "target": ""}],
    "zopa": "",
    "leverage_points": []
  }
}
```

### `calibrate`

```json
{
  "calibrate": {
    "claims": [{"statement": "", "initial": 0.0, "adjusted": 0.0, "reasoning": ""}]
  }
}
```

### `options`

```json
{
  "real_options": {
    "options": [{"name": "", "type": "call|put|wait", "value": "", "expiry": "", "trigger": ""}]
  }
}
```

### `cause`

```json
{
  "cause": {
    "title": "",
    "nodes": [],
    "edges": [{"from": "", "to": "", "sign": "+|-", "label": ""}],
    "diagram_text": ""
  }
}
```

### `morph`

```json
{
  "morph": {
    "dimensions": [{"name": "", "options": []}],
    "combinations": [{"name": "", "selections": {}, "score": 0.0}]
  }
}
```

## Cross-View Fields

These fields can appear alongside any view:

### `monte_carlo`

```json
{
  "monte_carlo": {
    "clusters": [{"name": "", "frequency": 0, "narrative": ""}],
    "evpi": {"variable": "", "current_range": "", "resolved_range": ""}
  }
}
```

### `criteria`

```json
{
  "criteria": [{"rank": 0, "name": "", "weight": ""}]
}
```
