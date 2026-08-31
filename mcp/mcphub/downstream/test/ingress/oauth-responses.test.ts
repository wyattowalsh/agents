import assert from "node:assert/strict";
import { chmod, mkdtemp, readFile, rm, stat, writeFile } from "node:fs/promises";
import type { IncomingHttpHeaders, IncomingMessage, ServerResponse } from "node:http";
import os from "node:os";
import path from "node:path";
import { Readable } from "node:stream";
import test from "node:test";

import {
  CaptureEvidenceRecorder,
  parseCaptureEvidenceRecord,
  validateCaptureEvidenceForPublic,
} from "../../src/ingress/capture-evidence.js";
import {
  createThingsIngressRequestListener,
  remoteOAuthChallenge,
  type ThingsIngressOptions,
} from "../../src/ingress/http.js";
import {
  CaptureOnlyOAuthHandler,
  ProductionOAuthHandler,
} from "../../src/ingress/oauth-handler.js";
import { issuerBoundAuthorizationRedirect } from "../../src/ingress/oauth-responses.js";
import {
  OAUTH_SCOPES,
  THINGS_ISSUER,
} from "../../src/policy/oauth-policy.js";
import { createTrustedOAuthRequestContext } from "../../src/policy/oauth-ingress-contract.js";
import {
  ThingsOAuthService,
  canonicalJson,
  sha256,
} from "../../src/oauth/index.js";
import type { ThingsProtocolHandler } from "../../src/protocol/types.js";
import { createStoreFixture, loadFixture } from "../oauth/helpers.js";

const context = createTrustedOAuthRequestContext({
  connectionKey: "a".repeat(32),
  listenerId: "oauth-loopback-46684",
  sourceIp: "127.0.0.1",
});

async function invokeRemoteIngress(
  options: ThingsIngressOptions,
  input: {
    readonly body?: string;
    readonly headers?: IncomingHttpHeaders;
    readonly method: string;
    readonly rawHeaders?: readonly string[];
    readonly target: string;
  },
): Promise<Readonly<{
  body: string;
  headers: ReadonlyMap<string, unknown>;
  status: number;
}>> {
  const request = Readable.from(input.body === undefined ? [] : [Buffer.from(input.body)]) as
    unknown as IncomingMessage;
  Object.defineProperties(request, {
    headers: { value: input.headers ?? {} },
    method: { value: input.method },
    rawHeaders: { value: input.rawHeaders ?? [] },
    socket: {
      value: {
        localAddress: "127.0.0.1",
        localPort: options.kind === "local-bearer" ? 46683 : 46684,
        remoteAddress: "127.0.0.1",
      },
    },
    url: { value: input.target },
  });
  return await new Promise((resolve, reject) => {
    const headers = new Map<string, unknown>();
    let body = "";
    const response = {
      destroy: (error?: Error) => reject(error ?? new Error("response_destroyed")),
      end: (chunk?: unknown) => {
        if (chunk !== undefined) body += Buffer.from(chunk as Uint8Array).toString("utf8");
        response.headersSent = true;
        resolve({ body, headers, status: response.statusCode });
      },
      hasHeader: (name: string) => headers.has(name.toLowerCase()),
      headersSent: false,
      setHeader: (name: string, value: unknown) => {
        headers.set(name.toLowerCase(), value);
        return response;
      },
      shouldKeepAlive: true,
      statusCode: 200,
    } as unknown as ServerResponse & { headersSent: boolean; statusCode: number };
    createThingsIngressRequestListener(options)(request, response);
  });
}

function serviceFixture(): Readonly<{
  close(): void;
  service: ThingsOAuthService;
}> {
  const fixture = createStoreFixture();
  const metadata = loadFixture("dcr-approved.json");
  return {
    close: () => fixture.close(),
    service: new ThingsOAuthService({
      store: fixture.store,
      clientPolicy: {
        registrationMode: "dcr",
        approvedClientId: null,
        approvedCallbacks: ["https://chatgpt.com/connector_platform_oauth_redirect"],
        approvedMetadataDigest: sha256(canonicalJson(metadata)),
      },
      cimdResolver: null,
      registrationPrincipal: "approved-operator",
      verifyLoginProof: async () => ({ accountKey: "account", principal: "principal" }),
    }),
  };
}

