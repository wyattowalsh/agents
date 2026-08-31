import {
  THINGS_AUTHORIZATION_ENDPOINT,
  THINGS_ISSUER,
  OAUTH_SCOPES,
  THINGS_REGISTRATION_ENDPOINT,
  THINGS_RESOURCE,
  THINGS_REVOCATION_ENDPOINT,
  THINGS_TOKEN_ENDPOINT,
} from "../policy/oauth-policy.js";
import { OAuthSecurityError } from "../security/common/errors.js";

export function protectedResourceMetadata() {
  return Object.freeze({
    resource: THINGS_RESOURCE,
    authorization_servers: Object.freeze([THINGS_ISSUER]),
    bearer_methods_supported: Object.freeze(["header"]),
    scopes_supported: OAUTH_SCOPES,
  });
}

export function authorizationServerMetadata() {
  return Object.freeze({
    issuer: THINGS_ISSUER,
    authorization_endpoint: THINGS_AUTHORIZATION_ENDPOINT,
    token_endpoint: THINGS_TOKEN_ENDPOINT,
    registration_endpoint: THINGS_REGISTRATION_ENDPOINT,
    revocation_endpoint: THINGS_REVOCATION_ENDPOINT,
    authorization_response_iss_parameter_supported: true,
    code_challenge_methods_supported: Object.freeze(["S256"]),
    grant_types_supported: Object.freeze(["authorization_code", "refresh_token"]),
    response_types_supported: Object.freeze(["code"]),
    scopes_supported: OAUTH_SCOPES,
    token_endpoint_auth_methods_supported: Object.freeze([
      "none",
      "private_key_jwt",
      "client_secret_basic",
    ]),
  });
}

export function issuerBoundAuthorizationError(error: OAuthSecurityError) {
  return Object.freeze({ ...error.publicPayload(), iss: THINGS_ISSUER });
}
