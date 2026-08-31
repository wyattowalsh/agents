import { describe, expect, it } from "vitest";

import {
  CatalogContractError,
  THINGS_SERVER_COUNTS,
  THINGS_TOOL_COUNT,
  canonicalSha256,
  parseThingsManifestProjection,
  validateThingsCatalog,
} from "../../src/protocol/index.js";
import {
  makeSyntheticContract,
  readCapabilityManifest,
} from "./helpers.js";
import { projectThingsManifestForRuntime } from "../../src/runtime/settings-contract.js";

function object(value: unknown): Record<string, unknown> {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("test_object_required");
  }
  return value as Record<string, unknown>;
}

function array(value: unknown): unknown[] {
  if (!Array.isArray(value)) throw new Error("test_array_required");
  return value;
}

function expectCatalogError(value: unknown, code: string): void {
  let thrown: unknown;
  try {
    parseThingsManifestProjection(value);
  } catch (error) {
    thrown = error;
  }
  expect(thrown).toBeInstanceOf(CatalogContractError);
  expect((thrown as CatalogContractError).code).toBe(code);
}

function expectProviderError(action: () => unknown, code: string): void {
  let thrown: unknown;
  try {
    action();
  } catch (error) {
    thrown = error;
  }
  expect(thrown).toBeInstanceOf(CatalogContractError);
  expect((thrown as CatalogContractError).code).toBe(code);
}

