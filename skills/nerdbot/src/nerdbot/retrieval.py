"""Dependency-light lexical and SQLite FTS retrieval for wiki/index content."""

from __future__ import annotations

import os
import re
import sqlite3
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from nerdbot.contracts import GENERATED_ARTIFACTS
from nerdbot.safety import (
    ensure_safe_target,
    fsync_parent_directory,
    normalize_vault_relative_path,
    reject_hardlinked_file,
)

SEARCH_ROOTS = ("wiki", "indexes")
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")
HEADING_PATTERN = re.compile(r"^(?P<marks>#{1,6})\s+(?P<title>.+?)\s*$", re.MULTILINE)
BLOCK_REF_PATTERN = re.compile(r"\^(?P<block>[A-Za-z0-9_-]+)\b")
SOURCE_ID_PATTERN = re.compile(r"\b(?:source_id|source-id|src)[:=\s]+(?P<id>src-[A-Za-z0-9_-]+)", re.IGNORECASE)
FRONTMATTER_PATTERN = re.compile(r"\A---\n(?P<body>.*?)\n---\n", re.DOTALL)


@dataclass(frozen=True, slots=True)
class QueryResult:
    """Public query result shape."""

    path: str
    heading: str | None
    block_ref: str | None
    snippet: str
    source_ids: tuple[str, ...]
    freshness_class: str
    confidence: float
    raw_inspection_needed: bool

    def to_dict(self) -> dict[str, object]:
        """Return the JSON-safe query result."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SearchDocument:
    """Searchable wiki/index document chunk with provenance metadata."""

    path: str
    heading: str | None
    block_ref: str | None
    text: str
    source_ids: tuple[str, ...]
    freshness_class: str


@dataclass(frozen=True, slots=True)
class FtsBuildResult:
    """Summary of a SQLite FTS build."""

    index_path: str
    document_count: int
    persisted: bool

    def to_dict(self) -> dict[str, object]:
        """Return the JSON-safe FTS build result."""
        return asdict(self)


def tokenize(value: str) -> set[str]:
    """Tokenize text for deterministic lexical matching."""
    return {token.lower() for token in TOKEN_PATTERN.findall(value)}


def extract_frontmatter_metadata(text: str) -> dict[str, Any]:
    """Extract simple YAML frontmatter scalars without adding dependencies."""
    match = FRONTMATTER_PATTERN.match(text)
    if not match:
        return {}
    metadata: dict[str, Any] = {}
    for line in match.group("body").splitlines():
        if ":" not in line or line.startswith((" ", "\t", "-")):
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip("\"'")
    return metadata


def extract_source_ids(text: str) -> tuple[str, ...]:
    """Return stable source IDs referenced in a chunk."""
    return tuple(sorted({match.group("id") for match in SOURCE_ID_PATTERN.finditer(text)}))


def extract_block_ref(text: str) -> str | None:
    """Return the first Obsidian block reference in a chunk, if present."""
    match = BLOCK_REF_PATTERN.search(text)
    return match.group("block") if match else None


def freshness_from_metadata(metadata: dict[str, Any]) -> str:
    """Return a supported freshness class from frontmatter metadata."""
    freshness = str(metadata.get("freshness_class") or metadata.get("freshness") or "unknown")
    return freshness if freshness in {"static", "slow", "medium", "fast", "unknown"} else "unknown"


def extract_heading_blocks(rel_path: str, text: str) -> list[SearchDocument]:
    """Split markdown into heading-aware chunks for better provenance."""
    metadata = extract_frontmatter_metadata(text)
    freshness_class = freshness_from_metadata(metadata)
    matches = list(HEADING_PATTERN.finditer(text))
    if not matches:
        return [
            SearchDocument(
                path=rel_path,
                heading=None,
                block_ref=extract_block_ref(text),
                text=text,
                source_ids=extract_source_ids(text),
                freshness_class=freshness_class,
            )
        ]
    documents: list[SearchDocument] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        chunk = text[start:end]
        documents.append(
            SearchDocument(
                path=rel_path,
                heading=match.group("title").strip(),
                block_ref=extract_block_ref(chunk),
                text=chunk,
                source_ids=extract_source_ids(chunk) or extract_source_ids(text),
                freshness_class=freshness_class,
            )
        )
    return documents


def iter_search_documents(root: Path) -> list[SearchDocument]:
    """Collect readable markdown/text chunks from wiki/ and indexes/."""
    documents: list[SearchDocument] = []
    for rel_root in SEARCH_ROOTS:
        base = root / rel_root
        if not base.is_dir() or base.is_symlink():
            continue
        for path in sorted(base.rglob("*")):
            rel_path = path.relative_to(root).as_posix()
            if rel_path.startswith("indexes/generated/"):
                continue
            if path.is_symlink() or not path.is_file() or path.suffix.lower() not in {".md", ".txt"}:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            documents.extend(extract_heading_blocks(rel_path, text))
    return documents


def build_snippet(text: str, query_tokens: set[str]) -> str:
    """Build a compact snippet around the first query token match."""
    collapsed = " ".join(text.split())
    lower = collapsed.lower()
    positions = [lower.find(token) for token in query_tokens if token and lower.find(token) >= 0]
    if not positions:
        return collapsed[:240]
    start = max(0, min(positions) - 80)
    end = min(len(collapsed), start + 240)
    prefix = "..." if start else ""
    suffix = "..." if end < len(collapsed) else ""
    return f"{prefix}{collapsed[start:end]}{suffix}"


def query_lexical(root: Path, query: str, *, limit: int = 5) -> list[QueryResult]:
    """Return read-only lexical matches from maintained wiki/index layers."""
    query_tokens = tokenize(query)
    if not query_tokens:
        return []
    scored: list[tuple[int, SearchDocument]] = []
    for document in iter_search_documents(root):
        score = len(query_tokens & tokenize(document.text))
        if score:
            scored.append((score, document))
    results: list[QueryResult] = []
    for score, document in sorted(scored, key=lambda item: (-item[0], item[1].path, item[1].heading or ""))[:limit]:
        results.append(
            QueryResult(
                path=document.path,
                heading=document.heading,
                block_ref=document.block_ref,
                snippet=build_snippet(document.text, query_tokens),
                source_ids=document.source_ids,
                freshness_class=document.freshness_class,
                confidence=min(0.95, 0.35 + score / max(len(query_tokens), 1)),
                raw_inspection_needed=not document.source_ids,
            )
        )
    return results


def default_fts_index_path(root: Path) -> Path:
    """Return the configured generated SQLite FTS path."""
    return root / normalize_vault_relative_path(GENERATED_ARTIFACTS["fts_index"], allowed_roots={"indexes"})


def _safe_fts_index_path(root: Path, index_path: Path | None) -> tuple[Path, str]:
    resolved_index_path = index_path or default_fts_index_path(root)
    rel_index_path = normalize_vault_relative_path(
        resolved_index_path.relative_to(root).as_posix(), allowed_roots={"indexes"}
    )
    ensure_safe_target(root, resolved_index_path)
    return resolved_index_path, rel_index_path


def _connect_fts(index_path: Path | None) -> sqlite3.Connection:
    return sqlite3.connect(":memory:" if index_path is None else index_path)


def _populate_fts(connection: sqlite3.Connection, documents: list[SearchDocument]) -> None:
    connection.execute(
        "CREATE VIRTUAL TABLE docs USING fts5(path, heading, block_ref, text, source_ids, freshness_class)"
    )
    connection.executemany(
        "INSERT INTO docs(path, heading, block_ref, text, source_ids, freshness_class) VALUES (?, ?, ?, ?, ?, ?)",
        [
            (
                document.path,
                document.heading or "",
                document.block_ref or "",
                document.text,
                "\n".join(document.source_ids),
                document.freshness_class,
            )
            for document in documents
        ],
    )
    connection.commit()


def build_fts_index(root: Path, *, index_path: Path | None = None) -> FtsBuildResult:
    """Build a persisted SQLite FTS5 index under indexes/generated/."""
    resolved_index_path, rel_index_path = _safe_fts_index_path(root, index_path)
    reject_hardlinked_file(resolved_index_path)
    resolved_index_path.parent.mkdir(parents=True, exist_ok=True)
    documents = iter_search_documents(root)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{resolved_index_path.name}.", suffix=".tmp", dir=resolved_index_path.parent
    )
    os.close(fd)
    temp_path = Path(temp_name)
    temp_path.unlink()
    try:
        with _connect_fts(temp_path) as connection:
            _populate_fts(connection, documents)
        ensure_safe_target(root, resolved_index_path)
        temp_path.replace(resolved_index_path)
        fsync_parent_directory(resolved_index_path)
    finally:
        Path(temp_name).unlink(missing_ok=True)
    return FtsBuildResult(index_path=rel_index_path, document_count=len(documents), persisted=True)


def _query_connection(connection: sqlite3.Connection, query_text: str, *, limit: int) -> list[QueryResult]:
    tokens = tokenize(query_text)
    rows = connection.execute(
        """
        SELECT path, heading, block_ref, text, source_ids, freshness_class, bm25(docs) AS rank
        FROM docs
        WHERE docs MATCH ?
        ORDER BY rank
        LIMIT ?
        """,
        (" OR ".join(tokens), limit),
    ).fetchall()
    results: list[QueryResult] = []
    for path, heading, block_ref, text, source_ids, freshness_class, rank in rows:
        score = max(0.35, min(0.95, 0.9 - float(rank)))
        result_source_ids = tuple(value for value in str(source_ids).split("\n") if value)
        results.append(
            QueryResult(
                path=path,
                heading=heading or None,
                block_ref=block_ref or None,
                snippet=build_snippet(text, tokens),
                source_ids=result_source_ids,
                freshness_class=freshness_class or "unknown",
                confidence=score,
                raw_inspection_needed=not result_source_ids,
            )
        )
    return results


def query_fts(root: Path, query_text: str, *, limit: int = 5, index_path: Path | None = None) -> list[QueryResult]:
    """Return FTS5/BM25 matches without writing when the index is absent."""
    tokens = tokenize(query_text)
    if not tokens:
        return []
    resolved_index_path, _rel_index_path = _safe_fts_index_path(root, index_path)
    if resolved_index_path.exists():
        with _connect_fts(resolved_index_path) as connection:
            return _query_connection(connection, query_text, limit=limit)
    documents = iter_search_documents(root)
    with _connect_fts(None) as connection:
        _populate_fts(connection, documents)
        return _query_connection(connection, query_text, limit=limit)


def query(root: Path, query_text: str, *, limit: int = 5, use_fts: bool = True) -> list[QueryResult]:
    """Return read-only query results, preferring transient/persisted FTS when available."""
    if use_fts:
        try:
            return query_fts(root, query_text, limit=limit)
        except sqlite3.Error:
            return query_lexical(root, query_text, limit=limit)
    return query_lexical(root, query_text, limit=limit)
