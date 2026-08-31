import type { McpHttpHandler } from "@modelcontextprotocol/server";
import { describe, expect, it, vi } from "vitest";

import {
  CLIENT_CAPABILITIES_META_KEY,
  CLIENT_INFO_META_KEY,
  HEADER_MISMATCH,
  INVALID_REQUEST,
  MCP_METHOD_HEADER,
  MCP_NAME_HEADER,
  MCP_PROTOCOL_VERSION_HEADER,
  METHOD_NOT_FOUND,
  MISSING_REQUIRED_CLIENT_CAPABILITY,
  MODERN_PROTOCOL_VERSION,
  PARSE_ERROR,
  PROTOCOL_VERSION_META_KEY,
  UNSUPPORTED_PROTOCOL_VERSION,
  withProtocolPreflight,
} from "../../src/protocol/index.js";
import {
  authOptions,
  modernBody,
  modernRequest,
  responseJson,
} from "./helpers.js";

function delegate(): {
  readonly handler: McpHttpHandler;
  readonly fetch: ReturnType<typeof vi.fn>;
} {
  const fetch = vi.fn(async (_request: Request, options?: unknown) =>
    Response.json({ options }),
  );
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

async function errorCode(response: Response): Promise<number> {
  const body = await responseJson(response);
  return (body.error as { code: number }).code;
}

describe("body-primary protocol preflight", () => {
  it("parses exactly once and passes the parsed object to SDK 2.0.0", async () => {
    const target = delegate();
    const handler = withProtocolPreflight(target.handler);
    const body = modernBody(1, "server/discover");
    const request = modernRequest(body);
    const options = authOptions();
    const response = await handler.fetch(request, options);

    expect(response.status).toBe(200);
    expect(target.fetch).toHaveBeenCalledOnce();
    expect(target.fetch.mock.calls[0]?.[1]).toEqual({
      ...options,
      parsedBody: body,
    });
    expect(request.bodyUsed).toBe(true);
  });

  it.each([
    ["GET", 405, INVALID_REQUEST],
    ["DELETE", 405, INVALID_REQUEST],
  ])("rejects %s without SDK dispatch", async (method, status, code) => {
    const target = delegate();
    const handler = withProtocolPreflight(target.handler);
    const response = await handler.fetch(
      new Request("http://127.0.0.1:46683/mcp/things", { method }),
    );
    expect(response.status).toBe(status);
    expect(await errorCode(response)).toBe(code);
    expect(target.fetch).not.toHaveBeenCalled();
  });

  it("sets Allow only for GET", async () => {
    const target = delegate();
    const handler = withProtocolPreflight(target.handler);
    const getResponse = await handler.fetch(
      new Request("http://127.0.0.1:46683/mcp/things"),
    );
    const deleteResponse = await handler.fetch(
      new Request("http://127.0.0.1:46683/mcp/things", {
        method: "DELETE",
      }),
    );
    expect(getResponse.headers.get("allow")).toBe("POST");
    expect(deleteResponse.headers.has("allow")).toBe(false);
  });

  it.each([
    [MCP_PROTOCOL_VERSION_HEADER, "2025-11-25", HEADER_MISMATCH],
    [MCP_PROTOCOL_VERSION_HEADER, "2099-01-01", UNSUPPORTED_PROTOCOL_VERSION],
    [MCP_METHOD_HEADER, "tools/list", HEADER_MISMATCH],
    [MCP_NAME_HEADER, "not-allowed", HEADER_MISMATCH],
  ])("rejects contradictory %s without fallback", async (header, value, code) => {
    const target = delegate();
    const handler = withProtocolPreflight(target.handler);
    const response = await handler.fetch(
      modernRequest(modernBody(2, "server/discover"), { [header]: value }),
    );
    expect(response.status).toBe(400);
    expect(await errorCode(response)).toBe(code);
    expect(target.fetch).not.toHaveBeenCalled();
  });

  it.each([
    [PROTOCOL_VERSION_META_KEY, undefined, HEADER_MISMATCH],
    [CLIENT_CAPABILITIES_META_KEY, undefined, MISSING_REQUIRED_CLIENT_CAPABILITY],
    [CLIENT_INFO_META_KEY, { name: "", version: "1" }, -32602],
  ])("rejects missing or malformed body metadata %s", async (key, value, code) => {
    const target = delegate();
    const handler = withProtocolPreflight(target.handler);
    const body = modernBody(3, "tools/list");
    const params = body.params as Record<string, unknown>;
    const meta = params._meta as Record<string, unknown>;
    if (value === undefined) {
      delete meta[key];
    } else {
      meta[key] = value;
    }
    const response = await handler.fetch(modernRequest(body));
    expect(response.status).toBe(400);
    expect(await errorCode(response)).toBe(code);
    expect(target.fetch).not.toHaveBeenCalled();
  });

  it.each([
    ["2025-11-25", HEADER_MISMATCH],
    ["2099-01-01", UNSUPPORTED_PROTOCOL_VERSION],
  ])("distinguishes conflicting supported body era %s from unsupported", async (version, code) => {
    const target = delegate();
    const handler = withProtocolPreflight(target.handler);
    const body = modernBody(31, "tools/list");
    const params = body.params as Record<string, unknown>;
    const meta = params._meta as Record<string, unknown>;
    meta[PROTOCOL_VERSION_META_KEY] = version;
    const response = await handler.fetch(modernRequest(body));
    expect(response.status).toBe(400);
    expect(await errorCode(response)).toBe(code);
    expect(target.fetch).not.toHaveBeenCalled();
  });

  it.each([
    ["mcp-session-id", "session"],
    ["last-event-id", "event"],
  ])("rejects transport state in %s", async (header, value) => {
    const target = delegate();
    const handler = withProtocolPreflight(target.handler);
    const response = await handler.fetch(
      modernRequest(modernBody(4, "tools/list"), { [header]: value }),
    );
    expect(response.status).toBe(400);
    expect(await errorCode(response)).toBe(HEADER_MISMATCH);
    expect(target.fetch).not.toHaveBeenCalled();
  });

  it("rejects malformed and oversized JSON before SDK dispatch", async () => {
    const target = delegate();
    const handler = withProtocolPreflight(target.handler, {
      maxRequestBodySize: 16,
    });
    const malformed = await handler.fetch(
      new Request("http://127.0.0.1:46683/mcp/things", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: "{",
      }),
    );
    const oversized = await handler.fetch(
      new Request("http://127.0.0.1:46683/mcp/things", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ payload: "x".repeat(20) }),
      }),
    );
    expect(await errorCode(malformed)).toBe(PARSE_ERROR);
    expect(oversized.status).toBe(413);
    expect(await errorCode(oversized)).toBe(INVALID_REQUEST);
    expect(target.fetch).not.toHaveBeenCalled();
  });

  it("cancels a lengthless multi-chunk body before retaining overflow", async () => {
    const target = delegate();
    const cancel = vi.fn();
    const encoder = new TextEncoder();
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(encoder.encode('{"jsonrpc":"2.0",'));
        controller.enqueue(encoder.encode('"payload":"too-large"}'));
      },
      cancel,
    });
    const request = new Request("http://127.0.0.1:46683/mcp/things", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: stream,
      duplex: "half",
    } as RequestInit & { duplex: "half" });
    expect(request.headers.has("content-length")).toBe(false);

    const response = await withProtocolPreflight(target.handler, {
      maxRequestBodySize: 24,
    }).fetch(request, authOptions());

    expect(response.status).toBe(413);
    expect(await errorCode(response)).toBe(INVALID_REQUEST);
    expect(cancel).toHaveBeenCalledOnce();
    expect(target.fetch).not.toHaveBeenCalled();
  });

  it("uses fatal UTF-8 decoding after the streaming bound", async () => {
    const target = delegate();
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(new Uint8Array([0xc3, 0x28]));
        controller.close();
      },
    });
    const response = await withProtocolPreflight(target.handler).fetch(
      new Request("http://127.0.0.1:46683/mcp/things", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: stream,
        duplex: "half",
      } as RequestInit & { duplex: "half" }),
      authOptions(),
    );
    expect(response.status).toBe(400);
    expect(await errorCode(response)).toBe(PARSE_ERROR);
    expect(target.fetch).not.toHaveBeenCalled();
  });

  it("does not reinterpret an unknown modern RPC as legacy", async () => {
    const target = delegate();
    target.fetch.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          jsonrpc: "2.0",
          id: 5,
          error: { code: METHOD_NOT_FOUND, message: "Method not found" },
        }),
        { status: 404, headers: { "content-type": "application/json" } },
      ),
    );
    const handler = withProtocolPreflight(target.handler);
    const response = await handler.fetch(
      modernRequest(modernBody(5, "things/unknown")),
      authOptions(),
    );
    expect(response.status).toBe(404);
    expect(await errorCode(response)).toBe(METHOD_NOT_FOUND);
    expect(target.fetch).toHaveBeenCalledOnce();
  });
});
