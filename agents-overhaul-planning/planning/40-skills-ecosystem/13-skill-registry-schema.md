# Skill Registry Schema

## YAML shape

```yaml
skills:
  - id: docs-steward
    name: docs-steward
    source: local
    repo_path: skills/docs-steward
    support_tier: validated
    spec:
      standard: agentskills.io
      has_skill_md: true
      has_scripts: false
      has_references: true
      has_assets: false
    harnesses:
      claude-code: project-skill
      github-copilot-cli: project-skill
      opencode: compatible-skill
      cursor-agent: agents-skill-compatible
      gemini-cli: extension-context-fallback
    cli_contract:
      deterministic: null
      json_output: null
      dry_run: null
    provenance:
      source_repo: wyattowalsh/agents
      ref: main
      checksum: null
    risks: []
    validation_gates:
      - skill-spec
      - docs-truth
      - activation-fixture
```

## CI validation

- Validate schema.
- Validate every `repo_path` exists.
- Validate every source-owned local skill has `SKILL.md`.
- Validate external skills have provenance.
- Validate docs matrix is generated from this schema.
