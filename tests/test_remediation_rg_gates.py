"""Regression gates for session-review closeout (no follow_redirects / secret dumps)."""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_no_follow_redirects_true_in_source_url_health() -> None:
    root = REPO / "mcp" / "source-url-health"
    for path in root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "follow_redirects=True" not in text, f"{path} still auto-follows redirects"
        assert "status >= 405" not in text, f"{path} still uses broad GET fallback"
        # Insecure TypeError strip of Host/SNI must not reappear.
        if path.name == "server.py":
            assert "except TypeError:" not in text or "rejected pin kwargs" in text


def test_local_values_true_only_on_allowlisted_sites() -> None:
    """Secret env materialization sites must stay False; baseURL carve-out is allowlisted."""
    allow_patterns = (
        re.compile(r"resolve_local_llm_base_url\([^)]*local_values=True"),
        re.compile(r"baseURL.*local_values=True", re.S),
    )
    paths = [
        REPO / "scripts" / "sync_agent_stack.py",
        REPO / "wagents" / "platforms" / "opencode.py",
        REPO / "wagents" / "platforms" / "base.py",
    ]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            if "local_values=True" not in line:
                continue
            # Allow only baseURL / resolve_local_llm_base_url lines
            window = "\n".join(text.splitlines()[max(0, i - 3) : i + 1])
            if any(p.search(window) for p in allow_patterns) or "baseURL" in window or "resolve_local_llm" in window:
                continue
            raise AssertionError(f"{path}:{i} unexpected local_values=True: {line.strip()}")


def test_secret_basename_literals_only_in_ssot() -> None:
    ssot = REPO / "wagents" / "hooks" / "policies" / "secret_paths.py"
    assert ssot.is_file()
    # Hook must not redefine full SECRET_BASENAMES table
    hook = (REPO / "hooks" / "wagents-hook.py").read_text(encoding="utf-8")
    assert "SECRET_BASENAMES = {" not in hook


def test_orchestrator_profiler_frontmatter_has_no_bash_tool() -> None:
    for rel in ("agents/orchestrator.md", "agents/performance-profiler.md"):
        text = (REPO / rel).read_text(encoding="utf-8")
        # tools line must not include Bash as a tool allow
        m = re.search(r"^tools:\s*(.+)$", text, re.M)
        assert m, rel
        assert "Bash" not in m.group(1)


def test_opencode_projected_agents_deny_bash() -> None:
    for rel in (
        ".opencode/agents/orchestrator.md",
        ".opencode/agents/performance-profiler.md",
    ):
        path = REPO / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        assert re.search(r"(?m)^\s*bash:\s*deny\s*$", text), f"{rel} should set bash: deny"


def test_secret_paths_ssot_shared_by_policy_and_hook() -> None:
    from wagents.hooks.policies.protected_file_guard import evaluate_protected_file
    from wagents.hooks.policies.secret_paths import is_secret_basename

    assert is_secret_basename(".env.mcphub")
    assert evaluate_protected_file(".env.mcphub")
    assert evaluate_protected_file("id_rsa")
    assert evaluate_protected_file(".env.example") is None
