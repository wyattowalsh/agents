import {
  LOCAL_THINGS_RESOURCE,
  REMOTE_THINGS_RESOURCE,
  THINGS_GROUP_NAME,
  THINGS_GROUP_PATH,
  THINGS_SERVER_COUNTS,
  THINGS_TOOL_COUNT,
  type ThingsServerName,
} from "./constants.js";
import { canonicalJson, canonicalSha256 } from "./canonical-json.js";
import type {
  AdaptedSchemaHashes,
  AuditedUpstreamSchemaHashes,
  ClosedJsonObjectSchema,
  JsonObject,
  ThingsImplementationKind,
  ThingsCatalogSnapshot,
  ThingsManifestProjection,
  ThingsManifestToolContract,
  ThingsPublicTool,
  ThingsRisk,
  ThingsScope,
  ThingsToolAnnotations,
  ValidatedThingsCatalog,
  ValidatedThingsRoute,
} from "./types.js";

const SHA256_PATTERN = /^[a-f0-9]{64}$/u;
const SERVER_TOOL_NAME_PATTERN = /^[a-z0-9][a-z0-9_]*$/u;
const PUBLIC_TOOL_NAME_PATTERN = /^[a-z0-9_]+__[a-z0-9][a-z0-9_]*$/u;
const SCOPES = new Set<ThingsScope>([
  "things.read",
  "things.write",
  "things.admin",
]);
const RISKS = new Set<ThingsRisk>([
  "read-only",
  "ui-handoff",
  "ui-visible",
  "single-write",
  "bulk-write",
  "destructive-write",
]);
const SERVERS = new Set<ThingsServerName>([
  "things-core",
  "things-shortcuts",
  "things-native",
]);
const IMPLEMENTATION_KINDS = new Set<ThingsImplementationKind>([
  "upstream-security-adapter",
  "fixed-shortcut-protocol",
  "fixed-applescript",
  "fixed-things-url-scheme",
]);
const BACKEND_PREREQUISITES = {
  "upstream-security-adapter": [
    "things-3-installed",
    "mcp-server-things-1.9.0-hash-verified",
    "things-core-adapter",
  ],
  "fixed-shortcut-protocol": [
    "things-3-installed",
    "shortcuts-cli",
    "things-plus-plus-shortcut-protocol-v1",
    "tcc-preauthorized",
  ],
  "fixed-applescript": [
    "things-3-installed",
    "osascript",
    "fixed-native-script-bundle-hash-verified",
    "tcc-preauthorized",
  ],
  "fixed-things-url-scheme": [
    "things-3-installed",
    "fixed-things-search-url-builder-hash-verified",
    "tcc-preauthorized",
  ],
} as const satisfies Readonly<Record<ThingsImplementationKind, readonly string[]>>;

export class CatalogContractError extends Error {
  public constructor(public readonly code: string) {
    super(code);
    this.name = "CatalogContractError";
  }
}

function fail(code: string): never {
  throw new CatalogContractError(code);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    return false;
  }
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

function record(value: unknown, code: string): Record<string, unknown> {
  return isRecord(value) ? value : fail(code);
}

function exactKeys(
  value: Record<string, unknown>,
  required: readonly string[],
  optional: readonly string[],
  code: string,
): void {
  const allowed = new Set([...required, ...optional]);
  if (
    required.some((key) => !(key in value)) ||
    Object.keys(value).some((key) => !allowed.has(key))
  ) {
    fail(code);
  }
}

function stringValue(value: unknown, code: string): string {
  return typeof value === "string" && value.length > 0 ? value : fail(code);
}

function booleanValue(value: unknown, code: string): boolean {
  return typeof value === "boolean" ? value : fail(code);
}

function serverValue(value: unknown): ThingsServerName {
  const server = stringValue(value, "catalog_manifest_server_invalid");
  return SERVERS.has(server as ThingsServerName)
    ? (server as ThingsServerName)
    : fail("catalog_manifest_server_invalid");
}

function scopeValue(value: unknown): ThingsScope {
  const scope = stringValue(value, "catalog_manifest_scope_invalid");
  return SCOPES.has(scope as ThingsScope)
    ? (scope as ThingsScope)
    : fail("catalog_manifest_scope_invalid");
}

