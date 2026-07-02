"""Regression tests for data-wizard visualization scripts."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("pandas")

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = ROOT / "skills" / "data-wizard" / "scripts"
GRAMMAR = ROOT / "skills" / "data-wizard" / "data" / "visualization-grammar.json"
TEMPLATE = ROOT / "skills" / "data-wizard" / "templates" / "dashboard.html"


def _load_module(name: str, filename: str):
    path = SCRIPT_DIR / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def viz_planner():
    return _load_module("data_wizard_viz_planner", "viz-planner.py")


@pytest.fixture(scope="module")
def viz_renderer():
    return _load_module("data_wizard_viz_renderer", "viz-renderer.py")


@pytest.fixture(scope="module")
def dashboard_builder():
    return _load_module("data_wizard_dashboard_builder", "dashboard-builder.py")


@pytest.fixture
def sales_csv(tmp_path: Path) -> Path:
    csv_path = tmp_path / "sales.csv"
    csv_path.write_text(
        "region,product,revenue,units\n"
        "North,Widget,1200,40\n"
        "South,Widget,900,30\n"
        "North,Gadget,1500,25\n"
        "South,Gadget,1100,22\n",
        encoding="utf-8",
    )
    return csv_path


def test_viz_planner_build_plan_compare_goal(viz_planner, sales_csv: Path) -> None:
    plan = viz_planner.build_plan(str(sales_csv), "compare regions", GRAMMAR, max_rows=100)

    assert plan["goal_category"] == "comparison"
    assert plan["data_summary"]["rows"] == 4
    assert "region" in plan["data_summary"]["categorical_columns"]
    assert "revenue" in plan["data_summary"]["numeric_columns"]
    assert len(plan["charts"]) >= 1
    assert plan["charts"][0]["type"] == "bar_chart"


def test_viz_planner_default_palette_is_viridis(viz_planner, sales_csv: Path) -> None:
    plan = viz_planner.build_plan(str(sales_csv), "compare regions", GRAMMAR, max_rows=100)

    assert plan["color_palette"] == "viridis"


def test_viz_planner_cli_emits_json(sales_csv: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_DIR / "viz-planner.py"),
            str(sales_csv),
            "--goal",
            "compare groups",
            "--grammar",
            str(GRAMMAR),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    plan = json.loads(result.stdout)
    assert plan["goal_category"] == "comparison"
    assert plan["charts"]


def test_grouped_bar_render_matplotlib(viz_planner, viz_renderer, sales_csv: Path, tmp_path: Path) -> None:
    pytest.importorskip("matplotlib")

    plan = viz_planner.build_plan(str(sales_csv), "compare regions", GRAMMAR, max_rows=100)
    grouped = next(chart for chart in plan["charts"] if chart["type"] == "grouped_bar")
    output_dir = tmp_path / "viz-output"

    result = viz_renderer.render_plan(
        {"charts": [grouped]},
        str(sales_csv),
        output_dir,
        "png",
        max_rows=100,
    )

    assert result["status"] == "success"
    assert len(result["outputs"]) == 1
    output_path = Path(result["outputs"][0]["path"])
    assert output_path.exists()
    assert output_path.suffix == ".png"


def test_stacked_bar_render_matplotlib(viz_renderer, sales_csv: Path, tmp_path: Path) -> None:
    pytest.importorskip("matplotlib")

    chart = {
        "id": "chart_stacked_revenue",
        "type": "stacked_bar",
        "title": "Revenue composition by region and product",
        "encodings": {
            "x": "region",
            "y": "revenue",
            "color": "product",
        },
    }
    output_dir = tmp_path / "stacked-output"

    result = viz_renderer.render_plan(
        {"charts": [chart]},
        str(sales_csv),
        output_dir,
        "png",
        max_rows=100,
    )

    assert result["status"] == "success"
    assert Path(result["outputs"][0]["path"]).exists()


def test_planner_renderer_grouped_bar_integration(viz_planner, viz_renderer, sales_csv: Path, tmp_path: Path) -> None:
    pytest.importorskip("matplotlib")

    plan = viz_planner.build_plan(str(sales_csv), "compare regions", GRAMMAR, max_rows=100)
    output_dir = tmp_path / "pipeline-output"

    result = viz_renderer.render_plan(plan, str(sales_csv), output_dir, "png", max_rows=100)

    assert result["status"] in {"success", "partial"}
    assert result["outputs"]
    for output in result["outputs"]:
        assert Path(output["path"]).exists()


def test_viz_renderer_parquet_respects_max_rows(viz_renderer, tmp_path: Path) -> None:
    pytest.importorskip("pyarrow")

    parquet_path = tmp_path / "sample.parquet"
    df = __import__("pandas").DataFrame({"region": ["North", "South", "East"], "revenue": [1, 2, 3]})
    df.to_parquet(parquet_path)

    loaded = viz_renderer.load_data(str(parquet_path), max_rows=2)

    assert len(loaded) == 2


def test_dashboard_builder_smoke(dashboard_builder, tmp_path: Path) -> None:
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(
        json.dumps(
            {
                "file": "sales.csv",
                "rows": 4,
                "columns": 4,
                "memory_mb": 0.01,
                "dtype_summary": {"numeric": 2, "categorical": 2},
            }
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "dashboard.html"

    result = dashboard_builder.write_dashboard(
        profile_path=profile_path,
        output_path=output_path,
        template_path=TEMPLATE,
        grammar_path=GRAMMAR,
        viz_plan_path=None,
        render_path=None,
        views=["summary"],
        title="Test Dashboard",
    )

    assert result["status"] == "success"
    assert output_path.exists()
    html = output_path.read_text(encoding="utf-8")
    assert "Test Dashboard" in html
    assert '<script id="data" type="application/json">' in html