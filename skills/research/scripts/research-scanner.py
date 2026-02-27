#!/usr/bin/env python3
"""Deterministic query pre-scan for research skill.

Extracts structured metadata from a research query using regex and keyword
matching (no LLM calls). Outputs JSON to stdout.

Usage:
  python research-scanner.py "What are the best practices for LLM agents?"
  python research-scanner.py "React vs Vue for enterprise apps in 2026"
  python research-scanner.py "check that 90% of startups fail in year one"
"""
import argparse
import json
import re
import sys

# --- Question type detection ---

_QUESTION_WORDS_EXPLORATORY = {"what", "how"}
_QUESTION_WORDS_CAUSAL = {"why"}
_QUESTION_WORDS_FACTUAL = {"is", "are", "does", "do", "did", "was", "were", "can", "has", "have", "will"}
_QUESTION_WORDS_COMPARATIVE = {"which"}
_QUESTION_WORDS_EVALUATIVE = {"should"}

_COMPARISON_PATTERNS = re.compile(
    r"\b(vs\.?|versus|compared\s+to|better\s+than|worse\s+than)\b", re.IGNORECASE
)
_COMPARISON_OR_PATTERN = re.compile(
    r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+or\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b"
)
_WHICH_BETTER = re.compile(r"\b(which|better|best)\b", re.IGNORECASE)


def detect_question_type(query: str) -> str:
    words = query.lower().split()
    if not words:
        return "exploratory"
    first = words[0]
    if first in _QUESTION_WORDS_EVALUATIVE:
        return "evaluative"
    if first in _QUESTION_WORDS_CAUSAL:
        return "causal"
    if first in _QUESTION_WORDS_COMPARATIVE or _WHICH_BETTER.search(query):
        if _COMPARISON_PATTERNS.search(query) or _COMPARISON_OR_PATTERN.search(query):
            return "comparative"
        if first in _QUESTION_WORDS_COMPARATIVE:
            return "comparative"
    if _COMPARISON_PATTERNS.search(query):
        return "comparative"
    if first in _QUESTION_WORDS_FACTUAL:
        return "factual"
    if first in _QUESTION_WORDS_EXPLORATORY:
        return "exploratory"
    # Declarative statements with factual claims
    question_words = _QUESTION_WORDS_EXPLORATORY | _QUESTION_WORDS_CAUSAL
    if not query.rstrip().endswith("?") and not any(w in words[:2] for w in question_words):
        return "factual"
    return "exploratory"


# --- Domain signal detection ---

_DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "technology": [
        "api", "framework", "library", "programming", "software", "code",
        "database", "cloud", "kubernetes", "docker", "react", "vue", "angular",
        "python", "javascript", "typescript", "rust", "go", "java", "c++",
        "llm", "ai", "machine learning", "deep learning", "neural",
        "microservice", "devops", "ci/cd", "git", "deployment", "server",
        "frontend", "backend", "fullstack", "algorithm", "data structure",
        "compiler", "operating system", "linux", "aws", "gcp", "azure",
        "agent", "rag", "vector", "embedding", "transformer", "model",
    ],
    "academic": [
        "paper", "study", "evidence", "research", "journal", "peer-reviewed",
        "meta-analysis", "systematic review", "randomized", "trial", "cohort",
        "hypothesis", "theory", "methodology", "statistical", "significance",
        "correlation", "causation", "longitudinal", "cross-sectional",
        "literature", "citation", "doi", "arxiv", "pubmed",
    ],
    "market": [
        "market", "competitor", "revenue", "pricing", "business model",
        "startup", "enterprise", "saas", "b2b", "b2c", "valuation",
        "funding", "ipo", "acquisition", "growth", "churn", "arr", "mrr",
        "market share", "competitive landscape", "industry", "sector",
    ],
    "policy": [
        "law", "regulation", "policy", "legislation", "compliance",
        "government", "federal", "gdpr", "hipaa", "sec", "fda",
        "executive order", "mandate", "statute", "ruling", "court",
        "constitutional", "treaty", "sanction",
    ],
    "health": [
        "health", "medical", "clinical", "disease", "treatment", "drug",
        "therapy", "diagnosis", "symptom", "patient", "hospital",
        "pharmaceutical", "fda", "vaccine", "genomic", "biomarker",
        "longevity", "fasting", "diet", "exercise", "nutrition",
    ],
    "finance": [
        "stock", "bond", "investment", "portfolio", "risk", "return",
        "interest rate", "inflation", "gdp", "fed", "monetary",
        "fiscal", "cryptocurrency", "bitcoin", "ethereum", "defi",
        "trading", "hedge fund", "etf", "mutual fund",
    ],
}


def detect_domains(query: str) -> list[str]:
    query_lower = query.lower()
    found: list[str] = []
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        for kw in keywords:
            if kw in query_lower:
                found.append(domain)
                break
    return sorted(set(found)) if found else ["general"]