test("serializes successful authorization responses with RFC 9207 iss", () => {
  const result = issuerBoundAuthorizationRedirect("https://chatgpt.com/callback", {
    code: "opaque-code",
    state: "client-state",
  });
  assert.equal(result.searchParams.get("iss"), THINGS_ISSUER);
  assert.equal(result.searchParams.get("code"), "opaque-code");
  assert.equal(result.searchParams.get("state"), "client-state");
});

test("serializes authorization errors through the same RFC 9207 path", () => {
  const result = issuerBoundAuthorizationRedirect("https://chatgpt.com/callback", {
    error: "access_denied",
    state: "client-state",
  });
  assert.equal(result.searchParams.get("iss"), THINGS_ISSUER);
  assert.equal(result.searchParams.get("error"), "access_denied");
});

test("removes preexisting query and fragment material", () => {
  const result = issuerBoundAuthorizationRedirect("https://chatgpt.com/callback?old=1#fragment", {
    error: "invalid_request",
  });
  assert.equal(result.hash, "");
  assert.equal(result.searchParams.has("old"), false);
});

test("rejects non-HTTPS authorization redirects", () => {
  assert.throws(
    () => issuerBoundAuthorizationRedirect("http://127.0.0.1/callback", { error: "access_denied" }),
    /authorization_redirect_invalid/u,
  );
});

test("rejects malformed response values", () => {
  assert.throws(
    () => issuerBoundAuthorizationRedirect("https://chatgpt.com/callback", { code: "", state: "s" }),
    /authorization_response_invalid/u,
  );
});

test("capture handler exposes protected-resource metadata", async () => {
  const response = await new CaptureOnlyOAuthHandler().fetch(
    new Request("https://mcp.w4w.dev/.well-known/oauth-protected-resource/mcp/things"),
    { route: "oauth-protected-resource", trustedContext: context },
  );
  assert.equal(response.status, 200);
  assert.equal((await response.json() as { resource: string }).resource, THINGS_ISSUER);
});

test("capture handler exposes authorization-server metadata", async () => {
  const response = await new CaptureOnlyOAuthHandler().fetch(
    new Request("https://mcp.w4w.dev/.well-known/oauth-authorization-server"),
    { route: "oauth-authorization-server", trustedContext: context },
  );
  assert.equal(response.status, 200);
  assert.equal((await response.json() as { issuer: string }).issuer, THINGS_ISSUER);
});

const CLOUDFLARE_FORWARDING_HEADERS = [
  "Cf-Connecting-Ip",
  "203.0.113.10",
  "True-Client-Ip",
  "203.0.113.10",
  "X-Forwarded-For",
  "203.0.113.10",
  "X-Forwarded-Host",
  "mcp.w4w.dev",
  "X-Forwarded-Proto",
  "https",
  "X-Forwarded-Port",
  "443",
  "Forwarded",
  "for=203.0.113.10;proto=https",
] as const;

function dummyProtocolHandler(): ThingsProtocolHandler {
  return {
    close: async () => undefined,
    fetch: async () => new Response(null, { status: 500 }),
  } as unknown as ThingsProtocolHandler;
}

