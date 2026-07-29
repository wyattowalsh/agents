#!/usr/bin/env python3
"""Run and record an idempotent docs-steward pass for the July 2026 corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path("planning/manifests/candidate-corpus-jul2026/docs-closure-evidence.json")

# This is intentionally narrower than docs/src. Authoring, hooks, harness prose,
# and other hand-maintained docs are inputs, not generator-owned outputs.
GENERATED_EXACT_PATHS = frozenset({
    "README.md",
    "docs/src/generated-sidebar.mjs",
    "docs/src/generated-site-data.mjs",
    "docs/src/generated-skill-indexes.mjs",
    "docs/src/generated-skill-research-index.mjs",
    "docs/src/generated-visual-assets.css",
    "docs/src/content/docs/architecture/instruction-loading.mdx",
    "docs/src/content/docs/architecture/progressive-disclosure.mdx",
    "docs/src/content/docs/cli.mdx",
    "docs/src/content/docs/external-skills.mdx",
    "docs/src/content/docs/harness-support.mdx",
    "docs/src/content/docs/index.mdx",
    "docs/src/content/docs/install.mdx",
    "docs/src/content/docs/reference.mdx",
    "docs/src/content/docs/runtimes.mdx",
})
GENERATED_PREFIXES = (
    "docs/public/generated-registries/",
    "docs/public/generated-reports/",
    "docs/public/generated-skill-indexes/",
    "docs/src/content/docs/agents/",
    "docs/src/content/docs/catalog/",
    "docs/src/content/docs/mcp/",
    "docs/src/content/docs/reports/",
    "docs/src/content/docs/skill-research/",
    "docs/src/content/docs/skills/",
    "docs/src/content/docs/surfaces/",
)
FALLBACK_IGNORED_PARTS = frozenset({
    ".astro",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "dist",
    "node_modules",
})
HAND_MAINTAINED_SENTINEL = "HAND-MAINTAINED"

PASS_ONE = (
    ("uv", "run", "wagents", "readme"),
    ("uv", "run", "wagents", "docs", "generate", "--no-installed"),
)
PASS_TWO = PASS_ONE
VALIDATIONS = (
    ("uv", "run", "wagents", "readme", "--check"),
    ("uv", "run", "wagents", "docs", "generate", "--no-installed", "--check"),
    ("uv", "run", "wagents", "catalog", "index", "--check", "--format", "json"),
    ("uv", "run", "wagents", "docs", "lint"),
    ("uv", "run", "wagents", "docs", "build"),
)
EXPECTED_COMMANDS = tuple(" ".join(command) for command in (*PASS_ONE, *PASS_TWO, *VALIDATIONS))


def output_path() -> Path:
    return ROOT / OUTPUT_RELATIVE


def safe_env() -> dict[str, str]:
    allowed = {
        "HOME",
        "LANG",
        "LC_ALL",
        "PATH",
        "SHELL",
        "TMPDIR",
        "TERM",
        "UV_CACHE_DIR",
        "XDG_CACHE_HOME",
        "XDG_CONFIG_HOME",
    }
    env = {key: value for key, value in os.environ.items() if key in allowed}
    env.update({"CI": "1", "NO_COLOR": "1", "DO_NOT_TRACK": "1", "NO_UPDATE_NOTIFIER": "1"})
    return env


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def snapshot_digest(value: dict[str, str]) -> str:
    return sha256_bytes(canonical(value).encode())


def _repository_files_from_git() -> list[Path] | None:
    completed = subprocess.run(
        ("git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"),
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    paths: list[Path] = []
    for raw in completed.stdout.split(b"\0"):
        if not raw:
            continue
        relative = raw.decode("utf-8", errors="surrogateescape")
        path = ROOT / relative
        if path.is_symlink() or path.is_file():
            paths.append(path)
    return sorted(set(paths), key=lambda path: path.relative_to(ROOT).as_posix())


def repository_files() -> list[Path]:
    from_git = _repository_files_from_git()
    if from_git is not None:
        return from_git
    paths: list[Path] = []
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if any(part in FALLBACK_IGNORED_PARTS for part in relative.parts):
            continue
        if path.is_symlink() or path.is_file():
            paths.append(path)
    return sorted(set(paths), key=lambda path: path.relative_to(ROOT).as_posix())


def _repository_fingerprint(path: Path) -> str:
    metadata = path.lstat()
    mode = stat.S_IMODE(metadata.st_mode)
    if stat.S_ISLNK(metadata.st_mode):
        payload = f"symlink\0{mode:o}\0{os.readlink(path)}".encode()
    elif stat.S_ISREG(metadata.st_mode):
        payload = b"file\0" + f"{mode:o}".encode() + b"\0" + path.read_bytes()
    else:
        payload = f"other\0{mode:o}\0{metadata.st_mode}".encode()
    return sha256_bytes(payload)


def repo_snapshot() -> dict[str, str]:
    return {path.relative_to(ROOT).as_posix(): _repository_fingerprint(path) for path in repository_files()}


def changed_paths(before: dict[str, str], after: dict[str, str]) -> list[str]:
    return sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path))


def custom_authoring_paths() -> set[str]:
    skills_root = ROOT / "skills"
    paths = (
        {
            f"docs/src/authoring/skills/{skill.parent.name}.mdx"
            for skill in skills_root.glob("*/SKILL.md")
            if skill.is_file()
        }
        if skills_root.is_dir()
        else set()
    )
    authoring_root = ROOT / "docs" / "src" / "authoring" / "skills"
    if authoring_root.is_dir():
        for path in authoring_root.glob("*.mdx"):
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if "GENERATED-AUTHORING: source=skills/" in text and any(
                line.strip() in {"source_kind: custom", 'source_kind: "custom"', "source_kind: 'custom'"}
                for line in text.splitlines()
            ):
                paths.add(path.relative_to(ROOT).as_posix())
    return paths


def _catalog_detail(relative: str) -> bool:
    if not relative.endswith(".mdx") or relative.endswith("/index.mdx"):
        return False
    return (
        relative.startswith("docs/src/content/docs/agents/")
        or relative.startswith("docs/src/content/docs/mcp/")
        or relative.startswith("docs/src/content/docs/skills/catalog/custom/")
        or relative.startswith("docs/src/content/docs/skills/catalog/external/")
    )


def protected_hand_authored_paths() -> set[str]:
    protected: set[str] = set()
    content_root = ROOT / "docs" / "src" / "content" / "docs"
    if not content_root.is_dir():
        return protected
    for path in content_root.rglob("*.mdx"):
        relative = path.relative_to(ROOT).as_posix()
        if _catalog_detail(relative):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        frontmatter = text.split("---", 2)[1] if text.startswith("---") and text.count("---") >= 2 else ""
        if HAND_MAINTAINED_SENTINEL in text or any(
            line.strip() == "composed: true" for line in frontmatter.splitlines()
        ):
            protected.add(relative)
    return protected


def is_allowed_generator_write(relative: str, *, custom_paths: set[str] | None = None) -> bool:
    if relative in GENERATED_EXACT_PATHS:
        return True
    if relative in (custom_paths if custom_paths is not None else custom_authoring_paths()):
        return True
    return any(relative.startswith(prefix) for prefix in GENERATED_PREFIXES)


def generated_files() -> list[Path]:
    custom_paths = custom_authoring_paths()
    protected = protected_hand_authored_paths()
    return [
        path
        for path in repository_files()
        if (relative := path.relative_to(ROOT).as_posix()) not in protected
        and is_allowed_generator_write(relative, custom_paths=custom_paths)
        and path.is_file()
        and not path.is_symlink()
    ]


def snapshot() -> dict[str, str]:
    return {path.relative_to(ROOT).as_posix(): sha256_bytes(path.read_bytes()) for path in generated_files()}


def run_command(argv: tuple[str, ...]) -> dict[str, Any]:
    started = time.monotonic()
    completed = subprocess.run(
        argv,
        cwd=ROOT,
        env=safe_env(),
        capture_output=True,
        check=False,
        timeout=1_200,
    )
    stdout = completed.stdout
    stderr = completed.stderr
    return {
        "command": " ".join(argv),
        "exit_code": completed.returncode,
        "status": "passed" if completed.returncode == 0 else "failed",
        "duration_seconds": round(time.monotonic() - started, 3),
        "stdout_sha256": sha256_bytes(stdout),
        "stderr_sha256": sha256_bytes(stderr),
        "stdout_bytes": len(stdout),
        "stderr_bytes": len(stderr),
    }


def run_sequence(commands: tuple[tuple[str, ...], ...]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for command in commands:
        result = run_command(command)
        results.append(result)
        if result["status"] != "passed":
            break
    return results


def _commands_passed(results: list[dict[str, Any]], expected: tuple[tuple[str, ...], ...]) -> bool:
    return len(results) == len(expected) and all(row.get("status") == "passed" for row in results)


def build_evidence() -> dict[str, Any]:
    custom_paths = custom_authoring_paths()
    protected_before = protected_hand_authored_paths()
    pre_repo = repo_snapshot()
    pre_generated = snapshot()

    first_commands = run_sequence(PASS_ONE)
    first_repo = repo_snapshot()
    first_generated = snapshot()
    first_changes = changed_paths(pre_repo, first_repo)
    unexpected_first = sorted(
        path
        for path in first_changes
        if path in protected_before or not is_allowed_generator_write(path, custom_paths=custom_paths)
    )

    first_passed = _commands_passed(first_commands, PASS_ONE) and not unexpected_first
    second_commands = run_sequence(PASS_TWO) if first_passed else []
    second_repo = repo_snapshot()
    second_generated = snapshot()
    second_changes = changed_paths(first_repo, second_repo)
    idempotent = _commands_passed(second_commands, PASS_TWO) and not second_changes

    validation_commands = run_sequence(VALIDATIONS) if idempotent else []
    final_repo = repo_snapshot()
    final_generated = snapshot()
    validation_changes = changed_paths(second_repo, final_repo)
    validations_passed = _commands_passed(validation_commands, VALIDATIONS) and not validation_changes
    all_passed = first_passed and idempotent and validations_passed and second_generated == final_generated

    unexpected_writes = sorted(set(unexpected_first) | set(validation_changes))
    return {
        "version": 2,
        "assurance_kind": "candidate-docs-steward-closure",
        "generation_status": "passed" if first_passed else "failed",
        "check_status": "passed" if validations_passed else "failed",
        "build_status": (
            "passed" if validations_passed and validation_commands[-1].get("status") == "passed" else "failed"
        ),
        "idempotence_status": "passed" if idempotent else "failed",
        "compare_and_swap_status": "passed" if not unexpected_first else "failed",
        "complete": all_passed,
        "allowed_write_policy": {
            "exact_paths": sorted(GENERATED_EXACT_PATHS),
            "prefixes": list(GENERATED_PREFIXES),
            "custom_authoring_paths": sorted(custom_paths),
            "protected_hand_authored_paths": sorted(protected_before),
        },
        "declared_write_set": sorted(final_generated),
        "preimage_digests": pre_generated,
        "postimage_digests": final_generated,
        "first_pass_digests": first_generated,
        "second_pass_digests": second_generated,
        "final_digests": final_generated,
        "pre_pass_digest": snapshot_digest(pre_generated),
        "first_pass_digest": snapshot_digest(first_generated),
        "second_pass_digest": snapshot_digest(second_generated),
        "final_digest": snapshot_digest(final_generated),
        "pre_pass_repo_digest": snapshot_digest(pre_repo),
        "first_pass_repo_digest": snapshot_digest(first_repo),
        "second_pass_repo_digest": snapshot_digest(second_repo),
        "final_repo_digest": snapshot_digest(final_repo),
        "first_pass_changed_paths": first_changes,
        "changed_between_passes": second_changes,
        "validation_writes": validation_changes,
        "unexpected_writes": unexpected_writes,
        "commands": [*first_commands, *second_commands, *validation_commands],
    }


def write_evidence(payload: dict[str, Any]) -> None:
    output = output_path()
    temporary = output.with_name(f".{output.name}.wagents-{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    os.replace(temporary, output)


def check_stored_evidence(stored: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    current = snapshot()
    declared = stored.get("declared_write_set")
    final_digests = stored.get("final_digests")
    if stored.get("version") != 2:
        errors.append("stored docs assurance has the wrong version")
    if stored.get("assurance_kind") != "candidate-docs-steward-closure":
        errors.append("stored docs assurance has the wrong assurance kind")
    for field in (
        "generation_status",
        "check_status",
        "build_status",
        "idempotence_status",
        "compare_and_swap_status",
    ):
        if stored.get(field) != "passed":
            errors.append(f"stored docs assurance {field} is not passed")
    if stored.get("complete") is not True:
        errors.append("stored docs assurance is incomplete")
    if stored.get("unexpected_writes"):
        errors.append("stored docs assurance contains unexpected writes")
    if stored.get("changed_between_passes") or stored.get("validation_writes"):
        errors.append("stored docs assurance is not stable after generation")
    if not isinstance(declared, list) or declared != sorted(current):
        errors.append("docs declared write set is stale")
    if not isinstance(final_digests, dict) or canonical(final_digests) != canonical(current):
        errors.append("docs generated-file digests are stale")
    if stored.get("final_digest") != snapshot_digest(current):
        errors.append("docs final aggregate digest is stale")
    commands = stored.get("commands")
    if not isinstance(commands, list) or len(commands) != len(EXPECTED_COMMANDS):
        errors.append("stored docs assurance has an incomplete command sequence")
    else:
        for index, (row, expected_command) in enumerate(zip(commands, EXPECTED_COMMANDS, strict=True)):
            if not isinstance(row, dict):
                errors.append(f"stored docs command {index} is not an object")
                continue
            if row.get("command") != expected_command or row.get("exit_code") != 0 or row.get("status") != "passed":
                errors.append(f"stored docs command {index} does not match the successful expected command")
            for digest_field in ("stdout_sha256", "stderr_sha256"):
                value = row.get(digest_field)
                if not isinstance(value, str) or len(value) != 64:
                    errors.append(f"stored docs command {index} has an invalid {digest_field}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.check:
        output = output_path()
        if not output.is_file():
            print(json.dumps({"ok": False, "errors": [f"missing evidence: {output}"]}, indent=2))
            return 1
        stored = json.loads(output.read_text(encoding="utf-8"))
        errors = check_stored_evidence(stored)
        print(json.dumps({"ok": not errors, "errors": errors}, indent=2))
        return 0 if not errors else 1

    payload = build_evidence()
    if args.apply:
        write_evidence(payload)
    print(
        json.dumps(
            {
                "ok": payload["complete"],
                "applied": args.apply,
                "write_set_count": len(payload["declared_write_set"]),
                "first_pass_digest": payload["first_pass_digest"],
                "second_pass_digest": payload["second_pass_digest"],
                "final_digest": payload["final_digest"],
                "first_pass_changed_paths": payload["first_pass_changed_paths"],
                "changed_between_passes": payload["changed_between_passes"],
                "validation_writes": payload["validation_writes"],
                "unexpected_writes": payload["unexpected_writes"],
                "commands": payload["commands"],
            },
            indent=2,
        )
    )
    return 0 if payload["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
