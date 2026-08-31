import { createHash, timingSafeEqual } from "node:crypto";
import { isIP } from "node:net";

import type { IncomingHttpHeaders, IncomingMessage } from "node:http";

import type { ListenerKind } from "../../ingress/constants.js";

export class IngressSecurityError extends Error {
  public constructor(
    public readonly code: string,
    public readonly status: number,
  ) {
    super(code);
    this.name = "IngressSecurityError";
  }
}

const FORWARDED_HEADERS = new Set([
  "cf-connecting-ip",
  "forwarded",
  "true-client-ip",
  "x-forwarded-for",
  "x-forwarded-host",
  "x-forwarded-port",
  "x-forwarded-proto",
  "x-real-ip",
]);

function digest(value: string): Buffer {
  return createHash("sha256").update(value, "utf8").digest();
}

function singleRawHeader(rawHeaders: readonly string[], name: string): string | undefined {
  const values: string[] = [];
  for (let index = 0; index < rawHeaders.length; index += 2) {
    const key = rawHeaders[index];
    const value = rawHeaders[index + 1];
    if (key?.toLowerCase() === name && value !== undefined) values.push(value);
  }
  if (values.length === 0) return undefined;
  if (values.length !== 1 || values[0]?.includes(",")) {
    throw new IngressSecurityError("credential_ambiguous", 401);
  }
  return values[0];
}

export function rejectForwardingHeaders(rawHeaders: readonly string[]): void {
  for (let index = 0; index < rawHeaders.length; index += 2) {
    const name = rawHeaders[index]?.toLowerCase();
    if (name !== undefined && FORWARDED_HEADERS.has(name)) {
      throw new IngressSecurityError("forwarding_header_forbidden", 400);
    }
  }
}

export function extractSingleBearer(rawHeaders: readonly string[]): string {
  const value = singleRawHeader(rawHeaders, "authorization");
  if (
    value === undefined ||
    !value.startsWith("Bearer ") ||
    value.length <= "Bearer ".length ||
    /[\u0000-\u0020\u007f]/u.test(value.slice("Bearer ".length))
  ) {
    throw new IngressSecurityError("credential_invalid", 401);
  }
  return value.slice("Bearer ".length);
}

export function requireExactBearer(actual: string, expected: string): void {
  if (
    expected.length === 0 ||
    expected.startsWith("replace-with-local-") ||
    !timingSafeEqual(digest(actual), digest(expected))
  ) {
    throw new IngressSecurityError("credential_invalid", 401);
  }
}

function canonicalLoopback(value: string | undefined): string {
  if (value === undefined) throw new IngressSecurityError("socket_identity_invalid", 403);
  const unwrapped = value.startsWith("::ffff:") ? value.slice(7) : value;
  if (unwrapped === "127.0.0.1" || unwrapped === "::1") return unwrapped;
  if (isIP(unwrapped) === 0) throw new IngressSecurityError("socket_identity_invalid", 403);
  throw new IngressSecurityError("socket_not_loopback", 403);
}

export interface AcceptedSocketIdentity {
  readonly kind: ListenerKind;
  readonly listenerId: "local-bearer-46683" | "oauth-loopback-46684";
  readonly localAddress: string;
  readonly localPort: 46683 | 46684;
  readonly peerAddress: string;
}

export function acceptedSocketIdentity(
  request: IncomingMessage,
  kind: ListenerKind,
): AcceptedSocketIdentity {
  const expectedPort = kind === "local-bearer" ? 46683 : 46684;
  const actualPort = request.socket.localPort;
  if (actualPort !== expectedPort) {
    throw new IngressSecurityError("socket_listener_mismatch", 403);
  }
  return Object.freeze({
    kind,
    listenerId:
      kind === "local-bearer" ? "local-bearer-46683" : "oauth-loopback-46684",
    localAddress: canonicalLoopback(request.socket.localAddress),
    localPort: expectedPort,
    peerAddress: canonicalLoopback(request.socket.remoteAddress),
  });
}

export function headersWithoutCredentials(
  headers: IncomingHttpHeaders,
): Headers {
  const result = new Headers();
  for (const [name, value] of Object.entries(headers)) {
    if (name === "authorization" || value === undefined) continue;
    if (Array.isArray(value)) {
      for (const item of value) result.append(name, item);
    } else {
      result.set(name, value);
    }
  }
  return result;
}

