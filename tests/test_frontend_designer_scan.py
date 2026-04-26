"""Tests for the frontend-designer read-only scanner."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_scanner():
    path = ROOT / "skills" / "frontend-designer" / "scripts" / "scan_frontend.py"
    spec = importlib.util.spec_from_file_location("frontend_scan", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


scanner = _load_scanner()


def test_scan_reports_legacy_tailwind_config_and_package_versions(tmp_path: Path):
    (tmp_path / "tailwind.config.js").write_text("module.exports = {}\n", encoding="utf-8")
    (tmp_path / "package.json").write_text(
        json.dumps({
            "dependencies": {"react": "19.2.5"},
            "devDependencies": {"tailwindcss": "4.2.4", "vite": "8.0.10"},
            "scripts": {"build": "vite build", "dev": "vite"},
        }),
        encoding="utf-8",
    )

    result = scanner.scan(tmp_path)

    assert result["tailwind_config_files"] == ["tailwind.config.js"]
    assert result["package_versions"]["react"] == "19.2.5"
    assert result["package_versions"]["tailwindcss"] == "4.2.4"
    assert result["package_scripts"]["build"] == "vite build"


def test_scan_flags_hardcoded_colors_physical_direction_and_default_fonts(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "Card.tsx").write_text(
        """
        "use client";
        export function Card() {
          return <section className="ml-4 text-left bg-[#ff0000]">Hi</section>
        }
        """,
        encoding="utf-8",
    )
    (src / "style.css").write_text(
        """
        .card {
          margin-left: 1rem;
          color: rgb(255 0 0);
          font-family: Inter, system-ui, sans-serif;
        }
        """,
        encoding="utf-8",
    )

    result = scanner.scan(tmp_path)

    assert result["use_client_count"] == 1
    assert result["hardcoded_color_count"] >= 2
    assert "#ff0000" in result["hardcoded_color_samples"]
    assert result["physical_direction_count"] >= 2
    assert "Inter" in result["default_font_mentions"]
    assert "system-ui" in result["default_font_mentions"]


def test_scan_accepts_clean_modern_css_with_supports_guard(tmp_path: Path):
    (tmp_path / "app.css").write_text(
        """
        @import "tailwindcss";
        @theme { --color-brand: oklch(0.72 0.11 178); }
        .card { container-type: inline-size; }
        @container (min-inline-size: 30rem) { .card { display: grid; } }
        @supports (anchor-name: --x) {
          .popover { anchor-name: --trigger; position-anchor: --trigger; }
        }
        """,
        encoding="utf-8",
    )

    result = scanner.scan(tmp_path)

    assert result["tailwind_config_files"] == []
    assert result["container_query_count"] >= 1
    assert result["supports_block_count"] == 1
    assert result["unguarded_experimental_features"] == []
