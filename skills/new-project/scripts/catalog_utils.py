#!/usr/bin/env python3
"""Shared catalog helpers for the new-project skill scripts."""

from __future__ import annotations

import json
import re
import shlex
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

SAFE_ENV_FILES = {".env.example", ".env.sample", ".env.template", ".env.test"}
SECRET_FILE_NAMES = {
    ".npmrc",
    "auth.json",
    "credentials.json",
    "kaggle.json",
    "secrets.toml",
}
SECRET_READER_COMMANDS = {"cat", "less", "more", "head", "tail"}
SECRET_COMMAND_PREFIXES = (
    ("security", "find-generic-password"),
    ("security", "find-internet-password"),
    ("gh", "auth", "token"),
    ("gcloud", "auth", "print-access-token"),
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_data(filename: str) -> dict[str, Any]:
    return load_json(DATA_DIR / filename)


def capability_index() -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in load_data("capabilities.json").get("capabilities", [])}


def preset_index() -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in load_data("presets.json").get("presets", [])}


def _add_capability(
    capability_id: str,
    reason: str,
    capabilities: dict[str, dict[str, Any]],
    selected: list[str],
    reasons: dict[str, list[str]],
    errors: list[str],
) -> None:
    if capability_id not in capabilities:
        errors.append(f"unknown capability: {capability_id}")
        return
    if capability_id not in selected:
        selected.append(capability_id)
    reasons.setdefault(capability_id, []).append(reason)


