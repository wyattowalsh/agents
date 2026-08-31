"""Test path setup for the standalone Things native workspace member."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
COMMON_ROOT = PACKAGE_ROOT.parents[1] / "packages" / "things-common"
for path in (PACKAGE_ROOT, COMMON_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


@pytest.fixture
def anyio_backend() -> str:
    """Keep hermetic async tests on asyncio without optional Trio."""
    return "asyncio"
