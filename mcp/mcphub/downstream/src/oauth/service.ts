import {
  ACCESS_TOKEN_TTL_MS,
  AUTHORIZATION_CODE_TTL_MS,
  AUTHORIZATION_TRANSACTION_TTL_MS,
  BROWSER_SESSION_TTL_MS,
  LOGIN_RATE_LIMIT,
  REFRESH_TOKEN_SLIDING_TTL_MS,
  REGISTRATION_RATE_LIMIT,
  THINGS_ISSUER,
  THINGS_ORIGIN,
  THINGS_RESOURCE,
  TOKEN_AUTHORIZATION_RATE_LIMIT,
  requireAuthorizationScopes,
  requireCatalogScopes,
  requireExactResource,
  requireObservedRegistrationMode,
  requireToolScope,
  type OAuthScope,
  type RegistrationMode,
  type ThingsScope,
} from "../policy/oauth-policy.js";
import {
  assertTrustedOAuthRequestContext,
  stableOAuthRateKey,
  type TrustedOAuthRequestContext,
} from "../policy/oauth-ingress-contract.js";
import { hashOpaque, randomOpaque } from "../security/common/crypto.js";
import { OAuthSecurityError } from "../security/common/errors.js";
import {
  requireApprovedCallback,
  validateApprovedCallbacks,
} from "../security/oauth/callbacks.js";
import {
  CimdMetadataResolver,
  type ApprovedClientPolicy,
  type ValidatedCimdClient,
  validateDcrMetadata,
} from "../security/oauth/clients.js";
import { assertPkceChallenge, derivePkceChallenge } from "../security/oauth/pkce.js";
import { verifyPrivateKeyJwt } from "../security/oauth/private-key-jwt.js";
import { OAuthSqliteStore } from "./store.js";
import type {
  AccessTokenClaims,
  AuthorizationRequest,
  BrowserSession,
  TokenPair,
} from "./types.js";

const CLIENT_STATE = /^[A-Za-z0-9._~-]{1,512}$/;
const BOUNDED_IDENTIFIER = /^[^\u0000-\u001f\u007f]{1,512}$/u;

export type ClientAuthentication =
  | { readonly kind: "none" }
  | { readonly kind: "private_key_jwt"; readonly assertion: string }
  | { readonly kind: "dcr_secret"; readonly clientSecret: string };

export interface VerifiedLoginIdentity {
  readonly accountKey: string;
  readonly principal: string;
}

export type LoginProofVerifier = (
  proof: unknown,
  expectedNonce: string,
) => Promise<VerifiedLoginIdentity>;

export interface OAuthServiceConfig {
  readonly store: OAuthSqliteStore;
  readonly clientPolicy: ApprovedClientPolicy;
  readonly cimdResolver: CimdMetadataResolver | null;
  readonly registrationPrincipal: string;
  readonly verifyLoginProof: LoginProofVerifier;
  readonly now?: () => number;
}

function requireOrigin(origin: string): void {
  if (origin !== THINGS_ORIGIN) {
    throw new OAuthSecurityError("oauth_origin_invalid", {
      httpStatus: 403,
      oauthError: "access_denied",
    });
  }
}

function requireClientState(value: string): void {
  if (!CLIENT_STATE.test(value)) {
    throw new OAuthSecurityError("oauth_state_invalid", { oauthError: "invalid_request" });
  }
}

function requireBoundedIdentifier(value: unknown): asserts value is string {
  if (typeof value !== "string" || !BOUNDED_IDENTIFIER.test(value)) {
    throw new OAuthSecurityError("oauth_client_metadata_invalid", { oauthError: "invalid_client" });
  }
}

function scopesText(scopes: readonly OAuthScope[]): string {
  return scopes.join(" ");
}

function sessionCookieValue(sessionToken: string): string {
  return `__Host-mcphub_things_session=${sessionToken}; Path=/; Secure; HttpOnly; SameSite=Lax`;
}

