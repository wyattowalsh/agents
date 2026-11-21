"""Keep macOS fixtures outside protected or symlinked system temporary roots."""

from __future__ import annotations

import os
import platform
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture(scope="session", autouse=True)
def native_fixture_directory() -> Iterator[None]:
    if platform.system() != "Darwin":
        yield
        return

    # macOS commonly routes TMPDIR through /var -> /private. Use a private,
    # disposable home directory instead of weakening production path checks.
    with tempfile.TemporaryDirectory(prefix="files-buddy-suite-", dir=Path.home()) as directory:
        previous_cache = tempfile.tempdir
        previous_environment = os.environ.get("TMPDIR")
        tempfile.tempdir = directory
        os.environ["TMPDIR"] = directory
        try:
            yield
        finally:
            tempfile.tempdir = previous_cache
            if previous_environment is None:
                os.environ.pop("TMPDIR", None)
            else:
                os.environ["TMPDIR"] = previous_environment
