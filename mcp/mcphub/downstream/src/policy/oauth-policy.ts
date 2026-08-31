import { OAuthSecurityError } from "../security/common/errors.js";

export const THINGS_RESOURCE = "https://mcp.w4w.dev/mcp/things" as const;
export const THINGS_ISSUER = THINGS_RESOURCE;
export const THINGS_ORIGIN = "https://mcp.w4w.dev" as const;
export const THINGS_AUTHORIZATION_ENDPOINT = `${THINGS_ORIGIN}/oauth/authorize` as const;
export const THINGS_TOKEN_ENDPOINT = `${THINGS_ORIGIN}/oauth/token` as const;
export const THINGS_REGISTRATION_ENDPOINT = `${THINGS_ORIGIN}/oauth/register` as const;
export const THINGS_REVOCATION_ENDPOINT = `${THINGS_ORIGIN}/oauth/revoke` as const;
export const THINGS_PROTECTED_RESOURCE_METADATA =
  `${THINGS_ORIGIN}/.well-known/oauth-protected-resource/mcp/things` as const;

export const THINGS_SCOPES = ["things.read", "things.write", "things.admin"] as const;
export type ThingsScope = (typeof THINGS_SCOPES)[number];
export const OFFLINE_ACCESS_SCOPE = "offline_access" as const;
export const OAUTH_SCOPES = Object.freeze([
  ...THINGS_SCOPES,
  OFFLINE_ACCESS_SCOPE,
] as const);
export type OAuthScope = (typeof OAUTH_SCOPES)[number];
export type RegistrationMode = "cimd" | "dcr";

export const AUTHORIZATION_TRANSACTION_TTL_MS = 10 * 60 * 1_000;
export const AUTHORIZATION_CODE_TTL_MS = 60 * 1_000;
export const ACCESS_TOKEN_TTL_MS = 10 * 60 * 1_000;
export const REFRESH_TOKEN_SLIDING_TTL_MS = 24 * 60 * 60 * 1_000;
export const REFRESH_TOKEN_ABSOLUTE_TTL_MS = 30 * 24 * 60 * 60 * 1_000;
export const BROWSER_SESSION_TTL_MS = 30 * 60 * 1_000;

export const LOGIN_RATE_LIMIT = Object.freeze({ limit: 5, windowMs: 15 * 60 * 1_000 });
export const REGISTRATION_RATE_LIMIT = Object.freeze({ limit: 10, windowMs: 60 * 60 * 1_000 });
export const TOKEN_AUTHORIZATION_RATE_LIMIT = Object.freeze({ limit: 30, windowMs: 60 * 1_000 });

const SCOPE_SET = new Set<string>(OAUTH_SCOPES);

export function normalizeScopes(scopes: readonly string[]): readonly ThingsScope[] {
  if (scopes.length === 0 || new Set(scopes).size !== scopes.length) {
    throw new OAuthSecurityError("oauth_catalog_scope_mismatch", {
      httpStatus: 403,
      oauthError: "invalid_scope",
    });
  }
  for (const scope of scopes) {
    if (!SCOPE_SET.has(scope)) {
      throw new OAuthSecurityError("oauth_catalog_scope_mismatch", {
        httpStatus: 403,
        oauthError: "invalid_scope",
      });
    }
  }
  return THINGS_SCOPES.filter((scope) => scopes.includes(scope));
}

export function requireCatalogScopes(scopes: readonly string[]): readonly ThingsScope[] {
  const normalized = normalizeScopes(scopes);
  if (normalized.length !== THINGS_SCOPES.length) {
    throw new OAuthSecurityError("oauth_catalog_scope_mismatch", {
      httpStatus: 403,
      oauthError: "invalid_scope",
    });
  }
  return normalized;
}

export function requireAuthorizationScopes(scopes: readonly string[]): readonly OAuthScope[] {
  const thingsScopes = requireCatalogScopes(scopes);
  if (!scopes.includes(OFFLINE_ACCESS_SCOPE)) {
    throw new OAuthSecurityError("oauth_catalog_scope_mismatch", {
      httpStatus: 403,
      oauthError: "invalid_scope",
    });
  }
  return Object.freeze([...thingsScopes, OFFLINE_ACCESS_SCOPE]);
}

export function requireToolScope(scopes: readonly string[], minimumScope: ThingsScope): void {
  const normalized = normalizeScopes(scopes);
  if (!normalized.includes(minimumScope)) {
    throw new OAuthSecurityError("oauth_scope_insufficient", {
      httpStatus: 403,
      oauthError: "invalid_scope",
    });
  }
}

export function requireExactResource(resource: string): void {
  if (resource !== THINGS_RESOURCE) {
    throw new OAuthSecurityError("oauth_resource_mismatch", {
      httpStatus: 403,
      oauthError: "access_denied",
    });
  }
}

export function requireObservedRegistrationMode(
  observed: RegistrationMode | null,
  requested: RegistrationMode,
): void {
  if (observed === null) {
    throw new OAuthSecurityError("oauth_registration_mode_unobserved", {
      httpStatus: 503,
      oauthError: "temporarily_unavailable",
    });
  }
  if (observed !== requested) {
    throw new OAuthSecurityError("oauth_registration_mode_mismatch", {
      httpStatus: 403,
      oauthError: "invalid_client",
    });
  }
}

export function requireIssuer(issuer: string): void {
  if (issuer !== THINGS_ISSUER) {
    throw new OAuthSecurityError("oauth_grant_binding_mismatch", {
      httpStatus: 403,
      oauthError: "invalid_grant",
    });
  }
}
