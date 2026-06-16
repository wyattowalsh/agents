"""Tests for portable path leak detection in wagents.repo_paths."""

import pytest

from wagents.repo_paths import contains_portable_path_leak


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Use ~/projects/agents for local work.", False),
        ("Path: /Users/alice/dev/agents/skills/foo", True),
        ("Path: /home/bob/projects/agents", True),
        ("Windows: C:\\Users\\alice\\projects", True),
        ("Portable: ${REPO_ROOT}/skills/demo", False),
        ("", False),
    ],
)
def test_contains_portable_path_leak(text: str, expected: bool):
    assert contains_portable_path_leak(text) is expected
