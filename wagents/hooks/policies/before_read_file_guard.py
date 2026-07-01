"""Block reads of secret-bearing files (Cursor ``beforeReadFile`` surface).

Cursor exposes a dedicated ``beforeReadFile`` event that fires before a file is
read into agent context. This guard denies reads of credential stores, key
material, and ``.env`` files so secrets never enter the model context.
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath

_SECRET_NAME_RE = re.compile(
    r"(?:^|[._-])(?:secret|secrets|token|tokens|credential|credentials|password|passwd)\b",
    re.IGNORECASE,
)
_SECRET_SUFFIXES = (
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".keystore",
    ".jks",
)
_SECRET_BASENAMES = {
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    ".npmrc",
    ".netrc",
    ".pgpass",
    ".htpasswd",
    "credentials.json",
    "service-account.json",
}


def _is_env_file(name: str) -> bool:
    return name == ".env" or name.startswith(".env.") or name.endswith(".env")


def evaluate_before_read_file(path: str) -> str | None:
    """Return a deny reason when ``path`` points at secret material, else ``None``."""
    if not path:
        return None

    normalized = path.replace("\\", "/")
    name = PurePosixPath(normalized).name
    if not name:
        return None

    lowered = name.lower()

    if _is_env_file(name):
        return (
            f"Reading '{name}' would pull environment secrets into context. "
            "Reference required variable names instead of opening the file."
        )

    if name in _SECRET_BASENAMES:
        return f"Reading '{name}' would expose credential/key material to the model context."

    if any(lowered.endswith(suffix) for suffix in _SECRET_SUFFIXES):
        return f"Reading '{name}' would expose private key/certificate material."

    if _SECRET_NAME_RE.search(name):
        return f"Reading '{name}' looks like a secret-bearing file; avoid loading it into context."

    return None
