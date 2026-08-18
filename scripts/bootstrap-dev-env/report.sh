# Text and JSON reports for bootstrap-dev-env.
# shellcheck shell=bash

_json_string_array() {
  local raw="$1"
  local first=1
  local line
  printf '['
  if [ -n "$raw" ]; then
    while IFS= read -r line || [ -n "$line" ]; do
      [ -n "$line" ] || continue
      if [ "$first" -eq 1 ]; then
        first=0
      else
        printf ','
      fi
      printf '"%s"' "$(json_escape "$line")"
    done <<EOF
${raw}
EOF
  fi
  printf ']'
}

emit_report() {
  local ok="true"
  local mode="dry-run"
  local line id status detail first
  if [ "${COUNTER_ERROR}" -gt 0 ] || [ -n "${BLOCKED_TEXT}" ]; then
    ok="false"
  fi
  if [ "${REQUIRE:-0}" -eq 1 ] && [ "${COUNTER_WARN}" -gt 0 ]; then
    ok="false"
  fi
  if [ "${CHECK:-0}" -eq 1 ] && [ "${COUNTER_WARN}" -gt 0 ]; then
    ok="false"
  fi
  if [ "${APPLY:-0}" -eq 1 ]; then
    mode="apply"
  elif [ "${CHECK:-0}" -eq 1 ]; then
    mode="check"
  fi

  if [ -z "${NEXT_TEXT}" ]; then
    if [ "$mode" = "dry-run" ]; then
      record_next "./scripts/bootstrap-dev-env.sh --apply"
    fi
  fi

  if [ "${FORMAT}" = "json" ]; then
    printf '{\n'
    printf '  "schema": "wagents.bootstrap-dev-env.v1",\n'
    printf '  "ok": %s,\n' "$ok"
    printf '  "mode": "%s",\n' "$(json_escape "$mode")"
    printf '  "profile": "%s",\n' "$(json_escape "${PROFILE}")"
    if [ -n "${AGENTS_ROOT}" ]; then
      printf '  "agents_root": "%s",\n' "$(json_escape "${AGENTS_ROOT}")"
    else
      printf '  "agents_root": null,\n'
    fi
    printf '  "harnesses": ['
    first=1
    for id in ${HARNESS_IDS}; do
      if [ "$first" -eq 1 ]; then
        first=0
      else
        printf ', '
      fi
      printf '"%s"' "$(json_escape "$id")"
    done
    printf '],\n'
    printf '  "phases": ['
    first=1
    if [ -n "${PHASES_TEXT}" ]; then
      while IFS= read -r line || [ -n "$line" ]; do
        [ -n "$line" ] || continue
        id="${line%%|*}"
        rest="${line#*|}"
        status="${rest%%|*}"
        detail="${rest#*|}"
        if [ "$first" -eq 1 ]; then
          first=0
        else
          printf ', '
        fi
        printf '{"id":"%s","status":"%s","detail":"%s"}' \
          "$(json_escape "$id")" "$(json_escape "$status")" "$(json_escape "$detail")"
      done <<EOF
${PHASES_TEXT}
EOF
    fi
    printf '],\n'
    printf '  "counters": {"run": %s, "skip": %s, "warn": %s, "error": %s},\n' \
      "${COUNTER_RUN}" "${COUNTER_SKIP}" "${COUNTER_WARN}" "${COUNTER_ERROR}"
    printf '  "blocked": '
    _json_string_array "${BLOCKED_TEXT}"
    printf ',\n'
    printf '  "next": '
    _json_string_array "${NEXT_TEXT}"
    printf '\n}\n'
  else
    printf '\nAgent dev-env %s (%s)\n' "$mode" "${PROFILE}"
    if [ -n "${AGENTS_ROOT}" ]; then
      printf 'Checkout: %s\n' "${AGENTS_ROOT}"
    else
      printf 'Checkout: (not resolved)\n'
    fi
    printf 'Harnesses: %s\n' "${HARNESS_IDS:-none}"
    if [ -n "${PHASES_TEXT}" ]; then
      printf 'Phases:\n'
      while IFS= read -r line || [ -n "$line" ]; do
        [ -n "$line" ] || continue
        id="${line%%|*}"
        rest="${line#*|}"
        status="${rest%%|*}"
        detail="${rest#*|}"
        if [ -n "$detail" ]; then
          printf '  - %s: %s (%s)\n' "$id" "$status" "$detail"
        else
          printf '  - %s: %s\n' "$id" "$status"
        fi
      done <<EOF
${PHASES_TEXT}
EOF
    fi
    printf 'Counters: run=%s skip=%s warn=%s error=%s\n' \
      "${COUNTER_RUN}" "${COUNTER_SKIP}" "${COUNTER_WARN}" "${COUNTER_ERROR}"
    if [ -n "${NEXT_TEXT}" ]; then
      printf 'Next:\n'
      while IFS= read -r line || [ -n "$line" ]; do
        [ -n "$line" ] || continue
        printf '  %s\n' "$line"
      done <<EOF
${NEXT_TEXT}
EOF
    fi
  fi

  if [ "$ok" = "true" ]; then
    return 0
  fi
  return 1
}
