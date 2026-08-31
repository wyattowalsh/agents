import type {
  IncomingMessage,
  RequestListener,
  ServerResponse,
} from "node:http";
import { randomBytes } from "node:crypto";

import type { AuthInfo } from "@modelcontextprotocol/server";

import type { ThingsOAuthService } from "../oauth/service.js";
import {
  createTrustedOAuthRequestContext,
} from "../policy/oauth-ingress-contract.js";
import {
  THINGS_PROTECTED_RESOURCE_METADATA,
  OAUTH_SCOPES,
} from "../policy/oauth-policy.js";
import type { ThingsProtocolHandler } from "../protocol/types.js";
import { OAuthSecurityError } from "../security/common/errors.js";
import {
  localBearerAuthInfo,
  remoteOAuthAuthInfo,
} from "../security/ingress/credentials.js";
import {
  acceptedSocketIdentity,
  headersWithoutCredentials,
  IngressSecurityError,
  rejectForwardingHeaders,
} from "../security/ingress/request-security.js";
import { readBoundedBody } from "./body.js";
import {
  DEFAULT_MAX_REQUEST_BODY_SIZE,
  LOCAL_LISTENER,
  REMOTE_LISTENER,
  type ListenerKind,
} from "./constants.js";
import type { OAuthIngressHandler } from "./oauth-handler.js";
import { decideIngressRoute } from "./route-policy.js";
import type { CaptureEvidenceRecorder } from "./capture-evidence.js";

export interface ThingsIngressOptions {
  readonly captureRecorder?: CaptureEvidenceRecorder;
  readonly kind: ListenerKind;
  readonly protocolHandler: ThingsProtocolHandler;
  readonly localBearerToken?: string;
  readonly oauthService?: ThingsOAuthService;
  readonly oauthHandler?: OAuthIngressHandler;
  readonly localControlPlane?: RequestListener;
  readonly remoteToolDispatchEnabled?: boolean;
  readonly remoteExpiresAt?: number;
  readonly maxRequestBodySize?: number;
}

export function remoteOAuthChallenge(): string {
  return `Bearer resource_metadata="${THINGS_PROTECTED_RESOURCE_METADATA}", scope="${OAUTH_SCOPES.join(" ")}"`;
}

function contentFree(
  response: ServerResponse,
  status: number,
  allow?: readonly string[],
  oauthChallenge = false,
): void {
  response.statusCode = status;
  response.setHeader("cache-control", "no-store");
  response.setHeader("content-length", "0");
  if (allow !== undefined && allow.length > 0) {
    response.setHeader("allow", allow.join(", "));
  }
  if (oauthChallenge) {
    response.setHeader("www-authenticate", remoteOAuthChallenge());
  }
  if (status >= 400) {
    response.setHeader("connection", "close");
    response.shouldKeepAlive = false;
  }
  response.end();
}

function singleClientAuthorization(rawHeaders: readonly string[]): string | undefined {
  const values: string[] = [];
  for (let index = 0; index < rawHeaders.length; index += 2) {
    if (rawHeaders[index]?.toLowerCase() === "authorization") {
      const value = rawHeaders[index + 1];
      if (value !== undefined) values.push(value);
    }
  }
  if (values.length === 0) return undefined;
  const value = values[0];
  if (
    values.length !== 1 ||
    value === undefined ||
    value.length > 8_192 ||
    value.includes(",") ||
    /[\u0000-\u001f\u007f]/u.test(value)
  ) {
    throw new IngressSecurityError("credential_ambiguous", 401);
  }
  return value;
}

async function writeFetchResponse(
  target: ServerResponse,
  response: Response,
): Promise<void> {
  target.statusCode = response.status;
  for (const [name, value] of response.headers) {
    if (name.toLowerCase() !== "set-cookie") target.setHeader(name, value);
  }
  const setCookies = response.headers.getSetCookie();
  if (setCookies.length > 0) target.setHeader("set-cookie", setCookies);
  if (response.body === null) {
    if (!target.hasHeader("content-length")) target.setHeader("content-length", "0");
    target.end();
    return;
  }
  const body = Buffer.from(await response.arrayBuffer());
  if (!target.hasHeader("content-length")) target.setHeader("content-length", body.byteLength);
  target.end(body);
}

function remoteHostAllowed(rawHeaders: readonly string[]): boolean {
  const hosts: string[] = [];
  for (let index = 0; index < rawHeaders.length; index += 2) {
    if (rawHeaders[index]?.toLowerCase() === "host" && rawHeaders[index + 1] !== undefined) {
      hosts.push(rawHeaders[index + 1] as string);
    }
  }
  const host = hosts[0]?.toLowerCase();
  return hosts.length === 1 && (host === "mcp.w4w.dev" || host === "mcp.w4w.dev:443");
}

