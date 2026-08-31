export type OAuthErrorCode =
  | "oauth_callback_not_allowed"
  | "oauth_catalog_scope_mismatch"
  | "oauth_client_assertion_invalid"
  | "oauth_client_assertion_replayed"
  | "oauth_client_metadata_invalid"
  | "oauth_code_expired"
  | "oauth_code_invalid"
  | "oauth_csrf_invalid"
  | "oauth_database_unsafe"
  | "oauth_grant_binding_mismatch"
  | "oauth_origin_invalid"
  | "oauth_pkce_invalid"
  | "oauth_rate_limited"
  | "oauth_refresh_expired"
  | "oauth_refresh_invalid"
  | "oauth_refresh_replayed"
  | "oauth_registration_mode_unobserved"
  | "oauth_registration_mode_mismatch"
  | "oauth_remote_disabled"
  | "oauth_resource_mismatch"
  | "oauth_scope_insufficient"
  | "oauth_session_invalid"
  | "oauth_state_expired"
  | "oauth_state_invalid"
  | "oauth_token_invalid"
  | "oauth_token_revoked";

type PublicOAuthError =
  | "access_denied"
  | "invalid_client"
  | "invalid_grant"
  | "invalid_request"
  | "invalid_scope"
  | "temporarily_unavailable";

export class OAuthSecurityError extends Error {
  readonly code: OAuthErrorCode;
  readonly httpStatus: number;
  readonly oauthError: PublicOAuthError;

  constructor(
    code: OAuthErrorCode,
    options: { httpStatus?: number; oauthError?: PublicOAuthError } = {},
  ) {
    super(code);
    this.name = "OAuthSecurityError";
    this.code = code;
    this.httpStatus = options.httpStatus ?? 400;
    this.oauthError = options.oauthError ?? "invalid_request";
  }

  publicPayload(): Readonly<{ error: PublicOAuthError; error_description: OAuthErrorCode }> {
    return Object.freeze({
      error: this.oauthError,
      error_description: this.code,
    });
  }
}