function materialForTokens(now: number, refreshExpiresAt = now + REFRESH_TOKEN_SLIDING_TTL_MS) {
  const accessToken = randomOpaque();
  const refreshToken = randomOpaque();
  const family = randomOpaque();
  return {
    accessToken,
    refreshToken,
    family,
    stored: {
      accessTokenHash: hashOpaque(accessToken),
      accessExpiresAt: now + ACCESS_TOKEN_TTL_MS,
      refreshTokenHash: hashOpaque(refreshToken),
      refreshExpiresAt,
      familyHash: hashOpaque(family),
    },
  };
}

function tokenPair(input: {
  readonly accessToken: string;
  readonly accessExpiresAt: number;
  readonly refreshToken: string;
  readonly refreshExpiresAt: number;
  readonly scopes: readonly OAuthScope[];
}): TokenPair {
  return Object.freeze({
    accessToken: input.accessToken,
    accessTokenExpiresAt: input.accessExpiresAt,
    refreshToken: input.refreshToken,
    refreshTokenExpiresAt: input.refreshExpiresAt,
    scope: scopesText(input.scopes),
    tokenType: "Bearer",
  });
}

function freshBrowserSession(now: number): BrowserSession {
  return Object.freeze({
    sessionToken: randomOpaque(),
    csrfToken: randomOpaque(),
    nonce: randomOpaque(),
    expiresAt: now + BROWSER_SESSION_TTL_MS,
  });
}

export class ThingsOAuthService {
  readonly #store: OAuthSqliteStore;
  readonly #clientPolicy: ApprovedClientPolicy;
  readonly #cimdResolver: CimdMetadataResolver | null;
  readonly #registrationPrincipalHash: string;
  readonly #verifyLoginProof: LoginProofVerifier;
  readonly #clock: () => number;

