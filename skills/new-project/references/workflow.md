# Workflow

Use this reference for every mutating `new-project` mode.

## Safe Sequence

1. Classify request intent and target path.
2. Run read-only preflight.
3. Resolve preset and capability IDs from `data/`.
4. Produce a blueprint listing files, commands, risks, approvals, and validation.
5. Ask for explicit approval for each mutation group.
6. Apply only the approved group.
7. Report created files, skipped files, commands run, and validation results.

## Default Conflict Policy

Skip existing files. If overwrite is necessary, list each file and ask for approval before editing.

## Mutating Command Policy

Do not run scaffold generators, package installs, cloud commands, release commands, Docker commands, or deploy commands until the blueprint includes the approval gate for that command category.
