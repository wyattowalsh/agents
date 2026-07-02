#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from wagents.hooks.render import prepare_hooks_for_render

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "config/hook-registry.json"
HARNESSES = ("cursor", "codex", "claude-code", "github-copilot", "gemini-cli", "grok-build", "opencode")


def _pre_tool_count(registry, harness, *, tier):
    hooks = prepare_hooks_for_render(registry, harness, perf_tier=tier)
    return sum(1 for hook in hooks if hook.get("logical_event") == "PreToolUse")


def run_assurance(*, tier="bundle"):
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    findings = []
    per = {}
    for harness in HARNESSES:
        try:
            count = _pre_tool_count(registry, harness, tier=tier)
        except Exception as exc:
            count = 0
            findings.append(str(harness) + ": render failed (" + str(exc) + ")")
        per[harness] = count
        if count == 0 and harness in {"cursor", "codex", "github-copilot"}:
            findings.append(str(harness) + ": no PreToolUse hooks rendered under " + tier + " tier")
    if per.get("cursor", 99) > 3:
        findings.append("cursor PreToolUse spawn budget exceeded: " + str(per.get("cursor")) + " > 3")
    if per.get("codex", 99) > 3:
        findings.append("codex PreToolUse spawn budget exceeded: " + str(per.get("codex")) + " > 3")
    if per.get("github-copilot", 99) > 2:
        findings.append("github-copilot PreToolUse spawn budget exceeded: " + str(per.get("github-copilot")) + " > 2")
    return {"tier": tier, "pre_tool_use_counts": per, "findings": findings, "ok": not findings}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = run_assurance()
    if args.json:
        json.dump(report, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write(chr(10))
    else:
        print("ok" if report["ok"] else "fail")
        for item in report["findings"]:
            print("- " + item)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
