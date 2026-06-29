"""Tests for wagents docs score heuristics."""

from __future__ import annotations

from wagents.docs_score import score_docs_surface, score_mdx_page, write_score_manifest


def test_score_mdx_page_rates_structured_page(tmp_repo, monkeypatch):
    import wagents.docs_score as score_mod

    monkeypatch.setattr(score_mod, "ROOT", tmp_repo)
    monkeypatch.setattr(score_mod, "CONTENT_DIR", tmp_repo / "docs" / "src" / "content" / "docs")

    mdx = score_mod.CONTENT_DIR / "agents" / "sample.mdx"
    mdx.parent.mkdir(parents=True, exist_ok=True)
    mdx.write_text(
        """---
title: Sample
description: Long description for the docs quality scorer: complete, informative, and suitable for readers browsing the agents catalog surface today.
---
import { LinkCard, Badge } from '@astrojs/starlight/components';

## What It Does

Use when validating docs.

```bash
wagents validate
```

See [Agents](/agents/) and [Skills](/skills/catalog/).
""",
        encoding="utf-8",
    )

    result = score_mdx_page(mdx)
    assert result.dimensions["description"] >= 4
    assert result.dimensions["usage_examples"] >= 4
    assert result.average >= 2.5


def test_score_docs_surface_respects_limit(tmp_repo, monkeypatch):
    import wagents.docs_score as score_mod

    monkeypatch.setattr(score_mod, "ROOT", tmp_repo)
    monkeypatch.setattr(score_mod, "CONTENT_DIR", tmp_repo / "docs" / "src" / "content" / "docs")

    content = score_mod.CONTENT_DIR / "mcp"
    content.mkdir(parents=True, exist_ok=True)
    for name in ("alpha.mdx", "beta.mdx"):
        (content / name).write_text(
            f"---\ntitle: {name}\ndescription: MCP stub page for scoring tests.\n---\n\n## Overview\n",
            encoding="utf-8",
        )

    scores = score_docs_surface(surface="mcp", limit=1)
    assert len(scores) == 1


def test_write_score_manifest_writes_json(tmp_repo, monkeypatch):
    import wagents.docs_score as score_mod

    monkeypatch.setattr(score_mod, "ROOT", tmp_repo)
    monkeypatch.setattr(score_mod, "CONTENT_DIR", tmp_repo / "docs" / "src" / "content" / "docs")

    mdx = score_mod.CONTENT_DIR / "hooks" / "sample.mdx"
    mdx.parent.mkdir(parents=True, exist_ok=True)
    mdx.write_text(
        "---\ntitle: Hook\ndescription: Hook docs page for manifest write test.\n---\n\n## Usage\n",
        encoding="utf-8",
    )
    scores = score_docs_surface(surface="hooks", limit=5)
    manifest = write_score_manifest(scores)
    assert manifest.exists()
    payload = manifest.read_text(encoding="utf-8")
    assert '"page_count"' in payload
