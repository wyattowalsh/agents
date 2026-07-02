#!/usr/bin/env python3
"""Build composable EDA HTML dashboard from profile JSON and optional viz artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE = SKILL_DIR / "templates" / "dashboard.html"
DEFAULT_GRAMMAR = SKILL_DIR / "data" / "visualization-grammar.json"

DEFAULT_VIEWS = ["summary", "quality", "columns", "correlations", "missing"]


def load_json(path: Path) -> dict:
    if not path.exists():
        print(json.dumps({"error": f"File not found: {path}"}), file=sys.stderr)
        sys.exit(1)
    return json.loads(path.read_text(encoding="utf-8"))


def load_grammar_views(grammar_path: Path) -> list[str]:
    if not grammar_path.exists():
        return DEFAULT_VIEWS
    grammar = json.loads(grammar_path.read_text(encoding="utf-8"))
    dashboard_views = grammar.get("dashboard_views", {}).get("views", {})
    if not dashboard_views:
        return DEFAULT_VIEWS
    return list(dashboard_views.keys())


def build_dashboard_payload(
    profile: dict,
    viz_plan: dict | None,
    render_result: dict | None,
    views: list[str] | None,
    title: str | None,
) -> dict:
    active_views = list(views or DEFAULT_VIEWS)
    payload: dict = {
        "view": " ".join(active_views),
        "title": title or f"EDA Report — {profile.get('file', 'dataset')}",
        "file": profile.get("file"),
        "rows": profile.get("rows"),
        "columns": profile.get("columns"),
        "memory_mb": profile.get("memory_mb"),
        "dtype_summary": profile.get("dtype_summary"),
        "column_profiles": profile.get("column_profiles"),
        "correlations": profile.get("correlations"),
        "missing_patterns": profile.get("missing_patterns"),
        "duplicates": profile.get("duplicates"),
        "dimensions": profile.get("dimensions"),
        "overall": profile.get("overall"),
    }

    if viz_plan:
        if "charts" not in active_views:
            active_views.append("charts")
        payload["viz_plan"] = viz_plan
        payload["view"] = " ".join(active_views)

    if render_result:
        payload["chart_outputs"] = render_result.get("outputs", [])
        if render_result.get("output_dir"):
            payload["chart_output_dir"] = render_result["output_dir"]

    return {k: v for k, v in payload.items() if v is not None}


def inject_dashboard_data(template_html: str, payload: dict) -> str:
    data_json = json.dumps(payload, default=str)
    pattern = r'(<script id="data" type="application/json">)(.*?)(</script>)'

    def repl(match: re.Match[str]) -> str:
        return f"{match.group(1)}{data_json}{match.group(3)}"

    updated, count = re.subn(pattern, repl, template_html, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError("Template missing <script id=\"data\" type=\"application/json\"> block")
    return updated


def write_dashboard(
    profile_path: Path,
    output_path: Path,
    template_path: Path,
    grammar_path: Path,
    viz_plan_path: Path | None,
    render_path: Path | None,
    views: list[str] | None,
    title: str | None,
) -> dict:
    profile = load_json(profile_path)
    viz_plan = load_json(viz_plan_path) if viz_plan_path else None
    render_result = load_json(render_path) if render_path else None

    if views is None:
        grammar_views = load_grammar_views(grammar_path)
        views = [v for v in grammar_views if v != "charts"]
        if (viz_plan or render_result) and "charts" in grammar_views:
            views.append("charts")

    payload = build_dashboard_payload(profile, viz_plan, render_result, views, title)
    template_html = template_path.read_text(encoding="utf-8")
    html = inject_dashboard_data(template_html, payload)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    return {
        "status": "success",
        "output": str(output_path.resolve()),
        "views": payload.get("view", "").split(),
        "title": payload.get("title"),
        "charts": len(payload.get("chart_outputs", [])),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build EDA HTML dashboard from profile JSON")
    parser.add_argument("profile", help="Path to data-profiler or quality-scorer JSON output")
    parser.add_argument(
        "--output",
        default="./data-wizard-dashboard.html",
        help="Output HTML path",
    )
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE), help="Dashboard HTML template")
    parser.add_argument("--grammar", default=str(DEFAULT_GRAMMAR), help="Visualization grammar JSON")
    parser.add_argument("--viz-plan", default=None, help="Optional viz-planner JSON output")
    parser.add_argument("--render-result", default=None, help="Optional viz-renderer JSON output")
    parser.add_argument("--views", nargs="*", default=None, help="Dashboard views to include")
    parser.add_argument("--title", default=None, help="Dashboard title override")
    args = parser.parse_args()

    try:
        result = write_dashboard(
            profile_path=Path(args.profile),
            output_path=Path(args.output),
            template_path=Path(args.template),
            grammar_path=Path(args.grammar),
            viz_plan_path=Path(args.viz_plan) if args.viz_plan else None,
            render_path=Path(args.render_result) if args.render_result else None,
            views=args.views,
            title=args.title,
        )
        print(json.dumps(result, indent=2, default=str))
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()