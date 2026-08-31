import assert from "node:assert/strict";
import test from "node:test";

import {
  CimdMetadataResolver,
  OAuthSecurityError,
  OAuthSqliteStore,
  THINGS_ISSUER,
  THINGS_ORIGIN,
  THINGS_RESOURCE,
  ThingsOAuthService,
  assertSafeHttpsUrl,
  authorizationServerMetadata,
  canonicalJson,
  contentFreeAuditRecord,
  createTrustedOAuthRequestContext,
  derivePkceChallenge,
  hashOpaque,
  issuerBoundAuthorizationError,
  protectedResourceMetadata,
  randomOpaque,
  requireApprovedCallback,
  requireAuthorizationScopes,
  requireToolScope,
  sha256,
} from "../../src/oauth/index.js";
import { createStoreFixture, loadFixture, requestContext } from "./helpers.js";

const CALLBACK = "https://chatgpt.com/connector_platform_oauth_redirect";
const CIMD_CLIENT = "https://chatgpt.com/oauth/client.json";

function hasCode(code: string): Readonly<{ name: "OAuthSecurityError"; message: string }> {
  return { name: "OAuthSecurityError", message: code };
}

async function login(service: ThingsOAuthService) {
  const initial = service.beginLoginSession();
  return service.completeLogin({
    sessionToken: initial.sessionToken,
    csrfToken: initial.csrfToken,
    nonce: initial.nonce,
    origin: THINGS_ORIGIN,
    requestContext: requestContext(),
    proof: { verified: true },
  });
}

