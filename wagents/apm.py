"""APM materialize: project repo SSOT (agents/, instructions/, config/*-registry) into .apm/ layout.

Produces consumable primitives for Microsoft APM (agent package manager).
"""

from __future__ import annotations

import contextlib
import json
from typing import TYPE_CHECKING, Any

import yaml

from wagents.parsing import parse_frontmatter

if TYPE_CHECKING:
    from pathlib import Path

# Marker comments used to update the mcp section of apm.yml without clobbering other content.
MCP_BEGIN = "# BEGIN WAGENTS-MCP: managed by `uv run wagents apm materialize` -- edit config/mcp-registry.json"
MCP_END = "# END WAGENTS-MCP"


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _write_text_if_changed(target: Path, content: str, *, check: bool = False) -> bool:
    """Write if content differs (or missing). Return True if would-write or wrote."""
    if check:
        if target.exists():
            try:
                return target.read_text(encoding="utf-8") != content
            except OSError:
                return True
        return True
    _ensure_dir(target.parent)
    target.write_text(content, encoding="utf-8")
    return True


def _clean_stale(dir_path: Path, live_names: set[str], *, check: bool = False) -> list[Path]:
    touched: list[Path] = []
    if not dir_path.exists():
        return touched
    for p in sorted(dir_path.iterdir()):
        if p.is_file() and p.name not in live_names:
            if check:
                touched.append(p)
            else:
                with contextlib.suppress(OSError):
                    p.unlink()
                touched.append(p)
    return touched


def materialize_agents(repo_root: Path, *, check: bool = False) -> list[Path]:
    """Convert agents/*.md (excluding README) into .apm/agents/*.agent.md.

    Maps name/description/tools (and any other scalar frontmatter we preserve) into
    the APM .agent.md frontmatter convention. Body is preserved verbatim.
    """
    agents_src = repo_root / "agents"
    apm_agents = repo_root / ".apm" / "agents"
    written: list[Path] = []
    if not agents_src.exists():
        return written

    live: set[str] = set()
    for src in sorted(agents_src.glob("*.md")):
        if src.name == "README.md":
            continue
        try:
            fm, body = parse_frontmatter(src.read_text(encoding="utf-8"))
        except Exception:
            # Skip malformed; real validate will catch
            continue
        name = str(fm.get("name") or src.stem)
        live.add(f"{name}.agent.md")

        apm_fm: dict[str, Any] = {
            "name": name,
            "description": fm.get("description", ""),
        }
        # Map tools if present (string or list form tolerated by APM consumers)
        if "tools" in fm and fm["tools"] not in (None, ""):
            apm_fm["tools"] = fm["tools"]
        # Pass through a few other portable agent keys when present
        for k in ("disallowedTools", "model", "permissionMode", "maxTurns", "memory"):
            if k in fm and fm[k] not in (None, ""):
                apm_fm[k] = fm[k]

        fm_block = "---\n" + yaml.safe_dump(apm_fm, sort_keys=False, allow_unicode=False).strip() + "\n---\n"
        content = fm_block + ("\n" + body.strip() + "\n" if body and body.strip() else "\n")
        target = apm_agents / f"{name}.agent.md"
        if _write_text_if_changed(target, content, check=check):
            written.append(target)

    # Remove stale generated
    stale = _clean_stale(apm_agents, live, check=check)
    written.extend(stale)
    return sorted(set(written))


