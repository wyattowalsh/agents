# Validation Matrix

| Check | Command | Expected Result |
| --- | --- | --- |
| OpenSpec | `uv run wagents openspec validate` | Change is complete and valid. |
| Lane diff | `git diff --check -- planning/60-ci-cd/00-quality-gates.md planning/70-evals/00-eval-operating-model.md openspec/changes/agents-c07-ci-evals-observability` | No whitespace errors. |
| Existing focused tests | `uv run pytest tests/test_distribution_metadata.py::test_platform_overhaul_registries_validate_against_schemas` | Required before schema-affecting implementation changes. |