function riskValue(value: unknown): ThingsRisk {
  const risk = stringValue(value, "catalog_manifest_risk_invalid");
  return RISKS.has(risk as ThingsRisk)
    ? (risk as ThingsRisk)
    : fail("catalog_manifest_risk_invalid");
}

function annotationsValue(value: unknown): ThingsToolAnnotations {
  const source = record(value, "catalog_annotations_invalid");
  exactKeys(
    source,
    [
      "readOnlyHint",
      "destructiveHint",
      "idempotentHint",
      "openWorldHint",
    ],
    [],
    "catalog_annotations_not_closed",
  );
  return {
    readOnlyHint: booleanValue(
      source.readOnlyHint,
      "catalog_annotation_read_only_invalid",
    ),
    destructiveHint: booleanValue(
      source.destructiveHint,
      "catalog_annotation_destructive_invalid",
    ),
    idempotentHint: booleanValue(
      source.idempotentHint,
      "catalog_annotation_idempotent_invalid",
    ),
    openWorldHint: booleanValue(
      source.openWorldHint,
      "catalog_annotation_open_world_invalid",
    ),
  };
}

function hashesValue(value: unknown): AdaptedSchemaHashes {
  const source = record(value, "catalog_manifest_hashes_invalid");
  exactKeys(
    source,
    ["inputSchemaSha256", "outputSchemaSha256", "status"],
    [],
    "catalog_manifest_hashes_not_closed",
  );
  const inputSchemaSha256 = stringValue(
    source.inputSchemaSha256,
    "catalog_manifest_input_hash_invalid",
  );
  const outputSchemaSha256 = stringValue(
    source.outputSchemaSha256,
    "catalog_manifest_output_hash_invalid",
  );
  if (
    !SHA256_PATTERN.test(inputSchemaSha256) ||
    !SHA256_PATTERN.test(outputSchemaSha256) ||
    source.status !== "frozen"
  ) {
    fail("catalog_manifest_hashes_invalid");
  }
  return { inputSchemaSha256, outputSchemaSha256, status: "frozen" };
}

function auditedUpstreamHashesValue(
  value: unknown,
  server: ThingsServerName,
): AuditedUpstreamSchemaHashes | null {
  if (server !== "things-core") {
    if (value !== undefined && value !== null) {
      fail("catalog_manifest_upstream_hashes_invalid");
    }
    return null;
  }
  const source = record(value, "catalog_manifest_upstream_hashes_invalid");
  exactKeys(
    source,
    ["inputSchemaSha256", "outputSchemaSha256"],
    [],
    "catalog_manifest_upstream_hashes_not_closed",
  );
  const inputSchemaSha256 = stringValue(
    source.inputSchemaSha256,
    "catalog_manifest_upstream_input_hash_invalid",
  );
  const outputSchemaSha256 = stringValue(
    source.outputSchemaSha256,
    "catalog_manifest_upstream_output_hash_invalid",
  );
  if (
    !SHA256_PATTERN.test(inputSchemaSha256) ||
    !SHA256_PATTERN.test(outputSchemaSha256)
  ) {
    fail("catalog_manifest_upstream_hashes_invalid");
  }
  return { inputSchemaSha256, outputSchemaSha256 };
}

function implementationKindValue(
  value: unknown,
  server: ThingsServerName,
  serverToolName: string,
): ThingsImplementationKind {
  const kind = stringValue(value, "catalog_manifest_implementation_kind_invalid");
  if (!IMPLEMENTATION_KINDS.has(kind as ThingsImplementationKind)) {
    fail("catalog_manifest_implementation_kind_invalid");
  }
  const implementationKind = kind as ThingsImplementationKind;
  const validForServer =
    (server === "things-core" && implementationKind === "upstream-security-adapter") ||
    (server === "things-shortcuts" && implementationKind === "fixed-shortcut-protocol") ||
    (server === "things-native" &&
      ((serverToolName === "open_search" && implementationKind === "fixed-things-url-scheme") ||
        (serverToolName !== "open_search" && implementationKind === "fixed-applescript")));
  if (!validForServer) fail("catalog_manifest_implementation_kind_mismatch");
  return implementationKind;
}

