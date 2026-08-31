import assert from "node:assert/strict";
import { generateKeyPairSync, sign, type KeyObject } from "node:crypto";
import { readFileSync } from "node:fs";
import test from "node:test";

import {
  THINGS_TOKEN_ENDPOINT,
  canonicalJson,
  sha256,
  validateCimdDocument,
  verifyPrivateKeyJwt,
  type ApprovedJwk,
} from "../../src/oauth/index.js";
import { createStoreFixture } from "./helpers.js";

const CALLBACK = "https://chatgpt.com/connector_platform_oauth_redirect";
const CLIENT_ID = "https://chatgpt.com/oauth/client.json";

function hasCode(code: string): Readonly<{ name: "OAuthSecurityError"; message: string }> {
  return { name: "OAuthSecurityError", message: code };
}

function rsaFixture(): {
  readonly approved: ApprovedJwk;
  readonly privateKey: KeyObject;
} {
  const pair = generateKeyPairSync("rsa", { modulusLength: 2048 });
  const exported = pair.publicKey.export({ format: "jwk" });
  if (exported.kty !== "RSA" || typeof exported.n !== "string" || typeof exported.e !== "string") {
    throw new Error("test RSA export was not a public JWK");
  }
  return {
    approved: {
      alg: "RS256",
      e: exported.e,
      kid: "test-rsa-key",
      kty: "RSA",
      n: exported.n,
      use: "sig",
    },
    privateKey: pair.privateKey,
  };
}

function assertion(
  privateKey: KeyObject,
  payload: Readonly<Record<string, unknown>>,
): string {
  const header = Buffer.from(
    JSON.stringify({ alg: "RS256", kid: "test-rsa-key", typ: "JWT" }),
    "utf8",
  ).toString("base64url");
  const claims = Buffer.from(JSON.stringify(payload), "utf8").toString("base64url");
  const signingInput = `${header}.${claims}`;
  const signature = sign("sha256", Buffer.from(signingInput, "ascii"), privateKey).toString("base64url");
  return `${signingInput}.${signature}`;
}

test("verifies an approved private_key_jwt and persists only a one-time JTI hash", () => {
  const fixture = createStoreFixture();
  const now = 40_000_000;
  const nowSeconds = Math.floor(now / 1_000);
  const key = rsaFixture();
  const metadata = {
    client_id: CLIENT_ID,
    redirect_uris: [CALLBACK],
    token_endpoint_auth_method: "private_key_jwt",
    jwks: { keys: [key.approved] },
  };
  const client = validateCimdDocument(metadata, {
    registrationMode: "cimd",
    approvedClientId: CLIENT_ID,
    approvedCallbacks: [CALLBACK],
    approvedMetadataDigest: sha256(canonicalJson(metadata)),
  });
  const rawJti = "private-jwt-jti-opaque-value";
  const jwt = assertion(key.privateKey, {
    iss: CLIENT_ID,
    sub: CLIENT_ID,
    aud: THINGS_TOKEN_ENDPOINT,
    iat: nowSeconds,
    nbf: nowSeconds,
    exp: nowSeconds + 120,
    jti: rawJti,
  });
  try {
    verifyPrivateKeyJwt({
      assertion: jwt,
      clientId: CLIENT_ID,
      approvedJwks: client.jwks,
      store: fixture.store,
      now,
    });
    assert.throws(
      () =>
        verifyPrivateKeyJwt({
          assertion: jwt,
          clientId: CLIENT_ID,
          approvedJwks: client.jwks,
          store: fixture.store,
          now: now + 1,
        }),
      hasCode("oauth_client_assertion_replayed"),
    );
    fixture.store.close();
    assert.equal(readFileSync(fixture.paths.databasePath).includes(Buffer.from(rawJti, "utf8")), false);
  } finally {
    fixture.close();
  }
});

test("rejects private-key assertions with wrong audience, time, signature, or key", () => {
  const fixture = createStoreFixture();
  const now = 50_000_000;
  const nowSeconds = Math.floor(now / 1_000);
  const key = rsaFixture();
  const base = {
    iss: CLIENT_ID,
    sub: CLIENT_ID,
    aud: THINGS_TOKEN_ENDPOINT,
    iat: nowSeconds,
    exp: nowSeconds + 120,
  };
  try {
    const cases = [
      { ...base, aud: "https://evil.example/token", jti: "wrong-audience" },
      { ...base, exp: nowSeconds - 1, jti: "expired" },
      { ...base, iat: nowSeconds + 120, exp: nowSeconds + 180, jti: "future" },
    ];
    for (const payload of cases) {
      assert.throws(
        () =>
          verifyPrivateKeyJwt({
            assertion: assertion(key.privateKey, payload),
            clientId: CLIENT_ID,
            approvedJwks: [key.approved],
            store: fixture.store,
            now,
          }),
        hasCode("oauth_client_assertion_invalid"),
      );
    }
    const other = rsaFixture();
    assert.throws(
      () =>
        verifyPrivateKeyJwt({
          assertion: assertion(other.privateKey, { ...base, jti: "wrong-signature" }),
          clientId: CLIENT_ID,
          approvedJwks: [key.approved],
          store: fixture.store,
          now,
        }),
      hasCode("oauth_client_assertion_invalid"),
    );
  } finally {
    fixture.close();
  }
});
