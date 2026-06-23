"""Tests for the design read-only scanner."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_scanner():
    path = ROOT / "skills" / "design" / "scripts" / "scan_frontend.py"
    spec = importlib.util.spec_from_file_location("frontend_scan", path)
    assert spec is not None
    assert spec.loader is not None
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


def test_scan_flags_mixed_guarded_and_unguarded_experimental_css(tmp_path: Path):
    (tmp_path / "app.css").write_text(
        """
        @supports (anchor-name: --x) {
          .popover { anchor-name: --trigger; position-anchor: --trigger; }
        }
        .menu { top: anchor(bottom); }
        """,
        encoding="utf-8",
    )

    result = scanner.scan(tmp_path)

    assert result["experimental_feature_counts"]["anchor-positioning"] >= 1
    assert result["unguarded_experimental_features"] == ["anchor-positioning"]


def test_scan_discovers_project_root_and_ignores_generated_directories(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"next": "16.0.7"}, "devDependencies": {"three": "0.182.0"}}),
        encoding="utf-8",
    )
    (tmp_path / "components.json").write_text("{}", encoding="utf-8")
    (src / "App.tsx").write_text("export const App = () => <main />\n", encoding="utf-8")
    generated = src / "node_modules"
    generated.mkdir()
    (generated / "Bad.tsx").write_text("<img src='x.png'>", encoding="utf-8")

    result = scanner.scan(src)

    assert result["project_root"] == str(tmp_path)
    assert result["package_versions"]["next"] == "16.0.7"
    assert result["package_versions"]["three"] == "0.182.0"
    assert result["components_json"] == str(tmp_path / "components.json")
    assert result["accessibility_signal_counts"]["img_without_alt"] == 0


def test_scan_prunes_ignored_dirs_and_uses_deterministic_file_order(tmp_path: Path):
    (tmp_path / "z.css").write_text(".z { font-family: Zeta; }\n", encoding="utf-8")
    (tmp_path / "a.css").write_text(".a { font-family: Alpha; }\n", encoding="utf-8")
    ignored = tmp_path / "node_modules" / "pkg"
    ignored.mkdir(parents=True)
    (ignored / "bad.css").write_text(".bad { font-family: Ignored; }\n", encoding="utf-8")

    result = scanner.scan(tmp_path)

    assert result["font_family_samples"] == ["Alpha", "Zeta"]


def test_scan_reports_accessibility_motion_and_text_layout_risks(tmp_path: Path):
    (tmp_path / "Widget.tsx").write_text(
        """
        export function Widget() {
          return (
            <section>
              <button><XIcon /></button>
              <div onClick={() => null}>Clickable</div>
              <input />
              <img src="/hero.png" />
              <p className="truncate overflow-hidden h-[48px]">Long status text</p>
            </section>
          )
        }
        """,
        encoding="utf-8",
    )
    (tmp_path / "motion.css").write_text(
        """
        .panel {
          transition: all 500ms;
          will-change: transform;
          animation: pulse 900ms infinite;
          outline: none;
        }
        """,
        encoding="utf-8",
    )

    result = scanner.scan(tmp_path)

    assert result["accessibility_signal_counts"]["icon_only_button_without_label"] == 1
    assert result["accessibility_signal_counts"]["click_handler_on_noninteractive"] == 1
    assert result["accessibility_signal_counts"]["field_without_label_signal"] == 1
    assert result["accessibility_signal_counts"]["img_without_alt"] == 1
    assert result["accessibility_signal_counts"]["img_without_dimensions"] == 1
    assert result["accessibility_signal_counts"]["focus_outline_removed"] == 1
    assert result["motion_signal_counts"]["transition_all_mentions"] == 1
    assert result["motion_signal_counts"]["will_change_mentions"] == 1
    assert result["motion_signal_counts"]["high_frequency_motion_mentions"] == 1
    assert result["motion_signal_counts"]["long_duration_mentions"] >= 2
    assert result["motion_signal_counts"]["unguarded_motion"] >= 1
    assert result["text_layout_risk_counts"]["nowrap_or_truncate"] >= 1
    assert result["text_layout_risk_counts"]["overflow_clipping"] >= 1
    assert result["text_layout_risk_counts"]["fixed_size"] >= 1


def test_scan_reports_badge_signals_proof_readiness_and_artifact_noise(tmp_path: Path):
    (tmp_path / "package.json").write_text(
        json.dumps({
            "dependencies": {"react": "19.2.5"},
            "devDependencies": {"vite": "8.0.10"},
            "scripts": {"dev": "vite", "build": "vite build"},
        }),
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text(
        """
        # Project

        <!-- BADGES:START -->
        [![npm](https://img.shields.io/npm/v/{package}.svg?style=flat-square&logo=npm&logoColor=white)](https://www.npmjs.com/package/{package})
        [![docs](https://shieldcn.dev/badge/docs-live.svg)](https://example.com/docs)
        [![go](https://pkg.go.dev/badge/example.com/project.svg)](https://pkg.go.dev/example.com/project)
        [![old deps](https://david-dm.org/example/project.svg)](https://david-dm.org/example/project)
        <!-- BADGES:END -->
        """,
        encoding="utf-8",
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "App.tsx").write_text("export const App = () => <main />\n", encoding="utf-8")
    (tmp_path / ".DS_Store").write_text("noise", encoding="utf-8")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "scan.pyc").write_bytes(b"x")
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist" / "design-v2.0.0.skill.zip").write_bytes(b"x")
    (tmp_path / "screenshots").mkdir()
    (tmp_path / "screenshots" / "home-screenshot.png").write_bytes(b"x")
    (tmp_path / "trace.har").write_text("{}", encoding="utf-8")

    result = scanner.scan(tmp_path)

    assert result["badge_signal_counts"]["badge_url_mentions"] >= 2
    assert result["badge_signal_counts"]["shieldcn_mentions"] == 1
    assert result["badge_signal_counts"]["badge_marker_mentions"] == 2
    assert result["badge_signal_counts"]["badge_placeholder_mentions"] >= 1
    assert result["badge_signal_counts"]["badge_image_urls"] >= 3
    assert result["badge_provider_counts"]["shields"] >= 1
    assert result["badge_provider_counts"]["shieldcn"] == 1
    assert result["badge_provider_counts"]["pkg_go_dev"] == 1
    assert result["badge_style_counts"]["style_mentions"] == 1
    assert result["badge_style_counts"]["logo_mentions"] == 1
    assert result["badge_style_counts"]["logo_color_mentions"] == 1
    assert result["badge_dead_service_counts"]["david-dm.org"] >= 1
    assert "{package}" in result["badge_placeholder_samples"]
    assert result["readme_badge_block"]["path"] == str(tmp_path / "README.md")
    assert result["readme_badge_block"]["has_badge_markers"] is True
    assert result["readme_badge_block"]["badge_marker_pairs"] == 1
    assert result["proof_readiness"]["runnable_scripts"] == ["build", "dev"]
    assert result["proof_readiness"]["has_browser_framework"] is True
    assert result["proof_readiness"]["needs_static_badge_proof"] is True
    assert result["proof_readiness"]["needs_rendered_proof"] is True
    assert result["proof_readiness"]["chrome_devtools_candidate"] is True
    assert result["risk_summary"]["badge_placeholders"] >= 1
    assert result["risk_summary"]["dead_badge_service_mentions"] >= 1
    assert result["risk_summary"]["artifact_noise_count"] >= 4
    assert result["artifact_noise"]["categories"]["macos_metadata"] == [".DS_Store"]
    assert "__pycache__" in result["artifact_noise"]["categories"]["python_cache"]
    assert "dist/design-v2.0.0.skill.zip" in result["artifact_noise"]["categories"]["packaged_zip"]
    assert "trace.har" in result["artifact_noise"]["categories"]["browser_trace"]
    assert "screenshots/home-screenshot.png" in result["artifact_noise"]["categories"]["screenshot_or_media"]


def test_scan_readme_only_badges_need_static_not_rendered_proof(tmp_path: Path):
    (tmp_path / "README.md").write_text(
        """
        # Project

        <!-- BADGES:START -->
        [![docs](https://shieldcn.dev/badge/docs-live.svg)](https://example.com/docs)
        <!-- BADGES:END -->
        """,
        encoding="utf-8",
    )

    result = scanner.scan(tmp_path)

    assert result["proof_readiness"]["needs_static_badge_proof"] is True
    assert result["proof_readiness"]["needs_rendered_proof"] is False