function requestUrl(request: IncomingMessage, kind: ListenerKind): URL {
  const base = kind === "local-bearer" ? LOCAL_LISTENER.resource : REMOTE_LISTENER.resource;
  return new URL(request.url ?? "/", base);
}

async function toFetchRequest(
  request: IncomingMessage,
  kind: ListenerKind,
  body: Uint8Array | undefined,
): Promise<Request> {
  const method = request.method ?? "GET";
  return new Request(requestUrl(request, kind), {
    method,
    headers: headersWithoutCredentials(request.headers),
    ...(body === undefined || method === "GET" || method === "HEAD" ? {} : { body }),
  });
}

function authInfo(options: ThingsIngressOptions, request: IncomingMessage): AuthInfo {
  if (options.kind === "local-bearer") {
    return localBearerAuthInfo(request.rawHeaders, options.localBearerToken ?? "");
  }
  if (options.oauthService === undefined) {
    throw new IngressSecurityError("remote_oauth_unavailable", 503);
  }
  return remoteOAuthAuthInfo(request.rawHeaders, options.oauthService);
}

export function createThingsIngressRequestListener(
  options: ThingsIngressOptions,
): RequestListener {
  const maximumBodySize = options.maxRequestBodySize ?? DEFAULT_MAX_REQUEST_BODY_SIZE;
  return (request, response) => {
    let remoteMcpRoute = false;
    void (async () => {
      if (
        options.kind === "remote-oauth" &&
        (options.remoteExpiresAt === undefined ||
          !Number.isSafeInteger(options.remoteExpiresAt) ||
          Date.now() >= options.remoteExpiresAt)
      ) {
        contentFree(response, 503);
        return;
      }
      const socket = acceptedSocketIdentity(request, options.kind);
      if (options.kind === "local-bearer") {
        rejectForwardingHeaders(request.rawHeaders);
      }
      if (options.kind === "remote-oauth" && !remoteHostAllowed(request.rawHeaders)) {
        throw new IngressSecurityError("host_invalid", 404);
      }
      const decision = decideIngressRoute({
        kind: options.kind,
        method: request.method,
        target: request.url,
      });
      if (decision.action === "delegate-local-control-plane") {
        if (options.localControlPlane === undefined) {
          contentFree(response, 503);
        } else {
          options.localControlPlane(request, response);
        }
        return;
      }
      if (decision.action === "not-found") {
        contentFree(response, 404);
        return;
      }

      if (decision.action === "method-not-allowed") {
        remoteMcpRoute = options.kind === "remote-oauth";
        if (options.kind === "remote-oauth" && options.remoteToolDispatchEnabled !== true) {
          // Capture has no oauthService; authInfo would 503. Emit the challenge instead.
          contentFree(
            response,
            options.captureRecorder === undefined ? 503 : 401,
            undefined,
            options.captureRecorder !== undefined,
          );
          return;
        }
        authInfo(options, request);
        contentFree(response, 405, decision.allow);
        return;
      }

      const body = await readBoundedBody(request, maximumBodySize);
      const fetchRequest = await toFetchRequest(request, options.kind, body);
      if (decision.route === "things-mcp") {
        remoteMcpRoute = options.kind === "remote-oauth";
        if (options.kind === "remote-oauth" && options.remoteToolDispatchEnabled !== true) {
          if (options.captureRecorder === undefined) {
            contentFree(response, 503);
          } else {
            await options.captureRecorder.observe(fetchRequest, decision.route, 401);
            contentFree(response, 401, undefined, true);
          }
          return;
        }
        const authenticated = authInfo(options, request);
        const protocolResponse = await options.protocolHandler.fetch(fetchRequest, {
          authInfo: authenticated,
        });
        await writeFetchResponse(response, protocolResponse);
        return;
      }

      if (options.oauthHandler === undefined) {
        contentFree(response, 503);
        return;
      }
      const trustedContext = createTrustedOAuthRequestContext({
        connectionKey: randomBytes(32).toString("base64url"),
        listenerId: "oauth-loopback-46684",
        sourceIp: socket.peerAddress,
      });
      const clientAuthorization = singleClientAuthorization(request.rawHeaders);
      await writeFetchResponse(
        response,
        await options.oauthHandler.fetch(fetchRequest, {
          ...(clientAuthorization === undefined ? {} : { clientAuthorization }),
          route: decision.route,
          trustedContext,
        }),
      );
    })().catch((error: unknown) => {
      if (response.headersSent) {
        response.destroy();
        return;
      }
      if (error instanceof IngressSecurityError) {
        contentFree(response, error.status, undefined, remoteMcpRoute && error.status >= 401);
        return;
      }
      if (error instanceof OAuthSecurityError) {
        contentFree(response, error.httpStatus, undefined, remoteMcpRoute);
        return;
      }
      contentFree(response, 500);
    });
  };
}
