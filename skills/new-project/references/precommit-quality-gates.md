# Pre-commit And Quality Gates

Use local hooks for fast feedback and mirror them in CI.

Recommended local gates:

- format/lint for active languages
- type-check where configured
- test smoke suite
- generated-file freshness checks when applicable
- secret scanning before commits or releases

Do not install hooks automatically unless the user asks. Adding `.pre-commit-config.yaml` is a file mutation; running hooks over all files can modify unrelated files and requires approval.
