import { THINGS_PATH, type ListenerKind } from "./constants.js";

export type IngressRouteId =
  | "things-mcp"
  | "oauth-origin"
  | "oauth-protected-resource"
  | "oauth-authorization-server"
  | "oauth-authorize"
  | "oauth-token"
  | "oauth-register"
  | "oauth-revoke"
  | "oauth-login"
  | "oauth-logout"
  | "oauth-login-css";

export type RouteDecision =
  | Readonly<{ action: "dispatch"; route: IngressRouteId }>
  | Readonly<{ action: "method-not-allowed"; allow: readonly string[] }>
  | Readonly<{ action: "delegate-local-control-plane" }>
  | Readonly<{ action: "not-found" }>;

const REMOTE_ROUTES = new Map<string, IngressRouteId>([
  ["GET /", "oauth-origin"],
  [`POST ${THINGS_PATH}`, "things-mcp"],
  [
    "GET /.well-known/oauth-protected-resource/mcp/things",
    "oauth-protected-resource",
  ],
  ["GET /.well-known/oauth-authorization-server", "oauth-authorization-server"],
  [
    "GET /.well-known/oauth-authorization-server/mcp/things",
    "oauth-authorization-server",
  ],
  ["GET /oauth/authorize", "oauth-authorize"],
  ["POST /oauth/authorize", "oauth-authorize"],
  ["POST /oauth/token", "oauth-token"],
  ["POST /oauth/register", "oauth-register"],
  ["POST /oauth/revoke", "oauth-revoke"],
  ["GET /oauth/login", "oauth-login"],
  ["POST /oauth/login", "oauth-login"],
  ["POST /oauth/session/logout", "oauth-logout"],
  ["GET /oauth/assets/login.css", "oauth-login-css"],
]);

const REMOTE_ALLOWED_PATHS = Object.freeze([
  "/",
  "/mcp/things",
  "/.well-known/oauth-protected-resource/mcp/things",
  "/.well-known/oauth-authorization-server",
  "/.well-known/oauth-authorization-server/mcp/things",
  "/oauth/authorize",
  "/oauth/token",
  "/oauth/register",
  "/oauth/revoke",
  "/oauth/login",
  "/oauth/session/logout",
  "/oauth/assets/login.css",
] as const);

const OAUTH_QUERY_KEYS = Object.freeze({
  "/oauth/authorize": new Set([
    "client_id",
    "code_challenge",
    "code_challenge_method",
    "redirect_uri",
    "registration_mode",
    "resource",
    "response_type",
    "scope",
    "state",
  ]),
} as const);

const DENIED_LOCAL_PATHS = new Set([
  "/mcp",
  "/mcp/",
  "/mcp/$smart",
  "/mcp/supathings",
  "/mcp/tunnel",
  "/mcp/things-core",
  "/mcp/things-native",
  "/mcp/things-shortcuts",
  "/messages",
  "/sse",
  "/sse/$smart",
  "/sse/supathings",
  "/sse/things",
  "/sse/things-core",
  "/sse/things-native",
  "/sse/things-shortcuts",
  "/$smart",
]);

const THINGS_BACKEND_SEGMENT = "(?:supathings|things-core|things-native|things-shortcuts)";
const USER_MCP_ALTERNATE = new RegExp(
  `^/[^/]+/(?:mcp|sse)(?:/(?:things|\\$smart|${THINGS_BACKEND_SEGMENT})(?:/.*)?)?$`,
  "u",
);
const DIRECT_TOOL_ALTERNATE = new RegExp(
  `^/api/(?:tools/call/${THINGS_BACKEND_SEGMENT}(?:/|$)|tools/${THINGS_BACKEND_SEGMENT}(?:/|$)|[^/]+/tools/${THINGS_BACKEND_SEGMENT}(?:/|$)|mcp/${THINGS_BACKEND_SEGMENT}(?:/|$))`,
  "u",
);

function rawTarget(value: string | undefined):
  | Readonly<{ hasQuery: boolean; path: string; query: URLSearchParams }>
  | undefined {
  if (
    value === undefined ||
    !value.startsWith("/") ||
    value.includes("#") ||
    /[\u0000-\u001f\u007f]/u.test(value)
  ) {
    return undefined;
  }
  const separator = value.indexOf("?");
  const path = separator === -1 ? value : value.slice(0, separator);
  const queryText = separator === -1 ? "" : value.slice(separator + 1);
  if (
    path.length === 0 ||
    path.includes("%") ||
    path.includes("\\") ||
    path.includes("//") ||
    path.includes(";") ||
    (path !== "/" && path.endsWith("/")) ||
    path.split("/").some((part) => part === "." || part === "..")
  ) {
    return undefined;
  }
  return {
    hasQuery: separator !== -1,
    path,
    query: new URLSearchParams(queryText),
  };
}