test("remote-oauth discovery accepts Cloudflare forwarding headers", async () => {
  const expiresAt = Date.now() + 60_000;
  const protocolHandler = dummyProtocolHandler();
  for (const host of ["mcp.w4w.dev", "mcp.w4w.dev:443"] as const) {
    const response = await invokeRemoteIngress(
      {
        kind: "remote-oauth",
        oauthHandler: new CaptureOnlyOAuthHandler(),
        protocolHandler,
        remoteExpiresAt: expiresAt,
        remoteToolDispatchEnabled: false,
      },
      {
        headers: { host },
        method: "GET",
        rawHeaders: ["Host", host, ...CLOUDFLARE_FORWARDING_HEADERS],
        target: "/.well-known/oauth-protected-resource/mcp/things",
      },
    );
    assert.equal(response.status, 200);
    assert.equal((JSON.parse(response.body) as { resource: string }).resource, THINGS_ISSUER);
  }
});

test("local-bearer rejects Cloudflare forwarding headers", async () => {
  const response = await invokeRemoteIngress(
    {
      kind: "local-bearer",
      localBearerToken: "opaque-token",
      protocolHandler: dummyProtocolHandler(),
    },
    {
      headers: { host: "127.0.0.1:46683" },
      method: "GET",
      rawHeaders: [
        "Host",
        "127.0.0.1:46683",
        "Authorization",
        "Bearer opaque-token",
        ...CLOUDFLARE_FORWARDING_HEADERS,
      ],
      target: "/mcp/things",
    },
  );
  assert.equal(response.status, 400);
  assert.equal(response.body, "");
});

