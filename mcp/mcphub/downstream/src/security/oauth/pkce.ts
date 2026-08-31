import { createHash } from "node:crypto";

import { constantTimeTextEqual } from "../common/crypto.js";
import { OAuthSecurityError } from "../common/errors.js";

const PKCE_VALUE = /^[A-Za-z0-9._~-]{43,128}$/;

export function assertPkceChallenge(challenge: string, method: string): void {
  if (method !== "S256" || !PKCE_VALUE.test(challenge)) {
    throw new OAuthSecurityError("oauth_pkce_invalid", { oauthError: "invalid_grant" });
  }
}

export function derivePkceChallenge(verifier: string): string {
  if (!PKCE_VALUE.test(verifier)) {
    throw new OAuthSecurityError("oauth_pkce_invalid", { oauthError: "invalid_grant" });
  }
  return createHash("sha256").update(verifier, "ascii").digest("base64url");
}

export function verifyPkce(verifier: string, expectedChallenge: string): void {
  const actualChallenge = derivePkceChallenge(verifier);
  if (!constantTimeTextEqual(actualChallenge, expectedChallenge)) {
    throw new OAuthSecurityError("oauth_pkce_invalid", { oauthError: "invalid_grant" });
  }
}
