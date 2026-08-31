import type {
  McpHandlerRequestOptions,
  McpHttpHandler,
} from "@modelcontextprotocol/server";

import {
  hasExactCatalogScopes,
  methodRequiresCatalogAuthorization,
  protocolAuthIdentity,
} from "./authorization.js";
import {
  CLIENT_CAPABILITIES_META_KEY,
  CLIENT_INFO_META_KEY,
  DEFAULT_MAX_REQUEST_BODY_SIZE,
  LAST_EVENT_ID_HEADER,
  LEGACY_PROTOCOL_VERSION,
  MCP_METHOD_HEADER,
  MCP_NAME_HEADER,
  MCP_PROTOCOL_VERSION_HEADER,
  MCP_SESSION_HEADER,
  MODERN_PROTOCOL_VERSION,
  NAME_BEARING_METHODS,
  PROTOCOL_VERSION_META_KEY,
  RESERVED_META_PREFIX,
  SUPPORTED_PROTOCOL_VERSIONS,
} from "./constants.js";
import {
  HEADER_MISMATCH,
  INVALID_PARAMS,
  INVALID_REQUEST,
  MISSING_REQUIRED_CLIENT_CAPABILITY,
  PARSE_ERROR,
  UNSUPPORTED_PROTOCOL_VERSION,
  jsonRpcErrorResponse,
  requestIdOf,
} from "./errors.js";
import type { ProtocolDispatchObserver } from "./dispatch-observer.js";
import type { JsonObject, ProtocolEventSink } from "./types.js";

interface ParsedRequest {
  readonly body: Record<string, unknown>;
  readonly id: string | number | null;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    return false;
  }
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

function rejection(
  eventSink: ProtocolEventSink | undefined,
  status: number,
  code: number,
  message: string,
  id: string | number | null,
  data?: JsonObject,
  headers?: Readonly<Record<string, string>>,
): Response {
  eventSink?.({ code: "protocol_rejected" });
  return jsonRpcErrorResponse(status, code, message, id, data, headers);
}

function unsupportedVersion(
  eventSink: ProtocolEventSink | undefined,
  id: string | number | null,
): Response {
  return rejection(
    eventSink,
    400,
    UNSUPPORTED_PROTOCOL_VERSION,
    "Unsupported protocol version",
    id,
    {
      supported: [...SUPPORTED_PROTOCOL_VERSIONS],
    },
  );
}

function conflictingSupportedVersion(
  eventSink: ProtocolEventSink | undefined,
  id: string | number | null,
): Response {
  return rejection(
    eventSink,
    400,
    HEADER_MISMATCH,
    "Protocol version metadata selects the wrong request era",
    id,
  );
}

function headerValue(
  headers: Headers,
  name: string,
): string | undefined {
  const value = headers.get(name);
  return value === null ? undefined : value;
}

function invalidSingleHeader(value: string | undefined): boolean {
  return (
    value !== undefined &&
    (value.length === 0 ||
      value.includes(",") ||
      /[\u0000-\u001f\u007f]/u.test(value))
  );
}

function mediaTypeIsJson(value: string | null): boolean {
  return value?.split(";", 1)[0]?.trim().toLowerCase() === "application/json";
}

function containsSessionMaterial(body: Record<string, unknown>): boolean {
  const params = isRecord(body.params) ? body.params : undefined;
  const meta = params !== undefined && isRecord(params._meta) ? params._meta : undefined;
  return (
    params?.sessionId !== undefined ||
    meta?.sessionId !== undefined ||
    meta?.[`${RESERVED_META_PREFIX}sessionId`] !== undefined
  );
}

function hasModernBodySignal(body: Record<string, unknown>): boolean {
  const params = isRecord(body.params) ? body.params : undefined;
  const meta = params !== undefined && isRecord(params._meta) ? params._meta : undefined;
  return (
    meta !== undefined &&
    Object.keys(meta).some((key) => key.startsWith(RESERVED_META_PREFIX))
  );
}