test("runs the constrained DCR code, refresh, replay, and revocation lifecycle", async () => {
  const fixture = createStoreFixture();
  const metadata = loadFixture("dcr-approved.json");
  let now = 10_000_000;
  const service = new ThingsOAuthService({
    store: fixture.store,
    clientPolicy: {
      registrationMode: "dcr",
      approvedClientId: null,
      approvedCallbacks: [CALLBACK],
      approvedMetadataDigest: sha256(canonicalJson(metadata)),
    },
    cimdResolver: null,
    registrationPrincipal: "approved-operator",
    verifyLoginProof: async (_proof, expectedNonce) => {
      assert.match(expectedNonce, /^[A-Za-z0-9_-]{43}$/);
      return { accountKey: "local-account-1", principal: "principal-1" };
    },
    now: () => now,
  });
  try {
    const browser = await login(service);
    assert.match(browser.setCookie, /^__Host-mcphub_things_session=/);
    assert.match(browser.setCookie, /; Path=\/; Secure; HttpOnly; SameSite=Lax$/);
    assert.equal(browser.setCookie.includes("Domain="), false);

    const registration = service.registerDcr({
      metadata,
      resource: THINGS_RESOURCE,
      requestContext: requestContext(),
    });
    assert.match(registration.clientId, /^dcr_[A-Za-z0-9_-]{43}$/);
    assert.match(registration.clientSecret, /^[A-Za-z0-9_-]{43}$/);

    const verifier = randomOpaque();
    const state = "predictable-client-state";
    const authorization = await service.beginAuthorization({
      browserSessionToken: browser.sessionToken,
      requestContext: requestContext(),
      request: {
        clientId: registration.clientId,
        registrationMode: "dcr",
        redirectUri: CALLBACK,
        codeChallenge: derivePkceChallenge(verifier),
        codeChallengeMethod: "S256",
        state,
        resource: THINGS_RESOURCE,
        scopes: ["things.admin", "offline_access", "things.read", "things.write"],
      },
    });
    assert.match(authorization.transactionNonce, /^[A-Za-z0-9_-]{43}$/);
    assert.equal(authorization.iss, THINGS_ISSUER);
    const approval = service.approveAuthorization({
      state,
      transactionNonce: authorization.transactionNonce,
      browserSessionToken: browser.sessionToken,
      csrfToken: browser.csrfToken,
      origin: THINGS_ORIGIN,
    });
    assert.equal(approval.iss, THINGS_ISSUER);
    assert.throws(
      () =>
        service.approveAuthorization({
          state,
          transactionNonce: authorization.transactionNonce,
          browserSessionToken: browser.sessionToken,
          csrfToken: browser.csrfToken,
          origin: THINGS_ORIGIN,
        }),
      hasCode("oauth_csrf_invalid"),
    );
    assert.match(approval.browserSession.setCookie, /^__Host-mcphub_things_session=/);
    assert.deepEqual(
      service.logout({
        sessionToken: approval.browserSession.sessionToken,
        csrfToken: approval.browserSession.csrfToken,
        origin: THINGS_ORIGIN,
      }),
      {
        clearCookie:
          "__Host-mcphub_things_session=; Path=/; Max-Age=0; Secure; HttpOnly; SameSite=Lax",
      },
    );
    const retryBrowser = await login(service);
    assert.match(retryBrowser.sessionToken, /^[A-Za-z0-9_-]{43}$/);

    const tokens = await service.exchangeAuthorizationCode({
      code: approval.code,
      codeVerifier: verifier,
      clientId: registration.clientId,
      registrationMode: "dcr",
      redirectUri: CALLBACK,
      resource: THINGS_RESOURCE,
      clientAuthentication: { kind: "dcr_secret", clientSecret: registration.clientSecret },
      requestContext: requestContext(),
    });
    assert.equal(tokens.scope, "things.read things.write things.admin offline_access");
    assert.equal(service.authorizeCatalog(tokens.accessToken, THINGS_RESOURCE).clientId, registration.clientId);
    assert.equal(
      service.authorizeToolCall(tokens.accessToken, THINGS_RESOURCE, "things.admin").clientId,
      registration.clientId,
    );

    now += 1_000;
    const rotated = await service.refresh({
      refreshToken: tokens.refreshToken,
      clientId: registration.clientId,
      registrationMode: "dcr",
      resource: THINGS_RESOURCE,
      clientAuthentication: { kind: "dcr_secret", clientSecret: registration.clientSecret },
      requestContext: requestContext(),
    });
    await service.revoke({
      token: rotated.accessToken,
      clientId: registration.clientId,
      registrationMode: "dcr",
      resource: THINGS_RESOURCE,
      clientAuthentication: { kind: "dcr_secret", clientSecret: registration.clientSecret },
      requestContext: requestContext(),
    });
    assert.throws(
      () => service.authorizeToolCall(rotated.accessToken, THINGS_RESOURCE, "things.read"),
      hasCode("oauth_token_revoked"),
    );
    await assert.rejects(
      service.refresh({
        refreshToken: tokens.refreshToken,
        clientId: registration.clientId,
        registrationMode: "dcr",
        resource: THINGS_RESOURCE,
        clientAuthentication: { kind: "dcr_secret", clientSecret: registration.clientSecret },
        requestContext: requestContext(),
      }),
      hasCode("oauth_refresh_replayed"),
    );
    await assert.rejects(
      service.refresh({
        refreshToken: rotated.refreshToken,
        clientId: registration.clientId,
        registrationMode: "dcr",
        resource: THINGS_RESOURCE,
        clientAuthentication: { kind: "dcr_secret", clientSecret: registration.clientSecret },
        requestContext: requestContext(),
      }),
      hasCode("oauth_refresh_invalid"),
    );
  } finally {
    fixture.close();
  }
});