def resolve_capabilities(
    requested_ids: list[str],
    without_ids: list[str] | None = None,
    capabilities: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Resolve requested capability IDs into a closed selection graph."""

    capabilities = capabilities or capability_index()
    excluded = set(without_ids or [])
    selected: list[str] = []
    reasons: dict[str, list[str]] = {}
    errors: list[str] = []

    for capability_id in requested_ids:
        if capability_id in excluded:
            errors.append(f"requested capability excluded by --without: {capability_id}")
            continue
        _add_capability(capability_id, "requested", capabilities, selected, reasons, errors)

    index = 0
    while index < len(selected):
        capability_id = selected[index]
        index += 1
        capability = capabilities.get(capability_id)
        if not capability:
            continue

        for field in ("requires", "implies"):
            for referenced_id in capability.get(field, []):
                if referenced_id in excluded:
                    errors.append(f"capability {capability_id} {field} excluded capability: {referenced_id}")
                    continue
                _add_capability(
                    referenced_id,
                    f"{field} by {capability_id}",
                    capabilities,
                    selected,
                    reasons,
                    errors,
                )

    conflicts = detect_conflicts(selected, capabilities)
    if conflicts:
        errors.extend(f"conflicting capabilities: {', '.join(conflict['capabilities'])}" for conflict in conflicts)

    auto_added = [capability_id for capability_id in selected if "requested" not in reasons.get(capability_id, [])]
    return {
        "ok": not errors,
        "capabilities": selected,
        "requested_capabilities": [item for item in requested_ids if item not in excluded],
        "auto_added_capabilities": auto_added,
        "reasons": reasons,
        "conflicts": conflicts,
        "errors": errors,
    }


def detect_conflicts(
    selected_ids: list[str], capabilities: dict[str, dict[str, Any]] | None = None
) -> list[dict[str, Any]]:
    capabilities = capabilities or capability_index()
    selected = set(selected_ids)
    conflicts: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()

    for capability_id in selected_ids:
        capability = capabilities.get(capability_id, {})
        for conflicting_id in capability.get("conflicts", []):
            if conflicting_id in selected:
                pair = tuple(sorted((capability_id, conflicting_id)))
                if pair not in seen:
                    seen.add(pair)
                    conflicts.append({"id": f"capability.{pair[0]}.{pair[1]}", "capabilities": list(pair)})

    for rule in load_data("conflicts.json").get("conflicts", []):
        rule_ids = rule.get("capabilities", [])
        matched = [capability_id for capability_id in rule_ids if capability_id in selected]
        if len(matched) >= 2:
            key = tuple(sorted(matched))
            if key not in seen:
                seen.add(key)
                conflicts.append({
                    "id": rule.get("id", "catalog.conflict"),
                    "capabilities": matched,
                    "resolution": rule.get("resolution"),
                })
    return conflicts


def command_tokens(command: str) -> list[str]:
    try:
        return shlex.split(command)
    except ValueError:
        return command.split()


def normalized_command_tokens(tokens: list[str]) -> list[str]:
    if len(tokens) < 3 or tokens[:2] != ["docker", "compose"]:
        return tokens

    normalized = tokens[:2]
    index = 2
    while index < len(tokens):
        token = tokens[index]
        if token in {"--env-file", "--file", "--project-name", "--profile", "-f", "-p"}:
            index += 2
            continue
        if token.startswith(("--env-file=", "--file=", "--project-name=", "--profile=")):
            index += 1
            continue
        normalized.extend(tokens[index:])
        break
    return normalized


def _contains_token_sequence(tokens: list[str], phrase: str) -> bool:
    phrase_tokens = phrase.split()
    if not phrase_tokens or len(phrase_tokens) > len(tokens):
        return False
    for index in range(0, len(tokens) - len(phrase_tokens) + 1):
        if tokens[index : index + len(phrase_tokens)] == phrase_tokens:
            return True
    return False


def classify_command(command: str) -> list[str]:
    tokens = command_tokens(command)
    normalized_tokens = normalized_command_tokens(tokens)
    groups = load_data("command-groups.json").get("groups", {})
    categories: list[str] = []

    for category, phrases in groups.items():
        if any(
            _contains_token_sequence(tokens, phrase) or _contains_token_sequence(normalized_tokens, phrase)
            for phrase in phrases
        ):
            categories.append(category)

    if command_reads_secret(command, tokens):
        categories.append("secret_read")

    return sorted(set(categories))


def required_approvals_for_commands(commands: list[str]) -> list[str]:
    approvals: set[str] = set()
    for command in commands:
        categories = classify_command(command)
        if "file_mutation" in categories:
            approvals.add("mutate-files")
        if "package_install" in categories:
            approvals.add("package-install")
        if "external_side_effect" in categories:
            approvals.add("external-side-effect")
    return sorted(approvals)


def command_reads_secret(command: str, tokens: list[str] | None = None) -> bool:
    tokens = tokens or command_tokens(command)
    lowered_tokens = [token.lower() for token in tokens]

    for prefix in SECRET_COMMAND_PREFIXES:
        if tuple(lowered_tokens[: len(prefix)]) == prefix:
            return True

    if (
        lowered_tokens
        and lowered_tokens[0] in SECRET_READER_COMMANDS
        and any(is_secret_like_path(token) for token in tokens[1:])
    ):
        return True

    return any(is_secret_like_path(token) for token in tokens)


def is_secret_like_path(value: str) -> bool:
    token = value.strip().strip("'\"")
    name = Path(token).name
    if name in SAFE_ENV_FILES:
        return False
    if name.startswith(".env"):
        return True
    return name in SECRET_FILE_NAMES


NPM_PACKAGE_RE = re.compile(r"^(?:@[a-z0-9][a-z0-9._~-]*/)?[a-z0-9][a-z0-9._~-]*$")
PYPI_PACKAGE_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$")


def resolve_package_alias(package: str) -> dict[str, Any]:
    alias = load_data("package-aliases.json").get("aliases", {}).get(package)
    if not alias:
        return {"input": package, "package": package, "notes": None, "resolved": False}
    return {"input": package, "package": alias.get("package"), "notes": alias.get("notes"), "resolved": True}


def valid_package_name(package: str, ecosystem: str) -> bool:
    pattern = NPM_PACKAGE_RE if ecosystem == "npm" else PYPI_PACKAGE_RE
    return bool(pattern.fullmatch(package))
