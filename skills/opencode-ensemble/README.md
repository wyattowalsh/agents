# OpenCode Ensemble Skill

Guidance for using OpenCode Ensemble to coordinate multiple AI coding agents safely and effectively.

Source provenance:

- Upstream: `hueyexe/opencode-ensemble`
- Tag: `v0.14.2`
- Commit: `b6bc7f706c13aa42d32e836ea647677d0b14c2f7`
- License: MIT

Install from upstream:

```bash
npx skills@latest add hueyexe/opencode-ensemble --skill opencode-ensemble
```

Use this skill when you want your agent to decide whether a team is worthwhile, split work into independent slices, choose `explore` vs `build` teammates, select model strategy, write teammate prompts, review results, and clean up safely.

This repo keeps OpenCode plugin specs on `@latest` and configures thinking levels through OpenCode agent variants. The local skill examples therefore avoid explicit `team_spawn.model` values by default so teammates inherit the configured agent defaults.

## Structure

```text
opencode-ensemble/
├── SKILL.md
└── references/
    ├── coordination-patterns.md
    ├── prompt-recipes.md
    ├── lead-checklists.md
    ├── anti-patterns.md
    └── eval-scenarios.md
```

`SKILL.md` is the short operational guide. Reference files provide deeper patterns, prompt recipes, checklists, anti-patterns, and pressure scenarios.
