"""Nerdbot command-line interface."""

from __future__ import annotations

import argparse
import json
import shlex
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from nerdbot.contracts import (
    MODE_SUMMARIES,
    MODE_VISUALS,
    MODES,
    READ_ONLY_MODES,
    REQUIRED_EXPANSION_LANES,
    SAFETY_PROMISES,
    VERSION,
)
from nerdbot.legacy import kb_bootstrap, kb_inventory, kb_lint
from nerdbot.workflows import (
    build_create_result,
    build_derive_result,
    build_enrich_result,
    build_improve_result,
    build_ingest_result,
    build_migrate_result,
    build_query_result,
    build_replay_result,
    build_watch_classify_result,
    command_envelope,
)


def emit_json(payload: dict[str, Any], *, compact: bool = False) -> None:
    """Print a JSON payload using the established script output style."""
    indent = None if compact else 2
    print(json.dumps(payload, indent=indent, ensure_ascii=False))


def legacy_error_payload(payload: str) -> dict[str, Any]:
    """Normalize legacy JSON-string error payloads into package JSON objects."""
    parsed = json.loads(payload)
    if not isinstance(parsed, dict):
        return {"error": "legacy command failed", "details": parsed}
    return parsed


def emit_text(payload: str) -> None:
    """Print human-oriented CLI output."""
    print(payload)


def emit_workflow_error(command: str, mode: str, target: str, exc: Exception, *, compact: bool) -> int:
    """Emit the shared structured error envelope for workflow failures."""
    emit_json(
        command_envelope(command=command, mode=mode, target=target, dry_run=True, errors=[str(exc)]),
        compact=compact,
    )
    return 1


def add_common_json_flag(parser: argparse.ArgumentParser) -> None:
    """Add the common compact-output flag."""
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON instead of pretty-printed JSON")


def add_dry_run_apply_flags(parser: argparse.ArgumentParser) -> None:
    """Add the shared dry-run/apply approval flags."""
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--apply", action="store_true", help="Apply the planned additive changes")
    group.add_argument("--dry-run", action="store_true", help="Preview changes without writing files")