  constructor(config: OAuthServiceConfig) {
    requireBoundedIdentifier(config.registrationPrincipal);
    this.#store = config.store;
    this.#clientPolicy = Object.freeze({
      registrationMode: config.clientPolicy.registrationMode,
      approvedClientId: config.clientPolicy.approvedClientId,
      approvedCallbacks: Object.freeze([...config.clientPolicy.approvedCallbacks]),
      approvedMetadataDigest: config.clientPolicy.approvedMetadataDigest,
    });
    validateApprovedCallbacks(this.#clientPolicy.approvedCallbacks);
    this.#cimdResolver = config.cimdResolver;
    this.#registrationPrincipalHash = hashOpaque(config.registrationPrincipal);
    this.#verifyLoginProof = config.verifyLoginProof;
    this.#clock = config.now ?? Date.now;
  }

  beginLoginSession(): BrowserSession & { readonly setCookie: string } {
    const now = this.#clock();
    const session = freshBrowserSession(now);
    this.#store.putBrowserSession({
      sessionHash: hashOpaque(session.sessionToken),
      principalHash: hashOpaque(randomOpaque()),
      csrfHash: hashOpaque(session.csrfToken),
      nonceHash: hashOpaque(session.nonce),
      authenticated: false,
      now,
      expiresAt: session.expiresAt,
    });
    return Object.freeze({ ...session, setCookie: sessionCookieValue(session.sessionToken) });
  }

  async completeLogin(input: {
    readonly sessionToken: string;
    readonly csrfToken: string;
    readonly nonce: string;
    readonly origin: string;
    readonly requestContext: TrustedOAuthRequestContext;
    readonly proof: unknown;
  }): Promise<BrowserSession & { readonly setCookie: string }> {
    requireOrigin(input.origin);
    const requestContext = assertTrustedOAuthRequestContext(input.requestContext);
    const now = this.#clock();
    const oldSessionHash = hashOpaque(input.sessionToken);
    this.#store.consumeRateLimit(
      stableOAuthRateKey(requestContext, "login"),
      LOGIN_RATE_LIMIT,
      now,
    );
    this.#store.consumeRateLimit(
      stableOAuthRateKey(requestContext, "login", oldSessionHash),
      LOGIN_RATE_LIMIT,
      now,
    );
    const previous = this.#store.validateBrowserSession(oldSessionHash, now, false);
    if (previous.authenticated || previous.nonceHash !== hashOpaque(input.nonce)) {
      throw new OAuthSecurityError("oauth_session_invalid", { httpStatus: 401 });
    }
    let identity: VerifiedLoginIdentity;
    try {
      identity = await this.#verifyLoginProof(input.proof, input.nonce);
    } catch {
      throw new OAuthSecurityError("oauth_session_invalid", { httpStatus: 401 });
    }
    requireBoundedIdentifier(identity.accountKey);
    requireBoundedIdentifier(identity.principal);
    const next = freshBrowserSession(now);
    this.#store.rotateBrowserSession({
      oldSessionHash,
      oldCsrfHash: hashOpaque(input.csrfToken),
      newSessionHash: hashOpaque(next.sessionToken),
      newPrincipalHash: hashOpaque(identity.principal),
      newCsrfHash: hashOpaque(next.csrfToken),
      newNonceHash: hashOpaque(next.nonce),
      now,
      expiresAt: next.expiresAt,
    });
    return Object.freeze({ ...next, setCookie: sessionCookieValue(next.sessionToken) });
  }

  logout(input: {
    readonly sessionToken: string;
    readonly csrfToken: string;
    readonly origin: string;
  }): Readonly<{ clearCookie: string }> {
    requireOrigin(input.origin);
    this.#store.consumeAndRevokeBrowserSession(
      hashOpaque(input.sessionToken),
      hashOpaque(input.csrfToken),
      this.#clock(),
    );
    return Object.freeze({
      clearCookie:
        "__Host-mcphub_things_session=; Path=/; Max-Age=0; Secure; HttpOnly; SameSite=Lax",
    });
  }

  registerDcr(input: {
    readonly metadata: unknown;
    readonly resource: string;
    readonly requestContext: TrustedOAuthRequestContext;
  }): Readonly<{
    clientId: string;
    clientSecret: string;
    clientSecretExpiresAt: 0;
    tokenEndpointAuthMethod: "client_secret_basic";
  }> {
    const requestContext = assertTrustedOAuthRequestContext(input.requestContext);
    const now = this.#clock();
    this.#store.consumeRateLimit(
      stableOAuthRateKey(requestContext, "registration"),
      REGISTRATION_RATE_LIMIT,
      now,
    );
    const metadata = validateDcrMetadata(input.metadata, input.resource, this.#clientPolicy);
    const clientId = `dcr_${randomOpaque()}`;
    const clientSecret = randomOpaque();
    this.#store.putDcrClient({
      clientId,
      clientSecret,
      metadataDigest: metadata.metadataDigest,
      redirectUri: metadata.redirectUri,
      principalHash: this.#registrationPrincipalHash,
      resource: input.resource,
      now,
    });
    return Object.freeze({
      clientId,
      clientSecret,
      clientSecretExpiresAt: 0,
      tokenEndpointAuthMethod: "client_secret_basic",
    });
  }

  async beginAuthorization(input: {
    readonly request: AuthorizationRequest;
    readonly browserSessionToken: string;
    readonly requestContext: TrustedOAuthRequestContext;
  }): Promise<Readonly<{ state: string; transactionNonce: string; iss: typeof THINGS_ISSUER }>> {
    const now = this.#clock();
    const { request } = input;
    const requestContext = assertTrustedOAuthRequestContext(input.requestContext);
    this.#store.consumeRateLimit(
      stableOAuthRateKey(requestContext, "authorization"),
      TOKEN_AUTHORIZATION_RATE_LIMIT,
      now,
    );
    this.#store.consumeRateLimit(
      stableOAuthRateKey(requestContext, "authorization", request.clientId),
      TOKEN_AUTHORIZATION_RATE_LIMIT,
      now,
    );
    requireClientState(request.state);
    requireExactResource(request.resource);
    requireObservedRegistrationMode(this.#clientPolicy.registrationMode, request.registrationMode);
    assertPkceChallenge(request.codeChallenge, request.codeChallengeMethod);
    const scopes = requireAuthorizationScopes(request.scopes);
    const session = this.#store.validateBrowserSession(hashOpaque(input.browserSessionToken), now, true);
    await this.#validateAuthorizationClient(request, session.principalHash);
    const transactionNonce = randomOpaque();
    this.#store.putAuthorizationTransaction(
      {
        stateHash: hashOpaque(request.state),
        clientId: request.clientId,
        registrationMode: request.registrationMode,
        redirectUri: request.redirectUri,
        codeChallenge: request.codeChallenge,
        principalHash: session.principalHash,
        resource: request.resource,
        scopes,
        nonceHash: hashOpaque(transactionNonce),
        expiresAt: now + AUTHORIZATION_TRANSACTION_TTL_MS,
      },
      now,
    );
    return Object.freeze({ state: request.state, transactionNonce, iss: THINGS_ISSUER });
  }

  approveAuthorization(input: {
    readonly state: string;
    readonly transactionNonce: string;
    readonly browserSessionToken: string;
    readonly csrfToken: string;
    readonly origin: string;
  }): Readonly<{
    code: string;
    redirectUri: string;
    state: string;
    iss: typeof THINGS_ISSUER;
    browserSession: BrowserSession & { readonly setCookie: string };
  }> {
    requireOrigin(input.origin);
    requireClientState(input.state);
    const now = this.#clock();
    const session = this.#store.consumeBrowserCsrf(
      hashOpaque(input.browserSessionToken),
      hashOpaque(input.csrfToken),
      now,
    );
    if (!session.authenticated) {
      throw new OAuthSecurityError("oauth_session_invalid", { httpStatus: 401 });
    }
    const code = randomOpaque();
    const grant = this.#store.consumeStateAndIssueCode(
      hashOpaque(input.state),
      hashOpaque(code),
      now + AUTHORIZATION_CODE_TTL_MS,
      { principalHash: session.principalHash, nonceHash: hashOpaque(input.transactionNonce) },
      now,
    );
    const next = freshBrowserSession(now);
    this.#store.rotateBrowserSessionAfterConsent({
      oldSessionHash: hashOpaque(input.browserSessionToken),
      newSessionHash: hashOpaque(next.sessionToken),
      newPrincipalHash: session.principalHash,
      newCsrfHash: hashOpaque(next.csrfToken),
      newNonceHash: hashOpaque(next.nonce),
      now,
      expiresAt: next.expiresAt,
    });
    const browserSession = Object.freeze({
      ...next,
      setCookie: sessionCookieValue(next.sessionToken),
    });
    return Object.freeze({
      code,
      redirectUri: grant.redirectUri,
      state: input.state,
      iss: THINGS_ISSUER,
      browserSession,
    });
  }

  denyAuthorization(input: {
    readonly state: string;
    readonly transactionNonce: string;
    readonly browserSessionToken: string;
    readonly csrfToken: string;
    readonly origin: string;
  }): Readonly<{
    redirectUri: string;
    state: string;
    iss: typeof THINGS_ISSUER;
    browserSession: BrowserSession & { readonly setCookie: string };
  }> {
    requireOrigin(input.origin);
    requireClientState(input.state);
    const now = this.#clock();
    const session = this.#store.consumeBrowserCsrf(
      hashOpaque(input.browserSessionToken),
      hashOpaque(input.csrfToken),
      now,
    );
    if (!session.authenticated) {
      throw new OAuthSecurityError("oauth_session_invalid", { httpStatus: 401 });
    }
    const denied = this.#store.consumeStateForDenial(
      hashOpaque(input.state),
      { principalHash: session.principalHash, nonceHash: hashOpaque(input.transactionNonce) },
      now,
    );
    const next = freshBrowserSession(now);
    this.#store.rotateBrowserSessionAfterConsent({
      oldSessionHash: hashOpaque(input.browserSessionToken),
      newSessionHash: hashOpaque(next.sessionToken),
      newPrincipalHash: session.principalHash,
      newCsrfHash: hashOpaque(next.csrfToken),
      newNonceHash: hashOpaque(next.nonce),
      now,
      expiresAt: next.expiresAt,
    });
    const browserSession = Object.freeze({
      ...next,
      setCookie: sessionCookieValue(next.sessionToken),
    });
    return Object.freeze({
      redirectUri: denied.redirectUri,
      state: input.state,
      iss: THINGS_ISSUER,
      browserSession,
    });
  }

  async exchangeAuthorizationCode(input: {
    readonly code: string;
    readonly codeVerifier: string;
    readonly clientId: string;
    readonly registrationMode: RegistrationMode;
    readonly redirectUri: string;
    readonly resource: string;
    readonly clientAuthentication: ClientAuthentication;
    readonly requestContext: TrustedOAuthRequestContext;
  }): Promise<TokenPair> {
    requireExactResource(input.resource);
    const now = this.#clock();
    const requestContext = assertTrustedOAuthRequestContext(input.requestContext);
    this.#store.consumeRateLimit(
      stableOAuthRateKey(requestContext, "client"),
      TOKEN_AUTHORIZATION_RATE_LIMIT,
      now,
    );
    this.#store.consumeRateLimit(
      stableOAuthRateKey(requestContext, "token"),
      TOKEN_AUTHORIZATION_RATE_LIMIT,
      now,
    );
    this.#store.consumeRateLimit(
      stableOAuthRateKey(requestContext, "client", input.clientId),
      TOKEN_AUTHORIZATION_RATE_LIMIT,
      now,
    );
    const client = await this.#authenticateClient(
      input.clientId,
      input.registrationMode,
      input.resource,
      input.clientAuthentication,
      now,
    );
    if (client !== null && client.redirectUri !== input.redirectUri) {
      throw new OAuthSecurityError("oauth_grant_binding_mismatch", { oauthError: "invalid_grant" });
    }
    const codeChallenge = derivePkceChallenge(input.codeVerifier);
    const material = materialForTokens(now);
    const grant = this.#store.exchangeCode(
      hashOpaque(input.code),
      {
        clientId: input.clientId,
        registrationMode: input.registrationMode,
        redirectUri: input.redirectUri,
        codeChallenge,
        resource: input.resource,
      },
      material.stored,
      now,
    );
    return tokenPair({
      accessToken: material.accessToken,
      accessExpiresAt: material.stored.accessExpiresAt,
      refreshToken: material.refreshToken,
      refreshExpiresAt: material.stored.refreshExpiresAt,
      scopes: grant.scopes,
    });
  }

  async refresh(input: {
    readonly refreshToken: string;
    readonly clientId: string;
    readonly registrationMode: RegistrationMode;
    readonly resource: string;
    readonly clientAuthentication: ClientAuthentication;
    readonly requestContext: TrustedOAuthRequestContext;
  }): Promise<TokenPair> {
    requireExactResource(input.resource);
    const now = this.#clock();
    const requestContext = assertTrustedOAuthRequestContext(input.requestContext);
    this.#store.consumeRateLimit(
      stableOAuthRateKey(requestContext, "token"),
      TOKEN_AUTHORIZATION_RATE_LIMIT,
      now,
    );
    this.#store.consumeRateLimit(
      stableOAuthRateKey(requestContext, "client", input.clientId),
      TOKEN_AUTHORIZATION_RATE_LIMIT,
      now,
    );
    await this.#authenticateClient(
      input.clientId,
      input.registrationMode,
      input.resource,
      input.clientAuthentication,
      now,
    );
    const material = materialForTokens(now);
    const claims = this.#store.rotateRefreshToken(
      hashOpaque(input.refreshToken),
      { clientId: input.clientId, resource: input.resource },
      material.stored,
      now,
    );
    return tokenPair({
      accessToken: material.accessToken,
      accessExpiresAt: material.stored.accessExpiresAt,
      refreshToken: material.refreshToken,
      refreshExpiresAt: claims.refreshExpiresAt,
      scopes: claims.scopes,
    });
  }

  authorizeCatalog(accessToken: string, resource: string): AccessTokenClaims {
    requireExactResource(resource);
    const claims = this.#store.validateAccessToken(hashOpaque(accessToken), resource, this.#clock());
    requireCatalogScopes(claims.scopes);
    return claims;
  }

  authorizeToolCall(accessToken: string, resource: string, minimumScope: ThingsScope): AccessTokenClaims {
    requireExactResource(resource);
    const claims = this.#store.validateAccessToken(hashOpaque(accessToken), resource, this.#clock());
    requireToolScope(claims.scopes, minimumScope);
    return claims;
  }

  async revoke(input: {
    readonly token: string;
    readonly clientId: string;
    readonly registrationMode: RegistrationMode;
    readonly resource: string;
    readonly clientAuthentication: ClientAuthentication;
    readonly requestContext: TrustedOAuthRequestContext;
  }): Promise<void> {
    requireExactResource(input.resource);
    const now = this.#clock();
    const requestContext = assertTrustedOAuthRequestContext(input.requestContext);
    this.#store.consumeRateLimit(
      stableOAuthRateKey(requestContext, "client"),
      TOKEN_AUTHORIZATION_RATE_LIMIT,
      now,
    );
    this.#store.consumeRateLimit(
      stableOAuthRateKey(requestContext, "client", input.clientId),
      TOKEN_AUTHORIZATION_RATE_LIMIT,
      now,
    );
    await this.#authenticateClient(
      input.clientId,
      input.registrationMode,
      input.resource,
      input.clientAuthentication,
      now,
    );
    this.#store.revokeToken(
      hashOpaque(input.token),
      { clientId: input.clientId, resource: input.resource },
      now,
    );
  }

  async #validateAuthorizationClient(
    request: AuthorizationRequest,
    authenticatedPrincipalHash: string,
  ): Promise<void> {
    if (request.registrationMode === "cimd") {
      const client = await this.#resolveCimd();
      if (client.clientId !== request.clientId || client.redirectUri !== request.redirectUri) {
        throw new OAuthSecurityError("oauth_client_metadata_invalid", { oauthError: "invalid_client" });
      }
      return;
    }
    const metadataDigest = this.#clientPolicy.approvedMetadataDigest;
    if (metadataDigest === null) {
      throw new OAuthSecurityError("oauth_client_metadata_invalid", { oauthError: "invalid_client" });
    }
    requireApprovedCallback(request.redirectUri, validateApprovedCallbacks(this.#clientPolicy.approvedCallbacks));
    this.#store.validateDcrAuthorizationClient({
      clientId: request.clientId,
      metadataDigest,
      redirectUri: request.redirectUri,
      principalHash: this.#registrationPrincipalHash,
      resource: request.resource,
    });
    if (authenticatedPrincipalHash.length !== 64) {
      throw new OAuthSecurityError("oauth_session_invalid", { httpStatus: 401 });
    }
  }

  async #authenticateClient(
    clientId: string,
    registrationMode: RegistrationMode,
    resource: string,
    authentication: ClientAuthentication,
    now: number,
  ): Promise<ValidatedCimdClient | null> {
    requireBoundedIdentifier(clientId);
    requireObservedRegistrationMode(this.#clientPolicy.registrationMode, registrationMode);
    if (registrationMode === "dcr") {
      if (authentication.kind !== "dcr_secret") {
        throw new OAuthSecurityError("oauth_client_metadata_invalid", {
          httpStatus: 401,
          oauthError: "invalid_client",
        });
      }
      this.#store.verifyDcrClient(clientId, authentication.clientSecret, resource);
      return null;
    }
    const client = await this.#resolveCimd();
    if (client.clientId !== clientId) {
      throw new OAuthSecurityError("oauth_client_metadata_invalid", {
        httpStatus: 401,
        oauthError: "invalid_client",
      });
    }
    if (client.tokenEndpointAuthMethod === "none") {
      if (authentication.kind !== "none") {
        throw new OAuthSecurityError("oauth_client_metadata_invalid", {
          httpStatus: 401,
          oauthError: "invalid_client",
        });
      }
      return client;
    }
    if (authentication.kind !== "private_key_jwt") {
      throw new OAuthSecurityError("oauth_client_metadata_invalid", {
        httpStatus: 401,
        oauthError: "invalid_client",
      });
    }
    verifyPrivateKeyJwt({
      assertion: authentication.assertion,
      clientId,
      approvedJwks: client.jwks,
      store: this.#store,
      now,
    });
    return client;
  }

  async #resolveCimd(): Promise<ValidatedCimdClient> {
    if (this.#cimdResolver === null) {
      throw new OAuthSecurityError("oauth_client_metadata_invalid", {
        httpStatus: 503,
        oauthError: "temporarily_unavailable",
      });
    }
    return this.#cimdResolver.resolve(this.#clientPolicy, this.#clock());
  }
}
