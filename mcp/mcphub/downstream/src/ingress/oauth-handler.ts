import { createHash } from "node:crypto";

import {
  authorizationServerMetadata,
  issuerBoundAuthorizationError,
  protectedResourceMetadata,
} from "../oauth/metadata.js";
import {
  ThingsOAuthService,
  type ClientAuthentication,
} from "../oauth/service.js";
import type { AuthorizationRequest, BrowserSession, TokenPair } from "../oauth/types.js";
import {
  THINGS_ORIGIN,
  THINGS_RESOURCE,
  OAUTH_SCOPES,
  type RegistrationMode,
} from "../policy/oauth-policy.js";
import type { TrustedOAuthRequestContext } from "../policy/oauth-ingress-contract.js";
import { OAuthSecurityError } from "../security/common/errors.js";
import { issuerBoundAuthorizationRedirect } from "./oauth-responses.js";
import type { IngressRouteId } from "./route-policy.js";
import type { CaptureEvidenceRecorder } from "./capture-evidence.js";

export interface OAuthIngressRequestContext {
  readonly clientAuthorization?: string;
  readonly route: Exclude<IngressRouteId, "things-mcp">;
  readonly trustedContext: TrustedOAuthRequestContext;
}

export interface OAuthIngressHandler {
  fetch(request: Request, context: OAuthIngressRequestContext): Promise<Response>;
}

const SESSION_COOKIE = "__Host-mcphub_things_session";
const CLIENT_ASSERTION_TYPE =
  "urn:ietf:params:oauth:client-assertion-type:jwt-bearer";
const AUTHORIZATION_KEYS = Object.freeze([
  "client_id",
  "code_challenge",
  "code_challenge_method",
  "redirect_uri",
  "registration_mode",
  "resource",
  "response_type",
  "scope",
  "state",
] as const);
const LOGIN_KEYS = Object.freeze([
  ...AUTHORIZATION_KEYS,
  "account_key",
  "csrf_token",
  "nonce",
  "password",
] as const);
const TOKEN_KEYS = Object.freeze([
  "client_assertion",
  "client_assertion_type",
  "client_id",
  "code",
  "code_verifier",
  "grant_type",
  "redirect_uri",
  "refresh_token",
  "registration_mode",
  "resource",
] as const);
const REVOKE_KEYS = Object.freeze([
  "client_assertion",
  "client_assertion_type",
  "client_id",
  "registration_mode",
  "resource",
  "token",
  "token_type_hint",
] as const);

const LOGIN_CSS = `:root{color-scheme:light dark;font-family:ui-sans-serif,system-ui,sans-serif}body{display:grid;min-height:100vh;margin:0;place-items:center;background:#f4f4f5;color:#18181b}main{box-sizing:border-box;width:min(32rem,calc(100% - 2rem));padding:2rem;border:1px solid #d4d4d8;border-radius:1rem;background:#fff;box-shadow:0 1rem 3rem #0001}h1{margin-top:0}label{display:grid;gap:.4rem;margin:1rem 0}input,button{box-sizing:border-box;width:100%;padding:.75rem;border:1px solid #a1a1aa;border-radius:.5rem;font:inherit}button{cursor:pointer;background:#18181b;color:#fff}.secondary{background:#fff;color:#18181b}@media(prefers-color-scheme:dark){body{background:#09090b;color:#fafafa}main{background:#18181b;border-color:#3f3f46}.secondary{background:#27272a;color:#fafafa}}`;
const LOGIN_CSS_INTEGRITY = `sha256-${createHash("sha256")
  .update(LOGIN_CSS, "utf8")
  .digest("base64")}`;

function responseHeaders(contentType: string): Headers {
  return new Headers({
    "cache-control": "no-store",
    "content-security-policy":
      "default-src 'none'; style-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
    "content-type": contentType,
    pragma: "no-cache",
    "referrer-policy": "no-referrer",
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
  });
}

function json(value: unknown, status = 200): Response {
  return Response.json(value, {
    status,
    headers: responseHeaders("application/json; charset=utf-8"),
  });
}

function empty(status: number): Response {
  const headers = responseHeaders("application/octet-stream");
  headers.set("content-length", "0");
  return new Response(null, { status, headers });
}

function html(value: string, status = 200, setCookie?: string): Response {
  const headers = responseHeaders("text/html; charset=utf-8");
  if (setCookie !== undefined) headers.append("set-cookie", setCookie);
  return new Response(`<!doctype html>${value}`, { status, headers });
}

