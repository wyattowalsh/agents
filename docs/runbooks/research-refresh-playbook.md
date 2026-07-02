# Research Refresh Playbook

Guidance for same-day source verification, source prioritization, confidence
labeling, and research-basis hygiene when updating research-heavy skills or a
local research backlog (fast-moving areas: MCP auth/spec revisions, agent
platform guidance, GitHub Actions security).

## When to refresh

- Before implementing anything tagged with research more than ~30 days old,
  re-verify at least the primary sources for that item.
- Before starting a new wave of a multi-week program (see
  `openspec/changes/*/design.md` "research refresh" tasks) — fast-moving
  areas can shift meaningfully within weeks.
- When a source URL 404s or its content structure changed enough that cited
  line/section references no longer resolve.

## Source prioritization order

1. **Primary vendor docs** (e.g., `modelcontextprotocol.io`, GitHub's own
   Actions/security docs, `docs.astral.sh` for `uv`/`ruff`/`ty`) — highest
   trust, check first.
2. **`llms.txt` / `llms-full.txt`** for the vendor's docs domain, per the
   Docs Lookup resolution order in `instructions/global.md`.
3. **Official changelogs / release notes** for the specific tool/library
   version in use.
4. **Secondary community sources** (blog posts, third-party guides) — use
   only to corroborate primary sources, never as the sole basis for an
   implementation decision.

## Confidence labeling

Use the same `Impact` / `Effort` / `Confidence` triage tags as a research
backlog when recording refreshed findings:

- `Confidence=H` — verified directly against current primary-source docs
  within the last refresh cycle.
- `Confidence=M` — verified against primary docs, but the docs are ambiguous
  or the feature is marked experimental/preview.
- `Confidence=L` — inferred from indirect evidence (issue threads, secondary
  blog posts) without a primary-source citation; flag explicitly and prefer
  asking before implementing.

## Refresh checklist

- [ ] Re-fetch each cited "Research Basis" URL; confirm it still resolves and
      still supports the claim it was cited for.
- [ ] Note the refresh date next to any claim whose supporting source
      changed materially.
- [ ] Downgrade `Confidence` for any item whose primary source could not be
      re-verified.
- [ ] Cross-reference related topic files before starting implementation
      (e.g., an MCP-related item should be checked against both an MCP
      backlog file and an infra/security backlog file) to avoid duplicate or
      conflicting guidance.
- [ ] For OpenSpec programs, record refresh evidence in that change's
      `design.md` or `tasks.md` research-refresh task rather than only in
      local scratch notes.

## Non-goals

- This playbook does not replace `/research` for open-ended technical
  investigation — it is specifically about keeping already-recorded
  backlog/research claims current before they're implemented.
- Do not promote local, gitignored research notes into tracked git as part of
  a refresh; track implementation status via OpenSpec changes instead.
