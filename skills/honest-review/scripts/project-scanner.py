#!/usr/bin/env python3
"""Wave 0 deterministic pre-scan: detect project type, compute metrics, stratify risk."""
from __future__ import annotations
import json, os, re, subprocess, sys
from collections import Counter
from pathlib import Path

MANIFEST_MAP: dict[str, tuple[str, str, str | None]] = {
    "pyproject.toml": ("python", "pyproject.toml", "uv"), "setup.py": ("python", "setup.py", "pip"),
    "requirements.txt": ("python", "requirements.txt", "pip"),
    "package.json": ("javascript", "package.json", None), "Cargo.toml": ("rust", "cargo", "cargo"),
    "go.mod": ("go", "go.mod", "go"), "Gemfile": ("ruby", "bundler", "bundler"),
    "pom.xml": ("java", "maven", "maven"), "build.gradle": ("java", "gradle", "gradle"),
    "build.gradle.kts": ("kotlin", "gradle", "gradle"),
}
LANG_EXT: dict[str, str] = {
    ".py": "python", ".js": "javascript", ".ts": "typescript", ".tsx": "typescript",
    ".jsx": "javascript", ".rs": "rust", ".go": "go", ".rb": "ruby",
    ".java": "java", ".kt": "kotlin", ".swift": "swift", ".c": "c",
    ".cpp": "cpp", ".cs": "csharp", ".php": "php",
}
FW_KW: dict[str, str] = {
    "fastapi": "fastapi", "flask": "flask", "django": "django", "express": "express",
    "react": "react", "next": "nextjs", "vue": "vue", "angular": "angular",
    "rails": "rails", "spring": "spring", "actix": "actix", "axum": "axum",
    "gin": "gin", "echo": "echo", "svelte": "svelte", "nuxt": "nuxt",
    "fastify": "fastify", "hono": "hono",
}
TEST_KW: dict[str, str] = {
    "pytest": "pytest", "unittest": "unittest", "jest": "jest", "mocha": "mocha",
    "vitest": "vitest", "rspec": "rspec", "junit": "junit",
}
HIGH_RISK_RE = re.compile(
    r"(auth|login|session|token|password|credential|secret|crypto|encrypt|decrypt|"
    r"payment|billing|checkout|stripe|invoice|user[_-]?data|pii|gdpr|privacy|"
    r"admin|permission|rbac|acl|security|migration|schema)", re.I)
SKIP = {".git", "node_modules", "__pycache__", ".venv", "venv", ".tox",
        "dist", "build", ".next", ".nuxt", "target", "vendor", ".mypy_cache"}

def _git(args: list[str], cwd: Path) -> str:
    try:
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=15)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""

def _metrics(p: Path) -> tuple[int, int]:
    try: lines = p.read_text(errors="replace").splitlines()
    except OSError: return 0, 0
    loc = sum(1 for ln in lines if ln.strip() and not ln.strip().startswith("#"))
    mx = 0
    for ln in lines:
        s = ln.lstrip()
        if s:
            d = (len(ln) - len(s)) // 4 or (len(ln) - len(s)) // 2
            mx = max(mx, d)
    return loc, mx

def _risk(path: str, loc: int, nest: int, hot: set[str]) -> tuple[str, list[str]]:
    r: list[str] = []
    if HIGH_RISK_RE.search(path): r.append("security/data-sensitive path")
    if loc > 300: r.append(f"high LOC ({loc})")
    if nest >= 5: r.append(f"high complexity (nesting {nest})")
    if path in hot: r.append("frequently changed (hot file)")
    if len(r) >= 2 or any("security" in x for x in r): return "HIGH", r
    return ("MEDIUM", r) if r else ("LOW", r)

def _node_pm(root: Path) -> str:
    for lock, pm in [("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"), ("bun.lockb", "bun"), ("bun.lock", "bun")]:
        if (root / lock).exists(): return pm
    return "npm"

