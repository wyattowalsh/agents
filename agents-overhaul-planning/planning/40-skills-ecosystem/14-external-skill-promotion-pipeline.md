# External Skill Promotion Pipeline

## Objective

Convert high-quality external skills and skill-adjacent tools into safe, traceable, repo-compatible assets.

## Candidate Sources

- Official/vendor skills: `microsoft/skills`, `google/skills`, `cloudflare/skills`, `supabase/agent-skills`.
- Curated indexes: `VoltAgent/awesome-agent-skills`, `skillmatic-ai/awesome-agent-skills`, `Prat011/awesome-llm-skills`.
- Community skill suites: `NeoLabHQ/context-engineering-kit`, `Orchestra-Research/AI-Research-SKILLs`, `Weizhena/Deep-Research-skills`, `antfu/skills`, `samber/cc-skills-golang`.
- Domain skills: `ios-simulator-skill`, `Pretty-mermaid-skills`, `skill.color-expert`, `finance-skills`.
- Skill builders/managers: `refly`, `skillkit`, `OpenPackage`, `tech-leads-club/agent-skills`.

## Promotion Steps

1. Intake repository metadata into `planning/manifests/external-repo-evaluation-final.json`.
2. Validate skill structure against Agent Skills spec: required `SKILL.md`, frontmatter, optional `scripts/`, `references/`, `assets/`, progressive disclosure fit, no hidden destructive behavior.
3. Run license and provenance review.
4. Run static/security review for scripts.
5. Classify as direct skill candidate, wrapper skill, reference-only, or quarantine.
6. Write or update OpenSpec child change.
7. Add conformance fixture: skill package validation, install dry-run, docs rendering, no unexpected network/secret access.
8. Add docs and AI-instruction fragments.
9. Promote only after validation passes.

## CLI Contract for Promoted Skills

Every promoted skill with scripts should expose:

```text
--help
--version
--json
--dry-run
--check
--output <path>
```

Recommended behavior: deterministic outputs where possible; non-zero exit code on failure; machine-readable diagnostics under `--json`; no mutation without explicit `--apply`; no network without documented flags/env vars; no secrets printed to stdout/stderr.
