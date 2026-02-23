"""Shared utilities for skill-creator scripts."""
from __future__ import annotations

import re
import sys

import yaml


def _warn(msg: str) -> None:
    print(f"[skill-creator] {msg}", file=sys.stderr)


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML between --- delimiters and the body text below."""
    if not content.startswith("---"):
        return {}, content
    m = re.search(r'\n---\s*\n', content[3:])
    if m is None:
        return {}, content
    end = 3 + m.start() + 1  # +1 for the leading \n
    try:
        fm = yaml.safe_load(content[3:end].strip())
        if not isinstance(fm, dict):
            fm = {}
    except yaml.YAMLError as exc:
        _warn(f"YAML parse error: {exc}")
        fm = {}
    return fm, content[end + 3:].strip()
