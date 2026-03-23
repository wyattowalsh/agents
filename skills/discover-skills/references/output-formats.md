# Output Formats Reference

Templates for discovery reports, install commands, spec sketches, and journal entries.

---

## 1. Interactive Report Template

```markdown
## Discovery Report — {YYYY-MM-DD}

**Session**: {journal_filename}
**Skills audited**: {total_skills} ({repo_count} repo + {installed_count} installed)
**Domains scanned**: {domain_count}
**Gaps identified**: {gap_count}

### Coverage Summary

| Domain | Existing Skills | Coverage | Gaps |
|--------|----------------|----------|------|
| {domain} | {skill_list} | {score} | {gap_list} |

### A. External Skills to Install ({total_candidates} found)

#### High Confidence ({high_count})
| # | Skill | Source | Installs | Install Command | Fills Gap |
|---|-------|--------|----------|-----------------|-----------|
| {n} | {name} | {repo} | {count} | `npx skills add {source} -s {name} -g -y -a antigravity claude-code codex crush cursor gemini-cli github-copilot opencode` | {gap} |

#### Medium Confidence ({medium_count})
| # | Skill | Source | Installs | Install Command | Fills Gap |
|---|-------|--------|----------|-----------------|-----------|

#### Worth Investigating ({investigate_count})
| # | Skill | Source | URL | Notes |
|---|-------|--------|-----|-------|

### B. Custom Skills to Create ({proposal_count} proposals)

| # | Name | Description | Use Cases | NOT For | Complexity |
|---|------|-------------|-----------|---------|------------|
| {n} | {name} | {desc} | {cases} | {not_for} | {complexity} |

---

> **Actions**: Pick numbers to install (A) or create (B).
> Type `A1, A3, A5` to install specific skills, `all A` for all external, or `B2` to create a custom skill.
> Type `save` to save this session for later.
```

---

## 2. Install Command Templates

Single skill:

```bash
npx skills add {owner}/{repo} -s {skill_name} -g -y -a antigravity claude-code codex crush cursor gemini-cli github-copilot opencode
```

Multiple skills from same repo:

```bash
npx skills add {owner}/{repo} -s {skill1} -s {skill2} -g -y -a antigravity claude-code codex crush cursor gemini-cli github-copilot opencode
```

---

## 3. Spec Sketch Template

Output of ideator for custom skill proposals:

```markdown
### {name}

**Description**: {CSO-optimized description with "Use when" and "NOT for"}

**Use Cases**:
1. {case_1}
2. {case_2}
3. {case_3}

**Scope**:
- IS for: {scope_in}
- NOT for: {scope_out} ({existing_skill_names})

**Estimated Complexity**: {low|medium|high}
- low: single-mode, no scripts, 1-2 references
- medium: 2-3 modes, 1-2 scripts, 2-4 references
- high: 4+ modes, scripts + templates, 4+ references

**Notes**: {any relevant context, similar external skills, structural references}

**Create**: `wagents new skill {name}` then `/skill-creator create {name}`
```

---

## 4. Journal Format

YAML frontmatter + markdown body + STATE blocks:

```markdown
---
session_type: discovery
status: In Progress
created: {ISO timestamp}
updated: {ISO timestamp}
total_skills_audited: {N}
gap_count: {N}
candidates_found: {N}
proposals_made: {N}
installed: []
rejected: []
---

# Discovery Session — {date}

## Gap Report
{gap report summary}

## External Candidates
{candidate list}

## Custom Proposals
{proposal list}

<!-- STATE
wave_completed: 2
candidates_found: 30
proposals_made: 5
next_action: "Wave 3: ideator synthesizing proposals"
-->
```

### Journal STATUS Values

| Status | Meaning |
|--------|---------|
| `In Progress` | Active session, waves still running |
| `Paused` | User typed `save`, resume later |
| `Complete` | All actions taken or deferred |

### STATE Block Convention

Append `<!-- STATE -->` HTML comments at end of journal. Agents parse last STATE block to resume mid-session. Fields are freeform but should include `wave_completed`, `candidates_found`, `proposals_made`, and `next_action`.
