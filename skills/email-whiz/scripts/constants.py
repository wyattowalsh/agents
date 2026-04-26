"""Shared constants for email-whiz scripts."""

import os
from pathlib import Path


def get_agent_dir(skill_name: str) -> Path:
    """Get the base directory for a skill based on the active agent."""
    agent = os.environ.get("AGENT_NAME", "").lower()
    for cli, folder in [("GEMINI_CLI", ".gemini"), ("COPILOT_CLI", ".copilot"), ("CODEX_CLI", ".codex")]:
        if os.environ.get(cli) == "1" or folder.strip(".") in agent:
            return Path.home() / folder / skill_name
    return Path.home() / ".claude" / skill_name


EMAIL_WHIZ_DIR = str(get_agent_dir("email-whiz"))
