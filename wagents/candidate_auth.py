"""Name-only credential variable extraction for untrusted candidate text."""

from __future__ import annotations

import re

ENV_NAME_RE = re.compile(r"(?<![A-Za-z0-9_])([A-Z][A-Z0-9_]{2,})(?![A-Za-z0-9_])")
AUTH_MARKERS = (
    "ACCESS_KEY",
    "ACCOUNT_ID",
    "API_KEY",
    "APP_PASSWORD",
    "AUTH_TOKEN",
    "CLIENT_ID",
    "CLIENT_SECRET",
    "CONNECTION_STRING",
    "CREDENTIAL",
    "DATABASE_URL",
    "OAUTH",
    "PASSWORD",
    "PRIVATE_KEY",
    "PROFILE",
    "SECRET",
    "SERVICE_ACCOUNT",
    "SESSION_TOKEN",
    "TOKEN",
)
PROVIDER_PREFIXES = (
    "ANTHROPIC_",
    "APIFY_",
    "APP_STORE_",
    "ASC_",
    "AWS_",
    "AZURE_",
    "DATABRICKS_",
    "DATADOG_",
    "FIGMA_",
    "GCP_",
    "GITHUB_",
    "GOOGLE_",
    "LANGFUSE_",
    "LANGSMITH_",
    "NOTION_",
    "OPENAI_",
    "SLACK_",
    "STRIPE_",
    "SUPABASE_",
    "XAI_",
    "ZOTERO_",
)


def is_auth_env_name(value: str) -> bool:
    """Return whether a syntactically isolated token looks like an auth variable name."""
    return bool(ENV_NAME_RE.fullmatch(value)) and (
        any(marker in value for marker in AUTH_MARKERS) or value.startswith(PROVIDER_PREFIXES)
    )


def _is_assignment_value(text: str, start: int) -> bool:
    line_prefix = text[text.rfind("\n", 0, start) + 1 : start].rstrip()
    return bool(re.search(r"(?:=|:\s*[\"']?)\s*$", line_prefix))


def _has_name_context(text: str, start: int, end: int) -> bool:
    prefix = text[max(0, start - 32) : start]
    suffix = text[end : min(len(text), end + 8)]
    return bool(
        re.search(r"(?:\$\{?|process\.env\.|Deno\.env\.(?:get|set)\([\"']|getenv\([\"'])$", prefix)
        or re.match(r"[\"'`]?\s*(?:=|:)", suffix)
        or re.search(r"(?:^|\s)(?:export|set|setx|env)\s+$", prefix)
    )


def extract_auth_env_names(text: str, *, limit: int = 100) -> list[str]:
    """Extract credential variable names while rejecting likely assignment values."""
    names: set[str] = set()
    for match in ENV_NAME_RE.finditer(text):
        name = match.group(1)
        if not is_auth_env_name(name) or _is_assignment_value(text, match.start(1)):
            continue
        if name.startswith(PROVIDER_PREFIXES) or _has_name_context(text, match.start(1), match.end(1)):
            names.add(name)
    return sorted(names)[:limit]
