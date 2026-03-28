#!/bin/bash
command -v jq &>/dev/null || exit 0
INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd // empty')
[ -z "$CWD" ] && exit 0
cd "$CWD" 2>/dev/null || exit 0

if command -v git &>/dev/null && git rev-parse --git-dir &>/dev/null 2>&1; then
  MODIFIED=$(git diff --name-only 2>/dev/null; git diff --cached --name-only 2>/dev/null)
  MODIFIED=$(echo "$MODIFIED" | sort -u)
  [ -z "$MODIFIED" ] && exit 0

  # Python syntax check (safe argument passing — no injection)
  PY=$(echo "$MODIFIED" | grep '\.py$')
  if [ -n "$PY" ]; then
    while IFS= read -r f; do
      [ -f "$f" ] && ! python3 -c "import py_compile, sys; py_compile.compile(sys.argv[1], doraise=True)" "$f" 2>/dev/null && {
        printf "Python syntax error in %s. Fix before going idle.\n" "$f" >&2; exit 2
      }
    done <<< "$PY"
    if command -v ruff &>/dev/null; then
      CRITICAL=$(echo "$PY" | xargs ruff check --select E9,F63,F7,F82 2>/dev/null)
      [ -n "$CRITICAL" ] && { printf "Critical lint errors. Fix before going idle:\n%s\n" "$CRITICAL" >&2; exit 2; }
    fi
  fi

  # Run modified tests only
  TESTS=$(echo "$MODIFIED" | grep -iE '(test_|_test\.|\.test\.|\.spec\.)' | grep -v '\.ipynb$')
  if [ -n "$TESTS" ]; then
    if [ -f "pyproject.toml" ] && command -v uv &>/dev/null; then
      uv run pytest $TESTS --tb=short -q 2>&1 | tail -5
      [ ${PIPESTATUS[0]} -ne 0 ] && { printf "Modified tests failing. Fix before going idle.\n" >&2; exit 2; }
    fi
  fi
fi
exit 0
