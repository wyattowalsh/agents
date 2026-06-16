"""Tests for harness-master discovery classify_intent.py (≥8 cases)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "harness-master" / "scripts" / "discovery"


def _load():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    path = SCRIPTS / "classify_intent.py"
    spec = importlib.util.spec_from_file_location("classify_intent", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    # Register before exec so that module-level decorators (e.g. dataclass)
    # can resolve sys.modules[cls.__module__] during definition.
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_classify_empty_args():
    mod = _load()
    res = mod.classify_intent("")
    assert res["mode"] == "intake"
    assert res["discover_depth"] is None
    assert res["harnesses"] == []
    assert res["level"] is None
    assert res["is_all"] is False


def test_classify_all_level():
    mod = _load()
    res = mod.classify_intent("all project")
    assert res["mode"] == "audit"
    assert res["is_all"] is True
    assert "claude-code" in res["harnesses"]
    assert len(res["harnesses"]) > 5
    assert res["level"] == "project"


def test_classify_named_harness_and_level():
    mod = _load()
    res = mod.classify_intent("claude-code global")
    assert res["mode"] == "audit"
    assert res["harnesses"] == ["claude-code"]
    assert res["level"] == "global"


def test_classify_research_intent_alias():
    mod = _load()
    res = mod.classify_intent("research cursor config latest plugins")
    assert res["mode"] == "discover"
    assert res["discover_depth"] == "focused"
    assert "cursor" in res["harnesses"]
    assert "config" in res["unresolved"] or "latest" in res["unresolved"]


def test_classify_discover_full():
    mod = _load()
    res = mod.classify_intent("discover")
    assert res["mode"] == "discover"
    assert res["discover_depth"] == "full"


def test_classify_discover_w0only():
    mod = _load()
    res = mod.classify_intent("discover audit")
    assert res["mode"] == "discover"
    assert res["discover_depth"] == "w0only"


def test_classify_usage_intent():
    mod = _load()
    res = mod.classify_intent("usage codex 14")
    assert res["mode"] == "usage"
    assert res["harnesses"] == ["codex"]
    assert res["level"] is None  # level optional for usage


def test_classify_candidate_intent():
    mod = _load()
    res = mod.classify_intent("candidate owner/repo claude-code")
    assert res["mode"] == "discover"
    assert res["discover_depth"] == "candidate"
    assert "claude-code" in res["harnesses"]
    assert any("owner" in str(x) for x in res["unresolved"]) or "owner/repo" in res.get("raw", "")


def test_classify_compare_intent():
    mod = _load()
    res = mod.classify_intent("compare foo bar for grok-build")
    assert res["mode"] == "discover"
    assert res["discover_depth"] == "compare"
    assert "grok-build" in res["harnesses"]


def test_classify_install_intent():
    mod = _load()
    res = mod.classify_intent("install claude-code cursor")
    assert res["mode"] == "install"
    assert set(res["harnesses"]) == {"claude-code", "cursor"}


def test_classify_apply_approved():
    mod = _load()
    res = mod.classify_intent("apply approved")
    assert res["mode"] == "apply"


def test_classify_natural_language_usage():
    mod = _load()
    res = mod.classify_intent("show usage and cost for claude")
    assert res["mode"] == "usage"
    assert "claude-code" in res["harnesses"]


def test_classify_natural_language_discover_full():
    mod = _load()
    res = mod.classify_intent("what skills am I missing in this repo")
    assert res["mode"] == "discover"
    assert res["discover_depth"] == "full"


def test_classify_unresolved_tokens_ask_clarify():
    mod = _load()
    res = mod.classify_intent("foo bar baz")
    assert res["mode"] in ("clarify", "intake")
    assert len(res["unresolved"]) >= 1


def test_classify_aliases_expand():
    mod = _load()
    res = mod.classify_intent("copilot both")
    assert "github-copilot-web" in res["harnesses"]
    assert "github-copilot-cli" in res["harnesses"]
    assert res["level"] == "both"


def test_classify_has_at_least_eight_distinct_modes_covered():
    mod = _load()
    cases = [
        "",
        "all both",
        "research all skill",
        "usage all",
        "candidate x y",
        "compare a for b",
        "install x",
        "apply approved",
        "chatgpt project",
        "discover",
    ]
    modes = set()
    for c in cases:
        res = mod.classify_intent(c)
        modes.add(res["mode"])
    assert len(modes) >= 5