import type { JsonObject, JsonValue } from "./types.js";

export const HEADER_MISMATCH = -32020 as const;
export const MISSING_REQUIRED_CLIENT_CAPABILITY = -32021 as const;
export const UNSUPPORTED_PROTOCOL_VERSION = -32022 as const;
export const METHOD_NOT_FOUND = -32601 as const;
export const INVALID_PARAMS = -32602 as const;
export const INVALID_REQUEST = -32600 as const;
export const PARSE_ERROR = -32700 as const;

type RequestId = string | number | null;

export function requestIdOf(body: unknown): RequestId {
  if (body === null || typeof body !== "object" || Array.isArray(body)) {
    return null;
  }
  const id = Object.getOwnPropertyDescriptor(body, "id")?.value;
  return typeof id === "string" || typeof id === "number" ? id : null;
}

export function jsonRpcErrorResponse(
  status: number,
  code: number,
  message: string,
  id: RequestId,
  data?: JsonObject,
  headers?: Readonly<Record<string, string>>,
): Response {
  const error: Record<string, JsonValue> = { code, message };
  if (data !== undefined) {
    error.data = data;
  }
  return new Response(
    JSON.stringify({ jsonrpc: "2.0", id, error }),
    {
      status,
      headers: {
        "content-type": "application/json",
        ...headers,
      },
    },
  );
}