function redirect(location: URL, setCookie: string): Response {
  const headers = responseHeaders("text/plain; charset=utf-8");
  headers.set("location", location.href);
  headers.set("content-length", "0");
  headers.append("set-cookie", setCookie);
  return new Response(null, { status: 303, headers });
}

function escaped(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function hidden(name: string, value: string): string {
  return `<input type="hidden" name="${escaped(name)}" value="${escaped(value)}">`;
}

function page(body: string): string {
  return `<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Things++ authorization</title><link rel="stylesheet" href="/oauth/assets/login.css" integrity="${LOGIN_CSS_INTEGRITY}"></head><body><main>${body}</main></body></html>`;
}

function originPage(): string {
  return page(
    `<h1>Things++</h1><p>This host is the Things++ OAuth origin for ChatGPT. The MCP resource is <a href="${escaped(THINGS_RESOURCE)}">${escaped(THINGS_RESOURCE)}</a>.</p><p>Paste that resource URL into the connector. Apex <code>/</code> is this landing page; tool dispatch stays off until public activation.</p>`,
  );
}

function loginCssResponse(): Response {
  const headers = responseHeaders("text/css; charset=utf-8");
  headers.set("cache-control", "public, max-age=31536000, immutable");
  return new Response(LOGIN_CSS, { headers });
}

function loginPage(
  session: BrowserSession,
  authorization?: AuthorizationRequest,
): string {
  const continuation =
    authorization === undefined
      ? ""
      : [
          hidden("client_id", authorization.clientId),
          hidden("code_challenge", authorization.codeChallenge),
          hidden("code_challenge_method", authorization.codeChallengeMethod),
          hidden("redirect_uri", authorization.redirectUri),
          hidden("registration_mode", authorization.registrationMode),
          hidden("resource", authorization.resource),
          hidden("response_type", "code"),
          hidden("scope", authorization.scopes.join(" ")),
          hidden("state", authorization.state),
        ].join("");
  return page(`<h1>Authorize Things++</h1><p>Sign in to the local Things++ control plane. Credentials never leave this OAuth origin.</p><form method="post" action="/oauth/login">${hidden("csrf_token", session.csrfToken)}${hidden("nonce", session.nonce)}${continuation}<label>Account<input name="account_key" autocomplete="username" required></label><label>Password<input type="password" name="password" autocomplete="current-password" required></label><button type="submit">Continue</button></form>`);
}

function consentPage(input: {
  readonly authorization: AuthorizationRequest;
  readonly csrfToken: string;
  readonly transactionNonce: string;
}): string {
  const scopes = input.authorization.scopes.map((scope) => `<li>${escaped(scope)}</li>`).join("");
  const common = `${hidden("csrf_token", input.csrfToken)}${hidden("state", input.authorization.state)}${hidden("transaction_nonce", input.transactionNonce)}`;
  return page(`<h1>Approve Things++ access</h1><p>Client: ${escaped(input.authorization.clientId)}</p><p>Requested independent scopes:</p><ul>${scopes}</ul><form method="post" action="/oauth/authorize">${common}${hidden("decision", "approve")}<button type="submit">Approve</button></form><form method="post" action="/oauth/authorize">${common}${hidden("decision", "deny")}<button class="secondary" type="submit">Deny</button></form>`);
}

function loggedInPage(csrfToken: string): string {
  return page(`<h1>Signed in</h1><p>This local OAuth session is ready. Return to the client to start authorization.</p><form method="post" action="/oauth/session/logout">${hidden("csrf_token", csrfToken)}<button class="secondary" type="submit">Sign out</button></form>`);
}

function registrationMode(clientId: string, explicit: string | undefined): RegistrationMode {
  const derived = clientId.startsWith("https://")
    ? "cimd"
    : clientId.startsWith("dcr_")
      ? "dcr"
      : undefined;
  if (derived === undefined || (explicit !== undefined && explicit !== derived)) {
    throw new OAuthSecurityError("oauth_registration_mode_mismatch", {
      httpStatus: 403,
      oauthError: "invalid_client",
    });
  }
  return derived;
}

function bounded(value: string | null, name: string): string {
  if (
    value === null ||
    value.length < 1 ||
    value.length > 2_048 ||
    /[\u0000-\u001f\u007f]/u.test(value)
  ) {
    throw new OAuthSecurityError("oauth_client_metadata_invalid", {
      oauthError: name === "state" ? "invalid_request" : "invalid_client",
    });
  }
  return value;
}

function assertAllowedKeys(params: URLSearchParams, allowed: readonly string[]): void {
  const seen = new Set<string>();
  for (const key of params.keys()) {
    if (!allowed.includes(key) || seen.has(key)) {
      throw new OAuthSecurityError("oauth_client_metadata_invalid", {
        oauthError: "invalid_request",
      });
    }
    seen.add(key);
  }
}

function authorizationRequest(params: URLSearchParams): AuthorizationRequest {
  assertAllowedKeys(params, AUTHORIZATION_KEYS);
  const clientId = bounded(params.get("client_id"), "client_id");
  const responseType = bounded(params.get("response_type"), "response_type");
  const challengeMethod = bounded(
    params.get("code_challenge_method"),
    "code_challenge_method",
  );
  if (responseType !== "code" || challengeMethod !== "S256") {
    throw new OAuthSecurityError("oauth_pkce_invalid", { oauthError: "invalid_request" });
  }
  const scope = bounded(params.get("scope"), "scope");
  const scopes = scope.split(" ");
  if (scopes.some((entry) => entry.length === 0)) {
    throw new OAuthSecurityError("oauth_catalog_scope_mismatch", {
      httpStatus: 403,
      oauthError: "invalid_scope",
    });
  }
  return Object.freeze({
    clientId,
    registrationMode: registrationMode(
      clientId,
      params.get("registration_mode") ?? undefined,
    ),
    redirectUri: bounded(params.get("redirect_uri"), "redirect_uri"),
    codeChallenge: bounded(params.get("code_challenge"), "code_challenge"),
    codeChallengeMethod: "S256",
    state: bounded(params.get("state"), "state"),
    resource: bounded(params.get("resource"), "resource"),
    scopes,
  });
}

function contentType(request: Request, expected: string): void {
  const raw = request.headers.get("content-type");
  if (raw === null) {
    throw new OAuthSecurityError("oauth_client_metadata_invalid", {
      oauthError: "invalid_request",
    });
  }
  const parts = raw.split(";").map((part) => part.trim().toLowerCase());
  if (
    parts[0] !== expected ||
    parts.length > 2 ||
    (parts.length === 2 && parts[1] !== "charset=utf-8")
  ) {
    throw new OAuthSecurityError("oauth_client_metadata_invalid", {
      oauthError: "invalid_request",
    });
  }
}

async function strictText(request: Request): Promise<string> {
  try {
    return new TextDecoder("utf-8", { fatal: true }).decode(await request.arrayBuffer());
  } catch {
    throw new OAuthSecurityError("oauth_client_metadata_invalid", {
      oauthError: "invalid_request",
    });
  }
}

async function form(request: Request, allowed: readonly string[]): Promise<URLSearchParams> {
  contentType(request, "application/x-www-form-urlencoded");
  const params = new URLSearchParams(await strictText(request));
  assertAllowedKeys(params, allowed);
  return params;
}

async function jsonBody(request: Request): Promise<unknown> {
  contentType(request, "application/json");
  try {
    return JSON.parse(await strictText(request)) as unknown;
  } catch (error) {
    if (error instanceof OAuthSecurityError) throw error;
    throw new OAuthSecurityError("oauth_client_metadata_invalid", {
      oauthError: "invalid_request",
    });
  }
}

function sessionCookie(request: Request): string | undefined {
  const raw = request.headers.get("cookie");
  if (raw === null || /[\u0000-\u001f\u007f]/u.test(raw)) return undefined;
  const values: string[] = [];
  for (const part of raw.split(";")) {
    const separator = part.indexOf("=");
    if (separator === -1) continue;
    const name = part.slice(0, separator).trim();
    if (name === SESSION_COOKIE) values.push(part.slice(separator + 1).trim());
  }
  const value = values[0];
  if (values.length !== 1 || value === undefined || !/^[A-Za-z0-9_-]{43,128}$/u.test(value)) {
    return undefined;
  }
  return value;
}

function requiredSessionCookie(request: Request): string {
  const token = sessionCookie(request);
  if (token === undefined) {
    throw new OAuthSecurityError("oauth_session_invalid", { httpStatus: 401 });
  }
  return token;
}

function parseBasic(value: string): Readonly<{ clientId: string; clientSecret: string }> {
  if (!value.startsWith("Basic ")) {
    throw new OAuthSecurityError("oauth_client_metadata_invalid", {
      httpStatus: 401,
      oauthError: "invalid_client",
    });
  }
  const encoded = value.slice("Basic ".length);
  if (!/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/u.test(encoded)) {
    throw new OAuthSecurityError("oauth_client_metadata_invalid", {
      httpStatus: 401,
      oauthError: "invalid_client",
    });
  }
  let decoded: string;
  try {
    decoded = new TextDecoder("utf-8", { fatal: true }).decode(Buffer.from(encoded, "base64"));
  } catch {
    throw new OAuthSecurityError("oauth_client_metadata_invalid", {
      httpStatus: 401,
      oauthError: "invalid_client",
    });
  }
  const separator = decoded.indexOf(":");
  if (separator < 1 || separator !== decoded.lastIndexOf(":")) {
    throw new OAuthSecurityError("oauth_client_metadata_invalid", {
      httpStatus: 401,
      oauthError: "invalid_client",
    });
  }
  return Object.freeze({
    clientId: bounded(decoded.slice(0, separator), "client_id"),
    clientSecret: bounded(decoded.slice(separator + 1), "client_secret"),
  });
}

function clientAuthentication(
  params: URLSearchParams,
  authorization: string | undefined,
): Readonly<{
  authentication: ClientAuthentication;
  clientId: string;
  registrationMode: RegistrationMode;
}> {
  if (authorization !== undefined) {
    const basic = parseBasic(authorization);
    const supplied = params.get("client_id");
    if (supplied !== null && supplied !== basic.clientId) {
      throw new OAuthSecurityError("oauth_client_metadata_invalid", {
        httpStatus: 401,
        oauthError: "invalid_client",
      });
    }
    if (params.get("client_assertion") !== null || params.get("client_assertion_type") !== null) {
      throw new OAuthSecurityError("oauth_client_metadata_invalid", {
        httpStatus: 401,
        oauthError: "invalid_client",
      });
    }
    const authentication: ClientAuthentication = {
      kind: "dcr_secret",
      clientSecret: basic.clientSecret,
    };
    return Object.freeze({
      authentication,
      clientId: basic.clientId,
      registrationMode: registrationMode(
        basic.clientId,
        params.get("registration_mode") ?? undefined,
      ),
    });
  }
  const clientId = bounded(params.get("client_id"), "client_id");
  const assertion = params.get("client_assertion");
  const assertionType = params.get("client_assertion_type");
  let authentication: ClientAuthentication;
  if (assertion !== null || assertionType !== null) {
    if (assertionType !== CLIENT_ASSERTION_TYPE || assertion === null) {
      throw new OAuthSecurityError("oauth_client_assertion_invalid", {
        httpStatus: 401,
        oauthError: "invalid_client",
      });
    }
    authentication = {
      kind: "private_key_jwt",
      assertion: bounded(assertion, "client_assertion"),
    };
  } else {
    authentication = { kind: "none" };
  }
  return Object.freeze({
    authentication,
    clientId,
    registrationMode: registrationMode(
      clientId,
      params.get("registration_mode") ?? undefined,
    ),
  });
}

function tokenResponse(tokens: TokenPair, now: number): Response {
  return json({
    access_token: tokens.accessToken,
    expires_in: Math.max(1, Math.floor((tokens.accessTokenExpiresAt - now) / 1_000)),
    refresh_token: tokens.refreshToken,
    scope: tokens.scope,
    token_type: tokens.tokenType,
  });
}

function oauthError(error: OAuthSecurityError, authorizationRoute: boolean): Response {
  return json(
    authorizationRoute ? issuerBoundAuthorizationError(error) : error.publicPayload(),
    error.httpStatus,
  );
}

/**
 * Capture mode exposes only immutable discovery metadata. Interactive OAuth
 * and tool dispatch remain unavailable while an observed-wire receipt is built.
 */
export class CaptureOnlyOAuthHandler implements OAuthIngressHandler {
  readonly #recorder: CaptureEvidenceRecorder | undefined;

  public constructor(recorder?: CaptureEvidenceRecorder) {
    this.#recorder = recorder;
  }

  public async fetch(
    request: Request,
    context: OAuthIngressRequestContext,
  ): Promise<Response> {
    if (context.route === "oauth-protected-resource") {
      await this.#recorder?.observe(request, context.route, 200);
      return json(protectedResourceMetadata());
    }
    if (context.route === "oauth-authorization-server") {
      await this.#recorder?.observe(request, context.route, 200);
      return json(authorizationServerMetadata());
    }
    if (context.route === "oauth-origin") {
      return html(originPage());
    }
    if (context.route === "oauth-login-css") {
      return loginCssResponse();
    }
    await this.#recorder?.observe(request, context.route, 503);
    return empty(503);
  }
}

export class ProductionOAuthHandler implements OAuthIngressHandler {
  readonly #service: ThingsOAuthService;
  readonly #clock: () => number;

  public constructor(service: ThingsOAuthService, now: () => number = Date.now) {
    this.#service = service;
    this.#clock = now;
  }

  public async fetch(
    request: Request,
    context: OAuthIngressRequestContext,
  ): Promise<Response> {
    try {
      switch (context.route) {
        case "oauth-origin":
          return html(originPage());
        case "oauth-protected-resource":
          return json(protectedResourceMetadata());
        case "oauth-authorization-server":
          return json(authorizationServerMetadata());
        case "oauth-login-css":
          return loginCssResponse();
        case "oauth-login":
          return request.method === "GET"
            ? this.#beginLogin()
            : await this.#completeLogin(request, context);
        case "oauth-logout":
          return await this.#logout(request);
        case "oauth-authorize":
          return request.method === "GET"
            ? this.#beginAuthorization(request)
            : await this.#completeAuthorization(request);
        case "oauth-register":
          return await this.#register(request, context);
        case "oauth-token":
          return await this.#token(request, context);
        case "oauth-revoke":
          return await this.#revoke(request, context);
        default: {
          const exhaustive: never = context.route;
          return exhaustive;
        }
      }
    } catch (error) {
      if (error instanceof OAuthSecurityError) {
        if (context.route === "oauth-login" || context.route === "oauth-logout") {
          return empty(error.httpStatus);
        }
        return oauthError(error, context.route === "oauth-authorize");
      }
      return empty(500);
    }
  }

  #beginLogin(): Response {
    const session = this.#service.beginLoginSession();
    return html(loginPage(session), 200, session.setCookie);
  }

  #beginAuthorization(request: Request): Response {
    const authorization = authorizationRequest(new URL(request.url).searchParams);
    const session = this.#service.beginLoginSession();
    return html(loginPage(session, authorization), 200, session.setCookie);
  }

  async #completeLogin(
    request: Request,
    context: OAuthIngressRequestContext,
  ): Promise<Response> {
    const params = await form(request, LOGIN_KEYS);
    const accountKey = bounded(params.get("account_key"), "account_key");
    const csrfToken = bounded(params.get("csrf_token"), "csrf_token");
    const nonce = bounded(params.get("nonce"), "nonce");
    const password = params.get("password");
    if (password === null) {
      throw new OAuthSecurityError("oauth_session_invalid", { httpStatus: 401 });
    }
    const browser = await this.#service.completeLogin({
      sessionToken: requiredSessionCookie(request),
      csrfToken,
      nonce,
      origin: request.headers.get("origin") ?? "",
      requestContext: context.trustedContext,
      proof: { accountKey, nonce, password },
    });
    if (params.get("client_id") === null) {
      return html(loggedInPage(browser.csrfToken), 200, browser.setCookie);
    }
    const authorization = authorizationRequest(params);
    const transaction = await this.#service.beginAuthorization({
      request: authorization,
      browserSessionToken: browser.sessionToken,
      requestContext: context.trustedContext,
    });
    return html(
      consentPage({
        authorization,
        csrfToken: browser.csrfToken,
        transactionNonce: transaction.transactionNonce,
      }),
      200,
      browser.setCookie,
    );
  }

  async #completeAuthorization(request: Request): Promise<Response> {
    const params = await form(request, [
      "csrf_token",
      "decision",
      "state",
      "transaction_nonce",
    ]);
    const common = {
      state: bounded(params.get("state"), "state"),
      transactionNonce: bounded(params.get("transaction_nonce"), "transaction_nonce"),
      browserSessionToken: requiredSessionCookie(request),
      csrfToken: bounded(params.get("csrf_token"), "csrf_token"),
      origin: request.headers.get("origin") ?? "",
    };
    const decision = params.get("decision");
    if (decision === "approve") {
      const approved = this.#service.approveAuthorization(common);
      return redirect(
        issuerBoundAuthorizationRedirect(approved.redirectUri, {
          code: approved.code,
          state: approved.state,
        }),
        approved.browserSession.setCookie,
      );
    }
    if (decision === "deny") {
      const denied = this.#service.denyAuthorization(common);
      return redirect(
        issuerBoundAuthorizationRedirect(denied.redirectUri, {
          error: "access_denied",
          state: denied.state,
        }),
        denied.browserSession.setCookie,
      );
    }
    throw new OAuthSecurityError("oauth_client_metadata_invalid", {
      oauthError: "invalid_request",
    });
  }

  async #logout(request: Request): Promise<Response> {
    const params = await form(request, ["csrf_token"]);
    const result = this.#service.logout({
      sessionToken: requiredSessionCookie(request),
      csrfToken: bounded(params.get("csrf_token"), "csrf_token"),
      origin: request.headers.get("origin") ?? "",
    });
    const headers = responseHeaders("application/octet-stream");
    headers.append("set-cookie", result.clearCookie);
    headers.set("content-length", "0");
    return new Response(null, { status: 204, headers });
  }

  async #register(
    request: Request,
    context: OAuthIngressRequestContext,
  ): Promise<Response> {
    const metadata = await jsonBody(request);
    const registered = this.#service.registerDcr({
      metadata,
      resource: THINGS_RESOURCE,
      requestContext: context.trustedContext,
    });
    return json(
      {
        client_id: registered.clientId,
        client_secret: registered.clientSecret,
        client_secret_expires_at: registered.clientSecretExpiresAt,
        token_endpoint_auth_method: registered.tokenEndpointAuthMethod,
      },
      201,
    );
  }

  async #token(
    request: Request,
    context: OAuthIngressRequestContext,
  ): Promise<Response> {
    const params = await form(request, TOKEN_KEYS);
    const client = clientAuthentication(params, context.clientAuthorization);
    const grantType = params.get("grant_type");
    if (grantType === "authorization_code") {
      const tokens = await this.#service.exchangeAuthorizationCode({
        code: bounded(params.get("code"), "code"),
        codeVerifier: bounded(params.get("code_verifier"), "code_verifier"),
        clientId: client.clientId,
        registrationMode: client.registrationMode,
        redirectUri: bounded(params.get("redirect_uri"), "redirect_uri"),
        resource: bounded(params.get("resource"), "resource"),
        clientAuthentication: client.authentication,
        requestContext: context.trustedContext,
      });
      return tokenResponse(tokens, this.#clock());
    }
    if (grantType === "refresh_token") {
      if (
        params.get("code") !== null ||
        params.get("code_verifier") !== null ||
        params.get("redirect_uri") !== null
      ) {
        throw new OAuthSecurityError("oauth_grant_binding_mismatch", {
          oauthError: "invalid_grant",
        });
      }
      const tokens = await this.#service.refresh({
        refreshToken: bounded(params.get("refresh_token"), "refresh_token"),
        clientId: client.clientId,
        registrationMode: client.registrationMode,
        resource: bounded(params.get("resource"), "resource"),
        clientAuthentication: client.authentication,
        requestContext: context.trustedContext,
      });
      return tokenResponse(tokens, this.#clock());
    }
    throw new OAuthSecurityError("oauth_grant_binding_mismatch", {
      oauthError: "invalid_grant",
    });
  }

  async #revoke(
    request: Request,
    context: OAuthIngressRequestContext,
  ): Promise<Response> {
    const params = await form(request, REVOKE_KEYS);
    const hint = params.get("token_type_hint");
    if (hint !== null && hint !== "access_token" && hint !== "refresh_token") {
      throw new OAuthSecurityError("oauth_client_metadata_invalid", {
        oauthError: "invalid_request",
      });
    }
    const client = clientAuthentication(params, context.clientAuthorization);
    await this.#service.revoke({
      token: bounded(params.get("token"), "token"),
      clientId: client.clientId,
      registrationMode: client.registrationMode,
      resource: bounded(params.get("resource"), "resource"),
      clientAuthentication: client.authentication,
      requestContext: context.trustedContext,
    });
    return empty(200);
  }
}

export const PRODUCTION_OAUTH_CONTENT_SHA256 = createHash("sha256")
  .update(
    JSON.stringify({
      authorizationKeys: AUTHORIZATION_KEYS,
      css: LOGIN_CSS,
      issuer: THINGS_RESOURCE,
      origin: THINGS_ORIGIN,
      scopes: OAUTH_SCOPES,
    }),
    "utf8",
  )
  .digest("hex");