# --- Entity extraction ---

_ENTITY_PATTERN = re.compile(
    r"""
    (?:                        # Match any of:
      "[^"]{2,}"               #   Quoted strings (2+ chars)
    | '[^']{2,}'               #   Single-quoted strings
    | `[^`]{2,}`               #   Backtick-quoted strings
    | (?<!\A)(?<![.!?]\s)      #   Not at very start of text, not after sentence end
      [A-Z][a-z]+              #   Capitalized word
      (?:\s+[A-Z][a-z]+)*     #   Followed by more capitalized words
    | [A-Z]{2,}(?:\.[A-Z]+)*  #   Acronyms like LLM, CI/CD, AWS
    | [a-z]+[A-Z]\w*          #   camelCase words like JavaScript
    | [A-Z][a-z]*(?:\.js|\.py|\.ts|\.go|\.rs)  # Tech names like React.js
    )
    """,
    re.VERBOSE,
)

_STOP_ENTITIES = {
    "What", "How", "Why", "When", "Where", "Which", "Who", "Is", "Are",
    "Does", "Do", "Can", "Should", "Will", "The", "This", "That", "These",
    "Those", "And", "But", "For", "Not", "With", "From", "Into", "Have",
    "Has", "Had", "Been", "Being", "Would", "Could", "May", "Might",
    "Shall", "Must", "Than", "Then", "Also", "Just", "Most", "Some",
    "Any", "All", "Each", "Every", "Both", "Few", "More", "Other",
    "Such", "Only", "Very", "Still", "Already", "Even",
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

_YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")
_TEMPORAL_WORDS = re.compile(
    r"\b(latest|current|recent|recently|new|newest|now|today|modern|"
    r"upcoming|emerging|future|trending|this\s+year|last\s+year|"
    r"past\s+(?:year|month|week|decade)|"
    r"state\s+of\s+the\s+art|cutting\s+edge|bleeding\s+edge)\b",
    re.IGNORECASE,
)


def detect_temporal_markers(query: str) -> list[str]:
    markers: list[str] = []
    for m in _YEAR_PATTERN.finditer(query):
        markers.append(m.group())
    for m in _TEMPORAL_WORDS.finditer(query):
        markers.append(m.group().lower())
    return sorted(set(markers))


# --- Comparison detection ---

def detect_comparison(query: str) -> bool:
    if _COMPARISON_PATTERNS.search(query):
        return True
    if _COMPARISON_OR_PATTERN.search(query):
        return True
    return bool(_WHICH_BETTER.search(query) and len(extract_entities(query)) >= 2)


# --- Claim extraction ---

_CLAIM_PATTERN = re.compile(
    r"\b(?:check|verify|confirm|validate|fact[- ]?check)\s+(?:that\s+|if\s+|whether\s+)?(.+)",
    re.IGNORECASE,
)


def extract_claim(query: str) -> str | None:
    m = _CLAIM_PATTERN.search(query)
    if m:
        return m.group(1).strip().rstrip(".")
    return None


# --- Mode suggestion ---

def suggest_mode(
    question_type: str,
    comparison: bool,
    claim: str | None,
    domains: list[str],
) -> str:
    if claim is not None:
        return "factcheck"
    if comparison or question_type == "comparative":
        return "compare"
    if question_type == "evaluative":
        return "investigate"
    # Academic/health domains with broad queries suggest survey
    if any(d in ("academic", "health") for d in domains) and question_type == "exploratory":
        return "survey"
    return "investigate"


# --- Complexity hints ---

def compute_complexity(
    domains: list[str],
    temporal: list[str],
    comparison: bool,
) -> dict[str, bool]:
    return {
        "multi_domain": len(domains) > 1 and "general" not in domains,
        "time_sensitive": len(temporal) > 0,
        "requires_comparison": comparison,
    }


# --- Main ---

def scan(query: str) -> dict:
    question_type = detect_question_type(query)
    domains = detect_domains(query)
    entities = extract_entities(query)
    temporal = detect_temporal_markers(query)
    comparison = detect_comparison(query)
    claim = extract_claim(query)
    mode = suggest_mode(question_type, comparison, claim, domains)
    complexity = compute_complexity(domains, temporal, comparison)

    return {
        "query": query,
        "question_type": question_type,
        "domain_signals": domains,
        "entities": entities,
        "temporal_markers": temporal,
        "comparison_detected": comparison,
        "claim_to_verify": claim,
        "suggested_mode": mode,
        "complexity_hints": complexity,
    }


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Deterministic query pre-scan for research. "
        "Extracts structured metadata from a research query using regex "
        "and keyword matching (no LLM calls).",
    )
    ap.add_argument(
        "query",
        help="The research query text to analyze.",
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
