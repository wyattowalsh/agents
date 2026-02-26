#!/usr/bin/env bash
# Validate email-whiz skill structure and content quality.
# Usage: bash scripts/validate-skill.sh [skill-dir]
# Exit 0: pass | Exit 1: failures found

set -euo pipefail

SKILL_DIR="${1:-$(dirname "$(dirname "$0")")}"
ERRORS=0
WARNINGS=0

red()   { echo -e "\033[31m$*\033[0m"; }
green() { echo -e "\033[32m$*\033[0m"; }
yellow(){ echo -e "\033[33m$*\033[0m"; }

fail()  { red "  ✗ $*"; ((ERRORS++)); }
warn()  { yellow "  ⚠ $*"; ((WARNINGS++)); }
pass()  { green "  ✓ $*"; }

echo "Validating: $SKILL_DIR"
echo "---"

# --- Required files ---
echo "Required files:"

REQUIRED_FILES=(
  "SKILL.md"
  "CHANGELOG.md"
  "references/triage-framework.md"
  "references/filter-patterns.md"
  "references/workflows.md"
  "references/templates.md"
  "references/inbox-zero-system.md"
  "references/analytics-guide.md"
  "references/tool-reference.md"
  "scripts/validate-skill.sh"
)

for f in "${REQUIRED_FILES[@]}"; do
  if [[ -f "$SKILL_DIR/$f" ]]; then
    pass "$f"
  else
    fail "$f — missing"
  fi
done

# --- Frontmatter fields ---
echo ""
echo "Frontmatter:"

SKILL_MD="$SKILL_DIR/SKILL.md"

check_frontmatter() {
  local field="$1"
  if grep -q "^$field" "$SKILL_MD"; then
    pass "$field present"
  else
    fail "$field missing from frontmatter"
  fi
}

check_frontmatter "name:"
check_frontmatter "description:"
check_frontmatter "argument-hint:"
check_frontmatter "model:"
check_frontmatter "disable-model-invocation:"
check_frontmatter "allowed-tools:"
check_frontmatter "context:"
check_frontmatter "license:"
check_frontmatter "metadata:"

# --- Description quality ---
echo ""
echo "Description quality:"

if grep -A15 "^description:" "$SKILL_MD" | grep -q "NOT for"; then
  pass "description contains NOT-for exclusions"
else
  fail "description missing NOT-for exclusions"
fi

if grep -A15 "^description:" "$SKILL_MD" | grep -qiE "Use when|Triggers:"; then
  pass "description contains Use-when trigger"
else
  warn "description may be missing Use-when trigger phrase"
fi

DESC=$(awk '/^description:/,/^[a-z]/' "$SKILL_MD" | head -20)
DESC_LEN=$(echo "$DESC" | wc -c)
if [[ $DESC_LEN -gt 1100 ]]; then
  fail "description exceeds 1024 chars (approx)"
else
  pass "description length OK"
fi

# --- SKILL.md size ---
echo ""
echo "File sizes:"

SKILL_LINES=$(wc -l < "$SKILL_MD")
if [[ $SKILL_LINES -le 500 ]]; then
  pass "SKILL.md: $SKILL_LINES lines (≤500)"
else
  fail "SKILL.md: $SKILL_LINES lines (exceeds 500-line limit)"
fi

for ref in triage-framework filter-patterns workflows templates inbox-zero-system analytics-guide tool-reference; do
  ref_file="$SKILL_DIR/references/$ref.md"
  if [[ -f "$ref_file" ]]; then
    ref_lines=$(wc -l < "$ref_file")
    if [[ $ref_lines -ge 50 && $ref_lines -le 500 ]]; then
      pass "references/$ref.md: $ref_lines lines (50-500)"
    elif [[ $ref_lines -lt 50 ]]; then
      warn "references/$ref.md: $ref_lines lines (below 50 minimum)"
    else
      fail "references/$ref.md: $ref_lines lines (exceeds 500-line limit)"
    fi
  fi
done

# --- Content quality ---
echo ""
echo "Content quality:"

if grep -q "^## Canonical Vocabulary" "$SKILL_MD"; then
  pass "Canonical Vocabulary section present"
else
  fail "Canonical Vocabulary section missing"
fi

if grep -q "^## Dispatch" "$SKILL_MD"; then
  pass "Dispatch table present"
else
  fail "Dispatch table missing"
fi

if grep -q "_empty_\|empty\|Empty\|(empty)" "$SKILL_MD"; then
  pass "Empty-args handler present in dispatch"
else
  fail "Empty-args handler missing from dispatch"
fi

if grep -q "^## Critical Rules" "$SKILL_MD"; then
  RULE_COUNT=$(grep -c "^[0-9]\+\." "$SKILL_MD" || true)
  if [[ $RULE_COUNT -ge 10 ]]; then
    pass "Critical Rules section present ($RULE_COUNT rules)"
  else
    warn "Critical Rules present but fewer than 10 rules ($RULE_COUNT found)"
  fi
else
  fail "Critical Rules section missing"
fi

if grep -q "^## Reference File Index" "$SKILL_MD"; then
  pass "Reference File Index present"
else
  fail "Reference File Index missing"
fi

if grep -q "^## Scope Boundaries\|NOT for" "$SKILL_MD"; then
  pass "Scope Boundaries present"
else
  fail "Scope Boundaries missing"
fi

# --- Reference File Index completeness ---
echo ""
echo "Reference file index completeness:"

REFS_IN_INDEX=(
  "triage-framework.md"
  "filter-patterns.md"
  "workflows.md"
  "templates.md"
  "inbox-zero-system.md"
  "analytics-guide.md"
  "tool-reference.md"
)

for ref in "${REFS_IN_INDEX[@]}"; do
  if grep -q "$ref" "$SKILL_MD"; then
    pass "$ref indexed"
  else
    fail "$ref not found in Reference File Index"
  fi
done

# --- Summary ---
echo ""
echo "=== Summary ==="
if [[ $ERRORS -eq 0 && $WARNINGS -eq 0 ]]; then
  green "PASS — no errors, no warnings"
elif [[ $ERRORS -eq 0 ]]; then
  yellow "PASS — 0 errors, $WARNINGS warning(s)"
else
  red "FAIL — $ERRORS error(s), $WARNINGS warning(s)"
fi

exit $ERRORS
