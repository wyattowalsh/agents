"""Tests for harness-master discovery merge_artifacts.py."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "harness-master" / "scripts" / "discovery"


def _load():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    path = SCRIPTS / "merge_artifacts.py"
    spec = importlib.util.spec_from_file_location("merge_artifacts", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_tier_from_installs() -> None:
    mod = _load()
    assert mod.tier_from_installs(1500) == "high"
    assert mod.tier_from_installs(500) == "medium"
    assert mod.tier_from_installs(10) == "investigate"
    assert mod.tier_from_installs(None) == "investigate"


def test_merge_candidates_dedup_and_existing_filter(tmp_path: Path) -> None:
    mod = _load()
    artifacts = tmp_path / "wave2"
    artifacts.mkdir()
    (artifacts / "W2-RS-00.json").write_text(
        json.dumps(
            {
                "task_id": "W2-RS-00",
                "role": "registry-scout",
                "status": "success",
                "candidates": [
                    {
                        "name": "redis-cache",
                        "source": "owner/redis-skills",
                        "install_count": 1200,
                        "fills_gap": "caching",
                    },
                    {
                        "name": "honest-review",
                        "source": "wyattowalsh/agents",
                        "install_count": 50,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    (artifacts / "W2-RS-01.json").write_text(
        json.dumps(
            {
                "task_id": "W2-RS-01",
                "role": "registry-scout",
                "status": "success",
                "candidates": [
                    {
                        "name": "redis-cache",
                        "source": "owner/redis-skills",
                        "install_count": 800,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = mod.merge_candidates(
        artifacts,
        existing_names={"honest-review"},
        agents=["codex", "cursor"],
    )

    assert result["total"] == 1
    assert result["errors"] == []
    high = result["tiers"]["high"]
    assert len(high) == 1
    assert high[0]["name"] == "redis-cache"
    assert high[0]["install_count"] == 1200
    assert "-a codex" in high[0]["install_command"]
    assert "-a cursor" in high[0]["install_command"]