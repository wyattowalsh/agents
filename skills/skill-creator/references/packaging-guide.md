# Packaging Guide

How to package skills into portable ZIP files for distribution and Claude Code Desktop import.

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
├── SKILL.md              ← Skill definition (frontmatter + body)
├── manifest.json         ← Auto-generated: name, version, files, timestamp
├── references/           ← Deep knowledge (if exists)
├── scripts/              ← Executable tools (if exists)
├── templates/            ← HTML/file templates (if exists)
└── evals/                ← Test cases (if exists)
```

Excluded automatically: `__pycache__/`, `.DS_Store`, `*.pyc`, `*.tmp`, `.git/`.

## Manifest Schema

Auto-generated `manifest.json`:

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

## Portability Checklist

Seven checks run before packaging. All must pass for a clean build:

| Check | What It Verifies | Fix |
|-------|-----------------|-----|
| `frontmatter_license` | `license` field populated | Add `license: MIT` (or appropriate SPDX) |
| `frontmatter_author` | `metadata.author` populated | Add `metadata.author: your-name` |
| `frontmatter_version` | `metadata.version` populated | Add `metadata.version: "1.0.0"` |
| `no_absolute_paths` | No `/Users/`, `/home/`, `/tmp/` paths in body | Use relative paths or environment variables |
| `reference_files_exist` | All `references/X` mentions resolve to files | Create missing files or remove stale references |
| `no_at_imports` | No `@path` imports in body | Remove repo-specific imports |
| `name_directory_match` | Frontmatter `name` matches directory name | Align name field with directory |

Use `--dry-run` to check portability without creating ZIPs.

## Cross-Agent Compatibility

Skills packaged with this system work across agents that support the agentskills.io spec:

| Agent | Import Method | Notes |
|-------|--------------|-------|
| Claude Code | Unzip to `~/.claude/skills/<name>/` | Full support including hooks |
| Claude Code Desktop | Import via skill manager | Reads `manifest.json` for metadata |
| Gemini CLI | Unzip to project `skills/` | Reads SKILL.md body only |
| Codex / Cursor / OpenCode | Unzip to project root | Reads SKILL.md as markdown instructions |

## Import Instructions

**Manual install:**
```bash
unzip <name>-v<version>.skill.zip -d ~/.claude/skills/<name>/
```

**Via npx (if published):**
```bash
npx skills add <source> --skill <name> -y -g
```

**Via wagents CLI:**
```bash
# Package a single skill
wagents package <name>

# Package all skills
wagents package --all

# Dry-run (check portability only)
wagents package --all --dry-run
```

Cross-references: `scripts/package.py`, `scripts/audit.py` (portability dimension).
