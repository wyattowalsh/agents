#!/usr/bin/env python3
"""Remove retired harness targets from canonical registries and authoring rows."""

from __future__ import annotations

import argparse
import json
import re
import shlex
from pathlib import Path
from typing import Any

import yaml

RETIRED_TARGETS = frozenset({
    "antigravity",
    "gemini-cli",
    "github-copilot",
    "github-copilot-cli",
    "github-copilot-web",
})
RETIRED_ALIAS_KEYS = frozenset({
    "antigravity",
    "google-antigravity",
    "gemini",
    "gemini-cli",
    "github-copilot",
    "gh-copilot",
    "copilot",
    "copilot-cli",
    "copilot-web",
    "copilot-cloud",
    "copilot-coding-agent",
})
RETIRED_MANAGED_PATH_MARKERS = (
    "/.gemini/",
    "/.copilot/",
    "/.config/.copilot/",
    "/.config/copilot-subagents.env",
    "/.github/copilot-instructions.md",
    "/.github/instructions",
    "/.github/hooks",
    "/instructions/copilot-global.md",
    "/platforms/copilot/agents",
)

JSON_REGISTRIES = (
    "agent-bundle.json",
    "config/harness-surface-registry.json",
    "config/hook-registry.json",
    "config/hook-surface-registry.json",
    "config/image-input-optimizer.json",
    "config/mcp-registry.json",
    "config/plugin-extension-registry.json",
    "config/rtk-integration.json",
    "config/sync-manifest.json",
    "planning/manifests/candidate-corpus-jul2026/promotion-overrides.json",
)
MARKDOWN_SECTION_RETIREMENTS = {
    "skills/harness-master/references/harness-surfaces.md": frozenset({
        "GitHub Copilot Web",
        "GitHub Copilot CLI",
        "Gemini CLI",
        "Antigravity",
    }),
    "skills/harness-master/references/harness-checklists.md": frozenset({
        "GitHub Copilot Web",
        "GitHub Copilot CLI",
        "Gemini CLI",
        "Antigravity",
    }),
    "skills/harness-master/references/latest-doc-sources.md": frozenset({
        "GitHub Copilot Web",
        "GitHub Copilot CLI",
        "Gemini CLI",
        "Antigravity",
    }),
}
INSTALL_TARGET_SEQUENCE = "antigravity claude-code codex crush cursor gemini-cli github-copilot opencode"
REMAINING_TARGET_SEQUENCE = "claude-code codex crush cursor grok opencode"
INSTALL_GUIDE_FILES = (
    "skills/harness-master/references/discovery/output-formats.md",
    "skills/harness-master/references/discovery/team-templates.md",
    "skills/skill-creator/references/packaging-guide.md",
)


def _without_retired(values: list[Any]) -> list[Any]:
    return [value for value in values if not isinstance(value, str) or value not in RETIRED_TARGETS]


def _rewrite_install_command(command: str) -> str:
    tokens = shlex.split(command)
    rewritten: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token not in {"-a", "--agent"}:
            if token not in RETIRED_TARGETS:
                rewritten.append(token)
            index += 1
            continue
        index += 1
        targets: list[str] = []
        while index < len(tokens) and not tokens[index].startswith("-"):
            if tokens[index] not in RETIRED_TARGETS:
                targets.append(tokens[index])
            index += 1
        if targets:
            rewritten.extend((token, *targets))
    return shlex.join(rewritten)


def _rewrite_body_install_commands(body: str) -> str:
    """Remove retired targets from Skills CLI commands without rewriting prose."""

    def rewrite_inline(match: re.Match[str]) -> str:
        return f"`{_rewrite_install_command(match.group(1))}`"

    inline = re.sub(
        r"`([^`\n]*\bnpx(?:\s+--yes)?\s+skills\s+add\b[^`\n]*)`",
        rewrite_inline,
        body,
    )
    rewritten: list[str] = []
    for line in inline.splitlines(keepends=True):
        stripped = line.strip()
        if stripped.startswith("npx ") and " skills add " in f" {stripped} ":
            leading = line[: len(line) - len(line.lstrip())]
            trailing = "\n" if line.endswith("\n") else ""
            line = leading + _rewrite_install_command(stripped) + trailing
        rewritten.append(line)
    return "".join(rewritten)


