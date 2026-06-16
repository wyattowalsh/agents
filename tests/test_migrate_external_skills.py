"""Tests for scripts/migrate_external_skills_to_authoring_mdx.py using tmp paths."""

from __future__ import annotations

from pathlib import Path

import pytest

# Import the migration function; script is executable but exposes the function for tests.
from scripts.migrate_external_skills_to_authoring_mdx import (
    migrate_external_skills_to_authoring_mdx,
)
from wagents.external_skills import ExternalSkillEntry, parse_external_skill_entries
from wagents.parsing import parse_frontmatter


@pytest.fixture
def sample_curated_entries() -> list[ExternalSkillEntry]:
    md = """
## Install Now After Trust Gate

```bash
npx skills add acme/tools --skill alpha --skill beta -y -g -a claude-code codex
```

## Inspect Then Install

```bash
npx skills add example/other --skill gamma -y -g -a claude-code
```
"""
    return parse_external_skill_entries(md)


def test_migrate_writes_one_mdx_per_entry_with_curated_fields(
    tmp_path: Path, sample_curated_entries: list[ExternalSkillEntry]
):
    auth = tmp_path / "authoring" / "skills"
    targets = migrate_external_skills_to_authoring_mdx(authoring_dir=auth, entries=sample_curated_entries)
    assert len(targets) == 3  # alpha, beta, gamma
    names = {t.stem for t in targets}
    assert names == {"alpha", "beta", "gamma"}

    # Inspect one
    p = auth / "alpha.mdx"
    assert p.exists()
    fm, body = parse_frontmatter(p.read_text(encoding="utf-8"))
    assert fm["name"] == "alpha"
    assert fm["source_kind"] == "curated-external"
    assert fm.get("source") == "acme/tools"
    assert "npx skills add acme/tools" in fm.get("install_command", "")
    assert "Install Now" in (fm.get("status") or "") or fm.get("status") == "install-now-after-trust-gate"
    # Body contains generated marker
    assert "GENERATED-AUTHORING" in body
    assert "config/external-skills.md" in body or "entry=alpha" in body


def test_migrate_dry_run_does_not_write(tmp_path: Path, sample_curated_entries: list[ExternalSkillEntry]):
    auth = tmp_path / "a2"
    targets = migrate_external_skills_to_authoring_mdx(authoring_dir=auth, entries=sample_curated_entries, dry_run=True)
    assert len(targets) == 3
    for t in targets:
        assert not t.exists()


def test_migrate_from_parsed_markdown_text(tmp_path: Path):
    md = """
## Keep Global Only Or Avoid

- `avoid/skills@bad-one`: risky, do not promote.
"""
    entries = parse_external_skill_entries(md)
    auth = tmp_path / "a3"
    targets = migrate_external_skills_to_authoring_mdx(authoring_dir=auth, entries=entries)
    assert len(targets) == 1
    fm, _ = parse_frontmatter((auth / "bad-one.mdx").read_text(encoding="utf-8"))
    assert fm["name"] == "bad-one"
    assert fm["source_kind"] == "curated-external"
    assert fm.get("status") == "global-only-or-avoid"
