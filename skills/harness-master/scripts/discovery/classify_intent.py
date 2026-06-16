#!/usr/bin/env python3
"""Classify harness-master $ARGUMENTS into explicit intent/mode, harnesses, level, and tokens.

Implements the Classification Gate and Logic from harness-master/SKILL.md.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from typing import Any

SUPPORTED_HARNESSES = [
    "claude-code",
    "claude-desktop",
    "chatgpt",
    "codex",
    "github-copilot-web",
    "github-copilot-cli",
    "cursor",
    "gemini-cli",
    "antigravity",
    "grok-build",
    "opencode",
    "perplexity-desktop",
    "cherry-studio",
]

HARNESS_ALIASES: dict[str, list[str]] = {
    "claude": ["claude-code"],
    "claude-code": ["claude-code"],
    "claude-desktop": ["claude-desktop"],
    "chatgpt": ["chatgpt"],
    "chatgpt-desktop": ["chatgpt"],
    "openai-chatgpt": ["chatgpt"],
    "codex": ["codex"],
    "cursor": ["cursor"],
    "cursor-agent": ["cursor"],
    "cursor-editor": ["cursor"],
    "cursor-desktop": ["cursor"],
    "cursor-cli": ["cursor"],
    "agent-cli": ["cursor"],
    "cursor-cloud": ["cursor"],
    "cursor-cloud-agent": ["cursor"],
    "cursor-background-agent": ["cursor"],
    "cursor-web": ["cursor"],
    "gemini": ["gemini-cli"],
    "gemini-cli": ["gemini-cli"],
    "antigravity": ["antigravity"],
    "google-antigravity": ["antigravity"],
    "github-copilot": ["github-copilot-web", "github-copilot-cli"],
    "copilot": ["github-copilot-web", "github-copilot-cli"],
    "gh-copilot": ["github-copilot-web", "github-copilot-cli"],
    "github-copilot-web": ["github-copilot-web"],
    "copilot-web": ["github-copilot-web"],
    "copilot-cloud": ["github-copilot-web"],
    "copilot-coding-agent": ["github-copilot-web"],
    "github-copilot-cli": ["github-copilot-cli"],
    "copilot-cli": ["github-copilot-cli"],
    "grok": ["grok-build"],
    "grok-build": ["grok-build"],
    "grok-cli": ["grok-build"],
    "opencode": ["opencode"],
    "open-code": ["opencode"],
    "perplexity": ["perplexity-desktop"],
    "perplexity-desktop": ["perplexity-desktop"],
    "perplexity-mac": ["perplexity-desktop"],
    "cherry": ["cherry-studio"],
    "cherrystudio": ["cherry-studio"],
    "cherry-ai": ["cherry-studio"],
    "cherry-studio": ["cherry-studio"],
}

LEVEL_ALIASES: dict[str, str] = {
    "project": "project",
    "repo": "project",
    "local": "project",
    "global": "global",
    "user": "global",
    "both": "both",
    "all-levels": "both",
}

# Legacy CLI tokens map to unified discover mode + depth.
DISCOVER_ALIASES: dict[str, str] = {
    "research": "focused",
    "candidate": "candidate",
    "compare": "compare",
    "sources": "sources",
}

OTHER_EXPLICIT_MODES = {
    "usage": "usage",
    "install": "install",
    "apply": "apply",
}

DETERMINISTIC_ALL_ORDER = [
    "claude-code",
    "claude-desktop",
    "chatgpt",
    "codex",
    "github-copilot-web",
    "github-copilot-cli",
    "cursor",
    "gemini-cli",
    "antigravity",
    "grok-build",
    "opencode",
    "perplexity-desktop",
    "cherry-studio",
]


@dataclass
class Classification:
    mode: str  # audit | discover | usage | install | apply | intake | clarify | refuse
    discover_depth: str | None = None  # full | focused | candidate | compare | w0only | journal | sources
    harnesses: list[str] = field(default_factory=list)
    level: str | None = None
    tokens: list[str] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)
    is_all: bool = False
    raw: str = ""
    notes: list[str] = field(default_factory=list)


def _normalize_token(t: str) -> str:
    t = t.strip().lower().replace("_", "-")
    return t


def _resolve_harness(token: str) -> list[str]:
    t = _normalize_token(token)
    if t in HARNESS_ALIASES:
        return list(HARNESS_ALIASES[t])
    if t in SUPPORTED_HARNESSES:
        return [t]
    return []


def _resolve_level(token: str) -> str | None:
    t = _normalize_token(token)
    return LEVEL_ALIASES.get(t)


def _split_tokens(argstr: str) -> list[str]:
    if not argstr:
        return []
    parts = re.split(r"[\s,]+", argstr.strip())
    return [p for p in parts if p]


def _dedupe_harnesses(harnesses: list[str]) -> list[str]:
    seen: set[str] = set()
    return [h for h in harnesses if not (h in seen or seen.add(h))]


def _collect_harness_level(
    tokens: list[str],
) -> tuple[list[str], str | None, list[str], bool]:
    harnesses: list[str] = []
    level: str | None = None
    unresolved: list[str] = []
    is_all = False
    for tok in tokens:
        if tok == "all":
            is_all = True
            continue
        h = _resolve_harness(tok)
        if h:
            harnesses.extend(h)
            continue
        lvl = _resolve_level(tok)
        if lvl:
            level = lvl
            continue
        unresolved.append(tok)
    return _dedupe_harnesses(harnesses), level, unresolved, is_all


def _infer_discover_depth_from_discover_tokens(remaining: list[str]) -> str:
    norm = {_normalize_token(t) for t in remaining}
    if norm & {"resume", "list"}:
        return "journal"
    if norm & {"audit", "gaps", "w0", "w0only"}:
        return "w0only"
    if norm & {"ideate", "proposals"}:
        return "ideate"
    return "full"


def _set_discover(cls: Classification, depth: str, remaining: list[str]) -> None:
    cls.mode = "discover"
    cls.discover_depth = depth
    harnesses, level, unresolved, is_all = _collect_harness_level(remaining)
    cls.harnesses = harnesses
    cls.level = level
    cls.unresolved = unresolved
    cls.is_all = is_all


def classify_intent(argstr: str | None) -> dict[str, Any]:
    """Return classification dict for the given argument string."""
    raw = (argstr or "").strip()
    tokens = _split_tokens(raw)
    norm_tokens = [_normalize_token(t) for t in tokens]

    cls = Classification(mode="audit", raw=raw, tokens=tokens)

    if not tokens:
        cls.mode = "intake"
        cls.notes.append("empty args -> ask for harnesses or all, then level")
        return _as_dict(cls)

    explicit_found: list[tuple[int, str]] = []
    for i, t in enumerate(norm_tokens):
        if t in DISCOVER_ALIASES or t == "discover" or t in OTHER_EXPLICIT_MODES:
            explicit_found.append((i, t))

    if explicit_found:
        idx, mode_tok = explicit_found[0]
        remaining = [tok for j, tok in enumerate(norm_tokens) if j != idx]

        if mode_tok == "discover":
            depth = _infer_discover_depth_from_discover_tokens(remaining)
            _set_discover(cls, depth, remaining)
            return _as_dict(cls)

        if mode_tok in DISCOVER_ALIASES:
            _set_discover(cls, DISCOVER_ALIASES[mode_tok], remaining)
            return _as_dict(cls)

        cls.mode = OTHER_EXPLICIT_MODES[mode_tok]
        harnesses, level, unresolved, is_all = _collect_harness_level(remaining)
        cls.harnesses = harnesses
        cls.level = level
        cls.unresolved = unresolved
        cls.is_all = is_all
        return _as_dict(cls)

    harnesses, level, unresolved, is_all = _collect_harness_level(norm_tokens)
    lower_raw = raw.lower()

    if "apply approved" in lower_raw or lower_raw.startswith("approved") or "do it" in lower_raw:
        cls.mode = "apply"

    for tok in norm_tokens:
        if tok in ("approved", "apply"):
            cls.mode = "apply"

    if is_all and harnesses:
        unresolved = ["all+named"] + unresolved

    cls.harnesses = harnesses
    cls.level = level
    cls.unresolved = [u for u in unresolved if u]
    cls.is_all = is_all

    nl = lower_raw
    if cls.mode == "audit":
        if any(k in nl for k in ("usage", "cost", "token", "quota", "usage/cost")):
            cls.mode = "usage"
        elif any(k in nl for k in ("missing", "expand", "what skills", "gap")):
            cls.mode = "discover"
            cls.discover_depth = "full"
        elif any(k in nl for k in ("find", "latest", "best", "plugins", "ecosystem", "research")):
            cls.mode = "discover"
            cls.discover_depth = "focused"

    if cls.mode == "apply":
        pass
    elif unresolved and not harnesses and not level and not is_all and cls.mode == "audit":
        cls.mode = "clarify"
    elif not harnesses and is_all:
        cls.harnesses = list(DETERMINISTIC_ALL_ORDER)
        cls.is_all = True
    elif cls.mode == "audit" and not harnesses and not is_all:
        cls.mode = "intake"

    return _as_dict(cls)


def _as_dict(cls: Classification) -> dict[str, Any]:
    return {
        "mode": cls.mode,
        "discover_depth": cls.discover_depth,
        "harnesses": cls.harnesses,
        "level": cls.level,
        "tokens": cls.tokens,
        "unresolved": cls.unresolved,
        "is_all": cls.is_all,
        "raw": cls.raw,
        "notes": cls.notes,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Classify harness-master intent from arguments string.")
    parser.add_argument("args", nargs="*", help="Argument tokens (or pass as single quoted string)")
    parser.add_argument("--args", dest="args_string", help="Full argument string (alternative to positional tokens)")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parsed = parser.parse_args(argv)
    argstr = (
        parsed.args_string
        if parsed.args_string is not None
        else (" ".join(parsed.args) if parsed.args else "")
    )
    result = classify_intent(argstr)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())