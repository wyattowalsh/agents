---
name: discover-skills
description: >-
  Discover new AI agent skills via deep audit, multi-source web research, and
  gap-driven ideation. Orchestrates a Pattern E team to audit existing skills,
  search skills.sh/GitHub/blogs/HN, and propose custom skills to fill gaps.
  Use when expanding your skill collection. NOT for creating skills
  (skill-creator) or installing known skills (npx skills add).
argument-hint: "[mode] [query]"
model: opus
license: MIT
metadata:
  author: wyattowalsh
  version: "1.0.0"
hooks:
  PreToolUse:
    - matcher: Edit
      hooks:
        - command: 'bash -c "echo BLOCKED: discover-skills is read-only — no file edits permitted >&2; exit 1"'
---

# Discover Skills

Systematic skill discovery engine. Audits your existing skill collection, identifies coverage gaps, researches new skills across multiple sources, and proposes custom skills to build — all via an orchestrated team of specialized subagents.

NOT for: ad-hoc "find me a skill for X" queries (use `vercel-labs/skills@find-skills`), creating skills (`/skill-creator`), or installing known skills (`npx skills add`).

## Dispatch

| `$ARGUMENTS` | Action |
|------------|--------|
| *(empty)* / `discover` | **Full discovery**: audit → research → ideate → interactive report |
| `audit` | **Audit only**: deep audit of existing skills, output gap analysis |
| `research [focus]` | **Research only**: web research, optionally focused on a domain |
| `ideate` | **Ideate only**: propose custom skills from prior audit/research |
| `resume [N or keyword]` | **Resume**: continue a saved discovery session |
| `list` | **List**: show saved discovery sessions |
| `install <owner/repo@skill>` | **Install**: install a previously discovered skill with confirmation |

### Auto-Detection Heuristic

If no mode keyword matches:

1. Domain name alone ("frontend", "testing") → **Research** focused on that domain
2. Question syntax ("what skills am I missing?") → **Full discovery**
3. `resume` or `continue` → **Resume** last active session
4. Ambiguous → ask: "Full discovery, focused research, or resume a prior session?"

### Skill Awareness

| Signal | Redirect |
|--------|----------|
| "Find me a skill for X" (ad-hoc query) | Suggest `npx skills find <query>` or `vercel-labs/skills@find-skills` |
| "Create a new skill" | Redirect to `/skill-creator` |
| "Install X skill" (known skill) | Run `npx skills add <source> -s <name> -g -y -a antigravity claude-code codex crush cursor gemini-cli github-copilot opencode` directly |

## Vocabulary

| Term | Definition |
|------|-----------|
| **gap** | A domain or capability with no existing skill coverage |
| **coverage** | Score (None/Low/Medium/Good) of existing skill depth per domain |
| **domain** | A category of skill functionality (e.g., Testing, Frontend, Security) |
| **candidate** | An external skill discovered during research, not yet installed |
| **proposal** | A custom skill idea with spec sketch, not yet created |
| **journal** | A saved discovery session in `~/.claude/discover-skills/` |
| **auditor** | Teammate that reads and categorizes all existing skills |
| **registry-scout** | Teammate that searches skills.sh via `npx skills find` |
| **web-researcher** | Teammate that searches GitHub, blogs, HN, Reddit |
| **ideator** | Teammate that synthesizes gaps + research into proposals |

## Orchestration: Pattern E Team

```
Lead (orchestrate + synthesize + present interactive report)
  ├── auditor
  │     Wave 1a: parallel subagents read repo skills (skills/*/SKILL.md)
  │     Wave 1b: read installed skills (~/.claude/skills/ + installed.mdx)
  │     → domain taxonomy, coverage scores, gap report (JSON)
  │
  ├── registry-scout
  │     Wave 2a: 15-20 parallel `npx skills find <query>` subagents
  │              (queries from references/research-queries.md, targeted by gap report)
  │     Wave 2b: deduplicate against existing skills
  │     → ranked external skill candidates with install commands
  │
  ├── web-researcher
  │     Wave 2a: parallel subagents across sources:
  │       - brave-search for "AI agent skills" + domain keywords
  │       - GitHub search for skill repos (SKILL.md in:path)
  │       - Community: Reddit, HN, dev.to, blog posts
  │     Wave 2b: fetch + extract promising leads
  │     → skill ideas from the web not on the registry
  │
  └── ideator
        Wave 3: synthesize gaps + all research findings
        → spec sketches (name, description, use cases, scope, complexity)
```

### Wave Sequencing

```
Wave 1: auditor (produces gap report needed by Wave 2)
    ↓ gap report shared via lead
Wave 2: registry-scout + web-researcher (parallel, both use gap report)
    ↓ all findings shared via lead
Wave 3: ideator (synthesizes everything into proposals)
    ↓ all outputs to lead
Wave 4: lead synthesizes interactive report (inline)
```

