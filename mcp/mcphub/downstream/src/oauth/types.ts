import type { OAuthScope, RegistrationMode } from "../policy/oauth-policy.js";

export interface AuthorizationRequest {
  readonly clientId: string;
  readonly registrationMode: RegistrationMode;
  readonly redirectUri: string;
  readonly codeChallenge: string;
  readonly codeChallengeMethod: "S256";
  readonly state: string;
  readonly resource: string;
  readonly scopes: readonly string[];
}

export interface AuthorizationTransaction {
  readonly stateHash: string;
  readonly clientId: string;
  readonly registrationMode: RegistrationMode;
  readonly redirectUri: string;
  readonly codeChallenge: string;
  readonly principalHash: string;
  readonly resource: string;
  readonly scopes: readonly OAuthScope[];
  readonly nonceHash: string;
  readonly expiresAt: number;
}

export interface AuthorizationCodeGrant {
  readonly codeHash: string;
  readonly clientId: string;
  readonly registrationMode: RegistrationMode;
  readonly redirectUri: string;
  readonly codeChallenge: string;
  readonly principalHash: string;
  readonly resource: string;
  readonly scopes: readonly OAuthScope[];
  readonly expiresAt: number;
}

export interface TokenPair {
  readonly accessToken: string;
  readonly accessTokenExpiresAt: number;
  readonly refreshToken: string;
  readonly refreshTokenExpiresAt: number;
  readonly scope: string;
  readonly tokenType: "Bearer";
}

export interface AccessTokenClaims {
  readonly clientId: string;
  readonly principalHash: string;
  readonly resource: string;
  readonly scopes: readonly OAuthScope[];
  readonly expiresAt: number;
}

export interface BrowserSession {
  readonly sessionToken: string;
  readonly csrfToken: string;
  readonly nonce: string;
  readonly expiresAt: number;
}

export interface RateLimitRule {
  readonly limit: number;
  readonly windowMs: number;
}
