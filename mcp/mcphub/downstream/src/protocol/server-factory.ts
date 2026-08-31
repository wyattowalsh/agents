import {
  ProtocolError,
  ProtocolErrorCode,
  Server,
  type AuthInfo,
  type CallToolResult,
  type ServerContext,
} from "@modelcontextprotocol/server";

import {
  DEFAULT_CACHE_HINT,
  LEGACY_PROTOCOL_VERSION,
  MODERN_PROTOCOL_VERSION,
} from "./constants.js";
import {
  hasExactCatalogScopes,
  protocolAuthIdentity,
} from "./authorization.js";
import type { ProtocolDispatchObserver } from "./dispatch-observer.js";
import type {
  ProtocolEventSink,
  ThingsCallContext,
  ThingsScope,
  ThingsToolProvider,
  ValidatedThingsCatalog,
} from "./types.js";

function isRecord(value: unknown): value is Record<string, unknown> {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    return false;
  }
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

function requireAuthIdentity(authInfo: AuthInfo | undefined) {
  const identity = protocolAuthIdentity(authInfo);
  if (identity === undefined) {
    throw new ProtocolError(
      ProtocolErrorCode.InvalidParams,
      "Tool authorization context unavailable",
    );
  }
  return identity;
}

function requireCatalogContext(context: ServerContext): void {
  const identity = requireAuthIdentity(context.http?.authInfo);
  if (!hasExactCatalogScopes(identity)) {
    throw new ProtocolError(
      ProtocolErrorCode.InvalidParams,
      "Catalog authorization unavailable",
    );
  }
}

function callContext(
  context: ServerContext,
  minimumScope: ThingsScope,
): ThingsCallContext {
  const identity = requireAuthIdentity(context.http?.authInfo);
  if (!identity.scopes.has(minimumScope)) {
    throw new ProtocolError(
      ProtocolErrorCode.InvalidParams,
      "Tool authorization scope unavailable",
    );
  }
  return {
    principal: identity.principal,
    clientId: identity.clientId,
    resource: identity.resource,
    scopes: identity.scopes,
    signal: context.mcpReq.signal,
  };
}

export function createThingsServerFactory(
  provider: ThingsToolProvider,
  catalog: ValidatedThingsCatalog,
  dispatchObserver: ProtocolDispatchObserver,
  eventSink?: ProtocolEventSink,
): () => Server {
  return () => {
    const server = new Server(
      { name: "things-plus-plus", version: "1.0.0" },
      {
        supportedProtocolVersions: [
          MODERN_PROTOCOL_VERSION,
          LEGACY_PROTOCOL_VERSION,
        ],
        capabilities: { tools: {} },
        cacheHints: {
          "server/discover": DEFAULT_CACHE_HINT,
          "tools/list": DEFAULT_CACHE_HINT,
        },
      },
    );
    server.setRequestHandler("tools/list", async (request, context) => {
      requireCatalogContext(context);
      if (request.params?.cursor !== undefined) {
        throw new ProtocolError(
          ProtocolErrorCode.InvalidParams,
          "Things catalog does not paginate",
        );
      }
      return { tools: [...catalog.tools] };
    });
    server.setRequestHandler(
      "tools/call",
      async (request, context): Promise<CallToolResult> => {
        const route = catalog.routesByName.get(request.params.name);
        const argumentsValue = request.params.arguments ?? {};
        if (route === undefined || !isRecord(argumentsValue)) {
          eventSink?.({ code: "provider_rejected" });
          throw new ProtocolError(
            ProtocolErrorCode.InvalidParams,
            "Unknown tool or invalid arguments",
          );
        }
        const providerContext = callContext(
          context,
          route.contract.minimumIndependentScope,
        );
        try {
          dispatchObserver.recordProviderDispatch();
          return await provider.call({
            server: route.contract.server,
            serverToolName: route.contract.serverToolName,
            publicToolName: route.contract.publicToolName,
            arguments: argumentsValue,
            context: providerContext,
          });
        } catch (error) {
          eventSink?.({ code: "provider_rejected" });
          if (error instanceof ProtocolError) {
            throw error;
          }
          throw new ProtocolError(
            ProtocolErrorCode.InternalError,
            "Tool execution unavailable",
          );
        }
      },
    );
    return server;
  };
}