**Dependency rule**: Wave N+1 cannot start until all Wave N agents are accounted for (Accounting Rule: N dispatched = N resolved).

### Teammate Model

All teammates and their nested subagents use `opus`. No downgrades.

### Mode-Specific Orchestration

| Mode | Teammates Used | Waves |
|------|---------------|-------|
| Full discovery | All 4 | 1 → 2 → 3 → 4 |
| Audit only | auditor | 1 only |
| Research [focus] | registry-scout + web-researcher | 2 only (with focus filter) |
| Ideate | ideator | 3 only (requires prior audit/research in journal) |

## Quality Verification

Before recommending any external skill:

| Signal | Threshold | Below threshold |
|--------|-----------|-----------------|
| Install count | >= 500 preferred | Move to "Worth Investigating" tier |
| Source reputation | Official repos preferred | Flag unknown authors |
| Duplication | Must not overlap existing skill | Exclude or note as "alternative to X" |
| Recency | Updated within 6 months | Flag as potentially stale |

**Confidence tiers**:
- **High**: >= 1K installs + reputable source + fills clear gap
- **Medium**: 100-999 installs or less-known source but fills gap
- **Investigate**: < 100 installs or unclear quality, but interesting concept

## Interactive Report Format

```markdown
## Discovery Report — {date}

### Coverage Summary
| Domain | Existing Skills | Coverage | Gaps |
|--------|----------------|----------|------|

### A. External Skills to Install ({N} found)

#### High Confidence
| # | Skill | Source | Installs | Install Command | Fills Gap |
|---|-------|--------|----------|-----------------|-----------|

#### Worth Investigating
| # | Skill | Source | URL | Notes |
|---|-------|--------|-----|-------|

### B. Custom Skills to Create ({N} proposals)
| # | Name | Description | Use Cases | NOT For | Complexity |
|---|------|-------------|-----------|---------|------------|

> Pick numbers to install (A) or create (B), or type "all A" / "all B".
```

After the user picks:
- **Install**: run `npx skills add <source> -s <name> -g -y -a antigravity claude-code codex crush cursor gemini-cli github-copilot opencode`
- **Create**: surface the command `wagents new skill <name>` and suggest running `/skill-creator create <name>`

## State Management

- **Path**: `~/.claude/discover-skills/`
- **Filename**: `{YYYY-MM-DD}-discovery-{slug}.md`
- **Format**: YAML frontmatter + markdown body + `<!-- STATE -->` blocks
- **Tracks**: `discovered_external`, `discovered_custom`, `installed`, `rejected`
- **Script**: `!uv run python skills/discover-skills/scripts/journal-store.py`

**Save protocol**:
- Audit only: save once after gap report
- Full discovery: save after each wave; final save after report
- Resume: load prior journal, check for new skills since last run

**Resume protocol**:
1. `resume` (no args): find `status: In Progress` journals. One → auto-resume. Multiple → show list.
2. `resume N`: Nth journal from `list` output.
3. `resume keyword`: search frontmatter for match.

## Critical Rules

1. **Never install without confirmation** — always present the report and wait for user selection
2. **Audit before research** — gap report drives query targeting; skip only if mode is `research [focus]`
3. **Deduplicate against inventory** — never recommend skills that duplicate existing coverage
4. **Full install command** — always include: `npx skills add <source> -s <name> -g -y -a antigravity claude-code codex crush cursor gemini-cli github-copilot opencode`
5. **NOT-for exclusions** — custom skill proposals must name existing skills they do NOT replace
6. **Save after each wave** — enables resume on interruption
7. **Accounting Rule** — N dispatched = N resolved before advancing to next wave
8. **Read-only** — PreToolUse Edit hook blocks file edits; only writes journals via script
9. **Verify quality** — check install count, source reputation, recency before recommending
10. **Deduplicate across sources** — same skill may appear in registry, GitHub, and blog posts

## Reference File Index

| File | Content | Load When |
|------|---------|-----------|
| `references/research-queries.md` | 42+ validated registry queries, GitHub/web/community search patterns, known-good repos | Wave 2 (before dispatching research teammates) |
| `references/gap-analysis.md` | 18-domain taxonomy, coverage scoring rubric, gap priority formula | Wave 1 (during audit), Wave 4 (building coverage summary) |
| `references/team-templates.md` | Full spawn prompts for all 4 teammates with role, input, output, quality checks | Wave 0 (before spawning team) |
| `references/output-formats.md` | Full report template, install command template, spec sketch template, journal format | Wave 4 (formatting output) |

**Loading rule**: Load ONE reference at a time per the "Load When" column. Do not preload.
