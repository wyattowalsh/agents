import { readFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import type {
  AuthInfo,
  CallToolResult,
  McpHandlerRequestOptions,
} from "@modelcontextprotocol/server";

import {
  CLIENT_CAPABILITIES_META_KEY,
  CLIENT_INFO_META_KEY,
  LOCAL_THINGS_RESOURCE,
  LOCAL_THINGS_CREDENTIAL_CLASS,
  MCP_METHOD_HEADER,
  MCP_NAME_HEADER,
  MCP_PROTOCOL_VERSION_HEADER,
  MODERN_PROTOCOL_VERSION,
  REMOTE_THINGS_CREDENTIAL_CLASS,
  REMOTE_THINGS_RESOURCE,
  PROTOCOL_VERSION_META_KEY,
  canonicalSha256,
  parseThingsManifestProjection,
  type JsonObject,
  type ThingsCatalogSnapshot,
  type ThingsManifestProjection,
  type ThingsManifestToolContract,
  type ThingsProviderCall,
  type ThingsPublicTool,
  type ThingsToolProvider,
} from "../../src/protocol/index.js";

const CAPABILITY_MANIFEST_RELATIVE_PATH =
  "openspec/changes/replace-supathings-with-things-plus-plus/capability-manifest.json";

export async function readCapabilityManifest(): Promise<Record<string, unknown>> {
  const sourceDirectory = dirname(fileURLToPath(import.meta.url));
  const candidates = [
    resolve(process.cwd(), CAPABILITY_MANIFEST_RELATIVE_PATH),
    resolve(process.cwd(), "../../..", CAPABILITY_MANIFEST_RELATIVE_PATH),
    resolve(sourceDirectory, "../../../../..", CAPABILITY_MANIFEST_RELATIVE_PATH),
    resolve(sourceDirectory, "../../../../../..", CAPABILITY_MANIFEST_RELATIVE_PATH),
  ];
  for (const candidate of new Set(candidates)) {
    try {
      return JSON.parse(await readFile(candidate, "utf8")) as Record<
        string,
        unknown
      >;
    } catch (error) {
      if (
        error === null ||
        typeof error !== "object" ||
        !("code" in error) ||
        error.code !== "ENOENT"
      ) {
        throw error;
      }
    }
  }
  throw new Error("capability_manifest_not_found");
}

interface SyntheticContract {
  readonly projection: ThingsManifestProjection;
  readonly snapshot: ThingsCatalogSnapshot;
}

function objectSchema(index: number, output: boolean): JsonObject {
  return {
    type: "object",
    additionalProperties: false,
    properties: output
      ? { ok: { type: "boolean" } }
      : { probe: { type: "integer", const: index } },
  };
}

function publicTool(
  contract: ThingsManifestToolContract,
  index: number,
): ThingsPublicTool {
  const inputSchema = objectSchema(index, false);
  const outputSchema = objectSchema(index, true);
  return {
    name: contract.publicToolName,
    description: `Synthetic conformance tool ${index}`,
    inputSchema: {
      ...inputSchema,
      type: "object",
      additionalProperties: false,
    },
    outputSchema: {
      ...outputSchema,
      type: "object",
      additionalProperties: false,
    },
    annotations: contract.annotations,
    _meta: {
      thingsMinimumScope: contract.minimumIndependentScope,
      thingsRisk: contract.risk,
      thingsSchemaContractId: contract.schemaContractId,
      securitySchemes: [
        {
          type: "oauth2",
          scopes: [contract.minimumIndependentScope],
        },
      ],
    },
  };
}

export async function makeSyntheticContract(): Promise<SyntheticContract> {
  const manifest = await readCapabilityManifest();
  const group = manifest.group as Record<string, unknown>;
  const counts = manifest.counts as Record<string, unknown>;
  const rows = manifest.tools as Array<Record<string, unknown>>;
  const seedProjection = parseThingsManifestProjection({
    schemaVersion: 1,
    group: {
      name: group.name,
      localPath: group.localPath,
      remotePath: group.remotePath,
      localResource: group.localResource,
      remoteResource: group.remoteResource,
      servers: group.servers,
    },
    counts: {
      tools: counts.tools,
      coreTools: counts.coreTools,
      shortcutTools: counts.shortcutTools,
      nativeTools: counts.nativeTools,
      supaOutcomes: counts.supaOutcomes,
      workflows: counts.workflows,
      legacyEvalIds: counts.legacyEvalIds,
      newEvalIds: counts.newEvalIds,
    },
    tools: rows.map((candidate) => ({
      server: candidate.server,
      serverToolName: candidate.serverToolName,
      publicToolName: candidate.publicToolName,
      expectedMcphubQualifiedName: candidate.expectedMcphubQualifiedName,
      qualifiedCapabilityId: candidate.qualifiedCapabilityId,
      minimumIndependentScope: candidate.minimumIndependentScope,
      risk: candidate.risk,
      annotations: candidate.annotations,
      schemaContractId: candidate.schemaContractId,
      ...(candidate.auditedUpstreamSchemaHashes === undefined
        ? {}
        : {
            auditedUpstreamSchemaHashes:
              candidate.auditedUpstreamSchemaHashes,
          }),
      backendPrerequisites: candidate.backendPrerequisites,
      implementationKind: candidate.implementationKind,
      testIds: candidate.testIds,
      adaptedSchemaHashes: {
        inputSchemaSha256: "0".repeat(64),
        outputSchemaSha256: "0".repeat(64),
        status: "frozen",
      },
    })),
  });
  const tools = rows.map((row, index) => {
    const contract = seedProjection.tools[index];
    if (contract === undefined) {
      throw new Error("synthetic_contract_row_missing");
    }
    const tool = publicTool(contract, index);
    return {
      tool,
      contract: {
        ...contract,
        adaptedSchemaHashes: {
          inputSchemaSha256: canonicalSha256(tool.inputSchema),
          outputSchemaSha256: canonicalSha256(tool.outputSchema),
          status: "frozen" as const,
        },
      },
    };
  });
  const projection = parseThingsManifestProjection({
    schemaVersion: 1,
    group: {
      name: group.name,
      localPath: group.localPath,
      remotePath: group.remotePath,
      localResource: group.localResource,
      remoteResource: group.remoteResource,
      servers: group.servers,
    },
    counts: {
      tools: counts.tools,
      coreTools: counts.coreTools,
      shortcutTools: counts.shortcutTools,
      nativeTools: counts.nativeTools,
      supaOutcomes: counts.supaOutcomes,
      workflows: counts.workflows,
      legacyEvalIds: counts.legacyEvalIds,
      newEvalIds: counts.newEvalIds,
    },
    tools: tools.map((entry) => entry.contract),
  });
  return {
    projection,
    snapshot: { tools: tools.map((entry) => entry.tool) },
  };
}

export class RecordingProvider implements ThingsToolProvider {
  public readonly calls: ThingsProviderCall[] = [];

  public constructor(
    private readonly value: ThingsCatalogSnapshot,
    private readonly result: CallToolResult = {
      content: [{ type: "text", text: "ok" }],
      structuredContent: { ok: true },
    },
  ) {}

  public async snapshot(): Promise<ThingsCatalogSnapshot> {
    return this.value;
  }

  public async call(request: ThingsProviderCall): Promise<CallToolResult> {
    this.calls.push(request);
    return this.result;
  }
}

export function modernBody(
  id: number,
  method: string,
  params: Readonly<Record<string, unknown>> = {},
): Record<string, unknown> {
  const existingMeta =
    params._meta !== null &&
    typeof params._meta === "object" &&
    !Array.isArray(params._meta)
      ? (params._meta as Readonly<Record<string, unknown>>)
      : {};
  return {
    jsonrpc: "2.0",
    id,
    method,
    params: {
      ...params,
      _meta: {
        ...existingMeta,
        [PROTOCOL_VERSION_META_KEY]: MODERN_PROTOCOL_VERSION,
        [CLIENT_CAPABILITIES_META_KEY]: {},
        [CLIENT_INFO_META_KEY]: {
          name: "things-conformance",
          version: "1.0.0",
        },
      },
    },
  };
}

export function modernRequest(
  body: Readonly<Record<string, unknown>>,
  headerOverrides: Readonly<Record<string, string>> = {},
): Request {
  const method = body.method;
  if (typeof method !== "string") {
    throw new Error("modern_request_method_missing");
  }
  const params = body.params as Readonly<Record<string, unknown>> | undefined;
  const headers: Record<string, string> = {
    "content-type": "application/json",
    [MCP_PROTOCOL_VERSION_HEADER]: MODERN_PROTOCOL_VERSION,
    [MCP_METHOD_HEADER]: method,
  };
  if (method === "tools/call") {
    const name = params?.name;
    if (typeof name !== "string") {
      throw new Error("modern_request_name_missing");
    }
    headers[MCP_NAME_HEADER] = name;
  }
  Object.assign(headers, headerOverrides);
  return new Request(LOCAL_THINGS_RESOURCE, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
}

export function legacyRequest(
  body: Readonly<Record<string, unknown>>,
): Request {
  return new Request(LOCAL_THINGS_RESOURCE, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      accept: "application/json, text/event-stream",
      [MCP_PROTOCOL_VERSION_HEADER]: "2025-11-25",
    },
    body: JSON.stringify(body),
  });
}

