# ADR-0000: Architecture Decision Record Template

Use this template for significant repository decisions. Copy to `docs/adr/NNNN-short-title.md` with the next sequential number.

## Status

Proposed | Accepted | Deprecated | Superseded by [ADR-XXXX](./XXXX-short-title.md)

## Context

What problem or constraint forces a decision? Link evidence (OpenSpec change, issue, metrics).

## Decision

State the decision in complete sentences. Be specific about defaults and non-goals.

## Consequences

### Positive

- …

### Negative / trade-offs

- …

## Alternatives Considered

| Option | Why not chosen |
| ------ | -------------- |
| … | … |

## Validation

How will we know this decision holds? List commands, gates, or observability checks.

```bash
# example
uv run wagents validate
```

## References

- Related runbooks:
- Related OpenSpec changes:
- Related config/registry paths:

---

## Naming Convention

- File: `docs/adr/NNNN-kebab-case-title.md` where `NNNN` is zero-padded (`0001`, `0012`).
- This file (`0000-template.md`) is the convention reference — do not accept it as a decision record.
- Prefer linking ADRs from OpenSpec `design.md` or runbooks when the decision affects maintainer workflow.
