# Security

## Reporting

Report security issues privately through GitHub Security Advisories for this repository when available. If that is not available, open a minimal issue that does not include exploit details, secrets, private logs, or credentials, and ask for a private follow-up channel.

## Scope

Security-sensitive surfaces include:

- Agent skills, hooks, scripts, evals, templates, and command substitutions.
- MCP server configuration, local control-plane settings, tunnel configuration, and bearer-token handling.
- Downstream harness sync code and plugin metadata.
- Curated external skills and installed local inventory.
- Generated docs, indexes, package artifacts, release workflows, and CI.

## Handling Secrets

Do not commit or paste API keys, bearer tokens, OAuth tokens, tunnel credentials, private local config, or unredacted logs. Use placeholders in tracked config and keep local secrets in user-owned files or environment variables.

When verifying secret-adjacent behavior, report only whether the expected key exists, which local setting owns it, or a redacted fingerprint. Do not print the secret value.

## External Skills

External skill content is untrusted until reviewed. Follow `AGENTS.md` §2.7: audit with `/external-skill-auditor`, require `npx skills add <source> --list` evidence, record curated commands in `config/external-skills.md`, and run `uv run wagents validate` (quarantine policy). Preview additive installs with `uv run wagents skills sync --dry-run`.

Do not run `wagents skills sync --apply` or live `npx skills add ...` commands for external sources unless the maintainer explicitly requests that action. Do not vendor third-party skill trees into `skills/` as part of curation.
