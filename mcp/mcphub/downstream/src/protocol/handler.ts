import {
  createMcpHandler,
  type McpHandlerRequestOptions,
} from "@modelcontextprotocol/server";

import { validateThingsCatalog } from "./catalog-validation.js";
import {
  attachProtocolDispatchObserver,
  ProtocolDispatchObserver,
} from "./dispatch-observer.js";
import { createThingsServerFactory } from "./server-factory.js";
import { withProtocolPreflight } from "./request-preflight.js";
import type {
  ThingsManifestProjection,
  ThingsProtocolHandler,
  ThingsProtocolOptions,
  ThingsToolProvider,
} from "./types.js";

export async function createThingsProtocolHandler(
  provider: ThingsToolProvider,
  manifestProjection: ThingsManifestProjection | unknown,
  options: ThingsProtocolOptions = {},
): Promise<ThingsProtocolHandler> {
  const snapshot = await provider.snapshot();
  const catalog = validateThingsCatalog(snapshot, manifestProjection);
  const dispatchObserver = new ProtocolDispatchObserver();
  const sdkHandler = createMcpHandler(
    createThingsServerFactory(
      provider,
      catalog,
      dispatchObserver,
      options.eventSink,
    ),
    {
      legacy: "stateless",
      responseMode: "json",
      keepAliveMs: 0,
      onerror: () => {
        options.eventSink?.({ code: "protocol_internal_error" });
      },
    },
  );
  const preflight = withProtocolPreflight(sdkHandler, {
    ...options,
    dispatchObserver,
  });
  const handler: ThingsProtocolHandler = {
    catalog,
    close: preflight.close,
    notify: preflight.notify,
    bus: preflight.bus,
    fetch: (
      request: Request,
      requestOptions?: McpHandlerRequestOptions,
    ): Promise<Response> => preflight.fetch(request, requestOptions),
  };
  attachProtocolDispatchObserver(handler, dispatchObserver);
  return handler;
}