function queryAllowed(path: string, query: URLSearchParams): boolean {
  if (query.size === 0) return true;
  const allowed = OAUTH_QUERY_KEYS[path as keyof typeof OAUTH_QUERY_KEYS];
  if (allowed === undefined) return false;
  const seen = new Set<string>();
  for (const [key] of query) {
    if (!allowed.has(key) || seen.has(key)) return false;
    seen.add(key);
  }
  return true;
}

function foldAsciiCase(value: string): string {
  return value.replace(/[A-Z]/gu, (character) => character.toLowerCase());
}

function isThingsSpecificAlternate(path: string): boolean {
  const candidate = foldAsciiCase(path);
  return (
    candidate === THINGS_PATH ||
    DENIED_LOCAL_PATHS.has(candidate) ||
    candidate.startsWith("/mcp/things/") ||
    candidate.startsWith("/mcp/things;") ||
    candidate.startsWith("/mcp/supathings/") ||
    candidate.startsWith("/sse/things") ||
    candidate.startsWith("/sse/supathings") ||
    candidate.startsWith("/things/") ||
    candidate === "/api/things" ||
    candidate.startsWith("/api/things/") ||
    candidate === "/api/$smart" ||
    candidate.startsWith("/api/$smart/") ||
    USER_MCP_ALTERNATE.test(candidate) ||
    /^\/[^/]+\/messages$/u.test(candidate) ||
    DIRECT_TOOL_ALTERNATE.test(candidate)
  );
}

function localPath(value: string | undefined): string | undefined {
  if (
    value === undefined ||
    !value.startsWith("/") ||
    value.includes("#") ||
    /[\u0000-\u001f\u007f]/u.test(value)
  ) {
    return undefined;
  }
  const separator = value.indexOf("?");
  return separator === -1 ? value : value.slice(0, separator);
}

function decodedThingsAlternate(path: string): boolean {
  try {
    const decoded = decodeURIComponent(path).replaceAll("\\", "/");
    const collapsed = decoded.replace(/\/{2,}/gu, "/");
    const normalized = new URL(collapsed, "http://local.invalid").pathname;
    return [decoded, collapsed, normalized].some(
      (candidate) => isThingsSpecificAlternate(candidate),
    );
  } catch {
    return false;
  }
}

export function decideIngressRoute(input: {
  readonly kind: ListenerKind;
  readonly method: string | undefined;
  readonly target: string | undefined;
}): RouteDecision {
  if (input.kind === "local-bearer") {
    const path = localPath(input.target);
    if (path === undefined) return { action: "not-found" };
    if (
      path !== THINGS_PATH &&
      !isThingsSpecificAlternate(path) &&
      !decodedThingsAlternate(path)
    ) {
      return { action: "delegate-local-control-plane" };
    }
  }
  const target = rawTarget(input.target);
  const method = input.method ?? "";
  if (target === undefined || !queryAllowed(target.path, target.query)) {
    return { action: "not-found" };
  }

  if (target.path === THINGS_PATH) {
    if (target.hasQuery) return { action: "not-found" };
    if (method === "POST") return { action: "dispatch", route: "things-mcp" };
    if (method === "GET") {
      return { action: "method-not-allowed", allow: ["POST"] };
    }
    if (method === "DELETE") {
      return { action: "method-not-allowed", allow: [] };
    }
    return { action: "not-found" };
  }

  if (input.kind === "local-bearer") return { action: "not-found" };

  const route = REMOTE_ROUTES.get(`${method} ${target.path}`);
  return route === undefined
    ? { action: "not-found" }
    : { action: "dispatch", route };
}

export function frozenRemoteRouteManifest(): readonly Readonly<{
  method: string;
  path: string;
  route: IngressRouteId;
}>[] {
  return Object.freeze(
    [...REMOTE_ROUTES].map(([key, route]) => {
      const separator = key.indexOf(" ");
      return Object.freeze({
        method: key.slice(0, separator),
        path: key.slice(separator + 1),
        route,
      });
    }),
  );
}

export function frozenCloudflareIngressManifest(): Readonly<{
  allowedPaths: typeof REMOTE_ALLOWED_PATHS;
  fallback: "http_status:404";
  hostname: "mcp.w4w.dev";
  origin: "http://127.0.0.1:46684";
  publicOrigin: "https://mcp.w4w.dev";
  publicResource: "https://mcp.w4w.dev/mcp/things";
  schemaVersion: 1;
}> {
  return Object.freeze({
    schemaVersion: 1,
    hostname: "mcp.w4w.dev",
    publicOrigin: "https://mcp.w4w.dev",
    publicResource: "https://mcp.w4w.dev/mcp/things",
    origin: "http://127.0.0.1:46684",
    allowedPaths: REMOTE_ALLOWED_PATHS,
    fallback: "http_status:404",
  });
}
