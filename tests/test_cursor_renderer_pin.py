"""Cursor agent renderer defaults model to cursor-grok-4.5-high."""

from __future__ import annotations

import yaml

from wagents.platforms import cursor as cursor_platform
from wagents.platforms.cursor import (
    CURSOR_DEFAULT_MODEL,
    CURSOR_MANAGED_AGENT_MARKER,
    _render_cursor_agent,
    _render_cursor_agents,
)


def test_cursor_default_model_constant_is_grok_high() -> None:
    assert CURSOR_DEFAULT_MODEL == "cursor-grok-4.5-high"


def test_render_cursor_agent_defaults_model_when_overlay_omits_model(tmp_path) -> None:
    agent_path = tmp_path / "sample-agent.md"
    agent_path.write_text(
        "---\nname: sample-agent\ndescription: Sample agent for pin tests.\n---\n\nBody.\n",
        encoding="utf-8",
    )
    overlay = {
        "name": "sample-agent",
        "description": "Overlay description",
        "readonly": False,
    }

    rendered = _render_cursor_agent(agent_path, overlay)
    data = yaml.safe_load(rendered.split("---\n", 2)[1])

    assert data["model"] == "cursor-grok-4.5-high"
    assert data["model"] == CURSOR_DEFAULT_MODEL
    assert CURSOR_MANAGED_AGENT_MARKER in rendered


def test_render_cursor_agent_ignores_overlay_fast_model(tmp_path) -> None:
    agent_path = tmp_path / "sample-agent.md"
    agent_path.write_text(
        "---\nname: sample-agent\ndescription: Sample agent for pin tests.\n---\n\nBody.\n",
        encoding="utf-8",
    )
    overlay = {
        "name": "sample-agent",
        "description": "Overlay description",
        "model": "cursor-grok-4.5-fast",
        "readonly": False,
    }

    rendered = _render_cursor_agent(agent_path, overlay)
    data = yaml.safe_load(rendered.split("---\n", 2)[1])

    assert data["model"] == CURSOR_DEFAULT_MODEL
    assert data["model"] == "cursor-grok-4.5-high"


def test_render_cursor_agent_ignores_overlay_inherit_model(tmp_path) -> None:
    agent_path = tmp_path / "sample-agent.md"
    agent_path.write_text(
        "---\nname: sample-agent\ndescription: Sample agent for pin tests.\n---\n\nBody.\n",
        encoding="utf-8",
    )
    overlay = {
        "name": "sample-agent",
        "description": "Overlay description",
        "model": "inherit",
        "readonly": False,
    }

    rendered = _render_cursor_agent(agent_path, overlay)
    data = yaml.safe_load(rendered.split("---\n", 2)[1])

    assert data["model"] == CURSOR_DEFAULT_MODEL
    assert data["model"] == "cursor-grok-4.5-high"


def test_render_cursor_agents_defaults_model_when_overlay_omits_model(
    tmp_path,
    monkeypatch,
) -> None:
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    agent_path = agents_dir / "pin-demo.md"
    agent_path.write_text(
        "---\nname: pin-demo\ndescription: Portable agent body.\n---\n\nDo the work.\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(cursor_platform, "_portable_agent_files", lambda: [agent_path])
    monkeypatch.setattr(
        cursor_platform,
        "_load_cursor_agent_overlays",
        lambda: {
            "pin-demo": {
                "name": "pin-demo",
                "description": "Demo without model key",
                "readonly": True,
            }
        },
    )

    rendered = _render_cursor_agents()
    assert set(rendered) == {"pin-demo.md"}
    data = yaml.safe_load(rendered["pin-demo.md"].split("---\n", 2)[1])
    assert data["model"] == "cursor-grok-4.5-high"
    assert data["readonly"] is True
