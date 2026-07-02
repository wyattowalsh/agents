"""Tests for MCPHub settings validation collector."""

from __future__ import annotations

from pathlib import Path

from scripts.validate.collectors.mcphub_settings import collect_mcphub_settings_errors


def test_collect_mcphub_settings_errors_passes_on_current_repo():
    repo_root = Path(__file__).resolve().parents[1]
    errors = collect_mcphub_settings_errors(repo_root)
    assert errors == []