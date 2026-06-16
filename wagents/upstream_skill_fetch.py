"""Fetch upstream SKILL.md (and related) for curated external skills via raw.githubusercontent.com.

Writes redacted snapshots to docs/src/skill-upstream/<id>.md for lazy preview in catalog pages.
Never vendors as canonical; always evidence/context only. Redacts local filesystem paths.
"""

from __future__ import annotations

import re
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from wagents import DOCS_DIR
from wagents.external_skills import ExternalSkillEntry

UPSTREAM_DIR = DOCS_DIR / "src" / "skill-upstream"

_LOCAL_PATH_PATTERN = re.compile(r"(/Users/|/home/|/private/|~/|C:\\\\|D:\\\\)")
_GITHUB_URL_RE = re.compile(r"^(?:github:)?([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)")


def _parse_github_source(install_source: str) -> tuple[str, str] | None:
    """Return (owner, repo) from install_source (owner/repo, github:owner/repo@ref, etc.)."""
    if not install_source:
        return None
    s = str(install_source).strip().removeprefix("github:")
    m = _GITHUB_URL_RE.match(s)
    if not m:
        return None
    owner = m.group(1)
    repo = m.group(2).split("@")[0]  # drop @commitish
    return owner, repo


def _candidate_paths(skill_id: str, subdir_hint: str = "") -> list[str]:
    """Return ordered candidate relative paths under the repo root for SKILL.md or similar."""
    sid = skill_id
    cands: list[str] = [
        f"skills/{sid}/SKILL.md",
        f"skills/{sid}/README.md",
        f"skills/{sid}/readme.md",
        f"{sid}/SKILL.md",
        "SKILL.md",
        f"src/skills/{sid}/SKILL.md",
        f"packages/{sid}/SKILL.md",
    ]
    if subdir_hint:
        hint = subdir_hint.strip("/\\")
        cands = [
            f"{hint}/skills/{sid}/SKILL.md",
            f"{hint}/{sid}/SKILL.md",
            f"{hint}/SKILL.md",
        ] + cands
    # dedup preserve order
    seen: set[str] = set()
    uniq: list[str] = []
    for c in cands:
        if c not in seen:
            seen.add(c)
            uniq.append(c)
    return uniq


def _redact_local_paths(text: str) -> str:
    return _LOCAL_PATH_PATTERN.sub("[REDACTED_LOCAL_PATH]", text)


def _fetch_text(url: str, timeout: int = 12) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "wagents-upstream-fetch/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if getattr(resp, "status", 200) != 200:
                return None
            data = resp.read()
            if isinstance(data, (bytes, bytearray)):
                return data.decode("utf-8", errors="replace")
            return str(data)
    except Exception:
        return None


def fetch_upstream_skill(skill_id: str, entry: ExternalSkillEntry) -> Path | None:
    """Resolve github install_source, attempt raw.githubusercontent.com for skills/<name>/SKILL.md (and peers).
    On success write redacted content (with frontmatter) to docs/src/skill-upstream/<id>.md and return the Path.
    Returns None if no github source or no matching public file fetched.
    """
    if not skill_id or not entry:
        return None
    parsed = _parse_github_source(entry.install_source)
    if not parsed:
        # also try entry.source as fallback
        parsed = _parse_github_source(entry.source)
    if not parsed:
        return None
    owner, repo = parsed

    # derive subdir hint from install_source beyond owner/repo
    src = (entry.install_source or entry.source or "").strip().removeprefix("github:")
    sub_hint = ""
    segs = [p for p in src.split("/") if p]
    if len(segs) > 2:
        sub_hint = "/".join(segs[2:])

    base = f"https://raw.githubusercontent.com/{owner}/{repo}"
    branches = ["main", "master", "HEAD", "trunk"]
    cands = _candidate_paths(skill_id, sub_hint)

    fetched_url: str | None = None
    content: str | None = None
    for br in branches:
        for cand in cands:
            url = f"{base}/{br}/{cand}"
            txt = _fetch_text(url)
            if txt and len(txt.strip()) > 20:
                content = txt
                fetched_url = url
                break
        if content:
            break

    if not content:
        return None

    redacted = _redact_local_paths(content)
    UPSTREAM_DIR.mkdir(parents=True, exist_ok=True)
    out_path = UPSTREAM_DIR / f"{skill_id}.md"

    fetched_at = datetime.now(tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    frontmatter: dict[str, Any] = {
        "skill": skill_id,
        "install_source": entry.install_source,
        "source": entry.source,
        "fetched_url": fetched_url,
        "fetched_at": fetched_at,
        "redacted": True,
    }
    body = redacted.strip() + "\n"
    out_path.write_text("---\n" + yaml.safe_dump(frontmatter, sort_keys=False) + "---\n\n" + body, encoding="utf-8")
    return out_path
