import { beforeEach, describe, expect, it, vi } from "vitest";

const upstream = vi.hoisted(() => ({
  callTool: vi.fn(),
  listTools: vi.fn(),
  transports: {} as Record<string, unknown>,
}));

vi.mock("@samanhappy/mcphub/dist/services/mcpService.js", () => ({
  handleCallToolRequest: upstream.callTool,
  handleListToolsRequest: upstream.listTools,
}));

vi.mock("@samanhappy/mcphub/dist/services/sseService.js", () => ({
  transports: upstream.transports,
}));

import type {
  ThingsManifestToolContract,
  ThingsProviderCall,
  ThingsPublicTool,
} from "../../src/protocol/index.js";
import { McpHubThingsProvider } from "../../src/runtime/provider.js";
import { makeSyntheticContract } from "./helpers.js";

interface RawCatalog {
  readonly contracts: readonly ThingsManifestToolContract[];
  readonly tools: readonly ThingsPublicTool[];
}

async function rawCatalog(): Promise<RawCatalog> {
  const { projection, snapshot } = await makeSyntheticContract();
  const toolsByPublicName = new Map(
    snapshot.tools.map((tool) => [tool.name, tool] as const),
  );
  const rawByServer = new Map(
    ["things-core", "things-shortcuts", "things-native"].map((server) => [
      server,
      [] as ThingsPublicTool[],
    ]),
  );
  for (const contract of projection.tools) {
    const publicTool = toolsByPublicName.get(contract.publicToolName);
    const serverTools = rawByServer.get(contract.server);
    if (publicTool === undefined || serverTools === undefined) {
      throw new Error("provider_adapter_fixture_invalid");
    }
    serverTools.push({
      ...publicTool,
      name: `${contract.server}-${contract.serverToolName}`,
    });
  }
  return {
    contracts: projection.tools,
    tools: [
      ...(rawByServer.get("things-core") ?? []),
      ...(rawByServer.get("things-native") ?? []),
      ...(rawByServer.get("things-shortcuts") ?? []),
    ],
  };
}

function callFor(contract: ThingsManifestToolContract): ThingsProviderCall {
  return {
    server: contract.server,
    serverToolName: contract.serverToolName,
    publicToolName: contract.publicToolName,
    arguments: Object.freeze({}),
    context: {
      principal: "provider-adapter-test",
      clientId: "provider-adapter-test",
      resource: "http://127.0.0.1:46683/mcp/things",
      scopes: new Set([contract.minimumIndependentScope]),
      signal: new AbortController().signal,
    },
  };
}

describe("MCPHub provider name adapter", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    for (const key of Object.keys(upstream.transports)) {
      delete upstream.transports[key];
    }
    upstream.callTool.mockResolvedValue({ content: [] });
  });

  it("normalizes the raw 41/8/21 arrival catalog to all 70 exact public names", async () => {
    const fixture = await rawCatalog();
    upstream.listTools.mockResolvedValue({ tools: fixture.tools });
    const provider = new McpHubThingsProvider();

    await provider.initialize();
    const snapshot = await provider.snapshot();

    expect(snapshot.tools).toHaveLength(70);
    expect(new Set(snapshot.tools.map((tool) => tool.name))).toEqual(
      new Set(fixture.contracts.map((contract) => contract.publicToolName)),
    );
    expect(snapshot.tools.slice(0, 41).map((tool) => tool.name)).toEqual(
      fixture.contracts.slice(0, 41).map((contract) => contract.publicToolName),
    );
    expect(snapshot.tools.slice(41, 49).map((tool) => tool.name)).toEqual(
      fixture.contracts.slice(62).map((contract) => contract.publicToolName),
    );
    expect(snapshot.tools.slice(49).map((tool) => tool.name)).toEqual(
      fixture.contracts.slice(41, 62).map((contract) => contract.publicToolName),
    );
    provider.close();
  });

  it("reverse maps all 70 exact calls without a public-name fallback", async () => {
    const fixture = await rawCatalog();
    upstream.listTools.mockResolvedValue({ tools: fixture.tools });
    const provider = new McpHubThingsProvider();
    await provider.initialize();

    for (const contract of fixture.contracts) {
      await provider.call(callFor(contract));
    }

    expect(upstream.callTool).toHaveBeenCalledTimes(70);
    for (const [index, call] of upstream.callTool.mock.calls.entries()) {
      const contract = fixture.contracts[index];
      if (contract === undefined) throw new Error("provider_adapter_contract_missing");
      expect(call[0]).toMatchObject({
        method: "tools/call",
        params: {
          name: `${contract.server}-${contract.serverToolName}`,
          arguments: {},
        },
      });
      expect(call[1]).toMatchObject({ group: "things" });
      expect(call[0].params.name).not.toBe(contract.publicToolName);
    }
    provider.close();
  });

  it.each([
    ["unknown raw prefix", "unknown-add_area", "upstream_tool_route_invalid"],
    ["public-form raw name", "things_core__add_area", "upstream_tool_route_invalid"],
    ["invalid raw suffix", "things-core-invalid-name", "upstream_server_tool_name_invalid"],
  ])("rejects %s without fallback", async (_label, name, code) => {
    const fixture = await rawCatalog();
    const first = fixture.tools[0];
    if (first === undefined) throw new Error("provider_adapter_tool_missing");
    upstream.listTools.mockResolvedValue({
      tools: [{ ...first, name }, ...fixture.tools.slice(1)],
    });
    const provider = new McpHubThingsProvider();

    await expect(provider.initialize()).rejects.toThrow(code);
    expect(upstream.listTools).toHaveBeenCalledTimes(1);
    provider.close();
  });

  it("rejects a canonical collision before exposing a snapshot", async () => {
    const fixture = await rawCatalog();
    const first = fixture.tools[0];
    const second = fixture.tools[1];
    if (first === undefined || second === undefined) {
      throw new Error("provider_adapter_tool_missing");
    }
    upstream.listTools.mockResolvedValue({
      tools: [first, { ...second, name: first.name }, ...fixture.tools.slice(2)],
    });
    const provider = new McpHubThingsProvider();

    await expect(provider.initialize()).rejects.toThrow(
      "upstream_tool_name_collision",
    );
    expect(upstream.listTools).toHaveBeenCalledTimes(1);
    provider.close();
  });

  it("rejects a wrong public/server pairing without dispatch fallback", async () => {
    const fixture = await rawCatalog();
    upstream.listTools.mockResolvedValue({ tools: fixture.tools });
    const contract = fixture.contracts[0];
    if (contract === undefined) throw new Error("provider_adapter_contract_missing");
    const provider = new McpHubThingsProvider();
    await provider.initialize();

    await expect(
      provider.call({
        ...callFor(contract),
        publicToolName: `things_shortcuts__${contract.serverToolName}`,
      }),
    ).rejects.toThrow("upstream_public_tool_name_invalid");
    await expect(
      provider.call({
        ...callFor(contract),
        publicToolName: `${contract.server}-${contract.serverToolName}`,
      }),
    ).rejects.toThrow("upstream_public_tool_name_invalid");
    expect(upstream.callTool).not.toHaveBeenCalled();
    provider.close();
  });
});