def rewrite_authoring_text(text: str) -> str:
    """Rewrite active install targets while preserving historical body prose."""
    if not text.startswith("---\n"):
        raise ValueError("authoring document must begin with YAML frontmatter")
    end = text.find("\n---", 4)
    if end < 0:
        raise ValueError("authoring document is missing its closing frontmatter fence")
    frontmatter = text[4:end]
    body = text[end:]
    if not any(target in frontmatter or target in body for target in RETIRED_TARGETS):
        return text

    rewritten: list[str] = []
    for line in frontmatter.splitlines():
        key, separator, raw_value = line.partition(":")
        if not separator or key not in {"install_command", "target_agents", "unsupported_target_agents"}:
            rewritten.append(line)
            continue
        value = yaml.safe_load(raw_value.strip())
        if key == "install_command":
            if not isinstance(value, str):
                raise ValueError("install_command must be a string")
            rewritten.append(f"{key}: {json.dumps(_rewrite_install_command(value))}")
            continue
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ValueError(f"{key} must be a list of strings")
        rewritten.append(f"{key}: {json.dumps(_without_retired(value))}")
    return "---\n" + "\n".join(rewritten) + _rewrite_body_install_commands(body)


def remove_markdown_h2_sections(text: str, headings: frozenset[str]) -> str:
    """Remove exact H2 sections and renumber a simple numbered contents list."""
    retired_anchors = {
        "#" + "".join(character.lower() if character.isalnum() else "-" for character in heading).strip("-")
        for heading in headings
    }
    kept: list[str] = []
    skipping = False
    for line in text.splitlines(keepends=True):
        if line.startswith("## "):
            heading = line[3:].strip()
            skipping = heading in headings
            if skipping:
                continue
        if skipping:
            continue
        if any(f"]({anchor})" in line for anchor in retired_anchors):
            continue
        kept.append(line)

    numbered = 0
    rewritten: list[str] = []
    for line in kept:
        stripped = line.lstrip()
        prefix_length = len(line) - len(stripped)
        if stripped[:1].isdigit() and ". [" in stripped:
            marker, separator, rest = stripped.partition(". ")
            if marker.isdigit() and separator:
                numbered += 1
                line = line[:prefix_length] + f"{numbered}. {rest}"
        rewritten.append(line)
    return "".join(rewritten)


def _rewrite_agent_bundle(payload: dict[str, Any]) -> None:
    skills = payload["adapters"]["agent-skills-cli"]
    skills["install"] = _rewrite_install_command(str(skills["install"]))
    skills["supportedAgents"] = _without_retired(skills["supportedAgents"])
    mapping = payload["adapters"]["openspec"]["toolMapping"]
    for target in RETIRED_TARGETS:
        mapping.pop(target, None)


def _rewrite_harness_rows(payload: dict[str, Any]) -> None:
    payload["harnesses"] = [
        row
        for row in payload.get("harnesses", [])
        if not isinstance(row, dict) or row.get("id") not in RETIRED_TARGETS
    ]


def _rewrite_hook_registry(payload: dict[str, Any]) -> None:
    kept: list[dict[str, Any]] = []
    for row in payload.get("hooks", []):
        if not isinstance(row, dict):
            continue
        harnesses = row.get("harnesses")
        if isinstance(harnesses, list):
            row["harnesses"] = _without_retired(harnesses)
            if not row["harnesses"]:
                continue
        kept.append(row)
    payload["hooks"] = kept


def _rewrite_hook_surface_registry(payload: dict[str, Any]) -> None:
    aliases: dict[str, Any] = {}
    for alias, target in payload.get("harness_aliases", {}).items():
        if alias in RETIRED_ALIAS_KEYS:
            continue
        if isinstance(target, list):
            filtered = _without_retired(target)
            if filtered:
                aliases[alias] = filtered
        elif target not in RETIRED_TARGETS:
            aliases[alias] = target
    payload["harness_aliases"] = aliases
    _rewrite_harness_rows(payload)


def _rewrite_mcp_registry(payload: dict[str, Any]) -> None:
    chrome = payload["servers"]["chrome-devtools"]
    chrome["exclude_from_harnesses"] = _without_retired(chrome.get("exclude_from_harnesses", []))
    ownership = chrome.get("ownership", {})
    for owner in ("plugin", "extension", "repo_mcp"):
        if isinstance(ownership.get(owner), list):
            ownership[owner] = _without_retired(ownership[owner])
    clients = payload["mcphub"]["clients"]["stdio_bridge"]["clients"]
    payload["mcphub"]["clients"]["stdio_bridge"]["clients"] = _without_retired(clients)