def _deps(root: Path) -> list[dict[str, str]]:
    deps: list[dict[str, str]] = []
    pp = root / "pyproject.toml"
    if pp.exists():
        txt = pp.read_text(errors="replace")
        for m in re.finditer(r"(?:dependencies|requires)\s*=\s*\[([^\]]*)\]", txt):
            for dm in re.finditer(r'"([a-zA-Z0-9_][a-zA-Z0-9_.-]*?)(\[[^\]]*\])?\s*([><=!~][^"]*)?"\s*', m.group(1)):
                deps.append({"name": dm.group(1).lower(), "version": (dm.group(3) or "").strip() or "*", "source": "pyproject.toml"})
    rq = root / "requirements.txt"
    if rq.exists():
        try:
            for line in rq.read_text(errors="replace").splitlines():
                line = line.strip()
                if line and not line.startswith(("#", "-")):
                    m = re.match(r"([a-zA-Z0-9_][a-zA-Z0-9_.-]*)\s*([><=!~].*)?", line)
                    if m: deps.append({"name": m.group(1).lower(), "version": (m.group(2) or "").strip() or "*", "source": "requirements.txt"})
        except OSError: pass
    pkg = root / "package.json"
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text(errors="replace"))
            for sec in ("dependencies", "devDependencies"):
                for n, v in data.get(sec, {}).items():
                    deps.append({"name": n, "version": v, "source": "package.json"})
        except (json.JSONDecodeError, OSError): pass
    return deps

def scan(root: Path) -> dict:
    root = root.resolve()
    langs: set[str] = set()
    bs: str | None = None
    pm: str | None = None
    for mf, (lang, b, p) in MANIFEST_MAP.items():
        if (root / mf).exists():
            langs.add(lang); bs = bs or b; pm = pm or p
    if "javascript" in langs or "typescript" in langs: pm = pm or _node_pm(root)
    if bs == "pyproject.toml": pm = "uv" if (root / "uv.lock").exists() else "pip"
    # Git stats
    hr = _git(["log", "--since=90 days ago", "--pretty=", "--name-only"], root)
    hc = Counter(hr.splitlines()) if hr else Counter()
    hot_files = [f for f, c in hc.most_common(20) if c >= 3]; hot_set = set(hot_files)
    br = _git(["shortlog", "-sn", "--all"], root)
    n_contrib = len(br.splitlines()) if br else 0
    high_blame: list[str] = []
    if n_contrib >= 3:
        for hf in hot_files[:10]:
            fb = _git(["shortlog", "-sn", "--all", "--", hf], root)
            if len(fb.splitlines()) >= max(2, n_contrib // 2): high_blame.append(hf)
    # Walk files
    deps = _deps(root); files: list[dict] = []; tloc = 0
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP]
        for fn in fns:
            ext = Path(fn).suffix
            if ext not in LANG_EXT: continue
            langs.add(LANG_EXT[ext])
            fp = Path(dp) / fn; rel = str(fp.relative_to(root))
            loc, nest = _metrics(fp); tloc += loc
            risk, reasons = _risk(rel, loc, nest, hot_set)
            files.append({"path": rel, "loc": loc, "max_nesting": nest, "risk": risk, "risk_reasons": reasons})
    files.sort(key=lambda f: ("HIGH", "MEDIUM", "LOW").index(f["risk"]))
    rs = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for f in files: rs[f["risk"]] += 1
    dep_names = {d["name"].lower() for d in deps}
    fws = sorted({fw for kw, fw in FW_KW.items() if any(kw in n for n in dep_names)})
    tfw = next((fw for kw, fw in TEST_KW.items() if kw in dep_names), None)
    if not tfw and (root / "pyproject.toml").exists() and "pytest" in (root / "pyproject.toml").read_text(errors="replace"):
        tfw = "pytest"
    return {"project_root": str(root), "languages": sorted(langs), "frameworks": fws,
            "build_system": bs, "test_framework": tfw, "package_manager": pm,
            "file_count": len(files), "total_loc": tloc, "files": files, "dependencies": deps,
            "git_stats": {"hot_files": hot_files, "high_blame_density": high_blame}, "risk_summary": rs}

if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    if not target.is_dir():
        print(f"Error: {target} is not a directory", file=sys.stderr); sys.exit(1)
    json.dump(scan(target), sys.stdout, indent=2); print()