test("validates CIMD none clients from an exact bounded metadata document", async () => {
  const fixture = createStoreFixture();
  const metadata = loadFixture("cimd-none.json");
  const body = Buffer.from(JSON.stringify(metadata), "utf8");
  let loadCount = 0;
  const resolver = new CimdMetadataResolver(async (clientId) => {
    loadCount += 1;
    return {
      status: 200,
      finalUrl: clientId,
      contentType: "application/json; charset=utf-8",
      body,
    };
  });
  const service = new ThingsOAuthService({
    store: fixture.store,
    clientPolicy: {
      registrationMode: "cimd",
      approvedClientId: CIMD_CLIENT,
      approvedCallbacks: [CALLBACK],
      approvedMetadataDigest: sha256(canonicalJson(metadata)),
    },
    cimdResolver: resolver,
    registrationPrincipal: "approved-operator",
    verifyLoginProof: async () => ({ accountKey: "account-2", principal: "principal-2" }),
    now: () => 20_000_000,
  });
  try {
    const browser = await login(service);
    const verifier = randomOpaque();
    const state = randomOpaque();
    const authorization = await service.beginAuthorization({
      browserSessionToken: browser.sessionToken,
      requestContext: requestContext(),
      request: {
        clientId: CIMD_CLIENT,
        registrationMode: "cimd",
        redirectUri: CALLBACK,
        codeChallenge: derivePkceChallenge(verifier),
        codeChallengeMethod: "S256",
        state,
        resource: THINGS_RESOURCE,
        scopes: ["things.read", "things.write", "things.admin", "offline_access"],
      },
    });
    const approved = service.approveAuthorization({
      state,
      transactionNonce: authorization.transactionNonce,
      browserSessionToken: browser.sessionToken,
      csrfToken: browser.csrfToken,
      origin: THINGS_ORIGIN,
    });
    const tokens = await service.exchangeAuthorizationCode({
      code: approved.code,
      codeVerifier: verifier,
      clientId: CIMD_CLIENT,
      registrationMode: "cimd",
      redirectUri: CALLBACK,
      resource: THINGS_RESOURCE,
      clientAuthentication: { kind: "none" },
      requestContext: requestContext(),
    });
    assert.equal(service.authorizeCatalog(tokens.accessToken, THINGS_RESOURCE).clientId, CIMD_CLIENT);
    assert.equal(loadCount, 1);
    await assert.rejects(
      service.refresh({
        refreshToken: tokens.refreshToken,
        clientId: CIMD_CLIENT,
        registrationMode: "cimd",
        resource: THINGS_RESOURCE,
        clientAuthentication: { kind: "dcr_secret", clientSecret: randomOpaque() },
        requestContext: requestContext(),
      }),
      hasCode("oauth_client_metadata_invalid"),
    );
  } finally {
    fixture.close();
  }
});

test("fails closed on callbacks, origins, scope implication, and registration substitution", async () => {
  const fixture = createStoreFixture();
  const metadata = loadFixture("dcr-approved.json");
  const adversarial = loadFixture("adversarial-callbacks.json");
  assert.ok(Array.isArray(adversarial));
  for (const callback of adversarial) {
    assert.equal(typeof callback, "string");
    assert.throws(
      () => requireApprovedCallback(callback, new Set([CALLBACK])),
      hasCode("oauth_callback_not_allowed"),
    );
  }
  const service = new ThingsOAuthService({
    store: fixture.store,
    clientPolicy: {
      registrationMode: "dcr",
      approvedClientId: null,
      approvedCallbacks: [CALLBACK],
      approvedMetadataDigest: sha256(canonicalJson(metadata)),
    },
    cimdResolver: null,
    registrationPrincipal: "approved-operator",
    verifyLoginProof: async () => ({ accountKey: "account-3", principal: "principal-3" }),
    now: () => 30_000_000,
  });
  try {
    const initial = service.beginLoginSession();
    await assert.rejects(
      service.completeLogin({
        sessionToken: initial.sessionToken,
        csrfToken: initial.csrfToken,
        nonce: initial.nonce,
        origin: "https://evil.example",
        requestContext: requestContext("203.0.113.20"),
        proof: {},
      }),
      hasCode("oauth_origin_invalid"),
    );
    assert.throws(() => requireToolScope(["things.admin"], "things.read"), hasCode("oauth_scope_insufficient"));
    assert.throws(
      () => requireAuthorizationScopes(["things.read", "things.write", "things.admin"]),
      hasCode("oauth_catalog_scope_mismatch"),
    );
    assert.throws(
      () => requireToolScope(["offline_access"], "things.read"),
      hasCode("oauth_scope_insufficient"),
    );
    assert.throws(
      () =>
        new ThingsOAuthService({
          store: fixture.store,
          clientPolicy: {
            registrationMode: null,
            approvedClientId: null,
            approvedCallbacks: [CALLBACK],
            approvedMetadataDigest: sha256(canonicalJson(metadata)),
          },
          cimdResolver: null,
          registrationPrincipal: "approved-operator",
          verifyLoginProof: async () => ({ accountKey: "account", principal: "principal" }),
        }).registerDcr({
          metadata,
          resource: THINGS_RESOURCE,
          requestContext: requestContext("203.0.113.20"),
        }),
      hasCode("oauth_registration_mode_unobserved"),
    );
  } finally {
    fixture.close();
  }
});