def _rewrite_plugin_registry(payload: dict[str, Any]) -> None:
    for row in payload.get("mcp_ownership", []):
        if not isinstance(row, dict):
            continue
        harnesses = row.get("harnesses")
        if not isinstance(harnesses, dict):
            continue
        for target in RETIRED_TARGETS:
            harnesses.pop(target, None)


def _rewrite_rtk_registry(payload: dict[str, Any]) -> None:
    harnesses = payload.get("harnesses", {})
    for target in RETIRED_TARGETS:
        harnesses.pop(target, None)


def _rewrite_sync_manifest(payload: dict[str, Any]) -> None:
    payload["managed"] = [
        row
        for row in payload.get("managed", [])
        if not (
            isinstance(row, dict)
            and isinstance(row.get("path"), str)
            and any(marker in row["path"] for marker in RETIRED_MANAGED_PATH_MARKERS)
        )
    ]


def _rewrite_promotion_overrides(payload: dict[str, Any]) -> None:
    for row in payload.get("overrides", []):
        if not isinstance(row, dict):
            continue
        target_agents = row.get("target_agents")
        if isinstance(target_agents, list):
            row["target_agents"] = _without_retired(target_agents)
        install_command = row.get("install_command")
        if isinstance(install_command, str):
            row["install_command"] = _rewrite_install_command(install_command)


def rewrite_registry(relative_path: str, payload: dict[str, Any]) -> None:
    if relative_path == "agent-bundle.json":
        _rewrite_agent_bundle(payload)
    elif relative_path in {
        "config/harness-surface-registry.json",
        "config/image-input-optimizer.json",
    }:
        _rewrite_harness_rows(payload)
    elif relative_path == "config/hook-registry.json":
        _rewrite_hook_registry(payload)
    elif relative_path == "config/hook-surface-registry.json":
        _rewrite_hook_surface_registry(payload)
    elif relative_path == "config/mcp-registry.json":
        _rewrite_mcp_registry(payload)
    elif relative_path == "config/plugin-extension-registry.json":
        _rewrite_plugin_registry(payload)
    elif relative_path == "config/rtk-integration.json":
        _rewrite_rtk_registry(payload)
    elif relative_path == "config/sync-manifest.json":
        _rewrite_sync_manifest(payload)
    elif relative_path == "planning/manifests/candidate-corpus-jul2026/promotion-overrides.json":
        _rewrite_promotion_overrides(payload)


def _render_json(path: Path, payload: dict[str, Any]) -> str:
    original = path.read_text(encoding="utf-8")
    indent: str | int = "\t" if "\n\t" in original[:500] else 2
    return json.dumps(payload, indent=indent, ensure_ascii=False) + "\n"


def collect_changes(repo_root: Path) -> dict[Path, str]:
    changes: dict[Path, str] = {}
    for relative_path in JSON_REGISTRIES:
        path = repo_root / relative_path
        payload = json.loads(path.read_text(encoding="utf-8"))
        rewrite_registry(relative_path, payload)
        rendered = _render_json(path, payload)
        if rendered != path.read_text(encoding="utf-8"):
            changes[path] = rendered
    for path in sorted((repo_root / "docs" / "src" / "authoring" / "skills").glob("*.mdx")):
        original = path.read_text(encoding="utf-8")
        rendered = rewrite_authoring_text(original)
        if rendered != original:
            changes[path] = rendered
    for relative_path, headings in MARKDOWN_SECTION_RETIREMENTS.items():
        path = repo_root / relative_path
        original = path.read_text(encoding="utf-8")
        rendered = remove_markdown_h2_sections(original, headings)
        if rendered != original:
            changes[path] = rendered
    for relative_path in INSTALL_GUIDE_FILES:
        path = repo_root / relative_path
        original = path.read_text(encoding="utf-8")
        rendered = original.replace(INSTALL_TARGET_SEQUENCE, REMAINING_TARGET_SEQUENCE)
        if rendered != original:
            changes[path] = rendered
    return changes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    changes = collect_changes(args.repo_root.resolve())
    if args.check:
        if changes:
            for path in changes:
                print(path.relative_to(args.repo_root.resolve()))
            return 1
        return 0
    for path, rendered in changes.items():
        path.write_text(rendered, encoding="utf-8")
    print(json.dumps({"changed_files": len(changes)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
