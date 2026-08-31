import { createPublicKey, verify as verifySignature } from "node:crypto";

import { THINGS_TOKEN_ENDPOINT } from "../../policy/oauth-policy.js";
import type { OAuthSqliteStore } from "../../oauth/store.js";
import { OAuthSecurityError } from "../common/errors.js";
import type { ApprovedJwk } from "./clients.js";

const JWT_PART = /^[A-Za-z0-9_-]+$/;
const MAX_ASSERTION_BYTES = 16 * 1_024;
const MAX_ASSERTION_LIFETIME_SECONDS = 5 * 60;
const CLOCK_SKEW_SECONDS = 60;

interface ParsedJwt {
  readonly encodedHeader: string;
  readonly encodedPayload: string;
  readonly signature: Buffer;
  readonly header: Record<string, unknown>;
  readonly claims: Record<string, unknown>;
}

function invalidAssertion(): never {
  throw new OAuthSecurityError("oauth_client_assertion_invalid", {
    httpStatus: 401,
    oauthError: "invalid_client",
  });
}

function objectValue(value: unknown): Record<string, unknown> {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    return invalidAssertion();
  }
  return value as Record<string, unknown>;
}

function decodePart(part: string): Buffer {
  if (!JWT_PART.test(part) || part.length > MAX_ASSERTION_BYTES) {
    return invalidAssertion();
  }
  const decoded = Buffer.from(part, "base64url");
  if (decoded.byteLength === 0 || decoded.toString("base64url") !== part) {
    return invalidAssertion();
  }
  return decoded;
}

function parseJsonPart(part: string): Record<string, unknown> {
  const decoded = decodePart(part);
  try {
    const text = new TextDecoder("utf-8", { fatal: true }).decode(decoded);
    return objectValue(JSON.parse(text));
  } catch {
    return invalidAssertion();
  }
}

function parseJwt(assertion: string): ParsedJwt {
  if (Buffer.byteLength(assertion, "utf8") > MAX_ASSERTION_BYTES) {
    return invalidAssertion();
  }
  const parts = assertion.split(".");
  if (parts.length !== 3) {
    return invalidAssertion();
  }
  const encodedHeader = parts[0];
  const encodedPayload = parts[1];
  const encodedSignature = parts[2];
  if (encodedHeader === undefined || encodedPayload === undefined || encodedSignature === undefined) {
    return invalidAssertion();
  }
  return {
    encodedHeader,
    encodedPayload,
    signature: decodePart(encodedSignature),
    header: parseJsonPart(encodedHeader),
    claims: parseJsonPart(encodedPayload),
  };
}

function stringClaim(claims: Record<string, unknown>, name: string): string {
  const value = claims[name];
  if (typeof value !== "string" || value.length === 0 || value.length > 1_024) {
    return invalidAssertion();
  }
  return value;
}

function timeClaim(claims: Record<string, unknown>, name: string): number {
  const value = claims[name];
  if (typeof value !== "number" || !Number.isSafeInteger(value) || value < 0) {
    return invalidAssertion();
  }
  return value;
}

function selectKey(header: Record<string, unknown>, keys: readonly ApprovedJwk[]): ApprovedJwk {
  const kid = header.kid;
  const alg = header.alg;
  const typ = header.typ;
  if (
    typeof kid !== "string" ||
    (alg !== "RS256" && alg !== "ES256") ||
    (typ !== undefined && typ !== "JWT")
  ) {
    return invalidAssertion();
  }
  const matches = keys.filter((key) => key.kid === kid && key.alg === alg);
  if (matches.length !== 1) {
    return invalidAssertion();
  }
  const key = matches[0];
  if (key === undefined) {
    return invalidAssertion();
  }
  return key;
}

function publicKey(key: ApprovedJwk) {
  if (key.kty === "RSA") {
    return createPublicKey({
      format: "jwk",
      key: { e: key.e, kty: key.kty, n: key.n },
    });
  }
  return createPublicKey({
    format: "jwk",
    key: {
      crv: key.crv,
      kty: key.kty,
      x: key.x,
      y: key.y,
    },
  });
}

export function verifyPrivateKeyJwt(input: {
  readonly assertion: string;
  readonly clientId: string;
  readonly approvedJwks: readonly ApprovedJwk[];
  readonly store: OAuthSqliteStore;
  readonly now: number;
  readonly audience?: string;
}): void {
  const parsed = parseJwt(input.assertion);
  const key = selectKey(parsed.header, input.approvedJwks);
  const issuer = stringClaim(parsed.claims, "iss");
  const subject = stringClaim(parsed.claims, "sub");
  const audience = stringClaim(parsed.claims, "aud");
  const jti = stringClaim(parsed.claims, "jti");
  const issuedAt = timeClaim(parsed.claims, "iat");
  const expiresAt = timeClaim(parsed.claims, "exp");
  const notBeforeValue = parsed.claims.nbf;
  const notBefore = notBeforeValue === undefined ? issuedAt : timeClaim(parsed.claims, "nbf");
  const expectedAudience = input.audience ?? THINGS_TOKEN_ENDPOINT;
  const nowSeconds = Math.floor(input.now / 1_000);
  if (
    issuer !== input.clientId ||
    subject !== input.clientId ||
    audience !== expectedAudience ||
    issuedAt > nowSeconds + CLOCK_SKEW_SECONDS ||
    issuedAt < nowSeconds - MAX_ASSERTION_LIFETIME_SECONDS ||
    notBefore > nowSeconds + CLOCK_SKEW_SECONDS ||
    expiresAt <= nowSeconds ||
    expiresAt > issuedAt + MAX_ASSERTION_LIFETIME_SECONDS ||
    expiresAt - issuedAt <= 0 ||
    jti.length > 256
  ) {
    return invalidAssertion();
  }
  const signingInput = Buffer.from(`${parsed.encodedHeader}.${parsed.encodedPayload}`, "ascii");
  let verified: boolean;
  try {
    verified =
      key.alg === "ES256"
        ? verifySignature(
            "sha256",
            signingInput,
            { key: publicKey(key), dsaEncoding: "ieee-p1363" },
            parsed.signature,
          )
        : verifySignature("sha256", signingInput, publicKey(key), parsed.signature);
  } catch {
    return invalidAssertion();
  }
  if (!verified) {
    return invalidAssertion();
  }
  input.store.consumeJwtJti(input.clientId, jti, expiresAt * 1_000, input.now);
}
