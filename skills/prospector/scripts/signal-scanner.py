#!/usr/bin/env python3
"""Deterministic pre-scan for prospector skill.

Extracts structured metadata from a niche/keyword query using regex and
keyword matching (no LLM calls). Outputs JSON to stdout.

Usage:
  python signal-scanner.py "developer tools for AI agents"
  python signal-scanner.py "CRM for freelancers"
  python signal-scanner.py scan
"""
import argparse
import json
import re
import sys

# --- Niche domain detection ---

_NICHE_DOMAINS: dict[str, list[str]] = {
    "developer_tools": [
        "developer", "dev", "devtool", "api", "sdk", "cli", "ide", "code",
        "programming", "software", "framework", "library", "plugin", "extension",
        "debugging", "testing", "deployment", "ci/cd", "devops", "git",
        "terminal", "linter", "formatter", "package", "build",
    ],
    "ai": [
        "ai", "llm", "machine learning", "deep learning", "neural",
        "transformer", "gpt", "claude", "agent", "rag", "vector",
        "embedding", "model", "inference", "fine-tune", "prompt",
        "copilot", "chatbot", "nlp", "computer vision",
    ],
    "saas": [
        "saas", "subscription", "b2b", "b2c", "platform", "dashboard",
        "analytics", "crm", "erp", "workflow", "automation", "integration",
        "no-code", "low-code", "zapier", "api-first",
    ],
    "ecommerce": [
        "ecommerce", "e-commerce", "shopify", "store", "checkout", "cart",
        "payment", "stripe", "inventory", "dropshipping", "marketplace",
        "product listing", "fulfillment", "woocommerce",
    ],
    "productivity": [
        "productivity", "project management", "task", "calendar", "scheduling",
        "meeting", "notes", "notion", "obsidian", "todo", "time tracking",
        "collaboration", "remote work", "async",
    ],
    "content": [
        "content", "blog", "seo", "newsletter", "writing", "publishing",
        "social media", "youtube", "tiktok", "instagram", "twitter",
        "creator", "influencer", "podcast", "video", "marketing",
    ],
    "finance": [
        "finance", "fintech", "banking", "accounting", "invoice", "expense",
        "budget", "tax", "payroll", "crypto", "trading", "investment",
        "billing", "revenue", "pricing", "stripe",
    ],
    "health": [
        "health", "wellness", "fitness", "medical", "telehealth", "mental health",
        "therapy", "nutrition", "diet", "exercise", "sleep", "wearable",
    ],
    "education": [
        "education", "edtech", "learning", "course", "tutorial", "training",
        "quiz", "student", "teacher", "school", "university", "certification",
        "skill", "bootcamp", "lms",
    ],
    "real_estate": [
        "real estate", "property", "rental", "tenant", "landlord", "lease",
        "mortgage", "listing", "mls", "proptech",
    ],
    "legal": [
        "legal", "law", "contract", "compliance", "regulation", "gdpr",
        "privacy", "terms of service", "trademark", "patent",
    ],
    "hr": [
        "hr", "human resources", "hiring", "recruiting", "onboarding",
        "employee", "talent", "resume", "interview", "payroll", "benefits",
    ],
}

# --- Pain keyword detection ---

_PAIN_KEYWORDS: list[str] = [
    "frustrated", "frustrating", "annoying", "painful", "hate",
    "wish there was", "looking for", "need a tool", "can't find",
    "manual", "tedious", "time-consuming", "broken", "buggy",
    "expensive", "overpriced", "complicated", "clunky", "slow",
    "shutting down", "end of life", "deprecated", "discontinued",
    "no good", "nothing works", "spend hours", "waste time",
    "built an internal", "cobbled together", "spreadsheet",
]

_SIGNAL_KEYWORDS: dict[str, list[str]] = {
    "pain_no_solution": [
        "no good tool", "can't find", "wish there was", "need a tool",
        "looking for tool", "nothing works", "no solution",
    ],
    "dying_product": [
        "shutting down", "end of life", "deprecated", "discontinued",
        "pivoting away", "sunsetting", "acquired and killed",
    ],
    "platform_expansion": [
        "new api", "just launched", "now supports", "integration",
        "plugin ecosystem", "marketplace", "app store", "extension",
    ],
    "rising_trend": [
        "trending", "growing", "exploding", "surge", "adoption",
        "breakout", "emerging", "hot", "viral",
    ],
    "terrible_ux": [
        "terrible ux", "bad ui", "clunky", "confusing interface",
        "hard to use", "awful design", "ugly", "unintuitive",
    ],
    "manual_workflow": [
        "manual", "tedious", "spend hours", "waste time", "spreadsheet",
        "copy paste", "built an internal", "cobbled together",
        "automate", "repetitive",
    ],
}

# --- Entity extraction ---

_ENTITY_PATTERN = re.compile(
    r"""
    (?:
      "[^"]{2,}"
    | '[^']{2,}'
    | (?<!\A)(?<![.!?]\s)
      [A-Z][a-z]+
      (?:\s+[A-Z][a-z]+)*
    | [A-Z]{2,}(?:\.[A-Z]+)*
    | [a-z]+[A-Z]\w*
    )
    """,
    re.VERBOSE,
)

