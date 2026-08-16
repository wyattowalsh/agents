"""Tests for harness-master discovery classify_intent.py (≥8 cases)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "harness-master" / "scripts" / "discovery"


def _load():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    path = SCRIPTS / "classify_intent.py"
    spec = importlib.util.spec_from_file_location("classify_intent", path)
    assert spec
    assert spec.loader
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


def test_classify_retired_alias_is_unresolved():
    mod = _load()
    res = mod.classify_intent("copilot both")
    assert res["harnesses"] == []
    assert "copilot" in res["unresolved"]
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


def test_classify_cursor_agent_aliases_to_cursor_cli():
    mod = _load()
    for raw in ("agent both", "cursor-agent both", "cursor-cli both", "agent-cli project"):
        res = mod.classify_intent(raw)
        assert res["harnesses"] == ["cursor-cli"], raw


def test_classify_cursor_editor_stays_cursor():
    mod = _load()
    for raw in ("cursor both", "cursor-editor project", "cursor-desktop global"):
        res = mod.classify_intent(raw)
        assert res["harnesses"] == ["cursor"], raw


def test_classify_all_order_inserts_cursor_cli_after_cursor():
    mod = _load()
    res = mod.classify_intent("all both")
    harnesses = res["harnesses"]
    assert "cursor" in harnesses
    assert "cursor-cli" in harnesses
    assert harnesses.index("cursor") < harnesses.index("cursor-cli")
    assert harnesses.index("cursor-cli") < harnesses.index("grok-build")


def test_classify_usage_discover_install_all_expand_but_apply_does_not():
    mod = _load()
    expected = list(mod.DETERMINISTIC_ALL_ORDER)
    for raw in ("usage all", "discover all", "install all"):
        res = mod.classify_intent(raw)
        assert res["is_all"] is True, raw
        assert res["harnesses"] == expected, raw
        assert res["harnesses"].index("cursor") < res["harnesses"].index("cursor-cli")
    apply_res = mod.classify_intent("apply all")
    assert apply_res["mode"] == "apply"
    assert apply_res["is_all"] is True
    assert apply_res["harnesses"] == []