function backendPrerequisitesValue(
  value: unknown,
  implementationKind: ThingsImplementationKind,
): readonly string[] {
  const expected = BACKEND_PREREQUISITES[implementationKind];
  if (!Array.isArray(value) || canonicalJson(value) !== canonicalJson(expected)) {
    fail("catalog_manifest_backend_prerequisites_invalid");
  }
  return [...expected];
}

function testIdsValue(
  value: unknown,
  server: ThingsServerName,
  serverToolName: string,
): readonly string[] {
  const expected = [
    `${server}-toolset-exact`,
    `${server}-${serverToolName.replaceAll("_", "-")}-contract`,
  ];
  if (!Array.isArray(value) || canonicalJson(value) !== canonicalJson(expected)) {
    fail("catalog_manifest_test_ids_invalid");
  }
  return expected;
}

function manifestToolValue(value: unknown): ThingsManifestToolContract {
  const source = record(value, "catalog_manifest_tool_invalid");
  exactKeys(
    source,
    [
      "server",
      "serverToolName",
      "publicToolName",
      "expectedMcphubQualifiedName",
      "qualifiedCapabilityId",
      "minimumIndependentScope",
      "risk",
      "annotations",
      "schemaContractId",
      "adaptedSchemaHashes",
      "backendPrerequisites",
      "implementationKind",
      "testIds",
    ],
    ["auditedUpstreamSchemaHashes"],
    "catalog_manifest_tool_not_closed",
  );
  const server = serverValue(source.server);
  const serverToolName = stringValue(
    source.serverToolName,
    "catalog_manifest_server_tool_name_invalid",
  );
  const publicToolName = stringValue(
    source.publicToolName,
    "catalog_manifest_public_tool_name_invalid",
  );
  const expectedMcphubQualifiedName = stringValue(
    source.expectedMcphubQualifiedName,
    "catalog_manifest_qualified_name_invalid",
  );
  const qualifiedCapabilityId = stringValue(
    source.qualifiedCapabilityId,
    "catalog_manifest_capability_id_invalid",
  );
  const schemaContractId = stringValue(
    source.schemaContractId,
    "catalog_manifest_schema_contract_invalid",
  );
  if (
    !SERVER_TOOL_NAME_PATTERN.test(serverToolName) ||
    serverToolName.includes("__") ||
    !PUBLIC_TOOL_NAME_PATTERN.test(publicToolName)
  ) {
    fail("catalog_manifest_tool_name_invalid");
  }
  const normalizedName = `${server.replaceAll("-", "_")}__${serverToolName}`;
  if (
    publicToolName !== normalizedName ||
    expectedMcphubQualifiedName !== normalizedName ||
    qualifiedCapabilityId !== `${server}/${serverToolName}` ||
    schemaContractId !== `${server}/${serverToolName}@v1`
  ) {
    fail("catalog_manifest_tool_identity_mismatch");
  }
  const implementationKind = implementationKindValue(
    source.implementationKind,
    server,
    serverToolName,
  );
  return {
    server,
    serverToolName,
    publicToolName,
    expectedMcphubQualifiedName,
    qualifiedCapabilityId,
    minimumIndependentScope: scopeValue(source.minimumIndependentScope),
    risk: riskValue(source.risk),
    annotations: annotationsValue(source.annotations),
    schemaContractId,
    adaptedSchemaHashes: hashesValue(source.adaptedSchemaHashes),
    auditedUpstreamSchemaHashes: auditedUpstreamHashesValue(
      source.auditedUpstreamSchemaHashes,
      server,
    ),
    backendPrerequisites: backendPrerequisitesValue(
      source.backendPrerequisites,
      implementationKind,
    ),
    implementationKind,
    testIds: testIdsValue(source.testIds, server, serverToolName),
  };
}