test("classifies canonical DNS and IP callback adversaries before allowlist equality", () => {
  const rejected = [
    "https://localhost./callback",
    "https://0.0.0.0/callback",
    "https://169.254.1.1/callback",
    "https://[::]/callback",
    "https://[::1]/callback",
    "https://[fe80::1]/callback",
    "https://[fc00::1]/callback",
    "https://[fd00::1]/callback",
    "https://[::ffff:127.0.0.1]/callback",
    "https://[::ffff:10.0.0.1]/callback",
    "https://[::ffff:192.168.1.1]/callback",
  ];
  for (const callback of rejected) {
    assert.throws(() => assertSafeHttpsUrl(callback), hasCode("oauth_callback_not_allowed"));
  }
  assert.equal(assertSafeHttpsUrl(CALLBACK).href, CALLBACK);
});

test("requires a branded socket-peer ingress context", async () => {
  const fixture = createStoreFixture();
  const service = new ThingsOAuthService({
    store: fixture.store,
    clientPolicy: {
      registrationMode: "dcr",
      approvedClientId: null,
      approvedCallbacks: [CALLBACK],
      approvedMetadataDigest: sha256(canonicalJson(loadFixture("dcr-approved.json"))),
    },
    cimdResolver: null,
    registrationPrincipal: "approved-operator",
    verifyLoginProof: async () => ({ accountKey: "account", principal: "principal" }),
  });
  try {
    const browser = service.beginLoginSession();
    await assert.rejects(
      service.completeLogin({
        sessionToken: browser.sessionToken,
        csrfToken: browser.csrfToken,
        nonce: browser.nonce,
        origin: THINGS_ORIGIN,
        requestContext: {
          connectionKey: "synthetic_connection_key_000000000001",
          listenerId: "oauth-loopback-46684",
          sourceIp: "203.0.113.10",
        },
        proof: {},
      }),
      hasCode("oauth_rate_limited"),
    );
    assert.equal(
      createTrustedOAuthRequestContext({
        connectionKey: "synthetic_connection_key_000000000002",
        listenerId: "oauth-loopback-46684",
        sourceIp: "[2001:db8::1]",
      }).sourceIp,
      "2001:db8::1",
    );
  } finally {
    fixture.close();
  }
});

test("persists stable pre-verification login buckets across restart", async () => {
  const fixture = createStoreFixture();
  const metadata = loadFixture("dcr-approved.json");
  const context = requestContext("203.0.113.50", "stable_login_connection_key_00000001");
  let verifierCalls = 0;
  let store = fixture.store;
  const makeService = () =>
    new ThingsOAuthService({
      store,
      clientPolicy: {
        registrationMode: "dcr",
        approvedClientId: null,
        approvedCallbacks: [CALLBACK],
        approvedMetadataDigest: sha256(canonicalJson(metadata)),
      },
      cimdResolver: null,
      registrationPrincipal: "approved-operator",
      verifyLoginProof: async () => {
        verifierCalls += 1;
        throw new Error("synthetic-invalid-proof");
      },
      now: () => 60_000_000,
    });
  try {
    const initialService = makeService();
    const browser = initialService.beginLoginSession();
    for (let attempt = 0; attempt < 5; attempt += 1) {
      await assert.rejects(
        initialService.completeLogin({
          sessionToken: browser.sessionToken,
          csrfToken: browser.csrfToken,
          nonce: browser.nonce,
          origin: THINGS_ORIGIN,
          requestContext: context,
          proof: { attackerVariant: attempt },
        }),
        hasCode("oauth_session_invalid"),
      );
    }
    assert.equal(verifierCalls, 5);
    store.close();
    store = new OAuthSqliteStore(fixture.paths);
    const restartedService = makeService();
    await assert.rejects(
      restartedService.completeLogin({
        sessionToken: browser.sessionToken,
        csrfToken: browser.csrfToken,
        nonce: browser.nonce,
        origin: THINGS_ORIGIN,
        requestContext: context,
        proof: { attackerVariant: "after-restart" },
      }),
      hasCode("oauth_rate_limited"),
    );
    assert.equal(verifierCalls, 5);
  } finally {
    store.close();
    fixture.close();
  }
});

