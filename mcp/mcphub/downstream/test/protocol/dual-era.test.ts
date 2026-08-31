import { describe, expect, it } from "vitest";

import {
  DEFAULT_CACHE_HINT,
  PROTOCOL_CONFORMANCE_CASE_IDS,
  LEGACY_PROTOCOL_VERSION,
  MODERN_PROTOCOL_VERSION,
  ProtocolConformanceError,
  THINGS_TOOL_COUNT,
  canonicalSha256,
  canonicalJson,
  createThingsProtocolHandler,
  runDualEraProtocolConformance,
} from "../../src/protocol/index.js";
import {
  RecordingProvider,
  authOptions,
  legacyRequest,
  makeSyntheticContract,
  modernBody,
  modernRequest,
  responseJson,
} from "./helpers.js";

function resultOf(body: Record<string, unknown>): Record<string, unknown> {
  const result = body.result;
  if (result === null || typeof result !== "object" || Array.isArray(result)) {
    throw new Error("response_result_missing");
  }
  return result as Record<string, unknown>;
}

function normalizedTools(result: Record<string, unknown>): unknown {
  return result.tools;
}

describe("dual-era public protocol", () => {
  it("serves modern discovery and independently valid tools/list", async () => {
    const { projection, snapshot } = await makeSyntheticContract();
    const provider = new RecordingProvider(snapshot);
    const handler = await createThingsProtocolHandler(provider, projection);

    const discoverResponse = await handler.fetch(
      modernRequest(modernBody(1, "server/discover")),
      authOptions(),
    );
    const discover = resultOf(await responseJson(discoverResponse));
    expect(discoverResponse.status).toBe(200);
    expect(discover.supportedVersions).toEqual([MODERN_PROTOCOL_VERSION]);
    expect(discover.capabilities).toEqual({ tools: {} });
    expect(discover.resultType).toBe("complete");
    expect(discover.ttlMs).toBe(DEFAULT_CACHE_HINT.ttlMs);
    expect(discover.cacheScope).toBe(DEFAULT_CACHE_HINT.cacheScope);

    const listResponse = await handler.fetch(
      modernRequest(modernBody(2, "tools/list")),
      authOptions(),
    );
    const list = resultOf(await responseJson(listResponse));
    expect(listResponse.status).toBe(200);
    expect(list.tools).toHaveLength(THINGS_TOOL_COUNT);
    expect(list.resultType).toBe("complete");
    expect(list.ttlMs).toBe(DEFAULT_CACHE_HINT.ttlMs);
    expect(list.cacheScope).toBe(DEFAULT_CACHE_HINT.cacheScope);
    expect(provider.calls).toHaveLength(0);

    const freshHandler = await createThingsProtocolHandler(provider, projection);
    const listWithoutDiscover = await freshHandler.fetch(
      modernRequest(modernBody(3, "tools/list")),
      authOptions(),
    );
    expect(listWithoutDiscover.status).toBe(200);
    expect(resultOf(await responseJson(listWithoutDiscover)).tools).toHaveLength(
      THINGS_TOOL_COUNT,
    );
  });

  it("serves legacy initialize and stateless tools/list without sessions", async () => {
    const { projection, snapshot } = await makeSyntheticContract();
    const provider = new RecordingProvider(snapshot);
    const handler = await createThingsProtocolHandler(provider, projection);
    const initialize = {
      jsonrpc: "2.0",
      id: 10,
      method: "initialize",
      params: {
        protocolVersion: LEGACY_PROTOCOL_VERSION,
        capabilities: {},
        clientInfo: { name: "legacy-conformance", version: "1.0.0" },
      },
    };
    const initializeResponse = await handler.fetch(
      legacyRequest(initialize),
      authOptions(),
    );
    const initializeResult = resultOf(await responseJson(initializeResponse));
    expect(initializeResponse.status).toBe(200);
    expect(initializeResult.protocolVersion).toBe(LEGACY_PROTOCOL_VERSION);
    expect(initializeResponse.headers.has("mcp-session-id")).toBe(false);

    const listResponse = await handler.fetch(
      legacyRequest({
        jsonrpc: "2.0",
        id: 11,
        method: "tools/list",
        params: {},
      }),
      authOptions(),
    );
    const listResult = resultOf(await responseJson(listResponse));
    expect(listResponse.status).toBe(200);
    expect(listResult.tools).toHaveLength(THINGS_TOOL_COUNT);
    expect(listResult).not.toHaveProperty("resultType");
    expect(listResult).not.toHaveProperty("ttlMs");
    expect(listResult).not.toHaveProperty("cacheScope");
    expect(listResponse.headers.has("mcp-session-id")).toBe(false);
  });

  it("normalizes modern and legacy catalogs byte-for-byte", async () => {
    const { projection, snapshot } = await makeSyntheticContract();
    const provider = new RecordingProvider(snapshot);
    const handler = await createThingsProtocolHandler(provider, projection);
    const modern = resultOf(
      await responseJson(
        await handler.fetch(
          modernRequest(modernBody(20, "tools/list")),
          authOptions(),
        ),
      ),
    );
    const legacy = resultOf(
      await responseJson(
        await handler.fetch(
          legacyRequest({
            jsonrpc: "2.0",
            id: 21,
            method: "tools/list",
            params: {},
          }),
          authOptions(),
        ),
      ),
    );
    expect(canonicalJson(normalizedTools(modern))).toBe(
      canonicalJson(normalizedTools(legacy)),
    );
  });

  it("routes tools/call through the exact manifest identity and independent scope", async () => {
    const { projection, snapshot } = await makeSyntheticContract();
    const provider = new RecordingProvider(snapshot);
    const handler = await createThingsProtocolHandler(provider, projection);
    const contract = projection.tools.find(
      (tool) => tool.minimumIndependentScope === "things.write",
    );
    if (contract === undefined) {
      throw new Error("write_contract_missing");
    }
    const response = await handler.fetch(
      modernRequest(
        modernBody(30, "tools/call", {
          name: contract.publicToolName,
          arguments: {},
        }),
      ),
      authOptions(["things.write"]),
    );
    expect(response.status).toBe(200);
    expect(provider.calls).toHaveLength(1);
    expect(provider.calls[0]).toMatchObject({
      server: contract.server,
      serverToolName: contract.serverToolName,
      publicToolName: contract.publicToolName,
      context: {
        principal: "subject:test",
        clientId: "things-conformance-client",
        resource: "http://127.0.0.1:46683/mcp/things",
      },
    });
  });

  it("runs every required case and mints only a complete digest-bound report", async () => {
    const { projection, snapshot } = await makeSyntheticContract();
    const provider = new RecordingProvider(snapshot);
    const handler = await createThingsProtocolHandler(
      provider,
      projection,
    );
    const report = await runDualEraProtocolConformance(
      handler,
      authOptions(),
    );
    expect(report.protocol.discoverySupportedVersions).toEqual([
      MODERN_PROTOCOL_VERSION,
    ]);
    expect(report.execution).toMatchObject({
      status: "passed",
      caseCount: 22,
      passedCaseCount: 22,
      caseIds: PROTOCOL_CONFORMANCE_CASE_IDS,
      sdkDispatchCount: 6,
      providerDispatchCount: 1,
    });
    expect(report.execution.cases.map((entry) => entry.id)).toEqual(
      PROTOCOL_CONFORMANCE_CASE_IDS,
    );
    expect(report.execution.cases.every((entry) => entry.status === "passed")).toBe(
      true,
    );
    expect(report.execution.resultBundleSha256).toBe(
      canonicalSha256(report.execution.cases),
    );
    for (const digest of [
      report.execution.errorMatrixSha256,
      report.execution.errorMatrixResultsSha256,
      report.execution.resultBundleSha256,
      ...report.execution.cases.map((entry) => entry.resultSha256),
    ]) {
      expect(digest).toMatch(/^[a-f0-9]{64}$/u);
    }
    expect(provider.calls).toHaveLength(1);
    expect(provider.calls[0]?.publicToolName).toBe(
      "things_core__get_server_capabilities",
    );

    const independentList = await handler.fetch(
      modernRequest(modernBody(99, "tools/list")),
      authOptions(),
    );
    expect(independentList.status).toBe(200);
  });

  it("fails when a negative case reaches an unexpected SDK and provider path", async () => {
    const { projection, snapshot } = await makeSyntheticContract();
    const provider = new RecordingProvider(snapshot);
    const handler = await createThingsProtocolHandler(provider, projection);
    const readContract = projection.tools.find(
      (tool) => tool.minimumIndependentScope === "things.read",
    );
    if (readContract === undefined) {
      throw new Error("read_contract_missing");
    }
    const originalFetch = handler.fetch.bind(handler);
    Object.defineProperty(handler, "fetch", {
      configurable: true,
      value: async (
        request: Request,
        options?: Parameters<typeof handler.fetch>[1],
      ): Promise<Response> => {
        let method: unknown;
        if (request.method === "POST") {
          try {
            const body = (await request.clone().json()) as Record<
              string,
              unknown
            >;
            method = body.method;
          } catch {
            method = undefined;
          }
        }
        if (method === "things/unknown") {
          await originalFetch(
            modernRequest(
              modernBody(777, "tools/call", {
                name: readContract.publicToolName,
                arguments: {},
              }),
            ),
            authOptions(["things.read"]),
          );
        }
        return originalFetch(request, options);
      },
    });

    await expect(
      runDualEraProtocolConformance(handler, authOptions()),
    ).rejects.toEqual(
      new ProtocolConformanceError(
        "protocol_conformance_unknown-modern-method_outcome_mismatch",
      ),
    );
    expect(provider.calls).toHaveLength(2);
  });

  it("does not expose a report builder that can bypass execution", async () => {
    const conformance = await import("../../src/protocol/conformance.js");
    expect(conformance).not.toHaveProperty("buildProtocolConformanceReport");
  });
});
