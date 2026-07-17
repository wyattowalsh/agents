"""Shared secret-path classification for fleet hooks and policy modules."""

from __future__ import annotations

from pathlib import Path

# Exact basenames that are always protected (non-.env secrets).
SECRET_BASENAMES: frozenset[str] = frozenset(
    {
        "credentials.json",
        "secrets.json",
        "service-account.json",
        "auth.json",
        "token.pickle",
        ".env.mcphub",  # also matched by env pattern; listed for explicit inventory
    }
)

# .env* are secret-class except explicit safe templates.
ENV_SAFE_BASENAMES: frozenset[str] = frozenset(
    {
        ".env.example",
        ".env.sample",
        ".env.template",
    }
)

PRIVATE_KEY_BASENAMES: frozenset[str] = frozenset(
    {
        "id_rsa",
        "id_ed25519",
        "id_ecdsa",
        "id_dsa",
    }
)

PRIVATE_KEY_SUFFIXES: frozenset[str] = frozenset({".pem", ".key", ".p12", ".pfx"})


def is_secret_env_basename(basename: str) -> bool:
    """Return True for `.env` and `.env.*` except safe templates."""
    if basename in ENV_SAFE_BASENAMES:
        return False
    return basename == ".env" or basename.startswith(".env.")


def is_secret_basename(basename: str) -> bool:
    name = basename or ""
    if name in SECRET_BASENAMES or is_secret_env_basename(name):
        return True
    if name.lower() in PRIVATE_KEY_BASENAMES:
        return True
    return Path(name).suffix.lower() in PRIVATE_KEY_SUFFIXES


def protected_basename_reason(path: str) -> str | None:
    """Return a deny reason if the path basename is secret-class; else None."""
    cleaned = (path or "").strip()
    if not cleaned:
        return None
    basename = Path(cleaned).name
    if is_secret_basename(basename):
        return f"Protected file: {cleaned}"
    return None
