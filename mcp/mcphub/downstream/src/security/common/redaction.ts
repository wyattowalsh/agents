const ALLOWED_AUDIT_FIELDS = new Set([
  "attemptCount",
  "code",
  "expiresAt",
  "registrationMode",
  "scopeCount",
  "status",
  "toolScope",
]);

const ALLOWED_CODES = new Set([
  "oauth_callback_not_allowed",
  "oauth_catalog_scope_mismatch",
  "oauth_client_assertion_invalid",
  "oauth_client_assertion_replayed",
  "oauth_client_metadata_invalid",
  "oauth_code_expired",
  "oauth_code_invalid",
  "oauth_csrf_invalid",
  "oauth_database_unsafe",
  "oauth_grant_binding_mismatch",
  "oauth_origin_invalid",
  "oauth_pkce_invalid",
  "oauth_rate_limited",
  "oauth_refresh_expired",
  "oauth_refresh_invalid",
  "oauth_refresh_replayed",
  "oauth_registration_mode_mismatch",
  "oauth_registration_mode_unobserved",
  "oauth_remote_disabled",
  "oauth_resource_mismatch",
  "oauth_scope_insufficient",
  "oauth_session_invalid",
  "oauth_state_expired",
  "oauth_state_invalid",
  "oauth_token_invalid",
  "oauth_token_revoked",
]);

const ALLOWED_STRINGS: Readonly<Record<string, ReadonlySet<string>>> = Object.freeze({
  code: ALLOWED_CODES,
  registrationMode: new Set(["cimd", "dcr"]),
  status: new Set(["accepted", "disabled", "rejected", "revoked"]),
  toolScope: new Set(["things.read", "things.write", "things.admin"]),
});

type AuditPrimitive = boolean | number | string | null;

export interface ContentFreeAuditRecord {
  readonly event: string;
  readonly fields: Readonly<Record<string, AuditPrimitive>>;
}

function safeAuditValue(key: string, value: unknown): AuditPrimitive | undefined {
  if (value === null || typeof value === "boolean") {
    return value;
  }
  if (typeof value === "number" && Number.isSafeInteger(value) && value >= 0) {
    return value;
  }
  if (typeof value === "string" && ALLOWED_STRINGS[key]?.has(value) === true) {
    return value;
  }
  return undefined;
}

export function contentFreeAuditRecord(
  event: string,
  fields: Readonly<Record<string, unknown>> = {},
): ContentFreeAuditRecord {
  const safeEvent = /^[a-z][a-z0-9_.-]{0,95}$/.test(event) ? event : "oauth.invalid_audit_event";
  const safeFields: Record<string, AuditPrimitive> = {};
  for (const [key, value] of Object.entries(fields)) {
    if (!ALLOWED_AUDIT_FIELDS.has(key)) {
      continue;
    }
    const safe = safeAuditValue(key, value);
    if (safe !== undefined) {
      safeFields[key] = safe;
    }
  }
  return Object.freeze({ event: safeEvent, fields: Object.freeze(safeFields) });
}