def add_root_flag(parser: argparse.ArgumentParser) -> None:
    """Add the shared KB root flag."""
    parser.add_argument("--root", default=".", help="KB root to inspect or update")


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level Nerdbot parser."""
    parser = argparse.ArgumentParser(
        prog="nerdbot",
        description="Local-first Obsidian-compatible knowledge-base toolkit.",
    )
    parser.add_argument("--version", action="version", version=f"nerdbot {VERSION}")
    subparsers = parser.add_subparsers(dest="command")

    bootstrap = subparsers.add_parser("bootstrap", help="Safely scaffold missing KB layers and starter files")
    bootstrap.add_argument("--root", default=".", help="KB root to create or update")
    bootstrap.add_argument("--force", action="store_true", help="Overwrite known starter files except activity/log.md")
    bootstrap.add_argument("--dry-run", action="store_true", help="Preview changes without writing files")
    add_common_json_flag(bootstrap)

    inventory = subparsers.add_parser("inventory", help="Inspect KB structure and risks without mutation")
    inventory.add_argument("--root", default=".", help="KB or repository root to inspect")
    inventory.add_argument("--max-examples", type=int, default=5, help="Maximum example paths per content class")
    add_common_json_flag(inventory)

    lint = subparsers.add_parser("lint", help="Run non-destructive KB lint checks")
    lint.add_argument("--root", default=".", help="KB or repository root to lint")
    lint.add_argument(
        "--fail-on",
        choices=("none", "critical", "warning"),
        default="warning",
        help="Return a non-zero exit code when findings reach this severity",
    )
    lint.add_argument(
        "--include-unlayered",
        action="store_true",
        help="Include markdown outside the default KB layers in link and coverage analysis",
    )
    add_common_json_flag(lint)

    plan = subparsers.add_parser("plan", help="Emit a safety-oriented plan skeleton for a Nerdbot mode")
    plan.add_argument("--mode", choices=MODES, required=True, help="Nerdbot workflow mode")
    plan.add_argument("--target", default=".", help="Topic, source, or KB path")
    plan.add_argument(
        "--view",
        choices=("json", "guide"),
        default="json",
        help="Render machine JSON or a visually richer terminal guide",
    )
    add_common_json_flag(plan)

    modes = subparsers.add_parser("modes", help="Show visually rich workflow options")
    modes.add_argument("--view", choices=("json", "guide"), default="guide", help="Render JSON or terminal guide")
    add_common_json_flag(modes)

    create = subparsers.add_parser("create", help="Dry-run/apply scaffold creation with operation journaling")
    add_root_flag(create)
    create.add_argument("--force", action="store_true", help="Overwrite known starter files except activity/log.md")
    add_dry_run_apply_flags(create)
    add_common_json_flag(create)

    ingest = subparsers.add_parser("ingest", help="Capture a local source or provided text under raw/ with provenance")
    add_root_flag(ingest)
    ingest.add_argument("--source", help="Local source path to capture")
    ingest.add_argument("--text", help="Inline text to capture as a source")
    ingest.add_argument("--capture-method", default="local-file", help="Capture method stored in source records")
    ingest.add_argument("--max-copy-bytes", type=int, default=50_000_000, help="Maximum local-file bytes to copy")
    ingest.add_argument(
        "--copy-outside-root",
        action="store_true",
        help="Intentionally copy a non-secret source from outside --root instead of writing a pointer stub",
    )
    add_dry_run_apply_flags(ingest)
    add_common_json_flag(ingest)

    enrich = subparsers.add_parser("enrich", help="Create a cited draft wiki page from a source path")
    add_root_flag(enrich)
    enrich.add_argument("--target", required=True, help="Source or canonical material path to cite")
    enrich.add_argument("--title", default="Nerdbot Draft", help="Draft wiki page title")
    add_dry_run_apply_flags(enrich)
    add_common_json_flag(enrich)

    audit = subparsers.add_parser("audit", help="Run inventory and lint as one read-only workflow")
    add_root_flag(audit)
    audit.add_argument("--include-unlayered", action="store_true", help="Include markdown outside default KB layers")
    audit.add_argument("--fail-on", choices=("none", "critical", "warning"), default="warning")
    add_common_json_flag(audit)

    query_parser = subparsers.add_parser("query", help="Read-only query over wiki/indexes with provenance")
    add_root_flag(query_parser)
    query_parser.add_argument("query", help="Question or search text")
    query_parser.add_argument("--limit", type=int, default=5, help="Maximum results")
    query_parser.add_argument("--lexical", action="store_true", help="Use lexical retrieval instead of FTS5")
    query_parser.add_argument("--semantic", action="store_true", help="Require optional semantic retrieval extra")
    add_common_json_flag(query_parser)

    derive = subparsers.add_parser("derive", help="Build rebuildable generated graph/FTS artifacts")
    add_root_flag(derive)
    derive.add_argument("--artifact", choices=("fts", "graph", "all"), default="all")
    derive.add_argument(
        "--include-unlayered", action="store_true", help="Include markdown outside default graph layers"
    )
    add_dry_run_apply_flags(derive)
    add_common_json_flag(derive)

    improve = subparsers.add_parser("improve", help="Queue review items for repairable KB lint findings")
    add_root_flag(improve)
    add_dry_run_apply_flags(improve)
    add_common_json_flag(improve)

    migrate = subparsers.add_parser("migrate", help="Create an additive migration plan with explicit approval gates")
    add_root_flag(migrate)
    migrate.add_argument("--target", required=True, help="Migration target path or scope")
    migrate.add_argument("--approval-token", help="Required token for apply: APPROVE-MIGRATION")
    add_dry_run_apply_flags(migrate)
    add_common_json_flag(migrate)

    replay = subparsers.add_parser("replay", help="Dry-run replay of operation journal entries")
    add_root_flag(replay)
    replay.add_argument("--operation-id", help="Operation ID to replay; defaults to all entries")
    add_common_json_flag(replay)

    watch = subparsers.add_parser("watch-classify", help="Classify a filesystem event without mutation")
    watch.add_argument("path", help="Vault-relative event path")
    watch.add_argument("--event-type", default="modified", help="Filesystem event type")
    watch.add_argument("--stable", action="store_true", help="Treat the event path as stable")
    add_common_json_flag(watch)

    return parser


def run_bootstrap(args: argparse.Namespace) -> int:
    """Run the compatibility bootstrap implementation."""
    module = kb_bootstrap()
    try:
        root = module.normalize_root(args.root)
        result = module.scaffold(root, force=args.force, dry_run=args.dry_run)
    except Exception as exc:  # pragma: no cover - CLI safeguard
        module.warn(str(exc))
        return emit_workflow_error("bootstrap", "create", args.root, exc, compact=args.compact)
    emit_json(result, compact=args.compact)
    return 0


def run_inventory(args: argparse.Namespace) -> int:
    """Run the compatibility inventory implementation."""
    module = kb_inventory()
    try:
        root = module.resolve_existing_root(args.root)
        result = module.build_inventory(root, max_examples=max(1, args.max_examples))
    except Exception as exc:  # pragma: no cover - CLI safeguard
        module.warn(str(exc))
        return emit_workflow_error("inventory", "audit", args.root, exc, compact=args.compact)
    emit_json(result, compact=args.compact)
    return 0


def run_lint(args: argparse.Namespace) -> int:
    """Run the compatibility lint implementation."""
    module = kb_lint()
    inventory_module = kb_inventory()
    try:
        root = inventory_module.resolve_existing_root(args.root)
        result = module.run_lint(root, include_unlayered=args.include_unlayered)
    except Exception as exc:  # pragma: no cover - CLI safeguard
        module.warn(str(exc))
        return emit_workflow_error("lint", "audit", args.root, exc, compact=args.compact)
    emit_json(result, compact=args.compact)
    return 1 if module.should_fail(result["issues"], args.fail_on) else 0


def build_suggested_next(mode: str, target_path: str) -> tuple[str, list[str]]:
    """Return the human command and argv-safe form for the next safe action."""
    _, argv = build_suggested_next_steps(mode, target_path)[0]
    return shlex.join(argv), argv


def build_suggested_next_steps(mode: str, target_path: str) -> list[tuple[str, list[str]]]:
    """Return ordered next commands while preserving the legacy first-step contract."""
    if mode == "create":
        argv = ["nerdbot", "bootstrap", "--root", target_path, "--dry-run"]
        return [(shlex.join(argv), argv)]
    if mode == "audit":
        steps = [
            ["nerdbot", "inventory", "--root", target_path],
            ["nerdbot", "lint", "--root", target_path, "--include-unlayered"],
        ]
        return [(shlex.join(argv), argv) for argv in steps]
    argv = ["nerdbot", "inventory", "--root", target_path]
    return [(shlex.join(argv), argv)]


def build_required_gates(mode: str) -> list[str]:
    """Return mode-specific plan gates without overstating read-only flows."""
    if mode == "query":
        return [
            "classify query scope",
            "inventory maintained wiki and indexes",
            "plan answer with note paths, provenance, confidence, and gaps",
            "inspect raw only to verify citations or confirm gaps",
            "handoff safe follow-up mode when the KB cannot answer confidently",
        ]
    if mode == "audit":
        return [
            "classify audit scope",
            "inventory layers, canonical material, vault state, and source surfaces",
            "lint structure, provenance, indexes, wikilinks, embeds, aliases, and activity log",
            "report critical, warning, and suggestion findings",
            "handoff the next smallest safe batch for explicit follow-up work",
        ]
    if mode == "migrate":
        return [
            "classify whether additive repair can avoid migration",
            "inventory canonical material, path consumers, vault state, and automation",
            "migration interview for authority, path consumers, wikilinks, aliases, Dataview, allowed moves, "
            "and rollback",
            "inversion against overwritten canon, broken references, unverifiable provenance, schema drift, "
            "and unclear rollback",
            "plan cutover gates with mapping pages, stable names, compatibility updates, lint, and explicit approval",
            "confirm destructive or high-impact changes before any move, rename, replacement, or cutover",
            "execute smallest approved migration batch",
            "verify provenance, indexes, schema, config, activity log, aliases, Dataview, and rollback readiness",
        ]
    return [
        "classify",
        "inventory",
        "plan",
        "confirm destructive or high-impact changes",
        "execute smallest additive batch",
        "verify provenance, indexes, schema, config, and activity log",
    ]


def build_plan_payload(mode: str, target: str) -> dict[str, Any]:
    """Build a conservative plan skeleton without mutating files."""
    target_path = Path(target).as_posix()
    next_command, next_argv = build_suggested_next(mode, target_path)
    next_steps = build_suggested_next_steps(mode, target_path)
    return {
        "mode": mode,
        "visual": MODE_VISUALS[mode],
        "summary": MODE_SUMMARIES[mode],
        "target": target_path,
        "read_only_default": mode in READ_ONLY_MODES,
        "required_gates": build_required_gates(mode),
        "safety_promises": list(SAFETY_PROMISES),
        "expansion_lanes_not_deferred": list(REQUIRED_EXPANSION_LANES),
        "suggested_next_command": next_command,
        "suggested_next_argv": next_argv,
        "suggested_next_commands": [command for command, _ in next_steps],
        "suggested_next_argvs": [argv for _, argv in next_steps],
    }


def build_modes_payload() -> dict[str, Any]:
    """Build the discoverable mode gallery payload."""
    return {
        "modes": [
            {
                "mode": mode,
                "visual": MODE_VISUALS[mode],
                "summary": MODE_SUMMARIES[mode],
                "read_only_default": mode in READ_ONLY_MODES,
            }
            for mode in MODES
        ],
        "safe_start": [
            "nerdbot modes",
            "nerdbot inventory --root ./kb",
            "nerdbot plan --mode ingest --target ./incoming/source.pdf --view guide",
        ],
    }


GUIDE_WIDTH = 92


def render_rule(label: str = "", *, width: int = GUIDE_WIDTH) -> str:
    """Render an ASCII rule that stays readable in narrow terminals and logs."""
    if not label:
        return "-" * width
    title = f" {label.strip()} "
    return title.center(width, "-")


def render_command_card(command: str, *, width: int = GUIDE_WIDTH) -> str:
    """Render a copy-friendly command line without requiring terminal styling packages."""
    return f"  $ {command}"[:width]


def render_modes_guide(payload: dict[str, Any]) -> str:
    """Render a dependency-free terminal mode gallery with a stronger visual hierarchy."""
    lines = [
        "Nerdbot Workflow Gallery",
        render_rule("local-first Obsidian KB cockpit"),
        "Choose a mode by risk posture, then preview its gate path before applying changes.",
        "",
        "Mode       Risk posture          Purpose",
        render_rule(),
    ]
    for item in payload["modes"]:
        access = "read-only" if item["read_only_default"] else "mutating after gates"
        lines.append(f"{item['visual']:<7} {item['mode']:<10} {access:<21} {item['summary']}")
    lines.extend(
        [
            render_rule(),
            "",
            "Safe starts:",
            "Review these dry-run/read-only commands before any `--apply` workflow.",
        ]
    )
    lines.extend(render_command_card(command) for command in payload["safe_start"])
    return "\n".join(lines)


def render_plan_guide(payload: dict[str, Any]) -> str:
    """Render a plan as a dependency-free, visually scannable terminal guide."""
    access = "read-only" if payload["read_only_default"] else "mutating after approval gates"
    title = f"{payload['visual']} Nerdbot {payload['mode']} plan"
    lines = [
        title,
        render_rule("workflow gate path"),
        f"Target: {payload['target']}",
        f"Default: {access}",
        f"Purpose: {payload['summary']}",
        "",
        "Gate path:",
    ]
    lines.extend(f"{index}. {gate}" for index, gate in enumerate(payload["required_gates"], start=1))
    lines.extend(["", render_rule("safety"), "Safety promises:"])
    lines.extend(f"- {promise}" for promise in payload["safety_promises"])
    lines.extend(["", render_rule("roadmap visibility"), "Expansion lanes kept visible:"])
    lines.extend(f"- {lane}" for lane in payload["expansion_lanes_not_deferred"])
    if len(payload["suggested_next_commands"]) == 1:
        lines.extend(["", render_rule("next safe command"), render_command_card(payload["suggested_next_command"])])
    else:
        lines.extend(["", render_rule("next safe commands"), "Next commands:"])
        lines.extend(render_command_card(command) for command in payload["suggested_next_commands"])
    return "\n".join(lines)


def run_plan(args: argparse.Namespace) -> int:
    """Emit a mode-specific plan skeleton."""
    payload = build_plan_payload(args.mode, args.target)
    if args.view == "guide":
        emit_text(render_plan_guide(payload))
    else:
        emit_json(payload, compact=args.compact)
    return 0


def run_modes(args: argparse.Namespace) -> int:
    """Show available workflow modes."""
    payload = build_modes_payload()
    if args.view == "guide":
        emit_text(render_modes_guide(payload))
    else:
        emit_json(payload, compact=args.compact)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Execute the Nerdbot CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        emit_text(render_modes_guide(build_modes_payload()))
        return 0
    if args.command == "bootstrap":
        return run_bootstrap(args)
    if args.command == "inventory":
        return run_inventory(args)
    if args.command == "lint":
        return run_lint(args)
    if args.command == "plan":
        return run_plan(args)
    if args.command == "modes":
        return run_modes(args)
    if args.command == "create":
        module = kb_bootstrap()
        try:
            root = module.normalize_root(args.root)
            emit_json(
                build_create_result(root=root, apply=args.apply, force=args.force, bootstrap_module=module),
                compact=args.compact,
            )
        except Exception as exc:  # pragma: no cover - CLI safeguard
            emit_json(
                command_envelope(command="create", mode="create", target=args.root, dry_run=True, errors=[str(exc)]),
                compact=args.compact,
            )
            return 1
        return 0
    if args.command == "ingest":
        try:
            exit_code, payload = build_ingest_result(args)
        except Exception as exc:  # pragma: no cover - CLI safeguard
            return emit_workflow_error("ingest", "ingest", args.source or "inline:text", exc, compact=args.compact)
        emit_json(payload, compact=args.compact)
        return exit_code
    if args.command == "enrich":
        try:
            payload = build_enrich_result(args)
        except Exception as exc:  # pragma: no cover - CLI safeguard
            return emit_workflow_error("enrich", "enrich", args.target, exc, compact=args.compact)
        emit_json(payload, compact=args.compact)
        return 0
    if args.command == "audit":
        inventory_module = kb_inventory()
        lint_module = kb_lint()
        try:
            root = inventory_module.resolve_existing_root(args.root)
            inventory = inventory_module.build_inventory(root)
            lint_result = lint_module.run_lint(root, include_unlayered=args.include_unlayered)
        except Exception as exc:  # pragma: no cover - CLI safeguard
            emit_json(
                command_envelope(command="audit", mode="audit", target=args.root, dry_run=True, errors=[str(exc)]),
                compact=args.compact,
            )
            return 1
        emit_json(
            command_envelope(
                command="audit",
                mode="audit",
                target=root.as_posix(),
                dry_run=True,
                payload={"inventory": inventory, "lint": lint_result},
            ),
            compact=args.compact,
        )
        return 1 if lint_module.should_fail(lint_result["issues"], args.fail_on) else 0
    if args.command == "query":
        try:
            payload = build_query_result(args)
        except Exception as exc:  # pragma: no cover - CLI safeguard
            return emit_workflow_error("query", "query", args.query, exc, compact=args.compact)
        emit_json(payload, compact=args.compact)
        return 2 if payload["status"] == "error" else 0
    if args.command == "derive":
        try:
            payload = build_derive_result(args)
        except Exception as exc:  # pragma: no cover - CLI safeguard
            return emit_workflow_error("derive", "derive", args.artifact, exc, compact=args.compact)
        emit_json(payload, compact=args.compact)
        return 0
    if args.command == "improve":
        try:
            payload = build_improve_result(args, lint_module=kb_lint(), inventory_module=kb_inventory())
        except Exception as exc:  # pragma: no cover - CLI safeguard
            return emit_workflow_error("improve", "improve", args.root, exc, compact=args.compact)
        emit_json(payload, compact=args.compact)
        return 0
    if args.command == "migrate":
        try:
            exit_code, payload = build_migrate_result(args)
        except Exception as exc:  # pragma: no cover - CLI safeguard
            return emit_workflow_error("migrate", "migrate", args.target, exc, compact=args.compact)
        emit_json(payload, compact=args.compact)
        return exit_code
    if args.command == "replay":
        try:
            payload = build_replay_result(args)
        except Exception as exc:  # pragma: no cover - CLI safeguard
            return emit_workflow_error("replay", "audit", args.root, exc, compact=args.compact)
        emit_json(payload, compact=args.compact)
        return 0
    if args.command == "watch-classify":
        try:
            payload = build_watch_classify_result(args)
        except Exception as exc:  # pragma: no cover - CLI safeguard
            return emit_workflow_error("watch-classify", "audit", args.path, exc, compact=args.compact)
        emit_json(payload, compact=args.compact)
        return 0
    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