test("rate limits attacker-varying codes and client assertions with stable buckets", async () => {
  const dcrFixture = createStoreFixture();
  const dcrMetadata = loadFixture("dcr-approved.json");
  const dcrService = new ThingsOAuthService({
    store: dcrFixture.store,
    clientPolicy: {
      registrationMode: "dcr",
      approvedClientId: null,
      approvedCallbacks: [CALLBACK],
      approvedMetadataDigest: sha256(canonicalJson(dcrMetadata)),
    },
    cimdResolver: null,
    registrationPrincipal: "approved-operator",
    verifyLoginProof: async () => ({ accountKey: "account", principal: "principal" }),
    now: () => 70_000_000,
  });
  try {
    const registered = dcrService.registerDcr({
      metadata: dcrMetadata,
      resource: THINGS_RESOURCE,
      requestContext: requestContext("203.0.113.60", "registration_connection_key_000001"),
    });
    const context = requestContext("203.0.113.61", "stable_code_connection_key_000000001");
    for (let attempt = 0; attempt < 30; attempt += 1) {
      await assert.rejects(
        dcrService.exchangeAuthorizationCode({
          code: randomOpaque(),
          codeVerifier: randomOpaque(),
          clientId: registered.clientId,
          registrationMode: "dcr",
          redirectUri: CALLBACK,
          resource: THINGS_RESOURCE,
          clientAuthentication: { kind: "dcr_secret", clientSecret: registered.clientSecret },
          requestContext: context,
        }),
        hasCode("oauth_code_invalid"),
      );
    }
    await assert.rejects(
      dcrService.exchangeAuthorizationCode({
        code: randomOpaque(),
        codeVerifier: randomOpaque(),
        clientId: registered.clientId,
        registrationMode: "dcr",
        redirectUri: CALLBACK,
        resource: THINGS_RESOURCE,
        clientAuthentication: { kind: "dcr_secret", clientSecret: registered.clientSecret },
        requestContext: context,
      }),
      hasCode("oauth_rate_limited"),
    );
  } finally {
    dcrFixture.close();
  }

  const assertionFixture = createStoreFixture();
  const privateMetadata = {
    client_id: CIMD_CLIENT,
    redirect_uris: [CALLBACK],
    token_endpoint_auth_method: "private_key_jwt",
    jwks: {
      keys: [
        {
          alg: "RS256",
          e: "AQAB",
          kid: "synthetic-key",
          kty: "RSA",
          n: "A".repeat(342),
          use: "sig",
        },
      ],
    },
  };
  const body = Buffer.from(JSON.stringify(privateMetadata), "utf8");
  const assertionService = new ThingsOAuthService({
    store: assertionFixture.store,
    clientPolicy: {
      registrationMode: "cimd",
      approvedClientId: CIMD_CLIENT,
      approvedCallbacks: [CALLBACK],
      approvedMetadataDigest: sha256(canonicalJson(privateMetadata)),
    },
    cimdResolver: new CimdMetadataResolver(async () => ({
      body,
      contentType: "application/json",
      finalUrl: CIMD_CLIENT,
      status: 200,
    })),
    registrationPrincipal: "approved-operator",
    verifyLoginProof: async () => ({ accountKey: "account", principal: "principal" }),
    now: () => 80_000_000,
  });
  try {
    const context = requestContext("203.0.113.70", "stable_assertion_connection_key_0001");
    for (let attempt = 0; attempt < 30; attempt += 1) {
      await assert.rejects(
        assertionService.exchangeAuthorizationCode({
          code: randomOpaque(),
          codeVerifier: randomOpaque(),
          clientId: CIMD_CLIENT,
          registrationMode: "cimd",
          redirectUri: CALLBACK,
          resource: THINGS_RESOURCE,
          clientAuthentication: { kind: "private_key_jwt", assertion: `invalid-${attempt}` },
          requestContext: context,
        }),
        hasCode("oauth_client_assertion_invalid"),
      );
    }
    await assert.rejects(
      assertionService.exchangeAuthorizationCode({
        code: randomOpaque(),
        codeVerifier: randomOpaque(),
        clientId: CIMD_CLIENT,
        registrationMode: "cimd",
        redirectUri: CALLBACK,
        resource: THINGS_RESOURCE,
        clientAuthentication: { kind: "private_key_jwt", assertion: "invalid-final" },
        requestContext: context,
      }),
      hasCode("oauth_rate_limited"),
    );
  } finally {
    assertionFixture.close();
  }
});

