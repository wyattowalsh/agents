# Python Testing Patterns

Use this reference for Python pytest mechanics. Route broader test strategy,
suite design, or cross-language testing plans to `test-architect`.

## Fixture Scope Cheat Sheet

| Scope | Lifetime | Use for |
|-------|----------|---------|
| `function` (default) | Each test | Mutable state, DB rows, temp files |
| `class` | All tests in a class | Shared read-only setup within a class |
| `module` | All tests in a file | Expensive setup shared across a file |
| `session` | Entire test run | DB connections, server startup |

```python
@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()

@pytest.fixture
def db_session(db_engine):
    with Session(db_engine) as session:
        yield session
        session.rollback()
```

## Conftest Skeleton

```python
# tests/conftest.py
import pytest

# Session-scoped: shared across all tests
@pytest.fixture(scope="session")
def app_config():
    return {"env": "test", "debug": True}

# Function-scoped: fresh per test
@pytest.fixture
def sample_user():
    return User(name="test", email="test@example.com")

# Autouse: applies to every test in this directory
@pytest.fixture(autouse=True)
def reset_caches():
    yield
    cache.clear()
```

## Marker Registration

```toml
# pyproject.toml
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests requiring external services",
]
addopts = "--strict-markers --cov --cov-fail-under=80"
testpaths = ["tests"]
```

Keep `[tool.pytest.ini_options]` as the compatible default unless the project
intentionally targets a newer pytest-only config surface. Register custom
markers in project config and enable strict marker behavior when the local
suite uses markers.

## Parametrize Pattern

```python
@pytest.mark.parametrize("input_val,expected", [
    ("hello", "HELLO"),
    ("", ""),
    ("123", "123"),
])
def test_uppercase(input_val, expected):
    assert uppercase(input_val) == expected
```

## Monkeypatch vs Mock

| Technique | Best for |
|-----------|----------|
| `monkeypatch.setenv` | Environment variables |
| `monkeypatch.setattr` | Module-level attributes, class methods |
| `monkeypatch.delattr` | Simulating missing attributes |
| `unittest.mock.patch` | Complex call tracking, return sequences |

```python
def test_reads_env(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")
    assert get_api_key() == "test-key"

def test_file_io(tmp_path):
    f = tmp_path / "data.txt"
    f.write_text("hello")
    assert read_file(f) == "hello"
```

## Time-Dependent Tests

```python
from freezegun import freeze_time

@freeze_time("2026-01-15 12:00:00")
def test_expiry_check():
    token = create_token(ttl_hours=1)
    assert not token.is_expired()
```

## Coverage Policy

- Follow the repo's configured coverage policy when one exists.
- Do not invent a coverage threshold for an established project.
- For new Python work, `--cov-fail-under=80` is a reasonable starting point, not a universal rule.
- Keep coverage settings in `pyproject.toml` or the repo's existing pytest config.
