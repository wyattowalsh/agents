---
skill: modern-python
source_type: curated-external
researched_at: '2026-06-16T20:04:00Z'
research_tier: standard
mean_confidence: 0.77
---

## Purpose

Configures and migrates Python projects to modern tooling: uv (deps/venv/tooling, replaces pip/pipx/poetry), ruff (unified lint+format), ty (fast type checking replacing mypy), pytest+cov, prek (fast pre-commit). Includes SessionStart hook to intercept legacy python/pip/pipx cmds and redirect. Security: detect-secrets, shellcheck, actionlint, zizmor, pip-audit, Dependabot. PEP 723 scripts, pyproject.toml, src layout, 3.11+. Based on trailofbits/cookiecutter-python.

## Harness Coverage

Python dev / setup agents. Includes hooks/.

## Trust And Risks

trust_tier=needs-inspection; status=inspect-then-install; provenance=verified-install-command; risks=Legacy cmd hook can surprise users expecting direct python/pip (exits non-zero with guidance); broad devtooling surface; migration alters lockfiles/envs. Respect user legacy if requested. policy=Inspect.; evidence=trailofbits batch in config + https://github.com/trailofbits/skills/plugins/modern-python (full SKILL.md + refs).

## Install Prerequisites

`npx skills add trailofbits/skills --skill modern-python -y -g ...` status=inspect-then-install; selector=named.

## Upstream Maintainer

[trailofbits/skills](https://github.com/trailofbits/skills) (William Tan).

## Comparable Alternatives

Language-specific from wshobson/agents (fastapi-templates etc), general python skills. This is scoped modern toolchain migration + hook.

> Web evidence from repo SKILL.md/README/hooks (2026).
