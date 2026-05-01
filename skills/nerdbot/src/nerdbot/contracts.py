"""Shared Nerdbot contracts used by the CLI and tests."""

from __future__ import annotations

VERSION = "0.1.0"
PYTHON_REQUIRES = ">=3.11"

MODES = (
    "create",
    "ingest",
    "enrich",
    "audit",
    "query",
    "derive",
    "improve",
    "migrate",
)

READ_ONLY_MODES = frozenset({"audit", "query"})
MUTATING_MODES = frozenset(set(MODES) - READ_ONLY_MODES)
ACTIVITY_LOG_MODES = tuple(mode for mode in MODES if mode not in READ_ONLY_MODES)

DEFAULT_LAYERS = (
    ".obsidian",
    "raw",
    "wiki",
    "schema",
    "config",
    "indexes",
    "activity",
)

SCHEMA_ENTITIES = {
    "Source": ("stable source ID", "raw path", "checksum when available"),
    "Extract": ("source ID", "extract path", "parser/adapter", "timestamp"),
    "Wiki page": ("path", "title", "kind", "status", "updated", "source count"),
    "Claim": ("claim text", "source reference", "evidence type", "notes"),
    "Review item": ("item ID", "mode", "target", "risk", "proposed action", "status"),
    "Activity entry": ("timestamp", "mode", "summary", "layer changes", "risk/rollback", "follow-up"),
}

SOURCE_RECORD_FIELDS = (
    "source_id",
    "original_location",
    "raw_path",
    "capture_method",
    "captured_at",
    "size_bytes",
    "checksum",
    "license_or_access_notes",
    "intended_wiki_coverage",
)

EVIDENCE_LEDGER_PATH = "indexes/evidence-ledger.md"
REVIEW_QUEUE_PATH = "indexes/review-queue.md"
OPERATION_JOURNAL_PATH = "activity/operations.jsonl"
RESEARCH_JOURNAL_DIR = "activity/research"

SOURCE_FRESHNESS_CLASSES = ("static", "slow", "medium", "fast", "unknown")
REVIEW_STATUSES = ("pending", "approved", "applied", "rejected", "blocked", "superseded")
AUTORESEARCH_POLICIES = ("journal-only", "review-queue", "approved-ingest")

CLAIM_RECORD_FIELDS = (
    "claim_id",
    "claim",
    "wiki_path",
    "source_id",
    "evidence_path",
    "evidence_type",
    "freshness_class",
    "review_status",
    "confidence",
    "updated",
    "notes",
)

QUERY_RESULT_FIELDS = (
    "path",
    "heading",
    "block_ref",
    "snippet",
    "source_ids",
    "freshness_class",
    "confidence",
    "raw_inspection_needed",
)

GRAPH_EDGE_FIELDS = ("source", "target", "edge_type", "evidence_path", "confidence")
GRAPH_EDGE_TYPES = ("links_to", "embeds", "aliases", "cites", "derives_from", "updates", "contradicts", "mentions")

WATCH_EVENT_FIELDS = ("path", "event_type", "risk", "stable", "action", "reason")
REPLAY_RESULT_FIELDS = ("operation_id", "status", "changed", "skipped", "review_needed", "failed", "resume_token")

GENERATED_ARTIFACTS = {
    "fts_index": "indexes/generated/nerdbot-fts.sqlite3",
    "graph_edges": "indexes/generated/graph-edges.jsonl",
    "graph_report": "indexes/generated/graph-report.md",
    "watch_checkpoints": "activity/checkpoints/",
}

REFERENCE_DOCS = (
    "implementation-charter.md",
    "current-state-and-compatibility.md",
    "pipeline-contracts.md",
    "schema-contracts.md",
    "kb-architecture.md",
    "kb-operations.md",
    "page-templates.md",
    "obsidian-vaults.md",
    "cli.md",
    "setup.md",
    "oss-dependencies.md",
    "source-acquisition.md",
    "ingestion-adapters.md",
    "retrieval.md",
    "graph.md",
    "watch-mode.md",
    "recovery-replay.md",
    "audit-checklist.md",
    "migration-playbooks.md",
)

REQUIRED_EXPANSION_LANES = (
    "graph analytics",
    "watch mode",
    "OpenDataLoader PDF adapter",
    "Granite Docling live model execution",
    "Crawlee large-crawl provider",
    "optional semantic embeddings",
    "MarkItDown fallback adapter",
)

SAFETY_PROMISES = (
    "inventory-first",
    "raw append-only",
    "activity log append-only",
    "query and audit read-only by default",
    "explicit approval for destructive migrations",
    "provenance required for substantive wiki claims",
)

MODE_SUMMARIES = {
    "create": "Scaffold a layered KB before synthesis starts.",
    "ingest": "Preserve sources in raw/ and queue normalized extracts.",
    "enrich": "Synthesize wiki pages from cited raw or canonical material.",
    "audit": "Read-only inventory and lint report.",
    "query": "Read-only answer from wiki/indexes with provenance and gaps.",
    "derive": "Generate rebuildable indexes, graph, or retrieval artifacts.",
    "improve": "Inventory-first repair for messy or legacy vaults.",
    "migrate": "Plan moves, rewrites, and cutovers with explicit approval.",
}

MODE_VISUALS = {
    "create": "[seed]",
    "ingest": "[raw]",
    "enrich": "[wiki]",
    "audit": "[scan]",
    "query": "[ask]",
    "derive": "[map]",
    "improve": "[fix]",
    "migrate": "[move]",
}