export function authOptions(
  scopes: readonly string[] = [
    "things.read",
    "things.write",
    "things.admin",
  ],
  overrides: {
    readonly token?: string;
    readonly clientId?: string;
    readonly resource?: string;
    readonly principal?: string;
    readonly credentialClass?: string;
  } = {},
): McpHandlerRequestOptions {
  const resource = overrides.resource ?? LOCAL_THINGS_RESOURCE;
  const credentialClass =
    overrides.credentialClass ??
    (resource === REMOTE_THINGS_RESOURCE
      ? REMOTE_THINGS_CREDENTIAL_CLASS
      : LOCAL_THINGS_CREDENTIAL_CLASS);
  const authInfo: AuthInfo = {
    token: overrides.token ?? "opaque-test-token",
    clientId: overrides.clientId ?? "things-conformance-client",
    scopes: [...scopes],
    resource: new URL(resource),
    extra: {
      principal: overrides.principal ?? "subject:test",
      credentialClass,
    },
  };
  return { authInfo };
}

export async function responseJson(
  response: Response,
): Promise<Record<string, unknown>> {
  const text = await response.text();
  if (response.headers.get("content-type")?.includes("text/event-stream")) {
    const data = text
      .split("\n")
      .filter((line) => line.startsWith("data:"))
      .map((line) => line.slice("data:".length).trim())
      .at(-1);
    if (data === undefined) {
      throw new Error("sse_response_missing_data");
    }
    return JSON.parse(data) as Record<string, unknown>;
  }
  return JSON.parse(text) as Record<string, unknown>;
}
