declare module "@samanhappy/mcphub/dist/services/mcpService.js" {
  export function handleListToolsRequest(
    request: unknown,
    extra: Readonly<Record<string, unknown>>,
  ): Promise<Readonly<{ tools: readonly unknown[] }>>;
  export function handleCallToolRequest(
    request: Readonly<{ method: "tools/call"; params: Readonly<Record<string, unknown>> }>,
    extra: Readonly<Record<string, unknown>>,
  ): Promise<unknown>;
}

declare module "@samanhappy/mcphub/dist/server.js" {
  type UpstreamApplication = ( (
    request: import("node:http").IncomingMessage,
    response: import("node:http").ServerResponse,
  ) => void) & {
    use(
      middleware: (
        request: import("node:http").IncomingMessage,
        response: import("node:http").ServerResponse,
        next: () => void,
      ) => void,
    ): unknown;
  };

  export default class AppServer {
    public constructor();
    public initialize(): Promise<void>;
    public shutdown(): Promise<void>;
    public getApp(): UpstreamApplication;
  }
}

declare module "@samanhappy/mcphub/dist/services/sseService.js" {
  export const transports: Record<string, Record<string, unknown>>;
}