async function readJsonRequest(
  request: Request,
  maxRequestBodySize: number,
  eventSink: ProtocolEventSink | undefined,
): Promise<ParsedRequest | Response> {
  const contentLength = request.headers.get("content-length");
  if (contentLength !== null) {
    if (!/^(0|[1-9][0-9]*)$/u.test(contentLength)) {
      return rejection(
        eventSink,
        400,
        INVALID_REQUEST,
        "Invalid Content-Length",
        null,
      );
    }
    if (Number(contentLength) > maxRequestBodySize) {
      return rejection(
        eventSink,
        413,
        INVALID_REQUEST,
        "Request body too large",
        null,
      );
    }
  }
  const reader = request.body?.getReader();
  if (reader === undefined) {
    return rejection(eventSink, 400, PARSE_ERROR, "Parse error", null);
  }
  const chunks: Uint8Array[] = [];
  let byteLength = 0;
  try {
    while (true) {
      const chunk = await reader.read();
      if (chunk.done) {
        break;
      }
      if (chunk.value.byteLength > maxRequestBodySize - byteLength) {
        try {
          await reader.cancel();
        } catch {
          // Cancellation is best effort after the fail-closed size decision.
        }
        return rejection(
          eventSink,
          413,
          INVALID_REQUEST,
          "Request body too large",
          null,
        );
      }
      byteLength += chunk.value.byteLength;
      chunks.push(chunk.value);
    }
  } catch {
    try {
      await reader.cancel();
    } catch {
      // Preserve the content-free parse failure below.
    }
    return rejection(eventSink, 400, PARSE_ERROR, "Parse error", null);
  }
  const bytes = new Uint8Array(byteLength);
  let offset = 0;
  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.byteLength;
  }
  let body: unknown;
  try {
    body = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes));
  } catch {
    return rejection(eventSink, 400, PARSE_ERROR, "Parse error", null);
  }
  if (!isRecord(body)) {
    return rejection(
      eventSink,
      400,
      INVALID_REQUEST,
      "Invalid Request",
      null,
    );
  }
  return { body, id: requestIdOf(body) };
}

function validateModern(
  request: Request,
  parsed: ParsedRequest,
  eventSink: ProtocolEventSink | undefined,
): Response | undefined {
  const { body, id } = parsed;
  const params = isRecord(body.params) ? body.params : undefined;
  const meta = params !== undefined && isRecord(params._meta) ? params._meta : undefined;
  const bodyVersion = meta?.[PROTOCOL_VERSION_META_KEY];
  if (typeof bodyVersion === "string" && bodyVersion !== MODERN_PROTOCOL_VERSION) {
    return bodyVersion === LEGACY_PROTOCOL_VERSION
      ? conflictingSupportedVersion(eventSink, id)
      : unsupportedVersion(eventSink, id);
  }
  if (bodyVersion !== MODERN_PROTOCOL_VERSION) {
    return rejection(
      eventSink,
      400,
      HEADER_MISMATCH,
      "Missing or malformed protocol-version metadata",
      id,
    );
  }

  const protocolHeader = headerValue(request.headers, MCP_PROTOCOL_VERSION_HEADER);
  const methodHeader = headerValue(request.headers, MCP_METHOD_HEADER);
  const nameHeader = headerValue(request.headers, MCP_NAME_HEADER);
  if (
    invalidSingleHeader(protocolHeader) ||
    protocolHeader !== MODERN_PROTOCOL_VERSION ||
    invalidSingleHeader(methodHeader) ||
    typeof body.method !== "string" ||
    methodHeader !== body.method
  ) {
    return rejection(
      eventSink,
      400,
      HEADER_MISMATCH,
      "Required MCP headers do not match the request body",
      id,
    );
  }

  if (meta === undefined || !isRecord(meta[CLIENT_CAPABILITIES_META_KEY])) {
    return rejection(
      eventSink,
      400,
      MISSING_REQUIRED_CLIENT_CAPABILITY,
      "Missing required client capabilities",
      id,
      { requiredCapabilities: {} },
    );
  }
  const clientInfo = meta[CLIENT_INFO_META_KEY];
  if (
    clientInfo !== undefined &&
    (!isRecord(clientInfo) ||
      typeof clientInfo.name !== "string" ||
      clientInfo.name.length === 0 ||
      typeof clientInfo.version !== "string" ||
      clientInfo.version.length === 0)
  ) {
    return rejection(
      eventSink,
      400,
      INVALID_PARAMS,
      "Invalid client information",
      id,
    );
  }

  if (NAME_BEARING_METHODS.has(body.method as "tools/call")) {
    const bodyName = params?.name;
    if (
      invalidSingleHeader(nameHeader) ||
      typeof bodyName !== "string" ||
      bodyName.length === 0 ||
      nameHeader !== bodyName
    ) {
      return rejection(
        eventSink,
        400,
        HEADER_MISMATCH,
        "Mcp-Name does not match the request body",
        id,
      );
    }
  } else if (nameHeader !== undefined) {
    return rejection(
      eventSink,
      400,
      HEADER_MISMATCH,
      "Mcp-Name is not valid for this method",
      id,
    );
  }
  return undefined;
}

