export const MODERN_PROTOCOL_VERSION = "2026-07-28" as const;
export const LEGACY_PROTOCOL_VERSION = "2025-11-25" as const;

export const SUPPORTED_PROTOCOL_VERSIONS = [
  MODERN_PROTOCOL_VERSION,
  LEGACY_PROTOCOL_VERSION,
] as const;

export const THINGS_GROUP_NAME = "things" as const;
export const THINGS_GROUP_PATH = "/mcp/things" as const;
export const LOCAL_THINGS_RESOURCE =
  "http://127.0.0.1:46683/mcp/things" as const;
export const REMOTE_THINGS_RESOURCE =
  "https://mcp.w4w.dev/mcp/things" as const;
export const THINGS_RESOURCES = [
  LOCAL_THINGS_RESOURCE,
  REMOTE_THINGS_RESOURCE,
] as const;
export const THINGS_SCOPES = [
  "things.read",
  "things.write",
  "things.admin",
] as const;
export const LOCAL_THINGS_CREDENTIAL_CLASS = "local-bearer" as const;
export const REMOTE_THINGS_CREDENTIAL_CLASS = "remote-oauth" as const;
export const THINGS_CREDENTIAL_CLASSES = [
  LOCAL_THINGS_CREDENTIAL_CLASS,
  REMOTE_THINGS_CREDENTIAL_CLASS,
] as const;

export const THINGS_TOOL_COUNT = 70 as const;
export const THINGS_SERVER_COUNTS = {
  "things-core": 41,
  "things-shortcuts": 21,
  "things-native": 8,
} as const;

export const DEFAULT_MAX_REQUEST_BODY_SIZE = 1_048_576 as const;
export const DEFAULT_CACHE_HINT = {
  ttlMs: 0,
  cacheScope: "private",
} as const;

export const PROTOCOL_VERSION_META_KEY =
  "io.modelcontextprotocol/protocolVersion" as const;
export const CLIENT_CAPABILITIES_META_KEY =
  "io.modelcontextprotocol/clientCapabilities" as const;
export const CLIENT_INFO_META_KEY =
  "io.modelcontextprotocol/clientInfo" as const;
export const RESERVED_META_PREFIX = "io.modelcontextprotocol/" as const;

export const MCP_PROTOCOL_VERSION_HEADER = "mcp-protocol-version" as const;
export const MCP_METHOD_HEADER = "mcp-method" as const;
export const MCP_NAME_HEADER = "mcp-name" as const;
export const MCP_SESSION_HEADER = "mcp-session-id" as const;
export const LAST_EVENT_ID_HEADER = "last-event-id" as const;

export const NAME_BEARING_METHODS = new Set(["tools/call"] as const);

export type ThingsServerName = keyof typeof THINGS_SERVER_COUNTS;
export type ThingsResource = (typeof THINGS_RESOURCES)[number];
export type ThingsCredentialClass =
  (typeof THINGS_CREDENTIAL_CLASSES)[number];
export type ProtocolVersion = (typeof SUPPORTED_PROTOCOL_VERSIONS)[number];