test("capture handler keeps interactive OAuth and tools disabled", async () => {
  const temporary = await mkdtemp(path.join(os.tmpdir(), "mcphub-capture-evidence-"));
  await chmod(temporary, 0o700);
  const evidencePath = path.join(temporary, "observed-wire.json");
  const receiptSha256 = "7".repeat(64);
  const capturedNow = Date.now();
  const expiresAt = capturedNow + 5 * 60 * 1_000;
  const recorder = new CaptureEvidenceRecorder({
    captureReceiptSha256: receiptSha256,
    createdAt: capturedNow - 1_000,
    expiresAt,
    now: () => capturedNow,
    path: evidencePath,
  });
  const handler = new CaptureOnlyOAuthHandler(recorder);
  let protocolDispatches = 0;
  const protocolHandler = {
    close: async () => undefined,
    fetch: async () => {
      protocolDispatches += 1;
      return new Response(null, { status: 500 });
    },
  } as unknown as ThingsProtocolHandler;
  const stateSentinel = "private-state-must-not-persist";
  const clientSentinel = "private-client-name-must-not-persist";
  const challengeSentinel = "a".repeat(43);
  try {
    const mcpBody = JSON.stringify({
      jsonrpc: "2.0",
      id: 1,
      method: "server/discover",
      params: {
        _meta: {
          "io.modelcontextprotocol/clientInfo": {
            name: clientSentinel,
            version: "1.0.0",
          },
          "io.modelcontextprotocol/protocolVersion": "2026-07-28",
        },
      },
    });
    const challenged = await invokeRemoteIngress(
      {
        captureRecorder: recorder,
        kind: "remote-oauth",
        oauthHandler: handler,
        protocolHandler,
        remoteExpiresAt: expiresAt,
        remoteToolDispatchEnabled: false,
      },
      {
        body: mcpBody,
        headers: {
          "content-type": "application/json",
          host: "mcp.w4w.dev",
          "mcp-method": "server/discover",
          "mcp-protocol-version": "2026-07-28",
        },
        method: "POST",
        rawHeaders: [
          "Host",
          "mcp.w4w.dev",
          "Content-Type",
          "application/json",
          "Mcp-Method",
          "server/discover",
          "Mcp-Protocol-Version",
          "2026-07-28",
        ],
        target: "/mcp/things",
      },
    );
    assert.equal(challenged.status, 401);
    assert.equal(challenged.headers.get("www-authenticate"), remoteOAuthChallenge());
    assert.equal(protocolDispatches, 0);
    for (const [route, target] of [
      [
        "oauth-protected-resource",
        "https://mcp.w4w.dev/.well-known/oauth-protected-resource/mcp/things",
      ],
      [
        "oauth-authorization-server",
        "https://mcp.w4w.dev/.well-known/oauth-authorization-server",
      ],
    ] as const) {
      const response = await handler.fetch(new Request(target), {
        route,
        trustedContext: context,
      });
      assert.equal(response.status, 200);
    }
    const authorize = new URL("https://mcp.w4w.dev/oauth/authorize");
    authorize.searchParams.set("client_id", "https://chatgpt.com/oauth/client.json");
    authorize.searchParams.set("code_challenge", challengeSentinel);
    authorize.searchParams.set("code_challenge_method", "S256");
    authorize.searchParams.set(
      "redirect_uri",
      "https://chatgpt.com/connector_platform_oauth_redirect",
    );
    authorize.searchParams.set("resource", THINGS_ISSUER);
    authorize.searchParams.set("response_type", "code");
    authorize.searchParams.set("scope", OAUTH_SCOPES.join(" "));
    authorize.searchParams.set("state", stateSentinel);
    const response = await handler.fetch(new Request(authorize), {
      route: "oauth-authorize",
      trustedContext: context,
    });
    assert.equal(response.status, 503);
    assert.equal(await response.text(), "");

    const evidenceBytes = await readFile(evidencePath);
    const evidence = parseCaptureEvidenceRecord({
      bytes: evidenceBytes,
      captureReceiptSha256: receiptSha256,
      now: capturedNow,
    });
    assert.equal(evidence.status, "observed-pass");
    assert.equal(evidence.registrationMode, "client-id-metadata-document");
    assert.equal(evidence.mcpProtocolVersion, "2026-07-28");
    assert.equal(evidence.modernDiscoveryObserved, true);
    assert.deepEqual(evidence.requiredIndependentScopes, [
      "things.read",
      "things.write",
      "things.admin",
    ]);
    assert.equal(evidence.offlineAccessRequested, true);
    assert.equal(evidence.resourceIndicatorObserved, true);
    assert.equal(evidence.pkceS256Observed, true);
    assert.equal(
      Date.parse(evidence.expiresAt) - Date.parse(evidence.capturedAt),
      24 * 60 * 60 * 1_000,
    );
    assert.deepEqual(evidence.routeStatuses, {
      authorization: 503,
      authorizationServerMetadata: 200,
      mcp: 401,
      protectedResourceMetadata: 200,
      registration: null,
    });
    const rawEvidence = evidenceBytes.toString("utf8");
    assert.doesNotMatch(rawEvidence, new RegExp(stateSentinel, "u"));
    assert.doesNotMatch(rawEvidence, new RegExp(clientSentinel, "u"));
    assert.doesNotMatch(rawEvidence, new RegExp(challengeSentinel, "u"));
    assert.equal((await stat(evidencePath)).mode & 0o777, 0o600);
    assert.equal(
      validateCaptureEvidenceForPublic({
        bytes: evidenceBytes,
        expectedRegistrationMode: "cimd",
        now: capturedNow,
      }).status,
      "observed-pass",
    );
    assert.throws(
      () =>
        validateCaptureEvidenceForPublic({
          bytes: evidenceBytes,
          expectedRegistrationMode: "dcr",
          now: capturedNow,
        }),
      /capture_evidence_invalid/u,
    );

    const racedPath = path.join(temporary, "raced-observed-wire.json");
    const racedRecorder = new CaptureEvidenceRecorder({
      captureReceiptSha256: "8".repeat(64),
      createdAt: capturedNow - 1_000,
      expiresAt,
      now: () => capturedNow,
      path: racedPath,
    });
    const racedBytes = Buffer.from("owner-created-between-check-and-publish\n", "utf8");
    await writeFile(racedPath, racedBytes, { flag: "wx", mode: 0o600 });
    await assert.rejects(
      racedRecorder.observe(
        new Request("https://mcp.w4w.dev/.well-known/oauth-protected-resource/mcp/things"),
        "oauth-protected-resource",
        500,
      ),
      /capture_evidence_path_exists/u,
    );
    assert.deepEqual(await readFile(racedPath), racedBytes);
  } finally {
    await rm(temporary, { recursive: true, force: true });
  }
});

