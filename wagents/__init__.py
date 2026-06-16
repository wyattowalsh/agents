"""CLI for managing centralized AI agent assets."""

import importlib.metadata
import re
from pathlib import Path

from wagents.context import resolve_repo_root

_discovered = resolve_repo_root()
ROOT = _discovered if _discovered is not None else Path(__file__).resolve().parent.parent
VERSION = importlib.metadata.version("wagents")
KEBAB_CASE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
GITHUB_BASE = "https://github.com/wyattowalsh/agents/blob/main"
DOCS_DIR = ROOT / "docs"
CONTENT_DIR = DOCS_DIR / "src" / "content" / "docs"