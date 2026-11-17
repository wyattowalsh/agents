#!/usr/bin/env python3
"""Export the canonical host-panel instructions as a narrow, deterministic plugin ZIP."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import re
import stat
import sys
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

PLUGIN_NAME = "host-panel"
SCHEMA_URL = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
SKILL_PATH = PurePosixPath("skills") / PLUGIN_NAME
TEMPLATE_PATH = Path("config/plugins/host-panel.json")
VERSION_RE = re.compile(
    r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-([0-9A-Za-z.-]+))?(?:\+([0-9A-Za-z.-]+))?"
)
INLINE_LINK_RE = re.compile(r"!?\[[^\]\n]*\]\(\s*(<[^>\n]+>|[^\s)]+)(?:\s+['\"][^\n]*?['\"])?\s*\)")
REFERENCE_LINK_RE = re.compile(r"^\s{0,3}\[[^\]\n]+\]:\s*(<[^>\n]+>|\S+)", re.MULTILINE)
MANIFEST_KEYS = {"$schema", "name", "description", "author", "license", "extensions"}
INTERFACE_KEYS = {
    "displayName",
    "shortDescription",
    "longDescription",
    "developerName",
    "category",
    "capabilities",
    "defaultPrompt",
}


class BuildError(ValueError):
    """An input or output violates the narrow plugin packaging contract."""


def validate_version(version: str) -> None:
    """Require a SemVer release identity without path or empty identifier segments."""
    match = VERSION_RE.fullmatch(version)
    if match is None:
        raise BuildError("release version must be SemVer, for example 0.1.0 or 0.1.0-rc.1")
    prerelease, metadata = match.group(4), match.group(5)
    if any(value is not None and any(not part for part in value.split(".")) for value in (prerelease, metadata)):
        raise BuildError("release version contains an empty identifier")
    if prerelease and any(part.isdigit() and len(part) > 1 and part.startswith("0") for part in prerelease.split(".")):
        raise BuildError("numeric prerelease identifiers must not have leading zeroes")


def _reject_symlinks(path: Path, boundary: Path) -> None:
    """Reject links at or below a trusted boundary, including existing parents."""
    try:
        relative = path.relative_to(boundary)
    except ValueError as exc:
        raise BuildError("path escapes its declared boundary") from exc
    current = boundary
    for part in ("", *relative.parts):
        if part:
            current /= part
        if current.is_symlink():
            raise BuildError(f"symbolic links are not allowed: {current}")


def _read_source(path: Path, root: Path) -> bytes:
    _reject_symlinks(path, root)
    try:
        before = path.stat()
        if not stat.S_ISREG(before.st_mode):
            raise BuildError(f"source must be a regular file: {path}")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as handle:
            opened = os.fstat(handle.fileno())
            if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
                raise BuildError(f"source changed while opening: {path}")
            payload = handle.read()
        _reject_symlinks(path, root)
        after = path.stat()
        if (before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise BuildError(f"source changed while reading: {path}")
        return payload
    except OSError as exc:
        raise BuildError(f"cannot read source {path}: {exc.strerror}") from exc


def _release_manifest(payload: bytes, version: str) -> bytes:
    try:
        manifest = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BuildError("manifest template must be valid UTF-8 JSON") from exc
    if not isinstance(manifest, dict) or set(manifest) != MANIFEST_KEYS:
        raise BuildError("manifest template must be versionless and contain only the approved metadata fields")
    if manifest["name"] != PLUGIN_NAME or manifest["$schema"] != SCHEMA_URL:
        raise BuildError("manifest name or schema does not match host-panel")
    if manifest["author"] != {"name": "Wyatt Walsh"} or manifest["license"] != "MIT":
        raise BuildError("manifest author or license does not match the canonical package")
    if not isinstance(manifest["description"], str) or not manifest["description"].strip():
        raise BuildError("manifest description must be nonempty")
    extensions = manifest["extensions"]
    if not isinstance(extensions, dict) or set(extensions) != {"com.openai"}:
        raise BuildError("only the OpenAI interface extension is allowed")
    openai_extension = extensions["com.openai"]
    if not isinstance(openai_extension, dict) or set(openai_extension) != {"interface"}:
        raise BuildError("the OpenAI extension must contain interface metadata only")
    interface = openai_extension["interface"]
    if not isinstance(interface, dict) or set(interface) != INTERFACE_KEYS:
        raise BuildError("manifest interface contains missing or unexpected fields")
    if any(
        not isinstance(interface[key], str) or not interface[key].strip() for key in INTERFACE_KEYS - {"capabilities"}
    ):
        raise BuildError("interface text fields must be nonempty strings")
    if interface["displayName"] != "Host Panel" or len(interface["shortDescription"]) > 30:
        raise BuildError("interface requires Host Panel and a shortDescription of at most 30 characters")
    if interface["capabilities"] != []:
        raise BuildError("this skills-only package must not declare app capabilities")
    manifest["version"] = version
    return (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _validate_links(files: dict[str, bytes]) -> None:
    """Require every local Markdown link to resolve to an included skill file."""
    prefix = f"{SKILL_PATH}/"
    for member, payload in files.items():
        try:
            content = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise BuildError(f"Markdown source is not UTF-8: {member}") from exc
        destinations = [
            match.group(1).strip("<>")
            for pattern in (INLINE_LINK_RE, REFERENCE_LINK_RE)
            for match in pattern.finditer(content)
        ]
        for destination in destinations:
            try:
                parsed = urlsplit(destination)
            except ValueError as exc:
                raise BuildError(f"invalid link in {member}: {destination}") from exc
            if parsed.scheme in {"http", "https", "mailto"} or (not parsed.scheme and parsed.netloc):
                continue
            if parsed.scheme:
                raise BuildError(f"unsupported link scheme in {member}: {destination}")
            target = unquote(parsed.path)
            if not target:
                continue
            if target.startswith("/") or "\\" in target or "\x00" in target:
                raise BuildError(f"local link escapes the package in {member}: {destination}")
            resolved = posixpath.normpath(str(PurePosixPath(member).parent / target))
            if not resolved.startswith(prefix) or resolved not in files:
                raise BuildError(f"local link is missing or outside the package in {member}: {destination}")


def build_plugin(repo_root: Path, output: Path, release_version: str) -> dict[str, str | int]:
    """Build a release archive without modifying source files or replacing outputs.

    Parameters
    ----------
    repo_root
        Repository containing the canonical host-panel skill and manifest template.
    output
        New ZIP path outside the source repository.
    release_version
        SemVer identity inserted only into the archived plugin.json.
    """
    validate_version(release_version)
    root = Path(os.path.abspath(repo_root))
    output = Path(os.path.abspath(output))
    _reject_symlinks(root, Path(root.anchor))
    _reject_symlinks(output, Path(output.anchor))
    if output.is_relative_to(root) or output.resolve().is_relative_to(root.resolve()):
        raise BuildError("output must be outside the source repository")
    if output.suffix != ".zip":
        raise BuildError("output must have a .zip extension")
    if output.exists():
        raise BuildError("refusing to overwrite an existing output")

    skill_root = root / SKILL_PATH
    references = skill_root / "references"
    _reject_symlinks(references, root)
    if not references.is_dir():
        raise BuildError("canonical references directory is missing")
    source_paths = [skill_root / "SKILL.md", *sorted(references.glob("*.md"))]
    if any("\\" in path.name or any(ord(character) < 32 for character in path.name) for path in source_paths):
        raise BuildError("source filename is not a safe archive member name")
    files = {path.relative_to(root).as_posix(): _read_source(path, root) for path in source_paths}
    try:
        skill_content = files[f"{SKILL_PATH}/SKILL.md"].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BuildError("canonical skill must be UTF-8 Markdown") from exc
    header = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", skill_content, re.DOTALL)
    if header is None or not re.search(
        r"^name:\s*(?:host-panel|'host-panel'|\"host-panel\")\s*$", header.group(1), re.MULTILINE
    ):
        raise BuildError("canonical skill frontmatter must name host-panel")
    _validate_links(files)
    template = _read_source(root / TEMPLATE_PATH, root)
    source_digest = hashlib.sha256()
    for name, payload in sorted({**files, TEMPLATE_PATH.as_posix(): template}.items()):
        source_digest.update(name.encode("utf-8") + b"\0" + hashlib.sha256(payload).digest())
    files["plugin.json"] = _release_manifest(template, release_version)

    output.parent.mkdir(parents=True, exist_ok=True)
    _reject_symlinks(output, Path(output.anchor))
    created = False
    try:
        with output.open("xb") as handle:
            created = True
            with zipfile.ZipFile(handle, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
                for name, payload in sorted(files.items()):
                    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                    info.create_system = 3
                    info.external_attr = (stat.S_IFREG | 0o644) << 16
                    info.compress_type = zipfile.ZIP_DEFLATED
                    archive.writestr(info, payload, compresslevel=9)
    except OSError as exc:
        if created:
            output.unlink(missing_ok=True)
        raise BuildError(f"cannot create new output: {exc.strerror}") from exc
    return {
        "output": str(output),
        "version": release_version,
        "files": len(files),
        "source_sha256": source_digest.hexdigest(),
        "archive_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out", type=Path, required=True, help="New ZIP path outside the source repository")
    parser.add_argument("--release-version", required=True, help="SemVer identity for the generated artifact")
    args = parser.parse_args(argv)
    try:
        result = build_plugin(args.repo_root, args.out, args.release_version)
    except (BuildError, OSError, UnicodeDecodeError) as exc:
        print(f"host-panel build failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