test("rekeys and revalidates CIMD cache entries across policy and key rotation", async () => {
  const metadata = loadFixture("cimd-none.json");
  const rotated = {
    client_id: CIMD_CLIENT,
    redirect_uris: [CALLBACK],
    token_endpoint_auth_method: "private_key_jwt",
    jwks: {
      keys: [
        {
          alg: "RS256",
          e: "AQAB",
          kid: "rotated-key",
          kty: "RSA",
          n: "B".repeat(342),
          use: "sig",
        },
      ],
    },
  };
  let selected: unknown = metadata;
  let loadCount = 0;
  const resolver = new CimdMetadataResolver(async () => {
    loadCount += 1;
    return {
      body: Buffer.from(JSON.stringify(selected), "utf8"),
      contentType: "application/json",
      finalUrl: CIMD_CLIENT,
      status: 200,
    };
  });
  const basePolicy = {
    registrationMode: "cimd" as const,
    approvedClientId: CIMD_CLIENT,
    approvedCallbacks: [CALLBACK],
    approvedMetadataDigest: sha256(canonicalJson(metadata)),
  };
  assert.equal((await resolver.resolve(basePolicy, 1)).tokenEndpointAuthMethod, "none");
  assert.equal((await resolver.resolve(basePolicy, 2)).tokenEndpointAuthMethod, "none");
  assert.equal(loadCount, 1);

  await assert.rejects(
    resolver.resolve({ ...basePolicy, approvedCallbacks: ["https://example.com/callback"] }, 3),
    hasCode("oauth_callback_not_allowed"),
  );
  assert.equal(loadCount, 2);

  selected = rotated;
  const rotatedPolicy = {
    ...basePolicy,
    approvedMetadataDigest: sha256(canonicalJson(rotated)),
  };
  const client = await resolver.resolve(rotatedPolicy, 4);
  assert.equal(client.tokenEndpointAuthMethod, "private_key_jwt");
  assert.equal(client.jwks[0]?.kid, "rotated-key");
  assert.equal((await resolver.resolve(rotatedPolicy, 5)).jwks[0]?.kid, "rotated-key");
  assert.equal(loadCount, 3);
});

test("publishes one exact issuer/resource and emits content-free audit/error records", () => {
  assert.deepEqual(protectedResourceMetadata(), {
    resource: THINGS_RESOURCE,
    authorization_servers: [THINGS_ISSUER],
    bearer_methods_supported: ["header"],
    scopes_supported: ["things.read", "things.write", "things.admin", "offline_access"],
  });
  const server = authorizationServerMetadata();
  assert.equal(server.issuer, THINGS_ISSUER);
  assert.equal(server.authorization_response_iss_parameter_supported, true);
  assert.deepEqual(
    issuerBoundAuthorizationError(new OAuthSecurityError("oauth_state_invalid")),
    { error: "invalid_request", error_description: "oauth_state_invalid", iss: THINGS_ISSUER },
  );
  const audit = contentFreeAuditRecord("oauth.token.rejected", {
    code: "oauth_token_invalid",
    token: "secret-token",
    path: "/Users/private",
    privateContent: "todo title",
  });
  assert.deepEqual(audit, {
    event: "oauth.token.rejected",
    fields: { code: "oauth_token_invalid" },
  });
  assert.equal(JSON.stringify(audit).includes("secret-token"), false);
  assert.equal(JSON.stringify(audit).includes("todo title"), false);
  assert.equal(hashOpaque(THINGS_RESOURCE).length, 64);
});
