"""Dry-run tests for scripts/curated_catalog_enrichment_wave.py ."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_wave_module():
    path = ROOT / "scripts" / "curated_catalog_enrichment_wave.py"
    spec = importlib.util.spec_from_file_location("curated_enrichment_wave", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_wave_dry_run_writes_w0_w1_w2_artifacts(tmp_path, monkeypatch):
    wave = _load_wave_module()

    # patch REPO so artifacts land in tmp
    monkeypatch.setattr(wave, "REPO", tmp_path)

    # stub the wagents reads/seeds so no fs side effects outside tmp
    from wagents.external_skills import ExternalSkillEntry

    def fake_entries():
        return [
            ExternalSkillEntry(
                name="alpha-skill",
                source="demo/alpha",
                install_source="demo/alpha",
                status="install-now-after-trust-gate",
                trust_tier="low",
                provenance_status="verified-install-command",
                install_command="npx ... alpha-skill",
                target_agents=("claude-code",),
                source_url="",
                notes="alpha",
            ),
            ExternalSkillEntry(
                name="beta-skill",
                source="demo/beta",
                install_source="demo/beta",
                status="install-now-after-trust-gate",
                trust_tier="low",
                provenance_status="verified-install-command",
                install_command="npx ... beta-skill",
                target_agents=("opencode",),
                source_url="",
                notes="beta",
            ),
        ]

    monkeypatch.setattr("wagents.external_skills.read_external_skill_entries", fake_entries)
    monkeypatch.setattr(
        "wagents.skill_research.seed_curated_config_research",
        lambda **kw: [],
    )

    # also stub collect/partition used in W2 to avoid full catalog load
    from wagents.catalog import CatalogNode
    from wagents.skill_docs import SkillDocNode

    def _fake_doc(name: str, src: str = "demo/alpha") -> SkillDocNode:
        return SkillDocNode(
            node=CatalogNode(
                kind="skill",
                id=name,
                title=name,
                description="d",
                metadata={"_skills_install_source": src},
                body="",
                source_path="",
                source="curated-external",
            ),
            source_type="curated-external",
            curated_status="install-now-after-trust-gate",
        )

    monkeypatch.setattr(
        "wagents.skill_docs.collect_skill_doc_nodes",
        lambda **kw: [_fake_doc("alpha-skill"), _fake_doc("beta-skill", "demo/beta")],
    )
    # ensure partition sees our curated
    # (real partition will group by source now)

    # since main() does parser.parse_args() from sys, patch sys.argv
    import sys

    old_argv = sys.argv[:]
    try:
        sys.argv = ["curated_catalog_enrichment_wave.py", "--session", "test-wave-dry", "--dry-run", "--batch-max", "2"]
        rc = wave.main()
    finally:
        sys.argv = old_argv

    assert rc == 0
    sess = tmp_path / "artifacts" / "test-wave-dry"
    assert (sess / "wave0" / "curated-inventory.json").exists()
    w0 = json.loads((sess / "wave0" / "curated-inventory.json").read_text())
    assert w0["count"] == 2
    assert (sess / "wave1" / "seed-plan.json").exists()
    assert (sess / "wave2" / "batches.json").exists()
    w2 = json.loads((sess / "wave2" / "batches.json").read_text())
    assert w2["total_batches"] >= 1
    wave2_md = list((sess / "wave2").glob("batch-*.md"))
    assert wave2_md or (sess / "wave2" / "batch-01.md").exists()


def test_wave_respects_curated_status_filter(tmp_path, monkeypatch):
    wave = _load_wave_module()
    monkeypatch.setattr(wave, "REPO", tmp_path)

    from wagents.external_skills import ExternalSkillEntry

    def fake_entries():
        return [
            ExternalSkillEntry("keep", "s/k", "s/k", "install-now-after-trust-gate", "l", "v", "", (), "", "n", ""),
            ExternalSkillEntry("skip", "s/s", "s/s", "inspect-then-install", "l", "v", "", (), "", "n", ""),
        ]

    monkeypatch.setattr("wagents.external_skills.read_external_skill_entries", fake_entries)
    monkeypatch.setattr("wagents.skill_research.seed_curated_config_research", lambda **kw: [])

    import sys

    old = sys.argv[:]
    try:
        sys.argv = ["x", "--session", "test-filt", "--dry-run", "--curated-status", "install-now-after-trust-gate"]
        rc = wave.main()
    finally:
        sys.argv = old

    assert rc == 0
    w0 = json.loads((tmp_path / "artifacts" / "test-filt" / "wave0" / "curated-inventory.json").read_text())
    assert w0["count"] == 1
    assert w0["rows"][0]["name"] == "keep"
