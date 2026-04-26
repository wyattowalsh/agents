#!/usr/bin/env python3
"""Read-only frontend signal scanner for frontend-designer."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable


TEXT_EXTENSIONS = {".css", ".js", ".jsx", ".ts", ".tsx", ".html", ".mdx"}
PACKAGE_NAMES = (
    "react",
    "react-dom",
    "tailwindcss",
    "vite",
    "shadcn",
    "@vitejs/plugin-react",
    "@vitejs/plugin-react-swc",
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


def iter_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        yield root
        return
    for path in root.rglob("*"):
        if path.is_file() and path.name not in {".DS_Store"}:
            yield path


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def load_package_json(root: Path) -> dict:
    package_path = root / "package.json" if root.is_dir() else root.parent / "package.json"
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


def scan(root: Path) -> dict:
    root = root.resolve()
    package_json = load_package_json(root)
    files = list(iter_files(root))
    text_files = [path for path in files if path.suffix in TEXT_EXTENSIONS or path.name == "package.json"]
    source_texts = [(path, read_text(path)) for path in text_files]
    combined = "\n".join(text for _, text in source_texts)
    supports_count = combined.count("@supports")

    feature_counts: dict[str, int] = {}
    unguarded_features: list[str] = []
    for feature, pattern in FEATURE_PATTERNS.items():
        count = sum(len(pattern.findall(text)) for _, text in source_texts)
        feature_counts[feature] = count
        if count and not any("@supports" in text and pattern.search(text) for _, text in source_texts):
            unguarded_features.append(feature)

    font_families = [match.group(1).strip() for _, text in source_texts for match in FONT_RE.finditer(text)]

    return {
        "target": str(root),
        "files_scanned": len(text_files),
        "package_versions": package_versions(package_json),
        "package_scripts": package_json.get("scripts", {}) if isinstance(package_json.get("scripts"), dict) else {},
        "tailwind_config_files": sorted(
            str(path.relative_to(root)) for path in files if path.name.startswith("tailwind.config.")
        ),
        "use_client_count": len(USE_CLIENT_RE.findall(combined)),
        "media_query_count": combined.count("@media"),
        "container_query_count": combined.count("@container"),
        "hardcoded_color_count": len(COLOR_RE.findall(combined)),
        "hardcoded_color_samples": sorted(set(COLOR_RE.findall(combined)))[:12],
        "physical_direction_count": len(PHYSICAL_CSS_RE.findall(combined)) + len(PHYSICAL_CLASS_RE.findall(combined)),
        "physical_direction_samples": sorted(set(PHYSICAL_CLASS_RE.findall(combined)))[:12],
        "font_family_count": len(font_families),
        "font_family_samples": font_families[:12],
        "default_font_mentions": sorted(set(DEFAULT_FONT_RE.findall(combined))),
        "supports_block_count": supports_count,
        "experimental_feature_counts": feature_counts,
        "unguarded_experimental_features": sorted(unguarded_features),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scan frontend files and print JSON signals.")
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