function validateLegacy(
  request: Request,
  parsed: ParsedRequest,
  eventSink: ProtocolEventSink | undefined,
): Response | undefined {
  const { body, id } = parsed;
  const protocolHeader = headerValue(request.headers, MCP_PROTOCOL_VERSION_HEADER);
  if (invalidSingleHeader(protocolHeader)) {
    return rejection(
      eventSink,
      400,
      HEADER_MISMATCH,
      "Malformed MCP-Protocol-Version header",
      id,
    );
  }
  if (body.method === "initialize") {
    const params = isRecord(body.params) ? body.params : undefined;
    const requested = params?.protocolVersion;
    if (typeof requested === "string" && requested !== LEGACY_PROTOCOL_VERSION) {
      return unsupportedVersion(eventSink, id);
    }
    if (
      requested !== LEGACY_PROTOCOL_VERSION ||
      (protocolHeader !== undefined && protocolHeader !== LEGACY_PROTOCOL_VERSION)
    ) {
      return rejection(
        eventSink,
        400,
        HEADER_MISMATCH,
        "Invalid legacy initialization",
        id,
      );
    }
    return undefined;
  }
  if (protocolHeader !== LEGACY_PROTOCOL_VERSION) {
    return rejection(
      eventSink,
      400,
      HEADER_MISMATCH,
      "Legacy requests require the compatibility protocol version",
      id,
    );
  }
  return undefined;
}

export function withProtocolPreflight(
  sdkHandler: McpHttpHandler,
  options: {
    readonly maxRequestBodySize?: number;
    readonly eventSink?: ProtocolEventSink;
    readonly dispatchObserver?: ProtocolDispatchObserver;
  } = {},
): McpHttpHandler {
  const maxRequestBodySize =
    options.maxRequestBodySize ?? DEFAULT_MAX_REQUEST_BODY_SIZE;
  if (!Number.isSafeInteger(maxRequestBodySize) || maxRequestBodySize <= 0) {
    throw new RangeError("protocol_max_request_body_size_invalid");
  }
  return {
    close: sdkHandler.close,
    notify: sdkHandler.notify,
    bus: sdkHandler.bus,
    fetch: async (
      request: Request,
      requestOptions?: McpHandlerRequestOptions,
    ): Promise<Response> => {
      if (request.method.toUpperCase() !== "POST") {
        return rejection(
          options.eventSink,
          405,
          INVALID_REQUEST,
          "Method not allowed",
          null,
          undefined,
          request.method.toUpperCase() === "GET" ? { allow: "POST" } : undefined,
        );
      }
      if (
        request.headers.has(MCP_SESSION_HEADER) ||
        request.headers.has(LAST_EVENT_ID_HEADER)
      ) {
        return rejection(
          options.eventSink,
          400,
          HEADER_MISMATCH,
          "Session transport metadata is forbidden",
          null,
        );
      }
      if (!mediaTypeIsJson(request.headers.get("content-type"))) {
        return rejection(
          options.eventSink,
          415,
          INVALID_REQUEST,
          "Content-Type must be application/json",
          null,
        );
      }
      const parsed = await readJsonRequest(
        request,
        maxRequestBodySize,
        options.eventSink,
      );
      if (parsed instanceof Response) {
        return parsed;
      }
      if (containsSessionMaterial(parsed.body)) {
        return rejection(
          options.eventSink,
          400,
          HEADER_MISMATCH,
          "Session transport metadata is forbidden",
          parsed.id,
        );
      }

      const protocolHeader = headerValue(
        request.headers,
        MCP_PROTOCOL_VERSION_HEADER,
      );
      const params = isRecord(parsed.body.params) ? parsed.body.params : undefined;
      const meta = params !== undefined && isRecord(params._meta) ? params._meta : undefined;
      const bodyVersion = meta?.[PROTOCOL_VERSION_META_KEY];
      if (
        typeof protocolHeader === "string" &&
        protocolHeader !== MODERN_PROTOCOL_VERSION &&
        protocolHeader !== LEGACY_PROTOCOL_VERSION
      ) {
        return unsupportedVersion(options.eventSink, parsed.id);
      }
      if (
        typeof bodyVersion === "string" &&
        bodyVersion !== MODERN_PROTOCOL_VERSION
      ) {
        return bodyVersion === LEGACY_PROTOCOL_VERSION
          ? conflictingSupportedVersion(options.eventSink, parsed.id)
          : unsupportedVersion(options.eventSink, parsed.id);
      }

      const modern =
        hasModernBodySignal(parsed.body) ||
        request.headers.has(MCP_METHOD_HEADER) ||
        request.headers.has(MCP_NAME_HEADER) ||
        protocolHeader === MODERN_PROTOCOL_VERSION;
      const invalid = modern
        ? validateModern(request, parsed, options.eventSink)
        : validateLegacy(request, parsed, options.eventSink);
      if (invalid !== undefined) {
        return invalid;
      }
      const identity = protocolAuthIdentity(requestOptions?.authInfo);
      if (
        identity === undefined ||
        (methodRequiresCatalogAuthorization(parsed.body.method) &&
          !hasExactCatalogScopes(identity))
      ) {
        return rejection(
          options.eventSink,
          403,
          INVALID_PARAMS,
          "Authorization unavailable",
          parsed.id,
        );
      }
      options.dispatchObserver?.recordSdkDispatch();
      return sdkHandler.fetch(request, {
        ...requestOptions,
        parsedBody: parsed.body,
      });
    },
  };
}
