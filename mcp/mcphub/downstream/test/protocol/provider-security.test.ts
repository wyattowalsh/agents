import { describe, expect, it } from "vitest";

import {
  HEADER_MISMATCH,
  createThingsProtocolHandler,
} from "../../src/protocol/index.js";
import {
  RecordingProvider,
  authOptions,
  makeSyntheticContract,
  modernBody,
  modernRequest,
  responseJson,
} from "./helpers.js";

async function rpcCode(response: Response): Promise<number> {
  const body = await responseJson(response);
  return (body.error as { code: number }).code;
}

describe("provider boundary", () => {
  it("does not invoke the provider for an unknown public name", async () => {
    const { projection, snapshot } = await makeSyntheticContract();
    const provider = new RecordingProvider(snapshot);
    const handler = await createThingsProtocolHandler(provider, projection);
    const response = await handler.fetch(
      modernRequest(
        modernBody(1, "tools/call", {
          name: "things_core__not_a_tool",
          arguments: {},
        }),
      ),
      authOptions(),
    );
    expect(response.status).toBe(200);
    expect(await rpcCode(response)).toBe(-32602);
    expect(provider.calls).toHaveLength(0);
  });

  it("maps an unknown modern RPC to HTTP 404/-32601 without provider fallback", async () => {
    const { projection, snapshot } = await makeSyntheticContract();
    const provider = new RecordingProvider(snapshot);
    const handler = await createThingsProtocolHandler(provider, projection);
    const response = await handler.fetch(
      modernRequest(modernBody(10, "things/unknown")),
      authOptions(),
    );
    expect(response.status).toBe(404);
    expect(await rpcCode(response)).toBe(-32601);
    expect(provider.calls).toHaveLength(0);
  });

  it("does not invoke the provider without the exact independent scope", async () => {
    const { projection, snapshot } = await makeSyntheticContract();
    const provider = new RecordingProvider(snapshot);
    const handler = await createThingsProtocolHandler(provider, projection);
    const contract = projection.tools.find(
      (tool) => tool.minimumIndependentScope === "things.admin",
    );
    if (contract === undefined) {
      throw new Error("admin_contract_missing");
    }
    const response = await handler.fetch(
      modernRequest(
        modernBody(2, "tools/call", {
          name: contract.publicToolName,
          arguments: {},
        }),
      ),
      authOptions(["things.write"]),
    );
    expect(response.status).toBe(200);
    expect(await rpcCode(response)).toBe(-32602);
    expect(provider.calls).toHaveLength(0);
  });

  it("does not invoke the provider for a noncanonical resource", async () => {
    const { projection, snapshot } = await makeSyntheticContract();
    const provider = new RecordingProvider(snapshot);
    const handler = await createThingsProtocolHandler(provider, projection);
    const contract = projection.tools[0];
    if (contract === undefined) {
      throw new Error("contract_missing");
    }
    const response = await handler.fetch(
      modernRequest(
        modernBody(3, "tools/call", {
          name: contract.publicToolName,
          arguments: {},
        }),
      ),
      authOptions(["things.write"], {
        resource: "https://example.invalid/mcp/things",
        credentialClass: "remote-oauth",
      }),
    );
    expect(response.status).toBe(403);
    expect(await rpcCode(response)).toBe(-32602);
    expect(provider.calls).toHaveLength(0);
  });

  it("accepts the exact remote resource identity", async () => {
    const { projection, snapshot } = await makeSyntheticContract();
    const provider = new RecordingProvider(snapshot);
    const handler = await createThingsProtocolHandler(provider, projection);
    const contract = projection.tools.find(
      (tool) => tool.minimumIndependentScope === "things.read",
    );
    if (contract === undefined) {
      throw new Error("read_contract_missing");
    }
    const response = await handler.fetch(
      modernRequest(
        modernBody(11, "tools/call", {
          name: contract.publicToolName,
          arguments: {},
        }),
      ),
      authOptions(["things.read"], {
        resource: "https://mcp.w4w.dev/mcp/things",
      }),
    );
    expect(response.status).toBe(200);
    expect(provider.calls[0]?.context.resource).toBe(
      "https://mcp.w4w.dev/mcp/things",
    );
  });

  it("rejects a name header mismatch before provider routing", async () => {
    const { projection, snapshot } = await makeSyntheticContract();
    const provider = new RecordingProvider(snapshot);
    const handler = await createThingsProtocolHandler(provider, projection);
    const contract = projection.tools[0];
    if (contract === undefined) {
      throw new Error("contract_missing");
    }
    const body = modernBody(4, "tools/call", {
      name: contract.publicToolName,
      arguments: {},
    });
    const request = modernRequest(body, { "mcp-name": "things_core__wrong" });
    const response = await handler.fetch(request, authOptions());
    expect(response.status).toBe(400);
    expect(await rpcCode(response)).toBe(HEADER_MISMATCH);
    expect(provider.calls).toHaveLength(0);
  });
});