export function parseThingsManifestProjection(
  value: unknown,
): ThingsManifestProjection {
  const source = record(value, "catalog_manifest_projection_invalid");
  exactKeys(
    source,
    ["schemaVersion", "group", "counts", "tools"],
    [],
    "catalog_manifest_projection_not_closed",
  );
  if (source.schemaVersion !== 1) {
    fail("catalog_manifest_schema_version_invalid");
  }
  const group = record(source.group, "catalog_manifest_group_invalid");
  exactKeys(
    group,
    [
      "name",
      "localPath",
      "remotePath",
      "localResource",
      "remoteResource",
      "servers",
    ],
    [],
    "catalog_manifest_group_not_closed",
  );
  if (
    group.name !== THINGS_GROUP_NAME ||
    group.localPath !== THINGS_GROUP_PATH ||
    group.remotePath !== THINGS_GROUP_PATH ||
    group.localResource !== LOCAL_THINGS_RESOURCE ||
    group.remoteResource !== REMOTE_THINGS_RESOURCE ||
    !Array.isArray(group.servers) ||
    canonicalJson(group.servers) !==
      canonicalJson(["things-core", "things-shortcuts", "things-native"])
  ) {
    fail("catalog_manifest_group_mismatch");
  }
  const counts = record(source.counts, "catalog_manifest_counts_invalid");
  exactKeys(
    counts,
    [
      "tools",
      "coreTools",
      "shortcutTools",
      "nativeTools",
      "supaOutcomes",
      "workflows",
      "legacyEvalIds",
      "newEvalIds",
    ],
    [],
    "catalog_manifest_counts_not_closed",
  );
  if (
    counts.tools !== THINGS_TOOL_COUNT ||
    counts.coreTools !== THINGS_SERVER_COUNTS["things-core"] ||
    counts.shortcutTools !== THINGS_SERVER_COUNTS["things-shortcuts"] ||
    counts.nativeTools !== THINGS_SERVER_COUNTS["things-native"] ||
    counts.supaOutcomes !== 37 ||
    counts.workflows !== 17 ||
    counts.legacyEvalIds !== 25 ||
    counts.newEvalIds !== 16
  ) {
    fail("catalog_manifest_counts_mismatch");
  }
  if (!Array.isArray(source.tools) || source.tools.length !== THINGS_TOOL_COUNT) {
    fail("catalog_manifest_tool_count_mismatch");
  }
  const tools = source.tools.map(manifestToolValue);
  const publicNames = new Set(tools.map((tool) => tool.publicToolName));
  const capabilityIds = new Set(
    tools.map((tool) => tool.qualifiedCapabilityId),
  );
  if (
    publicNames.size !== THINGS_TOOL_COUNT ||
    capabilityIds.size !== THINGS_TOOL_COUNT
  ) {
    fail("catalog_manifest_identity_collision");
  }
  return {
    schemaVersion: 1,
    group: {
      name: THINGS_GROUP_NAME,
      localPath: THINGS_GROUP_PATH,
      remotePath: THINGS_GROUP_PATH,
      localResource: LOCAL_THINGS_RESOURCE,
      remoteResource: REMOTE_THINGS_RESOURCE,
      servers: ["things-core", "things-shortcuts", "things-native"],
    },
    counts: {
      tools: THINGS_TOOL_COUNT,
      coreTools: THINGS_SERVER_COUNTS["things-core"],
      shortcutTools: THINGS_SERVER_COUNTS["things-shortcuts"],
      nativeTools: THINGS_SERVER_COUNTS["things-native"],
      supaOutcomes: 37,
      workflows: 17,
      legacyEvalIds: 25,
      newEvalIds: 16,
    },
    tools,
  };
}

function jsonObject(value: unknown, code: string): JsonObject {
  const source = record(value, code);
  canonicalJson(source);
  return source as JsonObject;
}

function closedObjectSchema(
  value: unknown,
  code: string,
): ClosedJsonObjectSchema {
  const schema = jsonObject(value, code);
  if (schema.type !== "object" || schema.additionalProperties !== false) {
    fail("catalog_provider_schema_not_closed");
  }
  return schema as ClosedJsonObjectSchema;
}

function publicToolValue(value: unknown): ThingsPublicTool {
  const source = record(value, "catalog_provider_tool_invalid");
  exactKeys(
    source,
    [
      "name",
      "description",
      "inputSchema",
      "outputSchema",
      "annotations",
      "_meta",
    ],
    [],
    "catalog_provider_tool_not_closed",
  );
  const inputSchema = closedObjectSchema(
    source.inputSchema,
    "catalog_provider_input_schema_invalid",
  );
  const outputSchema = closedObjectSchema(
    source.outputSchema,
    "catalog_provider_output_schema_invalid",
  );
  return {
    name: stringValue(source.name, "catalog_provider_name_invalid"),
    description: stringValue(
      source.description,
      "catalog_provider_description_invalid",
    ),
    inputSchema,
    outputSchema,
    annotations: annotationsValue(source.annotations),
    _meta: jsonObject(source._meta, "catalog_provider_meta_invalid"),
  };
}

