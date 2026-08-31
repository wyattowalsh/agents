/// <reference path="./upstream-mcphub.d.mts" />

import type { CallToolResult } from "@modelcontextprotocol/server";
import {
  handleCallToolRequest,
  handleListToolsRequest,
} from "@samanhappy/mcphub/dist/services/mcpService.js";
import { transports } from "@samanhappy/mcphub/dist/services/sseService.js";

import type { ThingsServerName } from "../protocol/constants.js";
import type {
  ThingsCatalogSnapshot,
  ThingsProviderCall,
  ThingsPublicTool,
  ThingsToolProvider,
} from "../protocol/types.js";

const GROUP = "things" as const;
const PROVIDER_SESSION = "things-plus-plus-stateless-provider";
const PROVIDER_READY_TIMEOUT_MS = 300_000;
const PROVIDER_READY_POLL_MS = 50;
const SERVER_TOOL_NAME_PATTERN = /^[a-z0-9][a-z0-9_]*$/u;
const TOOL_NAME_ROUTES = Object.freeze([
  Object.freeze({
    server: "things-core",
    upstreamPrefix: "things-core-",
    publicPrefix: "things_core__",
  }),
  Object.freeze({
    server: "things-shortcuts",
    upstreamPrefix: "things-shortcuts-",
    publicPrefix: "things_shortcuts__",
  }),
  Object.freeze({
    server: "things-native",
    upstreamPrefix: "things-native-",
    publicPrefix: "things_native__",
  }),
] as const satisfies readonly {
  readonly server: ThingsServerName;
  readonly upstreamPrefix: string;
  readonly publicPrefix: string;
}[]);

class UpstreamToolContractError extends Error {
  public constructor(code: string) {
    super(code);
    this.name = "UpstreamToolContractError";
  }
}

function failToolContract(code: string): never {
  throw new UpstreamToolContractError(code);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function tool(value: unknown): ThingsPublicTool {
  if (!isRecord(value)) return failToolContract("upstream_tool_invalid");
  const upstreamName = value.name;
  if (typeof upstreamName !== "string") {
    return failToolContract("upstream_tool_name_invalid");
  }
  const route = TOOL_NAME_ROUTES.find(({ upstreamPrefix }) =>
    upstreamName.startsWith(upstreamPrefix),
  );
  if (route === undefined) return failToolContract("upstream_tool_route_invalid");
  const serverToolName = upstreamName.slice(route.upstreamPrefix.length);
  if (!SERVER_TOOL_NAME_PATTERN.test(serverToolName)) {
    return failToolContract("upstream_server_tool_name_invalid");
  }
  return {
    ...value,
    name: `${route.publicPrefix}${serverToolName}`,
  } as unknown as ThingsPublicTool;
}

function upstreamToolName(request: ThingsProviderCall): string {
  const route = TOOL_NAME_ROUTES.find(({ server }) => server === request.server);
  if (route === undefined || !SERVER_TOOL_NAME_PATTERN.test(request.serverToolName)) {
    return failToolContract("upstream_tool_route_invalid");
  }
  if (request.publicToolName !== `${route.publicPrefix}${request.serverToolName}`) {
    return failToolContract("upstream_public_tool_name_invalid");
  }
  return `${route.upstreamPrefix}${request.serverToolName}`;
}

function callResult(value: unknown): CallToolResult {
  if (!isRecord(value) || !Array.isArray(value.content)) {
    throw new Error("upstream_call_result_invalid");
  }
  return value as unknown as CallToolResult;
}

function delay(milliseconds: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

export class McpHubThingsProvider implements ThingsToolProvider {
  #initialized = false;

  public async initialize(): Promise<void> {
    if (this.#initialized) return;
    transports[PROVIDER_SESSION] = Object.freeze({
      group: GROUP,
      clientCapabilities: Object.freeze({}),
    });
    this.#initialized = true;
    const deadline = Date.now() + PROVIDER_READY_TIMEOUT_MS;
    while (true) {
      try {
        await this.snapshot();
        return;
      } catch (error: unknown) {
        if (error instanceof UpstreamToolContractError) {
          this.close();
          throw error;
        }
        if (Date.now() >= deadline) {
          this.close();
          throw new Error("upstream_catalog_not_ready", { cause: error });
        }
        await delay(PROVIDER_READY_POLL_MS);
      }
    }
  }

  public async snapshot(): Promise<ThingsCatalogSnapshot> {
    if (!this.#initialized) throw new Error("upstream_provider_not_initialized");
    const result = await handleListToolsRequest(
      Object.freeze({ method: "tools/list", params: Object.freeze({}) }),
      Object.freeze({ sessionId: PROVIDER_SESSION, group: GROUP }),
    );
    if (!Array.isArray(result.tools) || result.tools.length !== 70) {
      throw new Error("upstream_catalog_not_closed");
    }
    const tools = result.tools.map(tool);
    if (new Set(tools.map((entry) => entry.name)).size !== tools.length) {
      return failToolContract("upstream_tool_name_collision");
    }
    return Object.freeze({ tools: Object.freeze(tools) });
  }

  public async call(request: ThingsProviderCall): Promise<CallToolResult> {
    if (!this.#initialized) throw new Error("upstream_provider_not_initialized");
    if (
      request.server !== "things-core" &&
      request.server !== "things-shortcuts" &&
      request.server !== "things-native"
    ) {
      throw new Error("upstream_server_forbidden");
    }
    return callResult(
      await handleCallToolRequest(
        Object.freeze({
          method: "tools/call" as const,
          params: Object.freeze({
            name: upstreamToolName(request),
            arguments: request.arguments,
          }),
        }),
        Object.freeze({
          group: GROUP,
          sessionId: PROVIDER_SESSION,
          username: request.context.principal,
          headers: Object.freeze({}),
        }),
      ),
    );
  }

  public close(): void {
    delete transports[PROVIDER_SESSION];
    this.#initialized = false;
  }
}
