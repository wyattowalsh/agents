#!/bin/bash
command -v jq &>/dev/null || exit 0
INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd // empty')
[ -z "$CWD" ] && exit 0
cd "$CWD" 2>/dev/null || exit 0

ISSUES=""

if command -v git &>/dev/null && git rev-parse --git-dir &>/dev/null 2>&1; then
  MODIFIED=$(git diff --name-only 2>/dev/null; git diff --cached --name-only 2>/dev/null)
  [ -z "$MODIFIED" ] && exit 0

  # Python syntax check
  PY=$(echo "$MODIFIED" | grep '\.py$' | sort -u)
  if [ -n "$PY" ]; then
    while IFS= read -r f; do
      [ -f "$f" ] && ! python3 -c "import py_compile, sys; py_compile.compile(sys.argv[1], doraise=True)" "$f" 2>/dev/null && \
        ISSUES="$(printf '%sSyntax error: %s\n' "$ISSUES" "$f")"
    done <<< "$PY"
  fi

  # Check for incomplete markers
  INCOMPLETE=$(echo "$MODIFIED" | while read -r f; do
    [ -f "$f" ] && grep -n 'TODO.*implement\|NotImplementedError\|raise NotImplementedError' "$f" 2>/dev/null | head -3
  done)
  [ -n "$INCOMPLETE" ] && ISSUES="$(printf '%sIncomplete implementation:\n%s\n\n' "$ISSUES" "$INCOMPLETE")"

  # Run only MODIFIED test files (not full suite — too slow and flaky-prone)
  TESTS=$(echo "$MODIFIED" | grep -iE '(test_|_test\.|\.test\.|\.spec\.)' | grep -v '\.ipynb$' | grep -v '\.ts$' | grep -v '\.tsx$')
  if [ -n "$TESTS" ]; then
    if [ -f "pyproject.toml" ] && command -v uv &>/dev/null; then
      OUT=$(uv run pytest $TESTS --tb=short -q 2>&1)
      PYTEST_EXIT=$?
      OUT=$(echo "$OUT" | tail -10)
      [ $PYTEST_EXIT -ne 0 ] && ISSUES="$(printf '%sModified tests failing:\n%s\n\n' "$ISSUES" "$OUT")"
    elif [ -f "package.json" ]; then
      HAS_TEST=$(jq -r '.scripts.test // empty' package.json 2>/dev/null)
      if [ -n "$HAS_TEST" ] && [ "$HAS_TEST" != 'echo "Error: no test specified" && exit 1' ]; then
        OUT=$(pnpm test 2>&1)
        PNPM_EXIT=$?
        OUT=$(echo "$OUT" | tail -10)
        [ $PNPM_EXIT -ne 0 ] && ISSUES="$(printf '%sTests failing:\n%s\n\n' "$ISSUES" "$OUT")"
      fi
    fi
  fi
fi

[ -n "$ISSUES" ] && { printf "Task cannot be marked complete:\n\n%s" "$ISSUES" >&2; exit 2; }
exit 0
