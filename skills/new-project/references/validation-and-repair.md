# Validation And Repair

Audit and doctor modes are read-only. Repair mode must be based on a preflight and blueprint.

## Repair Rules

1. Report dirty git state before any mutation.
2. Preserve unrelated changes.
3. Skip existing files by default.
4. Do not delete legacy docs, configs, or generated files.
5. Validate after each approved repair group.

Repair output must include created files, skipped files, unresolved risks, and verification commands.

## Executable Coverage

Run `uv run pytest tests/test_new_project.py` after changing catalog helpers, blueprint generation, plan validation, package alias resolution, or command safety classification. This targeted test file exercises transitive capability resolution, `--without` blocking, Docker Compose command normalization, secret-read rejection, blueprint approval derivation, and version-check alias hardening.