function metadataMatches(
  tool: ThingsPublicTool,
  contract: ThingsManifestToolContract,
): boolean {
  const schemes = tool._meta.securitySchemes;
  return (
    tool._meta.thingsMinimumScope === contract.minimumIndependentScope &&
    tool._meta.thingsRisk === contract.risk &&
    tool._meta.thingsSchemaContractId === contract.schemaContractId &&
    Array.isArray(schemes) &&
    schemes.some((entry) => {
      if (!isRecord(entry) || entry.type !== "oauth2") {
        return false;
      }
      return (
        Array.isArray(entry.scopes) &&
        entry.scopes.length === 1 &&
        entry.scopes[0] === contract.minimumIndependentScope
      );
    })
  );
}

function deepFreeze<T>(value: T, seen = new Set<object>()): T {
  if (value === null || typeof value !== "object" || seen.has(value)) {
    return value;
  }
  seen.add(value);
  for (const entry of Object.values(value)) {
    deepFreeze(entry, seen);
  }
  return Object.freeze(value);
}

export function validateThingsCatalog(
  snapshot: ThingsCatalogSnapshot,
  rawProjection: ThingsManifestProjection | unknown,
): ValidatedThingsCatalog {
  const projection = parseThingsManifestProjection(rawProjection);
  if (!Array.isArray(snapshot.tools) || snapshot.tools.length !== THINGS_TOOL_COUNT) {
    fail("catalog_provider_tool_count_mismatch");
  }
  const tools = snapshot.tools.map(publicToolValue);
  const names = new Set(tools.map((tool) => tool.name));
  if (names.size !== THINGS_TOOL_COUNT) {
    fail("catalog_provider_tool_name_collision");
  }
  const toolsByQualifiedName = new Map(
    tools.map((tool) => [tool.name, tool] as const),
  );
  const serverCounts: Record<ThingsServerName, number> = {
    "things-core": 0,
    "things-shortcuts": 0,
    "things-native": 0,
  };
  const canonicalTools: ThingsPublicTool[] = [];
  const routesByName = new Map<string, ValidatedThingsRoute>();
  for (const contract of projection.tools) {
    const tool = toolsByQualifiedName.get(
      contract.expectedMcphubQualifiedName,
    );
    if (tool === undefined) {
      fail("catalog_provider_tool_missing");
    }
    if (
      tool.name !== contract.publicToolName ||
      canonicalJson(tool.annotations) !== canonicalJson(contract.annotations) ||
      canonicalSha256(tool.inputSchema) !==
        contract.adaptedSchemaHashes.inputSchemaSha256 ||
      canonicalSha256(tool.outputSchema) !==
        contract.adaptedSchemaHashes.outputSchemaSha256 ||
      !metadataMatches(tool, contract)
    ) {
      fail(`catalog_provider_tool_mismatch:${contract.publicToolName}`);
    }
    serverCounts[contract.server] += 1;
    canonicalTools.push(tool);
    routesByName.set(contract.publicToolName, { contract, tool });
  }
  if (
    Object.entries(THINGS_SERVER_COUNTS).some(
      ([server, count]) =>
        serverCounts[server as ThingsServerName] !== count,
    )
  ) {
    fail("catalog_provider_server_count_mismatch");
  }

  const frozenTools = deepFreeze(canonicalTools);
  const frozenRoutes = new Map(
    [...routesByName.entries()].map(([name, route]) => [
      name,
      deepFreeze(route),
    ]),
  );
  return {
    tools: frozenTools,
    routesByName: frozenRoutes,
    serverCounts: deepFreeze(serverCounts),
    catalogSha256: canonicalSha256(frozenTools),
    scopeMapSha256: canonicalSha256(
      projection.tools.map((tool) => ({
        name: tool.publicToolName,
        minimumScope: tool.minimumIndependentScope,
      })),
    ),
    manifestProjectionSha256: canonicalSha256(projection),
  };
}