test("production handler serves exact well-known OAuth metadata routes", async () => {
  const fixture = serviceFixture();
  try {
    const handler = new ProductionOAuthHandler(fixture.service);
    const [resourceResponse, authorizationResponse, issuerPathResponse] = await Promise.all([
      handler.fetch(
        new Request("https://mcp.w4w.dev/.well-known/oauth-protected-resource/mcp/things"),
        { route: "oauth-protected-resource", trustedContext: context },
      ),
      handler.fetch(
        new Request("https://mcp.w4w.dev/.well-known/oauth-authorization-server"),
        { route: "oauth-authorization-server", trustedContext: context },
      ),
      handler.fetch(
        new Request("https://mcp.w4w.dev/.well-known/oauth-authorization-server/mcp/things"),
        { route: "oauth-authorization-server", trustedContext: context },
      ),
    ]);
    assert.equal(resourceResponse.status, 200);
    assert.equal(authorizationResponse.status, 200);
    assert.equal(issuerPathResponse.status, 200);
    const resource = await resourceResponse.json() as {
      resource: string;
      scopes_supported: readonly string[];
    };
    const authorization = await authorizationResponse.json() as {
      grant_types_supported: readonly string[];
      issuer: string;
      scopes_supported: readonly string[];
    };
    assert.equal(resource.resource, THINGS_ISSUER);
    assert.deepEqual(resource.scopes_supported, OAUTH_SCOPES);
    assert.equal(authorization.issuer, THINGS_ISSUER);
    assert.deepEqual(authorization.grant_types_supported, ["authorization_code", "refresh_token"]);
    assert.deepEqual(authorization.scopes_supported, OAUTH_SCOPES);
  } finally {
    fixture.close();
  }
});

test("unauthenticated production MCP returns an OAuth challenge", () => {
  const fixture = serviceFixture();
  return (async () => {
    let protocolDispatches = 0;
    const protocolHandler = {
      close: async () => undefined,
      fetch: async () => {
        protocolDispatches += 1;
        return new Response(null, { status: 500 });
      },
    } as unknown as ThingsProtocolHandler;
    try {
      const result = await invokeRemoteIngress(
        {
          kind: "remote-oauth",
          oauthHandler: new ProductionOAuthHandler(fixture.service),
          oauthService: fixture.service,
          protocolHandler,
          remoteExpiresAt: Date.now() + 60_000,
          remoteToolDispatchEnabled: true,
        },
        {
          body: "{}",
          headers: { "content-type": "application/json", host: "mcp.w4w.dev" },
          method: "POST",
          rawHeaders: [
            "Host",
            "mcp.w4w.dev",
            "Content-Type",
            "application/json",
          ],
          target: "/mcp/things",
        },
      );
      assert.equal(result.status, 401);
      assert.equal(result.body, "");
      assert.equal(result.headers.get("www-authenticate"), remoteOAuthChallenge());
      assert.equal(protocolDispatches, 0);
      const expired = await invokeRemoteIngress(
        {
          kind: "remote-oauth",
          oauthHandler: new ProductionOAuthHandler(fixture.service),
          oauthService: fixture.service,
          protocolHandler,
          remoteExpiresAt: Date.now() - 1,
          remoteToolDispatchEnabled: true,
        },
        {
          body: "{}",
          method: "POST",
          target: "/mcp/things",
        },
      );
      assert.equal(expired.status, 503);
      assert.equal(expired.headers.has("www-authenticate"), false);
      assert.equal(protocolDispatches, 0);
    } finally {
      fixture.close();
    }
    assert.equal(
      remoteOAuthChallenge(),
      `Bearer resource_metadata="https://mcp.w4w.dev/.well-known/oauth-protected-resource/mcp/things", scope="${OAUTH_SCOPES.join(" ")}"`,
    );
  })();
});