_STOP_ENTITIES = {
    "What", "How", "Why", "When", "Where", "Which", "Who", "Is", "Are",
    "Does", "Do", "Can", "Should", "Will", "The", "This", "That", "These",
    "Those", "And", "But", "For", "Not", "With", "From", "Into", "Have",
    "Has", "Had", "Been", "Being", "Would", "Could", "May", "Might",
    "Just", "Most", "Some", "Any", "All", "Each", "Every", "Both",
    "Few", "More", "Other", "Such", "Only", "Very", "Still", "Even",
    "In", "On", "At", "To", "Of", "By", "Up", "It", "If",
    "So", "Or", "No", "Yes", "My", "Our", "Its",
}


def extract_entities(query: str) -> list[str]:
    entities: list[str] = []
    for m in _ENTITY_PATTERN.finditer(query):
        raw = m.group().strip("\"'`")
        if raw not in _STOP_ENTITIES and len(raw) > 1:
            entities.append(raw)
    return sorted(set(entities))


# --- Temporal marker detection ---

_YEAR_PATTERN = re.compile(r"\b(20[12]\d)\b")
_TEMPORAL_WORDS = re.compile(
    r"\b(latest|current|recent|recently|new|newest|now|today|modern|"
    r"upcoming|emerging|future|trending|this\s+year|last\s+year|"
    r"past\s+(?:year|month|week|decade)|"
    r"state\s+of\s+the\s+art|cutting\s+edge)\b",
    re.IGNORECASE,
)


def detect_temporal_markers(query: str) -> list[str]:
    markers: list[str] = []
    for m in _YEAR_PATTERN.finditer(query):
        markers.append(m.group())
    for m in _TEMPORAL_WORDS.finditer(query):
        markers.append(m.group().lower())
    return sorted(set(markers))


# --- Niche domain detection ---

def detect_niche_domains(query: str) -> list[str]:
    query_lower = query.lower()
    found: list[str] = []
    for domain, keywords in _NICHE_DOMAINS.items():
        for kw in keywords:
            if kw in query_lower:
                found.append(domain)
                break
    return sorted(set(found)) if found else ["general"]


# --- Embedded signal detection ---

def detect_embedded_signals(query: str) -> list[str]:
    query_lower = query.lower()
    found: list[str] = []

    # Check general pain keywords
    for kw in _PAIN_KEYWORDS:
        if kw in query_lower:
            found.append("pain_point")
            break

    # Check specific signal types
    for signal_type, keywords in _SIGNAL_KEYWORDS.items():
        for kw in keywords:
            if kw in query_lower:
                found.append(signal_type)
                break

    return sorted(set(found))


# --- Breadth estimation ---

def estimate_breadth(
    niche_domains: list[str],
    entities: list[str],
    query: str,
) -> str:
    query_words = len(query.split())
    domain_count = len(niche_domains) if "general" not in niche_domains else 0

    if domain_count >= 3 or query_words >= 10:
        return "broad"
    if domain_count <= 1 and query_words <= 4 and len(entities) <= 1:
        return "narrow"
    return "moderate"


# --- Source suggestion ---

_SOURCE_MAP: dict[str, list[str]] = {
    "developer_tools": ["community", "technical", "competitor"],
    "ai": ["community", "technical", "competitor"],
    "saas": ["community", "market", "competitor"],
    "ecommerce": ["market", "seo", "competitor"],
    "productivity": ["community", "market", "competitor"],
    "content": ["community", "seo", "market"],
    "finance": ["market", "community", "competitor"],
    "health": ["community", "market", "seo"],
    "education": ["community", "market", "seo"],
    "real_estate": ["market", "seo", "community"],
    "legal": ["market", "community", "competitor"],
    "hr": ["market", "community", "competitor"],
    "general": ["community", "market", "technical", "seo", "competitor"],
}


def suggest_sources(niche_domains: list[str]) -> list[str]:
    sources: set[str] = set()
    for domain in niche_domains:
        for src in _SOURCE_MAP.get(domain, _SOURCE_MAP["general"]):
            sources.add(src)
    if not sources:
        sources = {"community", "market", "technical"}
    return sorted(sources)


# --- Main scan function ---

def scan(query: str) -> dict:
    if not query.strip():
        raise ValueError("query must not be empty")
    niche_domains = detect_niche_domains(query)
    entities = extract_entities(query)
    temporal_markers = detect_temporal_markers(query)
    embedded_signals = detect_embedded_signals(query)
    breadth = estimate_breadth(niche_domains, entities, query)
    sources = suggest_sources(niche_domains)

    # Determine mode
    query_stripped = query.strip().lower()
    suggested_mode = (
        "free_roam"
        if query_stripped in ("scan", "free-roam", "free_roam", "freeroam")
        else "mine"
    )

    return {
        "query": query,
        "niche_domains": niche_domains,
        "entities": entities,
        "temporal_markers": temporal_markers,
        "embedded_signals": embedded_signals,
        "suggested_mode": suggested_mode,
        "breadth": breadth,
        "suggested_sources": sources,
    }


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Deterministic pre-scan for prospector. "
        "Extracts structured metadata from a niche/keyword query using regex "
        "and keyword matching (no LLM calls).",
    )
    ap.add_argument(
        "query",
        help="The niche or keyword to analyze. Use 'scan' for free-roam mode.",
    )
    args = ap.parse_args()

    if not args.query.strip():
        print("Error: query must not be empty.", file=sys.stderr)
        sys.exit(1)

    result = scan(args.query)
    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
