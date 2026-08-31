import type { McpHttpHandler } from "@modelcontextprotocol/server";
import { describe, expect, it, vi } from "vitest";

import {
  INVALID_PARAMS,
  LEGACY_PROTOCOL_VERSION,
  LOCAL_THINGS_CREDENTIAL_CLASS,
  REMOTE_THINGS_CREDENTIAL_CLASS,
  REMOTE_THINGS_RESOURCE,
  withProtocolPreflight,
} from "../../src/protocol/index.js";
import {
  authOptions,
  legacyRequest,
  modernBody,
  modernRequest,
  responseJson,
} from "./helpers.js";

function delegate(): {
  readonly handler: McpHttpHandler;
  readonly fetch: ReturnType<typeof vi.fn>;
} {
  const fetch = vi.fn(async () => Response.json({ ok: true }));
  return {
    fetch,
    handler: {
      fetch,
      close: vi.fn(async () => undefined),
      notify: {} as McpHttpHandler["notify"],
      bus: {} as McpHttpHandler["bus"],
    },
  };
}

function legacyInitialize(): Request {
  return legacyRequest({
    jsonrpc: "2.0",
    id: 10,
    method: "initialize",
    params: {
      protocolVersion: LEGACY_PROTOCOL_VERSION,
      capabilities: {},
      clientInfo: { name: "auth-test", version: "1.0.0" },
    },
  });
}

function legacyList(): Request {
  return legacyRequest({
    jsonrpc: "2.0",
    id: 11,
    method: "tools/list",
    params: {},
  });
}

const CATALOG_REQUESTS: readonly [string, () => Request][] = [
  ["modern server/discover", () => modernRequest(modernBody(1, "server/discover"))],
  ["modern tools/list", () => modernRequest(modernBody(2, "tools/list"))],
  ["legacy initialize", legacyInitialize],
  ["legacy tools/list", legacyList],
];

async function expectRejected(
  requestFactory: () => Request,
  options: Parameters<McpHttpHandler["fetch"]>[1],
): Promise<void> {
  const target = delegate();
  const response = await withProtocolPreflight(target.handler).fetch(
    requestFactory(),
    options,
  );
  const body = await responseJson(response);
  expect(response.status).toBe(403);
  expect(body.error).toEqual({
    code: INVALID_PARAMS,
    message: "Authorization unavailable",
  });
  const serialized = JSON.stringify(body);
  for (const forbidden of [
    "opaque-test-token",
    "subject:test",
    "things-conformance-client",
    "example.invalid",
    "remote-oauth",
    "local-bearer",
  ]) {
    expect(serialized).not.toContain(forbidden);
  }
  expect(target.fetch).not.toHaveBeenCalled();
}

describe("protocol authorization boundary", () => {
  it.each(CATALOG_REQUESTS)(
    "requires the exact three-scope identity for %s",
    async (_name, requestFactory) => {
      await expectRejected(requestFactory, undefined);
      await expectRejected(requestFactory, authOptions(["things.read", "things.write"]));
      await expectRejected(
        requestFactory,
        authOptions([
          "things.read",
          "things.write",
          "things.admin",
          "things.extra",
        ]),
      );
      await expectRejected(
        requestFactory,
        authOptions([
          "things.read",
          "things.write",
          "things.admin",
          "things.admin",
        ]),
      );
    },
  );

  it.each(CATALOG_REQUESTS)(
    "rejects wrong resource, credential class, principal, client and token for %s",
    async (_name, requestFactory) => {
      await expectRejected(
        requestFactory,
        authOptions(undefined, {
          resource: "https://example.invalid/mcp/things",
          credentialClass: REMOTE_THINGS_CREDENTIAL_CLASS,
        }),
      );
      await expectRejected(
        requestFactory,
        authOptions(undefined, {
          credentialClass: REMOTE_THINGS_CREDENTIAL_CLASS,
        }),
      );
      await expectRejected(requestFactory, authOptions(undefined, { principal: "" }));
      await expectRejected(requestFactory, authOptions(undefined, { clientId: "" }));
      await expectRejected(requestFactory, authOptions(undefined, { token: "" }));
    },
  );

  it.each(CATALOG_REQUESTS)(
    "accepts exact local and remote credential classes for %s",
    async (_name, requestFactory) => {
      for (const options of [
        authOptions(undefined, {
          credentialClass: LOCAL_THINGS_CREDENTIAL_CLASS,
        }),
        authOptions(undefined, {
          resource: REMOTE_THINGS_RESOURCE,
          credentialClass: REMOTE_THINGS_CREDENTIAL_CLASS,
        }),
      ]) {
        const target = delegate();
        const response = await withProtocolPreflight(target.handler).fetch(
          requestFactory(),
          options,
        );
        expect(response.status).toBe(200);
        expect(target.fetch).toHaveBeenCalledOnce();
      }
    },
  );

  it("preserves per-tool independent scopes after identity validation", async () => {
    const target = delegate();
    const response = await withProtocolPreflight(target.handler).fetch(
      modernRequest(
        modernBody(20, "tools/call", {
          name: "things_core__context_stats",
          arguments: {},
        }),
      ),
      authOptions(["things.read"]),
    );
    expect(response.status).toBe(200);
    expect(target.fetch).toHaveBeenCalledOnce();
  });
});
