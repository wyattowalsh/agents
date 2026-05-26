# OpenSpec Governance

Use OpenSpec for non-trivial project workflow, public asset format, docs generation, validation behavior, or downstream agent tooling changes.

Default project artifacts:

- `openspec/config.yaml`
- `openspec/specs/`
- `openspec/changes/`

Do not commit generated downstream tool artifacts unless explicitly promoted. Validate with:

```bash
uv run wagents openspec validate
```
