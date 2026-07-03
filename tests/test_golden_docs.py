"""Golden snapshot tests for committed docs generator outputs."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_DIR = Path(__file__).resolve().parent / "fixtures" / "golden" / "docs"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_site_data_counts(text: str) -> dict[str, int]:
    match = re.search(r'"counts"\s*:\s*(\{[^}]+\})', text, flags=re.DOTALL)
    assert match is not None, "generated-site-data.mjs missing counts block"
    return json.loads(match.group(1))


class TestGoldenSidebar:
    def test_committed_sidebar_matches_golden(self) -> None:
        live = REPO_ROOT / "docs" / "src" / "generated-sidebar.mjs"
        golden = GOLDEN_DIR / "generated-sidebar.mjs"
        assert live.is_file(), "committed generated-sidebar.mjs is missing"
        assert golden.is_file(), "golden sidebar fixture is missing"
        assert _read_text(live) == _read_text(golden)

    def test_sidebar_structure_markers(self) -> None:
        text = _read_text(REPO_ROOT / "docs" / "src" / "generated-sidebar.mjs")
        for marker in (
            "export const navLinks",
            "export default",
            "Overview",
            "Surfaces",
            "Runtimes",
            "skills/catalog/custom",
            "skills/catalog/external",
            "{ label: 'Overview', link: '/' }",
        ):
            assert marker in text


class TestGoldenSiteData:
    def test_counts_match_golden(self) -> None:
        live_path = REPO_ROOT / "docs" / "src" / "generated-site-data.mjs"
        golden_path = GOLDEN_DIR / "generated-site-data-counts.json"
        live_counts = _extract_site_data_counts(_read_text(live_path))
        golden_counts = json.loads(golden_path.read_text(encoding="utf-8"))
        assert live_counts == golden_counts

    @pytest.mark.parametrize(
        "key",
        [
            "bundledAgents",
            "customMcp",
            "customSkills",
            "externalMcp",
            "externalSkills",
            "mcpTools",
            "skills",
            "supportedHarnesses",
        ],
    )
    def test_count_keys_are_positive_integers(self, key: str) -> None:
        live_path = REPO_ROOT / "docs" / "src" / "generated-site-data.mjs"
        counts = _extract_site_data_counts(_read_text(live_path))
        assert key in counts
        assert isinstance(counts[key], int)
        assert counts[key] >= 0


class TestGoldenCatalogIndex:
    def test_catalog_index_shape(self) -> None:
        index_path = REPO_ROOT / "docs" / "public" / "generated-registries" / "skills-catalog-index.json"
        shape_path = GOLDEN_DIR / "skills-catalog-index-shape.json"
        payload = json.loads(index_path.read_text(encoding="utf-8"))
        shape = json.loads(shape_path.read_text(encoding="utf-8"))

        for key in shape["required_top_level_keys"]:
            assert key in payload, f"missing top-level key: {key}"

        assert isinstance(payload["allSkillIndex"], list)
        assert isinstance(payload["customSkillIndex"], list)
        assert isinstance(payload["externalSkillIndex"], list)
        assert len(payload["allSkillIndex"]) >= len(payload["customSkillIndex"])