def _parse_claude_rule(path: Path) -> tuple[list[str], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return [], text
    _, frontmatter, body = text.split("---\n", 2)
    patterns: list[str] = []
    for line in frontmatter.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            patterns.append(stripped[2:].strip().strip('"'))
    return patterns, body.lstrip()


def _is_path_scoped_rule(patterns: list[str]) -> bool:
    if not patterns:
        return False
    return not (len(patterns) == 1 and patterns[0] == "**/*")


def materialize_scoped_rules(repo_root: Path, *, check: bool = False) -> list[Path]:
    """Project path-scoped .claude/rules/*.md into .apm/instructions/*.instructions.md."""
    rules_dir = repo_root / ".claude" / "rules"
    dst_dir = repo_root / ".apm" / "instructions"
    written: list[Path] = []
    if not rules_dir.exists():
        return written

    live: set[str] = set()
    for rule_path in sorted(rules_dir.glob("*.md")):
        patterns, body = _parse_claude_rule(rule_path)
        if not _is_path_scoped_rule(patterns):
            continue
        dst_name = f"{rule_path.stem}.instructions.md"
        live.add(dst_name)
        apply_to = ",".join(patterns) if patterns else "**/*"
        fm = {
            "description": f"Path-scoped rule: {rule_path.name}",
            "applyTo": apply_to,
        }
        content = (
            "---\n"
            + yaml.safe_dump(fm, sort_keys=False, allow_unicode=False).strip()
            + "\n---\n\n"
            + (body.strip() + "\n" if body.strip() else "\n")
        )
        tgt = dst_dir / dst_name
        if _write_text_if_changed(tgt, content, check=check):
            written.append(tgt)

    overlay_names = {
        "global.instructions.md",
        "claude-code.instructions.md",
        "codex.instructions.md",
        "copilot.instructions.md",
        "gemini-cli.instructions.md",
        "grok.instructions.md",
        "opencode.instructions.md",
        "opencode-agents-overlay.instructions.md",
    }
    if dst_dir.exists():
        for dst in sorted(dst_dir.glob("*.instructions.md")):
            if dst.name in overlay_names or dst.name in live:
                continue
            rule_stem = dst.name.removesuffix(".instructions.md")
            rule_path = rules_dir / f"{rule_stem}.md"
            if rule_path.exists():
                patterns, _ = _parse_claude_rule(rule_path)
                if _is_path_scoped_rule(patterns):
                    continue
            if check:
                written.append(dst)
            else:
                with contextlib.suppress(OSError):
                    dst.unlink()
                written.append(dst)
    return sorted(set(written))


def _resolve_global_body(root: Path) -> str:
    """Return global.md content. For overlays we keep simple (no deep @ resolve here)."""
    gm = root / "instructions" / "global.md"
    if not gm.exists():
        return ""
    return gm.read_text(encoding="utf-8").rstrip() + "\n"


def materialize_instructions(repo_root: Path, *, check: bool = False) -> list[Path]:
    """Convert instructions/global.md + platform overlays into .apm/instructions/*.instructions.md .

    Each gets a minimal frontmatter with description + applyTo glob.
    Global applies broadly; overlays are emitted as their own files (consumers pick).
    """
    src_dir = repo_root / "instructions"
    dst_dir = repo_root / ".apm" / "instructions"
    written: list[Path] = []
    if not src_dir.exists():
        return written

    # Global (always-on)
    global_src = src_dir / "global.md"
    if global_src.exists():
        body = global_src.read_text(encoding="utf-8")
        fm = {"description": "Global cross-platform AI agent instructions", "applyTo": "**/*"}
        content = "---\n" + yaml.safe_dump(fm, sort_keys=False, allow_unicode=False).strip() + "\n---\n\n" + body
        tgt = dst_dir / "global.instructions.md"
        if _write_text_if_changed(tgt, content, check=check):
            written.append(tgt)

    # Platform overlays (emit even shims so apm can surface platform-specific guidance)
    overlays: list[tuple[str, str, str]] = [
        ("claude-code-global.md", "claude-code.instructions.md", "**/*"),
        ("codex-global.md", "codex.instructions.md", "**/*"),
        ("copilot-global.md", "copilot.instructions.md", "**/*"),
        ("gemini-cli-global.md", "gemini-cli.instructions.md", "**/*"),
        ("grok-global.md", "grok.instructions.md", "**/*"),
        ("opencode-global.md", "opencode.instructions.md", "**/*"),
        ("opencode-agents-overlay.md", "opencode-agents-overlay.instructions.md", "**/*"),
    ]
    for src_name, dst_name, apply_glob in overlays:
        p = src_dir / src_name
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        # Strip leading @import lines for apm (APM loads the .instructions.md directly)
        lines = [ln for ln in text.splitlines() if not ln.strip().startswith("@./instructions/")]
        body = "\n".join(lines).strip() + "\n" if lines else ""
        fm = {
            "description": f"Platform overlay: {src_name}",
            "applyTo": apply_glob,
        }
        content = "---\n" + yaml.safe_dump(fm, sort_keys=False, allow_unicode=False).strip() + "\n---\n\n" + body
        tgt = dst_dir / dst_name
        if _write_text_if_changed(tgt, content, check=check):
            written.append(tgt)

    # No broad stale clean for instructions (they are additive name set)
    return sorted(set(written))


def _enabled_hooks_for_harness(registry: dict[str, Any], harness: str) -> list[dict[str, Any]]:
    hooks = registry.get("hooks", [])
    if not isinstance(hooks, list):
        return []
    return [h for h in hooks if isinstance(h, dict) and h.get("command") and harness in set(h.get("harnesses", []))]


def _render_claude_hooks_shape(registry: dict[str, Any]) -> dict[str, Any]:
    """Return Claude hooks shape consumed under .apm/hooks/."""
    # Shape: { "hooks": { "Event": [ { "matcher"?, "hooks": [ {"type":"command", ...} ] } ] } }
    event_map = {
        "SessionStart": "SessionStart",
        "UserPromptSubmit": "UserPromptSubmit",
        "PreToolUse": "PreToolUse",
        "PostToolUse": "PostToolUse",
        "Stop": "Stop",
        "PermissionRequest": "PermissionRequest",
    }
    rendered: dict[str, list[dict[str, Any]]] = {}
    for h in _enabled_hooks_for_harness(registry, "claude-code"):
        ev = event_map.get(str(h.get("logical_event", "")))
        if not ev:
            continue
        cmd = str(h["command"]).format(repo_root=".", harness="claude-code")
        entry = {"type": "command", "command": cmd}
        if h.get("timeout"):
            entry["timeout"] = int(h["timeout"])
        group: dict[str, Any] = {"hooks": [entry]}
        if h.get("matcher"):
            group["matcher"] = h["matcher"]
        rendered.setdefault(ev, []).append(group)
    return {"hooks": rendered} if rendered else {"hooks": {}}


def _render_cursor_hooks_shape(registry: dict[str, Any]) -> dict[str, Any]:
    """Cursor shape similar to copilot but with cursor event names."""
    event_map = {
        "SessionStart": "sessionStart",
        "UserPromptSubmit": "beforeSubmitPrompt",
        "PreToolUse": "preToolUse",
        "PostToolUse": "postToolUse",
        "Stop": "stop",
        "SessionEnd": "sessionEnd",
    }
    rendered: dict[str, list[dict[str, Any]]] = {}
    for h in _enabled_hooks_for_harness(registry, "cursor"):
        ev = event_map.get(str(h.get("logical_event", "")))
        if not ev:
            continue
        cmd = str(h["command"]).format(repo_root="${workspaceFolder}", harness="cursor")
        entry: dict[str, Any] = {"type": "command", "command": cmd}
        if h.get("timeout"):
            entry["timeout"] = int(h["timeout"])
        if h.get("mode") == "enforce" and ev.startswith("pre"):
            entry["failClosed"] = True
        group: dict[str, Any] = {"hooks": [entry]}
        if h.get("matcher"):
            group["matcher"] = h["matcher"]
        rendered.setdefault(ev, []).append(group)
    return {"version": 1, "hooks": rendered} if rendered else {"version": 1, "hooks": {}}


def _render_copilot_hooks_shape(registry: dict[str, Any]) -> dict[str, Any]:
    event_map = {
        "SessionStart": "sessionStart",
        "UserPromptSubmit": "userPromptSubmitted",
        "PreToolUse": "preToolUse",
        "PostToolUse": "postToolUse",
        "SessionEnd": "sessionEnd",
    }
    rendered: dict[str, list[dict[str, Any]]] = {}
    for h in _enabled_hooks_for_harness(registry, "github-copilot"):
        ev = event_map.get(str(h.get("logical_event", "")))
        if not ev:
            continue
        cmd = str(h["command"]).format(repo_root=".", harness="github-copilot")
        entry: dict[str, Any] = {
            "type": "command",
            "bash": cmd,
            "cwd": ".",
            "timeoutSec": int(h.get("timeout", 5)),
            "comment": h.get("description", h.get("id", "")),
        }
        rendered.setdefault(ev, []).append(entry)
    return {"version": int(registry.get("version", 1)), "hooks": rendered}


def materialize_hooks(repo_root: Path, *, check: bool = False) -> list[Path]:
    """Emit .apm/hooks/*.json for claude/cursor/copilot using shapes from hook-registry.json."""
    reg_path = repo_root / "config" / "hook-registry.json"
    if not reg_path.exists():
        return []
    try:
        registry = json.loads(reg_path.read_text(encoding="utf-8"))
    except Exception:
        return []

    dst = repo_root / ".apm" / "hooks"
    written: list[Path] = []

    # Claude
    claude = _render_claude_hooks_shape(registry)
    if claude.get("hooks"):
        tgt = dst / "claude-code.json"
        content = json.dumps(claude, indent=2) + "\n"
        if _write_text_if_changed(tgt, content, check=check):
            written.append(tgt)

    # Cursor
    cursor = _render_cursor_hooks_shape(registry)
    if cursor.get("hooks"):
        tgt = dst / "cursor.json"
        content = json.dumps(cursor, indent=2) + "\n"
        if _write_text_if_changed(tgt, content, check=check):
            written.append(tgt)

    # Copilot (github-copilot)
    cop = _render_copilot_hooks_shape(registry)
    if cop.get("hooks"):
        tgt = dst / "github-copilot.json"
        content = json.dumps(cop, indent=2) + "\n"
        if _write_text_if_changed(tgt, content, check=check):
            written.append(tgt)

    return sorted(set(written))


def _render_mcp_yaml_fragment(fragment: list[dict[str, Any]]) -> str:
    if not fragment:
        return "  mcp: []\n"
    dumped = yaml.safe_dump(fragment, sort_keys=False, allow_unicode=False, default_flow_style=False)
    # Indent under dependencies.mcp
    indented = "\n".join("  " + line if line else line for line in dumped.strip().splitlines())
    return "  mcp:\n" + indented + "\n"


def _update_apm_yml_mcp(repo_root: Path, fragment: list[dict[str, Any]], *, check: bool = False) -> list[Path]:
    """Update or create apm.yml , replacing only the mcp section delimited by markers.

    If no markers, append or create a dependencies.mcp section.
    """
    apm_path = repo_root / "apm.yml"
    frag_yaml = _render_mcp_yaml_fragment(fragment)
    marker_block = f"{MCP_BEGIN}\n{frag_yaml}{MCP_END}\n"

    written: list[Path] = []
    if check:
        # In check we still report intent; actual diffing is higher level or caller
        if not apm_path.exists():
            return [apm_path]
        try:
            text = apm_path.read_text(encoding="utf-8")
        except OSError:
            return [apm_path]
        if MCP_BEGIN not in text or MCP_END not in text:
            # would inject
            return [apm_path]
        # crude: if the block differs
        start = text.find(MCP_BEGIN)
        end = text.find(MCP_END, start)
        if end == -1:
            return [apm_path]
        current_block = text[start : end + len(MCP_END)]
        desired = f"{MCP_BEGIN}\n{frag_yaml}{MCP_END}"
        if current_block != desired:
            return [apm_path]
        return []

    if not apm_path.exists():
        content = (
            "name: agents\n"
            "version: 0.0.0\n"
            "description: wagents / agents repo primitives (agents, instructions, hooks)\n"
            "dependencies:\n"
            f"{marker_block}"
        )
        _ensure_dir(apm_path.parent)
        apm_path.write_text(content, encoding="utf-8")
        written.append(apm_path)
        return written

    text = apm_path.read_text(encoding="utf-8")
    if MCP_BEGIN in text and MCP_END in text:
        start = text.find(MCP_BEGIN)
        end = text.find(MCP_END, start) + len(MCP_END)
        new_text = text[:start] + f"{MCP_BEGIN}\n{frag_yaml}{MCP_END}" + text[end:]
    else:
        # Append a dependencies block or augment existing
        if "dependencies:" in text and "mcp:" not in text.split("dependencies:", 1)[1][:200]:
            # naive append under last dependencies
            new_text = text.rstrip() + "\n" + marker_block
        else:
            if "dependencies:" not in text:
                text = text.rstrip() + "\n\ndependencies:\n"
            new_text = text.rstrip() + "\n" + marker_block
    if new_text != text:
        apm_path.write_text(new_text, encoding="utf-8")
        written.append(apm_path)
    return written


def materialize(repo_root: Path, check: bool = False) -> dict[str, Any]:
    """Orchestrate all materializations + apm.yml mcp update."""
    touched: list[Path] = []
    touched.extend(materialize_agents(repo_root, check=check))
    touched.extend(materialize_instructions(repo_root, check=check))
    touched.extend(materialize_scoped_rules(repo_root, check=check))
    touched.extend(materialize_hooks(repo_root, check=check))
    # MCP stays wagents/MCPHub-owned; keep apm.yml lock-audit clean with an empty mcp list.
    mcp_frag: list[dict[str, Any]] = []
    touched.extend(_update_apm_yml_mcp(repo_root, mcp_frag, check=check))
    # Dedup preserve order
    seen: set[Path] = set()
    unique = []
    for p in touched:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return {
        "ok": True,
        "check": check,
        "touched": [str(p.relative_to(repo_root)) for p in unique],
        "mcp_count": len(mcp_frag),
    }


def doctor(repo_root: Path) -> dict[str, Any]:
    """Verify presence of apm surface + basic opencode.json contract + .apm generation."""
    checks: list[dict[str, Any]] = []
    ok = True

    # opencode.json keys
    oj = repo_root / "opencode.json"
    if not oj.exists():
        checks.append({"name": "opencode.json", "ok": False, "message": "missing opencode.json"})
        ok = False
    else:
        try:
            data = json.loads(oj.read_text(encoding="utf-8"))
        except Exception as e:
            checks.append({"name": "opencode.json", "ok": False, "message": f"unparsable: {e}"})
            ok = False
            data = {}
        required = ["plugin", "model", "instructions"]
        missing = [k for k in required if k not in data]
        skills_ok = isinstance(data.get("skills"), dict) and "paths" in data.get("skills", {})
        if missing or not skills_ok:
            msg = f"missing keys: {missing}; skills.paths present: {skills_ok}"
            checks.append({"name": "opencode.json", "ok": False, "message": msg})
            ok = False
        else:
            checks.append({"name": "opencode.json", "ok": True})

    # apm.yml
    ay = repo_root / "apm.yml"
    if ay.exists():
        checks.append({"name": "apm.yml", "ok": True})
    else:
        checks.append({"name": "apm.yml", "ok": False, "message": "missing (run materialize)"})
        ok = False

    # .apm generated
    apm_root = repo_root / ".apm"
    agents_ok = (apm_root / "agents").exists() and bool(list((apm_root / "agents").glob("*.agent.md")))
    instr_ok = (apm_root / "instructions").exists() and bool(
        list((apm_root / "instructions").glob("*.instructions.md"))
    )
    # hooks optional (may be empty set for this repo's filter)
    hooks_present = (apm_root / "hooks").exists()
    if not (agents_ok and instr_ok):
        checks.append({
            "name": ".apm/",
            "ok": False,
            "message": f"agents={agents_ok} instructions={instr_ok}",
        })
        ok = False
    else:
        checks.append({"name": ".apm/", "ok": True, "hooks": hooks_present})

    return {"ok": ok, "checks": checks, "repo_root": str(repo_root)}
