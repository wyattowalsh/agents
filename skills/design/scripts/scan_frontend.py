#!/usr/bin/env python3
"""Read-only frontend and interface design signal scanner for /design."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

TEXT_EXTENSIONS = {".css", ".js", ".jsx", ".ts", ".tsx", ".html", ".md", ".mdx"}
IGNORED_DIR_NAMES = {
    ".git",
    ".next",
    ".nuxt",
    ".svelte-kit",
    ".turbo",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "storybook-static",
}
PACKAGE_NAMES = (
    "react",
    "react-dom",
    "tailwindcss",
    "vite",
    "next",
    "remix",
    "three",
    "framer-motion",
    "motion",
    "shadcn",
    "@vitejs/plugin-react",
    "@vitejs/plugin-react-swc",
    "@react-three/fiber",
)

COLOR_RE = re.compile(r"(#[0-9a-fA-F]{3,8}\b|rgba?\([^)]+\)|hsla?\([^)]+\))")
USE_CLIENT_RE = re.compile(r"^\s*['\"]use client['\"]\s*;?", re.MULTILINE)
FONT_RE = re.compile(r"font-family\s*:\s*([^;]+)", re.IGNORECASE)
DEFAULT_FONT_RE = re.compile(r"\b(Inter|Roboto|Arial|system-ui)\b", re.IGNORECASE)
PHYSICAL_CSS_RE = re.compile(
    r"\b(margin|padding|border)-(left|right)\b|\b(left|right)\s*:|"
    r"\btext-align\s*:\s*(left|right)\b|\bfloat\s*:\s*(left|right)\b",
    re.IGNORECASE,
)
PHYSICAL_CLASS_RE = re.compile(
    r"\b(?:m[lr]|p[lr]|left|right|text-(?:left|right)|rounded-[lr]|border-[lr])-[A-Za-z0-9_\[\]/.-]+"
)
FEATURE_PATTERNS = {
    "anchor-positioning": re.compile(r"\banchor-name\b|\bposition-anchor\b|\banchor\(", re.IGNORECASE),
    "scroll-driven-animation": re.compile(
        r"\banimation-timeline\b|\bscroll-timeline\b|\bview-timeline\b",
        re.IGNORECASE,
    ),
    "scope": re.compile(r"@scope\b", re.IGNORECASE),
    "contrast-color": re.compile(r"\bcontrast-color\(", re.IGNORECASE),
    "view-transition": re.compile(r"\bview-transition-name\b|::view-transition|startViewTransition", re.IGNORECASE),
}

IMG_WITHOUT_ALT_RE = re.compile(r"<img\b(?![^>]*\balt=)[^>]*>", re.IGNORECASE)
IMG_WITHOUT_DIMENSIONS_RE = re.compile(r"<img\b(?!(?=[^>]*\bwidth=)(?=[^>]*\bheight=))[^>]*>", re.IGNORECASE)
INPUT_WITHOUT_LABEL_RE = re.compile(
    r"<(?:input|textarea|select)\b(?![^>]*(?:aria-label=|aria-labelledby=|id=))[^>]*>",
    re.IGNORECASE,
)
ICON_ONLY_BUTTON_RE = re.compile(
    r"<button\b(?![^>]*\baria-label=)[^>]*>\s*<(?:svg|[A-Z][A-Za-z0-9]*)\b",
    re.IGNORECASE,
)
CLICK_NONINTERACTIVE_RE = re.compile(r"<(?:div|span|section|article)\b[^>]*\bonClick=", re.IGNORECASE)
FOCUS_REMOVAL_RE = re.compile(r"\b(?:focus:)?outline-none\b|outline\s*:\s*none", re.IGNORECASE)
LANDMARK_RE = re.compile(
    r"<(?:main|nav|header|footer|aside)\b|\brole=[\"'](?:main|navigation|banner|contentinfo|complementary)",
    re.IGNORECASE,
)
LABEL_RE = re.compile(r"<label\b|\baria-label=|\baria-labelledby=", re.IGNORECASE)

MOTION_RE = re.compile(
    r"@keyframes\b|\banimation(?:-[a-z-]+)?\s*:|\btransition(?:-[a-z-]+)?\s*:|"
    r"\banimate-[A-Za-z0-9_\[\]/.-]+|\btransition-[A-Za-z0-9_\[\]/.-]+|"
    r"\bstartViewTransition\b|\brequestAnimationFrame\b",
    re.IGNORECASE,
)
REDUCED_MOTION_RE = re.compile(r"prefers-reduced-motion|motion-reduce|useReducedMotion", re.IGNORECASE)
HIGH_FREQUENCY_MOTION_RE = re.compile(r"\binfinite\b|\brequestAnimationFrame\b|\bsetInterval\b", re.IGNORECASE)
TRANSITION_ALL_RE = re.compile(r"\btransition\s*:\s*all\b|\btransition-all\b", re.IGNORECASE)
WILL_CHANGE_RE = re.compile(r"\bwill-change\s*:\s*(?:all|transform|opacity)|\bwill-change-\w+", re.IGNORECASE)
LONG_DURATION_RE = re.compile(
    r"(?:animation|transition)(?:-duration)?\s*:[^;]*\b(?:[4-9]\d\d|\d{4,})ms|"
    r"\bduration-(?:[4-9]\d\d|\d{4,})\b",
    re.IGNORECASE,
)

NOWRAP_RE = re.compile(r"\b(?:whitespace-nowrap|text-nowrap|truncate)\b|white-space\s*:\s*nowrap", re.IGNORECASE)
CLIPPING_RE = re.compile(r"\boverflow-hidden\b|overflow\s*:\s*hidden|\bline-clamp-\d+\b", re.IGNORECASE)
FIXED_SIZE_RE = re.compile(r"\b(?:h|w)-\[(?:\d+px|\d+rem)\]|\b(?:height|width)\s*:\s*\d+(?:px|rem)", re.IGNORECASE)
TABULAR_NUMS_RE = re.compile(r"\btabular-nums\b|font-variant-numeric\s*:\s*tabular-nums", re.IGNORECASE)
TEXT_WRAP_RE = re.compile(r"\btext-wrap\b|text-wrap\s*:", re.IGNORECASE)
BADGE_URL_RE = re.compile(
    r"(?:img\.shields\.io|shieldcn\.dev|badgen\.net|forthebadge\.com|badge\.svg|pkg\.go\.dev/badge|api\.scorecard\.dev)",
    re.IGNORECASE,
)
BADGE_IMAGE_RE = re.compile(
    r"(?:!\[[^\]]*\]\(([^)]+)\)|<img[^>]+src=[\"']([^\"']+)[\"'])",
    re.IGNORECASE,
)
SHIELDCN_RE = re.compile(r"shieldcn\.dev", re.IGNORECASE)
BADGE_MARKER_RE = re.compile(r"<!--\s*BADGES:(?:START|END)\s*-->", re.IGNORECASE)
BADGE_PLACEHOLDER_RE = re.compile(r"\{(?:owner|repo|package|pkg|workflow|branch|org|project)\}", re.IGNORECASE)
BADGE_PROVIDER_PATTERNS = {
    "shields": re.compile(r"img\.shields\.io", re.IGNORECASE),
    "shieldcn": SHIELDCN_RE,
    "badgen": re.compile(r"badgen\.net", re.IGNORECASE),
    "forthebadge": re.compile(r"forthebadge\.com", re.IGNORECASE),
    "native_github_actions": re.compile(r"github\.com/.+?/actions/workflows/.+?/badge\.svg", re.IGNORECASE),
    "codecov": re.compile(r"codecov\.io/.+?/badge\.svg|img\.shields\.io/codecov", re.IGNORECASE),
    "coveralls": re.compile(r"coveralls\.io/.+?/badge\.svg|img\.shields\.io/coveralls", re.IGNORECASE),
    "sonarcloud": re.compile(r"sonarcloud\.io/(?:api/project_badges|summary)", re.IGNORECASE),
    "openssf": re.compile(r"api\.scorecard\.dev|bestpractices\.dev", re.IGNORECASE),
    "pkg_go_dev": re.compile(r"pkg\.go\.dev/badge", re.IGNORECASE),
    "readthedocs": re.compile(r"readthedocs(?:\.org|\.io)", re.IGNORECASE),
}
DEAD_BADGE_SERVICE_PATTERNS = {
    "david-dm.org": re.compile(r"david-dm\.org", re.IGNORECASE),
    "godoc.org": re.compile(r"godoc\.org", re.IGNORECASE),
    "travis-ci.org": re.compile(r"travis-ci\.org", re.IGNORECASE),
}
BADGE_STYLE_RE = re.compile(r"(?:[?&]style=)(flat-square|flat|plastic|for-the-badge|social)", re.IGNORECASE)
BADGE_LOGO_RE = re.compile(r"(?:[?&]logo=)([A-Za-z0-9_.-]+)", re.IGNORECASE)
BADGE_LOGO_COLOR_RE = re.compile(r"(?:[?&]logoColor=)([A-Za-z0-9_.#%-]+)", re.IGNORECASE)
README_NAMES = ("README.md", "readme.md", "README.mdx", "README.rst", "README.adoc", "README.txt", "README")
SCREENSHOT_NAME_RE = re.compile(r"(?:screenshot|snapshot|trace|lighthouse)", re.IGNORECASE)
ARTIFACT_EXTENSIONS = {".har", ".heapsnapshot", ".trace", ".webm", ".mp4", ".zip"}
IMAGE_EXTENSIONS = {".apng", ".avif", ".gif", ".jpeg", ".jpg", ".png", ".webp"}
PROOF_SCRIPT_NAMES = ("dev", "start", "storybook", "preview", "build")
UI_FILE_EXTENSIONS = {".jsx", ".tsx", ".html", ".css"}


def is_ignored(path: Path) -> bool:
    return any(part in IGNORED_DIR_NAMES for part in path.parts)


def walk_sorted(root: Path, ignored_dirs: set[str]) -> Iterable[Path]:
    """Yield paths in deterministic order while pruning ignored directories."""
    for current, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(name for name in dirnames if name not in ignored_dirs)
        current_path = Path(current)
        for filename in sorted(filenames):
            yield current_path / filename
        for dirname in dirnames:
            yield current_path / dirname


def iter_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        if not is_ignored(root):
            yield root
        return
    for path in walk_sorted(root, IGNORED_DIR_NAMES):
        if path.is_file() and path.name not in {".DS_Store"}:
            yield path


def iter_noise_candidates(root: Path) -> Iterable[Path]:
    if root.is_file():
        yield root
        return
    for path in walk_sorted(root, {".git", "node_modules"}):
        path.relative_to(root)
        yield path


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def discover_project_root(target: Path) -> Path:
    start = target if target.is_dir() else target.parent
    markers = {
        "package.json",
        "components.json",
        "vite.config.ts",
        "vite.config.js",
        "next.config.js",
        "next.config.mjs",
    }
    for candidate in (start, *start.parents):
        if any((candidate / marker).exists() for marker in markers):
            return candidate
    return start


def load_package_json(project_root: Path) -> dict:
    package_path = project_root / "package.json"
    if not package_path.exists():
        return {}
    try:
        data = json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"_parse_error": str(package_path)}
    return data if isinstance(data, dict) else {}


def package_versions(package_json: dict) -> dict[str, str]:
    versions: dict[str, str] = {}
    for section in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        deps = package_json.get(section, {})
        if not isinstance(deps, dict):
            continue
        for name in PACKAGE_NAMES:
            if name in deps:
                versions[name] = str(deps[name])
    return versions


def count(pattern: re.Pattern[str], source_texts: list[tuple[Path, str]]) -> int:
    return sum(len(pattern.findall(text)) for _, text in source_texts)


def remove_supports_blocks(text: str) -> str:
    """Replace @supports blocks with whitespace so outside-feature offsets remain stable enough."""
    output: list[str] = []
    index = 0
    while True:
        match = re.search(r"@supports\b", text[index:], re.IGNORECASE)
        if not match:
            output.append(text[index:])
            break

        start = index + match.start()
        output.append(text[index:start])
        brace = text.find("{", start)
        if brace == -1:
            output.append(" " * (len(text) - start))
            break

        depth = 0
        end = brace
        while end < len(text):
            char = text[end]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    end += 1
                    break
            end += 1
        output.append(" " * (end - start))
        index = end
    return "".join(output)


def count_outside_supports(pattern: re.Pattern[str], source_texts: list[tuple[Path, str]]) -> int:
    return count(pattern, [(path, remove_supports_blocks(text)) for path, text in source_texts])


def sample(pattern: re.Pattern[str], source_texts: list[tuple[Path, str]], limit: int = 12) -> list[str]:
    values: list[str] = []
    for _, text in source_texts:
        for match in pattern.finditer(text):
            value = match.group(0)
            if value not in values:
                values.append(value)
            if len(values) >= limit:
                return values
    return values


def readme_info(root: Path, source_texts: list[tuple[Path, str]]) -> dict:
    readme_path = ""
    readme_format = ""
    for name in README_NAMES:
        candidate = root / name
        if candidate.is_file():
            readme_path = str(candidate)
            readme_format = candidate.suffix.lower().lstrip(".") or "plain"
            break

    readme_text = ""
    if readme_path:
        readme_text = read_text(Path(readme_path))
    elif len(source_texts) == 1 and source_texts[0][0].name.lower().startswith("readme"):
        readme_path = str(source_texts[0][0])
        readme_format = source_texts[0][0].suffix.lower().lstrip(".") or "plain"
        readme_text = source_texts[0][1]

    markers = BADGE_MARKER_RE.findall(readme_text)
    return {
        "path": readme_path,
        "format": readme_format,
        "has_badge_markers": bool(markers),
        "badge_marker_count": len(markers),
        "badge_marker_pairs": len(markers) // 2,
    }


def extract_badge_urls(source_texts: list[tuple[Path, str]], limit: int = 20) -> list[str]:
    urls: list[str] = []
    for _, text in source_texts:
        for md_url, html_url in BADGE_IMAGE_RE.findall(text):
            url = md_url or html_url
            if url and BADGE_URL_RE.search(url) and url not in urls:
                urls.append(url)
            if len(urls) >= limit:
                return urls
    return urls


def artifact_noise(root: Path) -> dict:
    categories: dict[str, list[str]] = {
        "macos_metadata": [],
        "python_cache": [],
        "packaged_zip": [],
        "browser_trace": [],
        "screenshot_or_media": [],
    }
    for path in iter_noise_candidates(root):
        name = path.name
        suffix = path.suffix.lower()
        display = str(path.relative_to(root)) if path != root else path.name
        if name == ".DS_Store":
            categories["macos_metadata"].append(display)
        if path.is_dir() and name == "__pycache__":
            categories["python_cache"].append(display)
        if suffix == ".zip":
            categories["packaged_zip"].append(display)
        if suffix in {".har", ".heapsnapshot", ".trace"} or name.endswith(".trace.json"):
            categories["browser_trace"].append(display)
        if suffix in ARTIFACT_EXTENSIONS - {".zip", ".har", ".heapsnapshot", ".trace"}:
            categories["browser_trace"].append(display)
        if suffix in IMAGE_EXTENSIONS and SCREENSHOT_NAME_RE.search(str(path)):
            categories["screenshot_or_media"].append(display)

    trimmed = {key: sorted(set(values))[:12] for key, values in categories.items()}
    return {
        "count": sum(len(values) for values in trimmed.values()),
        "categories": trimmed,
    }


def scan(root: Path) -> dict:
    target = root.resolve()
    project_root = discover_project_root(target).resolve()
    package_json = load_package_json(project_root)
    files = list(iter_files(target))
    text_files = [path for path in files if path.suffix in TEXT_EXTENSIONS or path.name == "package.json"]
    source_texts = [(path, read_text(path)) for path in text_files]
    combined = "\n".join(text for _, text in source_texts)
    supports_count = combined.count("@supports")

    feature_counts: dict[str, int] = {}
    unguarded_features: list[str] = []
    for feature, pattern in FEATURE_PATTERNS.items():
        feature_count = count(pattern, source_texts)
        feature_counts[feature] = feature_count
        if count_outside_supports(pattern, source_texts):
            unguarded_features.append(feature)

    font_families = [match.group(1).strip() for _, text in source_texts for match in FONT_RE.finditer(text)]
    motion_count = count(MOTION_RE, source_texts)
    reduced_motion_count = count(REDUCED_MOTION_RE, source_texts)
    versions = package_versions(package_json)
    scripts = package_json.get("scripts", {}) if isinstance(package_json.get("scripts"), dict) else {}
    runnable_scripts = sorted(name for name in PROOF_SCRIPT_NAMES if name in scripts)
    ui_file_count = sum(1 for path in text_files if path.suffix in UI_FILE_EXTENSIONS)
    badge_url_count = count(BADGE_URL_RE, source_texts)
    badge_placeholder_count = count(BADGE_PLACEHOLDER_RE, source_texts)
    badge_urls = extract_badge_urls(source_texts)
    badge_provider_counts = {name: count(pattern, source_texts) for name, pattern in BADGE_PROVIDER_PATTERNS.items()}
    dead_badge_counts = {name: count(pattern, source_texts) for name, pattern in DEAD_BADGE_SERVICE_PATTERNS.items()}
    readme_report = readme_info(project_root, source_texts)
    artifact_noise_report = artifact_noise(target)
    a11y_counts = {
        "img_without_alt": count(IMG_WITHOUT_ALT_RE, source_texts),
        "img_without_dimensions": count(IMG_WITHOUT_DIMENSIONS_RE, source_texts),
        "field_without_label_signal": count(INPUT_WITHOUT_LABEL_RE, source_texts),
        "icon_only_button_without_label": count(ICON_ONLY_BUTTON_RE, source_texts),
        "click_handler_on_noninteractive": count(CLICK_NONINTERACTIVE_RE, source_texts),
        "focus_outline_removed": count(FOCUS_REMOVAL_RE, source_texts),
        "landmark_mentions": count(LANDMARK_RE, source_texts),
        "label_mentions": count(LABEL_RE, source_texts),
    }
    motion_counts = {
        "motion_mentions": motion_count,
        "reduced_motion_mentions": reduced_motion_count,
        "high_frequency_motion_mentions": count(HIGH_FREQUENCY_MOTION_RE, source_texts),
        "transition_all_mentions": count(TRANSITION_ALL_RE, source_texts),
        "will_change_mentions": count(WILL_CHANGE_RE, source_texts),
        "long_duration_mentions": count(LONG_DURATION_RE, source_texts),
        "unguarded_motion": motion_count if motion_count and not reduced_motion_count else 0,
    }
    text_risk_counts = {
        "nowrap_or_truncate": count(NOWRAP_RE, source_texts),
        "overflow_clipping": count(CLIPPING_RE, source_texts),
        "fixed_size": count(FIXED_SIZE_RE, source_texts),
        "tabular_number_mentions": count(TABULAR_NUMS_RE, source_texts),
        "text_wrap_mentions": count(TEXT_WRAP_RE, source_texts),
    }

    return {
        "target": str(target),
        "project_root": str(project_root),
        "files_scanned": len(text_files),
        "ignored_directory_names": sorted(IGNORED_DIR_NAMES),
        "package_versions": versions,
        "package_scripts": scripts,
        "components_json": str(project_root / "components.json") if (project_root / "components.json").exists() else "",
        "tailwind_config_files": sorted(
            str(path.relative_to(target)) for path in files if path.name.startswith("tailwind.config.")
        ),
        "use_client_count": len(USE_CLIENT_RE.findall(combined)),
        "media_query_count": combined.count("@media"),
        "container_query_count": combined.count("@container"),
        "hardcoded_color_count": len(COLOR_RE.findall(combined)),
        "hardcoded_color_samples": sorted(set(COLOR_RE.findall(combined)))[:12],
        "physical_direction_count": count(PHYSICAL_CSS_RE, source_texts) + count(PHYSICAL_CLASS_RE, source_texts),
        "physical_direction_samples": sorted(set(PHYSICAL_CLASS_RE.findall(combined)))[:12],
        "font_family_count": len(font_families),
        "font_family_samples": font_families[:12],
        "default_font_mentions": sorted(set(DEFAULT_FONT_RE.findall(combined))),
        "supports_block_count": supports_count,
        "experimental_feature_counts": feature_counts,
        "unguarded_experimental_features": sorted(unguarded_features),
        "accessibility_signal_counts": a11y_counts,
        "motion_signal_counts": motion_counts,
        "text_layout_risk_counts": text_risk_counts,
        "text_layout_risk_samples": {
            "nowrap_or_truncate": sample(NOWRAP_RE, source_texts),
            "overflow_clipping": sample(CLIPPING_RE, source_texts),
            "fixed_size": sample(FIXED_SIZE_RE, source_texts),
        },
        "badge_signal_counts": {
            "badge_url_mentions": badge_url_count,
            "shieldcn_mentions": count(SHIELDCN_RE, source_texts),
            "badge_marker_mentions": count(BADGE_MARKER_RE, source_texts),
            "badge_placeholder_mentions": badge_placeholder_count,
            "badge_image_urls": len(badge_urls),
        },
        "badge_provider_counts": badge_provider_counts,
        "badge_style_counts": {
            "style_mentions": count(BADGE_STYLE_RE, source_texts),
            "logo_mentions": count(BADGE_LOGO_RE, source_texts),
            "logo_color_mentions": count(BADGE_LOGO_COLOR_RE, source_texts),
        },
        "badge_dead_service_counts": dead_badge_counts,
        "badge_url_samples": badge_urls,
        "badge_placeholder_samples": sample(BADGE_PLACEHOLDER_RE, source_texts),
        "readme_badge_block": readme_report,
        "artifact_noise": artifact_noise_report,
        "proof_readiness": {
            "runnable_scripts": runnable_scripts,
            "ui_file_count": ui_file_count,
            "has_components_json": bool((project_root / "components.json").exists()),
            "has_browser_framework": any(name in versions for name in ("next", "vite", "react", "react-dom", "remix")),
            "needs_static_badge_proof": bool(badge_url_count),
            "needs_rendered_proof": bool(ui_file_count or (project_root / "components.json").exists()),
            "chrome_devtools_candidate": bool(
                runnable_scripts or any(name in versions for name in ("next", "vite", "react", "react-dom"))
            ),
        },
        "risk_summary": {
            "accessibility_blocking_signals": sum(
                a11y_counts[name]
                for name in (
                    "img_without_alt",
                    "field_without_label_signal",
                    "icon_only_button_without_label",
                    "click_handler_on_noninteractive",
                    "focus_outline_removed",
                )
            ),
            "has_positive_accessibility_signals": bool(
                a11y_counts["landmark_mentions"] or a11y_counts["label_mentions"]
            ),
            "motion_needs_reduced_motion": bool(motion_counts["unguarded_motion"]),
            "text_clipping_signals": text_risk_counts["nowrap_or_truncate"] + text_risk_counts["overflow_clipping"],
            "artifact_noise_count": artifact_noise_report["count"],
            "badge_placeholders": badge_placeholder_count,
            "dead_badge_service_mentions": sum(dead_badge_counts.values()),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scan frontend/interface files and print JSON signals.")
    parser.add_argument("target", nargs="?", default=".", help="File or directory to scan")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    payload = scan(Path(args.target))
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
