export const LOCAL_LISTENER = Object.freeze({
  host: "127.0.0.1",
  id: "local-bearer-46683",
  port: 46683,
  resource: "http://127.0.0.1:46683/mcp/things",
} as const);

export const REMOTE_LISTENER = Object.freeze({
  host: "127.0.0.1",
  id: "oauth-loopback-46684",
  port: 46684,
  resource: "https://mcp.w4w.dev/mcp/things",
} as const);

export const THINGS_PATH = "/mcp/things" as const;
export const DEFAULT_MAX_REQUEST_BODY_SIZE = 1_048_576;

export type ListenerKind = "local-bearer" | "remote-oauth";

