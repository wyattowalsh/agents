# Packaging Guide

How to package skills into portable ZIP files for distribution.

## Contents

1. [ZIP Structure](#zip-structure)
2. [Manifest Schema](#manifest-schema)
3. [Portability Checklist](#portability-checklist)
4. [Cross-Agent Compatibility](#cross-agent-compatibility)
5. [Import Instructions](#import-instructions)

---

## ZIP Structure

Each skill packages as `<name>-v<version>.skill.zip`:

```
<name>-v<version>.skill.zip
└── <name>/
    ├── SKILL.md          ← Skill definition (frontmatter + body)
    ├── manifest.json     ← Auto-generated repo tooling metadata
    ├── references/       ← Deep knowledge (if exists)
    ├── scripts/          ← Executable tools (if exists)
    ├── templates/        ← HTML/file templates (if exists)
    ├── assets/           ← Bundled binary/static files (if exists)
    ├── evals/            ← Test cases (if exists)
    ├── reports/          ← Explicitly referenced report files only
    └── ...               ← Any other non-excluded skill files
```

Excluded automatically: `__pycache__/`, `.DS_Store`, `*.pyc`, `*.tmp`, `.git/`, and unreferenced `reports/` files.

`reports/` is for repo-local audit output and packaging evidence. A `reports/...` file is packaged only when `SKILL.md` explicitly references that exact file path. Unreferenced report files still appear in `files_excluded` during dry runs so reviewers can see what was intentionally left out.

## Manifest Schema

Auto-generated `manifest.json` (repo tooling, not part of the public skill spec):

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Skill name from frontmatter |
| `version` | string | From `metadata.version` (default: `"0.0.0"`) |
| `description` | string | From frontmatter description |
| `license` | string | SPDX identifier from frontmatter |
| `author` | string | From `metadata.author` |
| `files` | string[] | Relative paths of all included files |
| `created_at` | string | ISO 8601 timestamp |
| `packaged_by` | string | Always `"package.py"` |

When `package.py --all` generates the top-level repo-tooling manifest, each entry stays visible even if packaging is blocked, but `zip` is `null` unless the archive was actually emitted in that run.

## Portability Checklist

Nine checks run before packaging. Packaging is fail-closed by default: `--dry-run` exits non-zero on failures, and real packaging refuses to emit a ZIP unless `--force` is provided.

| Check | What It Verifies | Fix |
|-------|-----------------|-----|
| `required_name` | `name` field populated | Add `name: <directory-name>` |
| `required_description` | `description` field populated | Add a real CSO-optimized description |
| `frontmatter_license` | `license` field populated | Add `license: MIT` (or appropriate SPDX) |
| `frontmatter_author` | `metadata.author` populated | Add `metadata.author: your-name` |
| `frontmatter_version` | `metadata.version` populated | Add `metadata.version: "1.0.0"` |
| `no_absolute_paths` | No `/Users/`, `/home/`, `/tmp/` paths in body | Use relative paths or environment variables |
| `referenced_files_exist` | All packaged `references/`, `scripts/`, `templates/`, `assets/`, and explicit `reports/` paths mentioned in body resolve to files | Create missing files or remove stale references |
| `no_at_imports` | No `@path` imports in body | Remove repo-specific imports |
| `name_directory_match` | Frontmatter `name` matches directory name | Align name field with directory |

Use `--dry-run` to check portability without creating ZIPs. Use `--force` only when you explicitly accept portability drift for a one-off package.

## Cross-Agent Compatibility

Skills packaged with this system work across agents that support the agentskills.io spec:

| Agent | Import Method | Notes |
|-------|--------------|-------|
| Claude Code | Unzip to `~/.{gemini|copilot|codex|claude}/skills/` | Archive root already contains `<name>/`; full support including hooks |
| Claude Code Desktop | Import via skill manager | Reads `manifest.json` for metadata |
| Gemini CLI | Unzip to project `skills/` | Archive root already contains `<name>/`; reads SKILL.md body only |
| Codex / Cursor | Unzip or vendor the `<name>/` directory into the project's skill/instruction path | Reads SKILL.md as markdown instructions |
| OpenCode | Prefer `opencode.json` + `.opencode/skills/<name>/` or `skills.paths` | Native AGENTS.md support; can also read compatible skill locations like `.agents/skills/` and `.claude/skills/` |

## Import Instructions

**Manual install:**
```bash
unzip <name>-v<version>.skill.zip -d ~/.{gemini|copilot|codex|claude}/skills/
```

**Via npx (if published):**
```bash
npx skills add <source> --skill <name> -y -g --agent claude-code --agent codex --agent gemini-cli --agent antigravity --agent github-copilot --agent opencode
```

**Via package script:**
```bash
# Strict dry-run (no ZIP emitted)
uv run python skills/skill-creator/scripts/package.py skills/<name> --dry-run --format table

# Force packaging despite portability failures
uv run python skills/skill-creator/scripts/package.py skills/<name> --force

# Check every skill
uv run python skills/skill-creator/scripts/package.py --all --dry-run --format table
```

Cross-references: `scripts/package.py`, `scripts/audit.py` (portability dimension).
