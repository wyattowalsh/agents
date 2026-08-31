import { isIP } from "node:net";

import { hashOpaque } from "../security/common/crypto.js";
import { OAuthSecurityError } from "../security/common/errors.js";

const CONNECTION_KEY = /^[A-Za-z0-9_-]{32,128}$/u;
const trustedContexts = new WeakSet<object>();

export const OAUTH_INGRESS_CONTRACT = Object.freeze({
  listenerId: "oauth-loopback-46684",
  forwardedHeadersTrusted: false,
  remoteActivation: "digest-bound-receipt-required",
  sourceIpAuthority: "socket-peer-only",
  toolDispatch: "receipt-and-independent-scope-gated",
} as const);

export interface TrustedOAuthRequestContext {
  readonly connectionKey: string;
  readonly listenerId: typeof OAUTH_INGRESS_CONTRACT.listenerId;
  readonly sourceIp: string;
}

function canonicalIp(value: string): string {
  const unbracketed = value.startsWith("[") && value.endsWith("]") ? value.slice(1, -1) : value;
  if (isIP(unbracketed) === 0 || unbracketed.includes("%")) {
    throw new OAuthSecurityError("oauth_rate_limited", {
      httpStatus: 429,
      oauthError: "temporarily_unavailable",
    });
  }
  if (isIP(unbracketed) === 4) {
    return unbracketed
      .split(".")
      .map((part) => String(Number(part)))
      .join(".");
  }
  const url = new URL(`http://[${unbracketed}]/`);
  return url.hostname.slice(1, -1).toLowerCase();
}

export function createTrustedOAuthRequestContext(input: {
  readonly connectionKey: string;
  readonly listenerId: typeof OAUTH_INGRESS_CONTRACT.listenerId;
  readonly sourceIp: string;
}): TrustedOAuthRequestContext {
  if (
    input.listenerId !== OAUTH_INGRESS_CONTRACT.listenerId ||
    !CONNECTION_KEY.test(input.connectionKey)
  ) {
    throw new OAuthSecurityError("oauth_rate_limited", {
      httpStatus: 429,
      oauthError: "temporarily_unavailable",
    });
  }
  const context: TrustedOAuthRequestContext = Object.freeze({
    connectionKey: input.connectionKey,
    listenerId: input.listenerId,
    sourceIp: canonicalIp(input.sourceIp),
  });
  trustedContexts.add(context);
  return context;
}

export function assertTrustedOAuthRequestContext(
  value: TrustedOAuthRequestContext,
): TrustedOAuthRequestContext {
  if (!trustedContexts.has(value)) {
    throw new OAuthSecurityError("oauth_rate_limited", {
      httpStatus: 429,
      oauthError: "temporarily_unavailable",
    });
  }
  return value;
}

export function stableOAuthRateKey(
  context: TrustedOAuthRequestContext,
  purpose: "authorization" | "client" | "login" | "registration" | "token",
  stableSubject?: string,
): string {
  const trusted = assertTrustedOAuthRequestContext(context);
  if (stableSubject === undefined) {
    return `${purpose}:ip:${hashOpaque(trusted.sourceIp)}`;
  }
  return `${purpose}:subject:${hashOpaque(stableSubject)}`;
}
