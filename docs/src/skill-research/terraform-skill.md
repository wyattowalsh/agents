---
skill: terraform-skill
source_type: curated-external
researched_at: '2026-06-16T08:36:59Z'
research_tier: standard
mean_confidence: 0.72
---

## Purpose

Terraform & OpenTofu skill for AI coding agents. Encodes best practices for testing (decision matrix native `terraform test` vs Terratest; static/integration/E2E workflows), module development (structure, naming `terraform-<provider>-<name>`, versioning, public/private), state management (remote backends S3/Azure/GCS/TFC, locking, encryption, multi-team isolation, migration), CI/CD (GitHub Actions, GitLab, Atlantis, cost est Infracost, compliance), security/compliance (Trivy, Checkov, policy-as-code). Multi-cloud first-class (AWS default in examples but Azure/GCP equivalents provided). Includes decision flowcharts, DO/DONT patterns, cheat sheets, quick refs. Companion recommendations like code-intelligence plugin. Apache 2.0.

## Harness Coverage

Target agents: antigravity, claude-code, codex, crush, cursor, gemini-cli, github-copilot, grok, opencode. Install instructions cover Claude Code (via antonbabenko/agent-plugins marketplace), Gemini, Cursor, Copilot, OpenCode, Codex, Kiro, Antigravity (symlink), manual clone. Also acts as Kiro Power with optional terraform-mcp-server.

## Trust And Risks

inspect-then-install / needs-inspection. Apache 2.0. Maintainer antonbabenko (author of terraform-aws-modules collection, terraform-best-practices.com, pre-commit-terraform). Popular in IaC community. Source includes tests/ and validation. Config marks for inspection (generic provenance note); install via npx or per-agent clone/plugin. Risks: potential marketplace name clashes (use agent-plugins not direct for some hosts); optional LSP/MCP dependencies; ensure version compatibility (Terraform 1.0+/OpenTofu 1.6+); always review generated IaC as infrastructure changes are high-impact. No broad endorsements in web evidence beyond self-description.

## Install Prerequisites

`npx skills add antonbabenko/terraform-skill --skill terraform-skill -y -g -a antigravity claude-code codex crush cursor gemini-cli github-copilot grok opencode`

status=inspect-then-install; selector=named. Per-agent alternatives: git clone to ~/.cursor/skills etc or plugin marketplace. Recommends companion code-intelligence. Do not duplicate marketplace registrations. Verify with test prompt after install.

## Upstream Maintainer

antonbabenko (github.com/antonbabenko/terraform-skill). Apache 2.0. Based on field-tested patterns from terraform-aws-modules, terraform-best-practices.com, AWS Hero experience. Active CHANGELOG, CONTRIBUTING, CLAUDE.md for skill dev. Related: pre-commit-terraform, terraform-docs, tflint, trivy. High relevance for IaC agents.

## Comparable Alternatives

Official HashiCorp Terraform docs + testing guides; community awesome-terraform lists; other IaC skills (e.g. for Pulumi/CDK or cloud-specific); general devops-engineer or compliance skills; direct use of terraform-ls + agent code intelligence without domain skill.

> Web-augmented research; evidence only, not authority. Config in external-skills.md is authoritative for install.