test("capture GET MCP resource returns an OAuth challenge", async () => {
  const handler = new CaptureOnlyOAuthHandler();
  const protocolHandler = {
    close: async () => undefined,
    fetch: async () => new Response(null, { status: 500 }),
  } as unknown as ThingsProtocolHandler;
  const result = await invokeRemoteIngress(
    {
      captureRecorder: {
        observe: async () => undefined,
      } as unknown as CaptureEvidenceRecorder,
      kind: "remote-oauth",
      oauthHandler: handler,
      protocolHandler,
      remoteExpiresAt: Date.now() + 60_000,
      remoteToolDispatchEnabled: false,
    },
    {
      headers: { host: "mcp.w4w.dev" },
      method: "GET",
      rawHeaders: ["Host", "mcp.w4w.dev"],
      target: "/mcp/things",
    },
  );
  assert.equal(result.status, 401);
  assert.equal(result.body, "");
  assert.equal(result.headers.get("www-authenticate"), remoteOAuthChallenge());
});

test("RFC 8414 issuer-path authorization-server metadata reaches origin", async () => {
  const handler = new CaptureOnlyOAuthHandler();
  const protocolHandler = {
    close: async () => undefined,
    fetch: async () => new Response(null, { status: 500 }),
  } as unknown as ThingsProtocolHandler;
  const options = {
    kind: "remote-oauth" as const,
    oauthHandler: handler,
    protocolHandler,
    remoteExpiresAt: Date.now() + 60_000,
    remoteToolDispatchEnabled: false,
  };
  const root = await invokeRemoteIngress(options, {
    headers: { host: "mcp.w4w.dev" },
    method: "GET",
    rawHeaders: ["Host", "mcp.w4w.dev"],
    target: "/.well-known/oauth-authorization-server",
  });
  const issuerPath = await invokeRemoteIngress(options, {
    headers: { host: "mcp.w4w.dev" },
    method: "GET",
    rawHeaders: ["Host", "mcp.w4w.dev"],
    target: "/.well-known/oauth-authorization-server/mcp/things",
  });
  assert.equal(root.status, 200);
  assert.equal(issuerPath.status, 200);
  const rootBody = JSON.parse(root.body) as { issuer: string };
  const pathBody = JSON.parse(issuerPath.body) as { issuer: string };
  assert.equal(rootBody.issuer, THINGS_ISSUER);
  assert.equal(pathBody.issuer, THINGS_ISSUER);
});

test("apex origin landing is served on GET /", async () => {
  const handler = new CaptureOnlyOAuthHandler();
  const protocolHandler = {
    close: async () => undefined,
    fetch: async () => new Response(null, { status: 500 }),
  } as unknown as ThingsProtocolHandler;
  const options = {
    kind: "remote-oauth" as const,
    oauthHandler: handler,
    protocolHandler,
    remoteExpiresAt: Date.now() + 60_000,
    remoteToolDispatchEnabled: false,
  };
  const landing = await invokeRemoteIngress(options, {
    headers: { host: "mcp.w4w.dev" },
    method: "GET",
    rawHeaders: ["Host", "mcp.w4w.dev"],
    target: "/",
  });
  const css = await invokeRemoteIngress(options, {
    headers: { host: "mcp.w4w.dev" },
    method: "GET",
    rawHeaders: ["Host", "mcp.w4w.dev"],
    target: "/oauth/assets/login.css",
  });
  assert.equal(landing.status, 200);
  assert.match(landing.headers.get("content-type") as string, /text\/html/u);
  assert.match(landing.body, /Things\+\+/u);
  assert.match(landing.body, /https:\/\/mcp\.w4w\.dev\/mcp\/things/u);
  assert.equal(css.status, 200);
  assert.match(css.headers.get("content-type") as string, /text\/css/u);
});
