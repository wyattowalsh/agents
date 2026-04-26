# External Skill Import Checklist

Use this checklist before installing or promoting any third-party Agent Skill.

## 1. Source And Provenance

- Record the exact source string, registry URL, and source repository URL.
- Prefer official vendor repositories or high-reputation maintainers.
- Verify `npx skills add <source> --list` succeeds before install.
- Capture the observed install count and access date when citing registry data.
- Record license, resolved commit SHA, and a content hash before repo promotion.
- Treat source conflicts as blockers until resolved.

## 2. Skill Metadata

- `name` is kebab-case and matches the directory.
- `description` states what it does, when to use it, and when not to use it.
- Frontmatter does not request surprising model, tool, hook, or compatibility behavior.
- Body defines clear dispatch or usage boundaries.
- Any referenced files exist and are relevant.

## 3. Executable Surface

Inspect, but do not run, these surfaces first:

- `hooks` in frontmatter or platform settings.
- `scripts/`, executable bits, package scripts, and binaries.
- Shell snippets, command substitutions, and backtick commands.
- Package-manager calls such as `npm install`, `pip`, `uv add`, `bun install`, or `curl | sh`.
- Git commands, especially `reset`, `checkout`, `clean`, branch deletion, or force push.
- Filesystem writes outside the current project.

## 4. Network And Credential Risk

- Identify all URLs, API calls, telemetry endpoints, and upload paths.
- Flag automatic reads of `.env`, shell profiles, credentials, tokens, or cloud config.
- Require explicit user action for write-capable vendor operations.
- Reject skills that persist credentials or transmit source data without clear disclosure.
- Ensure examples redact secret values and avoid encouraging token pasting into logs.

## 5. Dedupe And Fit

- Compare against repo-owned skills first.
- Compare against global installed skills second.
- Promote only when the candidate adds a distinct domain, vendor workflow, or better retrieval surface.
- Keep personal workflow or credential-heavy deployment skills global-only.
- Build locally when the registry concept is useful but sources are weak or too broad.

## 6. Decision Template

| Outcome | Use When |
|---|---|
| `install now` | Trust gate passes and the skill fills a clear gap |
| `inspect then install` | Candidate is useful but scripts/provenance/credential behavior needs review |
| `keep global only` | Useful but duplicate, personal, or operational |
| `build locally` | External options are low-trust, stale, broad, or platform-specific |
| `avoid/duplicate` | Unsafe, source-conflicted, stale, or redundant |