describe("Things catalog validation", () => {
  it("binds the exact ordered 41/21/8 manifest routes and independent scope map", async () => {
    const { projection, snapshot } = await makeSyntheticContract();
    const manifest = await readCapabilityManifest();
    const actualProjection = projectThingsManifestForRuntime(manifest);
    const catalog = validateThingsCatalog(snapshot, projection);

    expect(actualProjection.counts).toEqual({
      tools: 70,
      coreTools: 41,
      shortcutTools: 21,
      nativeTools: 8,
      supaOutcomes: 37,
      workflows: 17,
      legacyEvalIds: 25,
      newEvalIds: 16,
    });
    expect(actualProjection.tools).toHaveLength(THINGS_TOOL_COUNT);
    expect(actualProjection.tools[0]).toMatchObject({
      auditedUpstreamSchemaHashes: {
        inputSchemaSha256: expect.stringMatching(/^[a-f0-9]{64}$/u),
        outputSchemaSha256: expect.stringMatching(/^[a-f0-9]{64}$/u),
      },
      backendPrerequisites: [
        "things-3-installed",
        "mcp-server-things-1.9.0-hash-verified",
        "things-core-adapter",
      ],
      implementationKind: "upstream-security-adapter",
      testIds: [
        "things-core-toolset-exact",
        "things-core-add-area-contract",
      ],
    });
    expect(
      Object.hasOwn(
        object(array(manifest.tools)[41]),
        "auditedUpstreamSchemaHashes",
      ),
    ).toBe(false);
    expect(actualProjection.tools[41]?.auditedUpstreamSchemaHashes).toBeNull();
    expect(catalog.tools).toHaveLength(THINGS_TOOL_COUNT);
    expect(catalog.serverCounts).toEqual(THINGS_SERVER_COUNTS);
    expect([...catalog.routesByName.keys()]).toEqual(
      projection.tools.map((tool) => tool.publicToolName),
    );
    expect(catalog.scopeMapSha256).toBe(
      canonicalSha256(
        projection.tools.map((tool) => ({
          name: tool.publicToolName,
          minimumScope: tool.minimumIndependentScope,
        })),
      ),
    );
  });

  it.each([
    "name",
    "inputSchema",
    "outputSchema",
    "annotations",
    "minimumScope",
  ])("fails closed when %s drifts", async (field) => {
    const { projection, snapshot } = await makeSyntheticContract();
    const tool = snapshot.tools[0];
    if (tool === undefined) {
      throw new Error("test_tool_missing");
    }
    const drifted =
      field === "name"
        ? { ...tool, name: "things_core__wrong" }
        : field === "inputSchema"
          ? { ...tool, inputSchema: { ...tool.inputSchema, properties: {} } }
          : field === "outputSchema"
            ? { ...tool, outputSchema: { ...tool.outputSchema, properties: {} } }
            : field === "annotations"
              ? {
                  ...tool,
                  annotations: {
                    ...tool.annotations,
                    readOnlyHint: !tool.annotations.readOnlyHint,
                  },
                }
              : {
                  ...tool,
                  _meta: { ...tool._meta, thingsMinimumScope: "things.admin" },
                };
    const tools = [drifted, ...snapshot.tools.slice(1)];

    expect(() => validateThingsCatalog({ tools }, projection)).toThrow(
      CatalogContractError,
    );
  });

  it("accepts reordered provider arrival and returns manifest-canonical order", async () => {
    const { projection, snapshot } = await makeSyntheticContract();
    const canonical = validateThingsCatalog(snapshot, projection);
    const providerArrivalOrder = [
      ...snapshot.tools.slice(0, THINGS_SERVER_COUNTS["things-core"]),
      ...snapshot.tools.slice(
        THINGS_SERVER_COUNTS["things-core"] +
          THINGS_SERVER_COUNTS["things-shortcuts"],
      ),
      ...snapshot.tools.slice(
        THINGS_SERVER_COUNTS["things-core"],
        THINGS_SERVER_COUNTS["things-core"] +
          THINGS_SERVER_COUNTS["things-shortcuts"],
      ),
    ];
    const reordered = validateThingsCatalog(
      { tools: providerArrivalOrder },
      projection,
    );

    expect(reordered.tools.map((tool) => tool.name)).toEqual(
      projection.tools.map((tool) => tool.publicToolName),
    );
    expect([...reordered.routesByName.keys()]).toEqual(
      projection.tools.map((tool) => tool.publicToolName),
    );
    expect(reordered.catalogSha256).toBe(canonical.catalogSha256);
    expect(reordered.scopeMapSha256).toBe(canonical.scopeMapSha256);
  });

  it("rejects missing, duplicate, and identity-swapped provider tools", async () => {
    const { projection, snapshot } = await makeSyntheticContract();
    const first = snapshot.tools[0];
    const second = snapshot.tools[1];
    if (first === undefined || second === undefined) {
      throw new Error("test_tools_missing");
    }

    expectProviderError(
      () =>
        validateThingsCatalog(
          { tools: snapshot.tools.slice(1) },
          projection,
        ),
      "catalog_provider_tool_count_mismatch",
    );

    expectProviderError(
      () =>
        validateThingsCatalog(
          { tools: [...snapshot.tools.slice(0, -1), first] },
          projection,
        ),
      "catalog_provider_tool_name_collision",
    );

    expectProviderError(
      () =>
        validateThingsCatalog(
          {
            tools: [
              { ...first, name: "things_core__unexpected_extra" },
              ...snapshot.tools.slice(1),
            ],
          },
          projection,
        ),
      "catalog_provider_tool_missing",
    );

    expectProviderError(
      () =>
        validateThingsCatalog(
          {
            tools: [
              { ...first, _meta: second._meta },
              { ...second, _meta: first._meta },
              ...snapshot.tools.slice(2),
            ],
          },
          projection,
        ),
      `catalog_provider_tool_mismatch:${first.name}`,
    );
  });

  it("rejects count-only manifest assertions", async () => {
    const { projection } = await makeSyntheticContract();

    const expectedCounts = {
      tools: 70,
      coreTools: 41,
      shortcutTools: 21,
      nativeTools: 8,
      supaOutcomes: 37,
      workflows: 17,
      legacyEvalIds: 25,
      newEvalIds: 16,
    } as const;
    for (const [key, expected] of Object.entries(expectedCounts)) {
      const drifted = structuredClone(projection) as unknown;
      object(object(drifted).counts)[key] = expected + 1;
      expectCatalogError(drifted, "catalog_manifest_counts_mismatch");
    }

    const missingCount = structuredClone(projection) as unknown;
    delete object(object(missingCount).counts).supaOutcomes;
    expectCatalogError(missingCount, "catalog_manifest_counts_not_closed");

    const extraCount = structuredClone(projection) as unknown;
    object(object(extraCount).counts).unexpectedCoverage = 1;
    expectCatalogError(extraCount, "catalog_manifest_counts_not_closed");

    const missingMetadata = structuredClone(projection) as unknown;
    delete object(array(object(missingMetadata).tools)[0])
      .auditedUpstreamSchemaHashes;
    expectCatalogError(
      missingMetadata,
      "catalog_manifest_upstream_hashes_invalid",
    );

    const extraMetadata = structuredClone(projection) as unknown;
    object(array(object(extraMetadata).tools)[0]).unexpectedMetadata = true;
    expectCatalogError(extraMetadata, "catalog_manifest_tool_not_closed");

    const invalidUpstreamHashes = structuredClone(projection) as unknown;
    object(
      object(array(object(invalidUpstreamHashes).tools)[0])
        .auditedUpstreamSchemaHashes,
    ).inputSchemaSha256 = "0".repeat(63);
    expectCatalogError(
      invalidUpstreamHashes,
      "catalog_manifest_upstream_hashes_invalid",
    );

    const openUpstreamHashes = structuredClone(projection) as unknown;
    object(
      object(array(object(openUpstreamHashes).tools)[0])
        .auditedUpstreamSchemaHashes,
    ).unexpected = "0".repeat(64);
    expectCatalogError(
      openUpstreamHashes,
      "catalog_manifest_upstream_hashes_not_closed",
    );

    const forbiddenNonCoreHashes = structuredClone(projection) as unknown;
    object(
      array(object(forbiddenNonCoreHashes).tools)[41],
    ).auditedUpstreamSchemaHashes = {
      inputSchemaSha256: "0".repeat(64),
      outputSchemaSha256: "0".repeat(64),
    };
    expectCatalogError(
      forbiddenNonCoreHashes,
      "catalog_manifest_upstream_hashes_invalid",
    );

    const invalidPrerequisites = structuredClone(projection) as unknown;
    object(array(object(invalidPrerequisites).tools)[0]).backendPrerequisites = [
      "things-3-installed",
    ];
    expectCatalogError(
      invalidPrerequisites,
      "catalog_manifest_backend_prerequisites_invalid",
    );

    const invalidImplementation = structuredClone(projection) as unknown;
    object(array(object(invalidImplementation).tools)[0]).implementationKind =
      "fixed-shortcut-protocol";
    expectCatalogError(
      invalidImplementation,
      "catalog_manifest_implementation_kind_mismatch",
    );

    const invalidTestIds = structuredClone(projection) as unknown;
    object(array(object(invalidTestIds).tools)[0]).testIds = [
      "things-core-toolset-exact",
    ];
    expectCatalogError(invalidTestIds, "catalog_manifest_test_ids_invalid");
  });
});
