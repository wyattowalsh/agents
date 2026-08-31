import type {
  AuthInfo,
  McpHandlerRequestOptions,
} from "@modelcontextprotocol/server";

import {
  hasExactCatalogScopes,
  protocolAuthIdentity,
} from "./authorization.js";
import { canonicalJson, canonicalSha256 } from "./canonical-json.js";
import {
  CLIENT_CAPABILITIES_META_KEY,
  CLIENT_INFO_META_KEY,
  DEFAULT_CACHE_HINT,
  LEGACY_PROTOCOL_VERSION,
  LOCAL_THINGS_CREDENTIAL_CLASS,
  LOCAL_THINGS_RESOURCE,
  MCP_METHOD_HEADER,
  MCP_NAME_HEADER,
  MCP_PROTOCOL_VERSION_HEADER,
  MODERN_PROTOCOL_VERSION,
  PROTOCOL_VERSION_META_KEY,
  REMOTE_THINGS_CREDENTIAL_CLASS,
  THINGS_TOOL_COUNT,
} from "./constants.js";
import { protocolDispatchSnapshot } from "./dispatch-observer.js";
import {
  HEADER_MISMATCH,
  INVALID_PARAMS,
  INVALID_REQUEST,
  METHOD_NOT_FOUND,
  MISSING_REQUIRED_CLIENT_CAPABILITY,
  PARSE_ERROR,
  UNSUPPORTED_PROTOCOL_VERSION,
} from "./errors.js";
import type {
  ProtocolConformanceCaseId,
  ProtocolConformanceCaseResult,
  ProtocolConformanceReport,
  ThingsProtocolHandler,
  ValidatedThingsCatalog,
  ValidatedThingsRoute,
} from "./types.js";

export const PROTOCOL_CONFORMANCE_CASE_IDS = [
  "modern-discover",
  "modern-list",
  "modern-call",
  "legacy-initialize",
  "legacy-list",
  "auth-absent-modern",
  "auth-absent-legacy",
  "scope-missing",
  "scope-extra",
  "resource-mismatch",
  "credential-class-mismatch",
  "principal-invalid",
  "client-invalid",
  "session-id-forbidden",
  "last-event-id-forbidden",
  "get-method-forbidden",
  "method-mismatch",
  "name-mismatch",
  "missing-client-capabilities",
  "unsupported-version",
  "unknown-modern-method",
  "parse-error",
] as const satisfies readonly ProtocolConformanceCaseId[];

export const FROZEN_ERROR_MATRIX_CASES = [
  {
    id: "method-mismatch",
    status: 400,
    code: HEADER_MISMATCH,
    sdkDispatch: false,
    providerDispatch: false,
  },
  {
    id: "name-mismatch",
    status: 400,
    code: HEADER_MISMATCH,
    sdkDispatch: false,
    providerDispatch: false,
  },
  {
    id: "missing-client-capabilities",
    status: 400,
    code: MISSING_REQUIRED_CLIENT_CAPABILITY,
    sdkDispatch: false,
    providerDispatch: false,
  },
  {
    id: "unsupported-version",
    status: 400,
    code: UNSUPPORTED_PROTOCOL_VERSION,
    sdkDispatch: false,
    providerDispatch: false,
  },
  {
    id: "unknown-modern-method",
    status: 404,
    code: METHOD_NOT_FOUND,
    sdkDispatch: true,
    providerDispatch: false,
  },
  {
    id: "parse-error",
    status: 400,
    code: PARSE_ERROR,
    sdkDispatch: false,
    providerDispatch: false,
  },
] as const;

interface CaseDefinition {
  readonly id: ProtocolConformanceCaseId;
  readonly request: () => Request;
  readonly requestOptions?: McpHandlerRequestOptions;
  readonly expectedHttpStatus: number;
  readonly expectedJsonRpcCode: number | null;
  readonly expectedSdkDispatchCount: number;
  readonly expectedProviderDispatchCount: number;
  readonly validate: (body: Record<string, unknown>) => void;
}

interface ExecutedCase {
  readonly result: ProtocolConformanceCaseResult;
  readonly body: Record<string, unknown>;
}

export class ProtocolConformanceError extends Error {
  public constructor(public readonly code: string) {
    super(code);
    this.name = "ProtocolConformanceError";
  }
}

function fail(code: string): never {
  throw new ProtocolConformanceError(code);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function modernBody(
  id: number,
  method: string,
  params: Readonly<Record<string, unknown>> = {},
): Record<string, unknown> {
  return {
    jsonrpc: "2.0",
    id,
    method,
    params: {
      ...params,
      _meta: {
        [PROTOCOL_VERSION_META_KEY]: MODERN_PROTOCOL_VERSION,
        [CLIENT_CAPABILITIES_META_KEY]: {},
        [CLIENT_INFO_META_KEY]: {
          name: "things-protocol-conformance",
          version: "1.0.0",
        },
      },
    },
  };
}

function modernRequest(
  body: Readonly<Record<string, unknown>>,
  headerOverrides: Readonly<Record<string, string>> = {},
): Request {
  const method = body.method;
  if (typeof method !== "string") {
    fail("protocol_conformance_modern_method_missing");
  }
  const headers: Record<string, string> = {
    "content-type": "application/json",
    [MCP_PROTOCOL_VERSION_HEADER]: MODERN_PROTOCOL_VERSION,
    [MCP_METHOD_HEADER]: method,
  };
  if (method === "tools/call") {
    const params = isRecord(body.params) ? body.params : undefined;
    if (typeof params?.name !== "string") {
      fail("protocol_conformance_modern_name_missing");
    }
    headers[MCP_NAME_HEADER] = params.name;
  }
  Object.assign(headers, headerOverrides);
  return new Request(LOCAL_THINGS_RESOURCE, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
}

function legacyRequest(id: number, method: "initialize" | "tools/list"): Request {
  const params =
    method === "initialize"
      ? {
          protocolVersion: LEGACY_PROTOCOL_VERSION,
          capabilities: {},
          clientInfo: {
            name: "things-protocol-conformance-legacy",
            version: "1.0.0",
          },
        }
      : {};
  return new Request(LOCAL_THINGS_RESOURCE, {
    method: "POST",
    headers: {
      accept: "application/json, text/event-stream",
      "content-type": "application/json",
      [MCP_PROTOCOL_VERSION_HEADER]: LEGACY_PROTOCOL_VERSION,
    },
    body: JSON.stringify({ jsonrpc: "2.0", id, method, params }),
  });
}

async function responseBody(
  response: Response,
  code: string,
): Promise<Record<string, unknown>> {
  if (response.headers.has("mcp-session-id")) {
    fail(code);
  }
  const text = await response.text();
  const encoded = response.headers
    .get("content-type")
    ?.includes("text/event-stream")
    ? text
        .split("\n")
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice("data:".length).trim())
        .at(-1)
    : text;
  if (encoded === undefined) {
    fail(code);
  }
  let body: unknown;
  try {
    body = JSON.parse(encoded);
  } catch {
    fail(code);
  }
  return isRecord(body) ? body : fail(code);
}

function resultOf(
  body: Record<string, unknown>,
  code: string,
): Record<string, unknown> {
  return isRecord(body.result) && body.error === undefined
    ? body.result
    : fail(code);
}

function errorCodeOf(body: Record<string, unknown>): number | null {
  if (body.error === undefined) {
    return null;
  }
  if (!isRecord(body.error) || typeof body.error.code !== "number") {
    fail("protocol_conformance_error_shape_invalid");
  }
  return body.error.code;
}

function exactModernCacheEnvelope(result: Record<string, unknown>): boolean {
  return (
    result.resultType === "complete" &&
    result.ttlMs === DEFAULT_CACHE_HINT.ttlMs &&
    result.cacheScope === DEFAULT_CACHE_HINT.cacheScope
  );
}

function authInfoWith(
  base: AuthInfo,
  overrides: {
    readonly token?: string;
    readonly clientId?: string;
    readonly scopes?: readonly string[];
    readonly resource?: string;
    readonly principal?: string;
    readonly credentialClass?: string;
  },
): McpHandlerRequestOptions {
  const resource =
    overrides.resource === undefined
      ? base.resource
      : new URL(overrides.resource);
  if (resource === undefined) {
    fail("protocol_conformance_auth_resource_missing");
  }
  return {
    authInfo: {
      ...base,
      token: overrides.token ?? base.token,
      clientId: overrides.clientId ?? base.clientId,
      scopes: [...(overrides.scopes ?? base.scopes)],
      resource,
      extra: {
        ...base.extra,
        principal: overrides.principal ?? base.extra?.principal,
        credentialClass:
          overrides.credentialClass ?? base.extra?.credentialClass,
      },
    },
  };
}

function exactAuthInfo(
  requestOptions: McpHandlerRequestOptions | undefined,
): AuthInfo {
  const identity = protocolAuthIdentity(requestOptions?.authInfo);
  if (identity === undefined || !hasExactCatalogScopes(identity)) {
    fail("protocol_conformance_auth_context_invalid");
  }
  return identity.authInfo;
}

function selectConformanceRoute(
  catalog: ValidatedThingsCatalog,
): ValidatedThingsRoute {
  const route = catalog.routesByName.get(
    "things_core__get_server_capabilities",
  );
  const required = route?.tool.inputSchema.required;
  if (
    route !== undefined &&
    route.contract.minimumIndependentScope === "things.read" &&
    route.tool.annotations.readOnlyHint &&
    (required === undefined ||
      (Array.isArray(required) && required.length === 0))
  ) {
    return route;
  }
  return fail("protocol_conformance_safe_call_route_missing");
}

function expectSuccess(body: Record<string, unknown>): void {
  if (body.jsonrpc !== "2.0" || body.error !== undefined || !isRecord(body.result)) {
    fail("protocol_conformance_success_shape_invalid");
  }
}

function expectError(body: Record<string, unknown>): void {
  if (body.jsonrpc !== "2.0" || !isRecord(body.error) || body.result !== undefined) {
    fail("protocol_conformance_error_shape_invalid");
  }
}

async function executeCase(
  handler: ThingsProtocolHandler,
  definition: CaseDefinition,
): Promise<ExecutedCase> {
  const before = protocolDispatchSnapshot(handler);
  const response = await handler.fetch(
    definition.request(),
    definition.requestOptions,
  );
  const body = await responseBody(
    response,
    `protocol_conformance_${definition.id}_response_invalid`,
  );
  const after = protocolDispatchSnapshot(handler);
  const sdkDispatchCount = after.sdk - before.sdk;
  const providerDispatchCount = after.provider - before.provider;
  const jsonRpcCode = errorCodeOf(body);
  if (
    response.status !== definition.expectedHttpStatus ||
    jsonRpcCode !== definition.expectedJsonRpcCode ||
    sdkDispatchCount !== definition.expectedSdkDispatchCount ||
    providerDispatchCount !== definition.expectedProviderDispatchCount
  ) {
    fail(`protocol_conformance_${definition.id}_outcome_mismatch`);
  }
  definition.validate(body);
  return {
    body,
    result: {
      id: definition.id,
      status: "passed",
      httpStatus: response.status,
      jsonRpcCode,
      sdkDispatchCount,
      providerDispatchCount,
      resultSha256: canonicalSha256({
        httpStatus: response.status,
        body,
      }),
    },
  };
}

function buildProtocolConformanceReport(
  catalog: ValidatedThingsCatalog,
  cases: readonly ProtocolConformanceCaseResult[],
): ProtocolConformanceReport {
  if (
    catalog.tools.length !== THINGS_TOOL_COUNT ||
    canonicalJson(cases.map((entry) => entry.id)) !==
      canonicalJson(PROTOCOL_CONFORMANCE_CASE_IDS) ||
    cases.some((entry) => entry.status !== "passed")
  ) {
    fail("protocol_conformance_execution_incomplete");
  }
  const errorMatrixResults = FROZEN_ERROR_MATRIX_CASES.map((expected) => {
    const actual = cases.find((entry) => entry.id === expected.id);
    if (
      actual === undefined ||
      actual.httpStatus !== expected.status ||
      actual.jsonRpcCode !== expected.code ||
      actual.sdkDispatchCount !== Number(expected.sdkDispatch) ||
      actual.providerDispatchCount !== Number(expected.providerDispatch)
    ) {
      fail("protocol_conformance_error_matrix_mismatch");
    }
    return {
      id: actual.id,
      httpStatus: actual.httpStatus,
      jsonRpcCode: actual.jsonRpcCode,
      sdkDispatchCount: actual.sdkDispatchCount,
      providerDispatchCount: actual.providerDispatchCount,
    };
  });
  const sdkDispatchCount = cases.reduce(
    (total, entry) => total + entry.sdkDispatchCount,
    0,
  );
  const providerDispatchCount = cases.reduce(
    (total, entry) => total + entry.providerDispatchCount,
    0,
  );
  if (sdkDispatchCount !== 6 || providerDispatchCount !== 1) {
    fail("protocol_conformance_dispatch_totals_mismatch");
  }
  return {
    schemaVersion: 1,
    protocol: {
      modern: MODERN_PROTOCOL_VERSION,
      legacy: LEGACY_PROTOCOL_VERSION,
      discoverySupportedVersions: [MODERN_PROTOCOL_VERSION],
      stateless: true,
      sessionsAccepted: false,
      getStreamAccepted: false,
    },
    catalog: {
      toolCount: THINGS_TOOL_COUNT,
      serverCounts: catalog.serverCounts,
      catalogSha256: catalog.catalogSha256,
      scopeMapSha256: catalog.scopeMapSha256,
      manifestProjectionSha256: catalog.manifestProjectionSha256,
    },
    isolation: {
      publicSdkPackage: "@modelcontextprotocol/server",
      publicSdkVersion: "2.0.0",
      privateV1ImportsInProtocol: 0,
    },
    execution: {
      status: "passed",
      caseCount: 22,
      passedCaseCount: 22,
      caseIds: [...PROTOCOL_CONFORMANCE_CASE_IDS],
      cases: [...cases],
      sdkDispatchCount,
      providerDispatchCount,
      errorMatrixSha256: canonicalSha256({
        schemaVersion: 1,
        cases: FROZEN_ERROR_MATRIX_CASES,
      }),
      errorMatrixResultsSha256: canonicalSha256(errorMatrixResults),
      resultBundleSha256: canonicalSha256(cases),
    },
  };
}

export async function runDualEraProtocolConformance(
  handler: ThingsProtocolHandler,
  requestOptions?: McpHandlerRequestOptions,
): Promise<ProtocolConformanceReport> {
  const baseAuth = exactAuthInfo(requestOptions);
  const exactOptions = authInfoWith(baseAuth, {});
  const safeRoute = selectConformanceRoute(handler.catalog);
  const callBody = modernBody(3, "tools/call", {
    name: safeRoute.contract.publicToolName,
    arguments: {},
  });
  const callOptions = authInfoWith(baseAuth, {
    scopes: [safeRoute.contract.minimumIndependentScope],
  });
  let modernTools: unknown;
  let legacyTools: unknown;
  const missingCapabilitiesBody = modernBody(19, "tools/list");
  const missingCapabilitiesParams = missingCapabilitiesBody.params;
  if (!isRecord(missingCapabilitiesParams) || !isRecord(missingCapabilitiesParams._meta)) {
    fail("protocol_conformance_missing_capabilities_fixture_invalid");
  }
  delete missingCapabilitiesParams._meta[CLIENT_CAPABILITIES_META_KEY];
  const unsupportedBody = modernBody(20, "tools/list");
  const unsupportedParams = unsupportedBody.params;
  if (!isRecord(unsupportedParams) || !isRecord(unsupportedParams._meta)) {
    fail("protocol_conformance_unsupported_fixture_invalid");
  }
  unsupportedParams._meta[PROTOCOL_VERSION_META_KEY] = "2099-01-01";
  const oppositeCredentialClass =
    baseAuth.extra?.credentialClass === LOCAL_THINGS_CREDENTIAL_CLASS
      ? REMOTE_THINGS_CREDENTIAL_CLASS
      : LOCAL_THINGS_CREDENTIAL_CLASS;

  const definitions: readonly CaseDefinition[] = [
    {
      id: "modern-discover",
      request: () => modernRequest(modernBody(1, "server/discover")),
      requestOptions: exactOptions,
      expectedHttpStatus: 200,
      expectedJsonRpcCode: null,
      expectedSdkDispatchCount: 1,
      expectedProviderDispatchCount: 0,
      validate(body) {
        expectSuccess(body);
        const result = resultOf(body, "protocol_conformance_modern_discover_failed");
        if (
          canonicalJson(result.supportedVersions) !==
            canonicalJson([MODERN_PROTOCOL_VERSION]) ||
          canonicalJson(result.capabilities) !== canonicalJson({ tools: {} }) ||
          !exactModernCacheEnvelope(result)
        ) {
          fail("protocol_conformance_modern_discover_mismatch");
        }
      },
    },
    {
      id: "modern-list",
      request: () => modernRequest(modernBody(2, "tools/list")),
      requestOptions: exactOptions,
      expectedHttpStatus: 200,
      expectedJsonRpcCode: null,
      expectedSdkDispatchCount: 1,
      expectedProviderDispatchCount: 0,
      validate(body) {
        expectSuccess(body);
        const result = resultOf(body, "protocol_conformance_modern_list_failed");
        if (!exactModernCacheEnvelope(result)) {
          fail("protocol_conformance_modern_list_envelope_mismatch");
        }
        modernTools = result.tools;
      },
    },
    {
      id: "modern-call",
      request: () => modernRequest(callBody),
      requestOptions: callOptions,
      expectedHttpStatus: 200,
      expectedJsonRpcCode: null,
      expectedSdkDispatchCount: 1,
      expectedProviderDispatchCount: 1,
      validate: expectSuccess,
    },
    {
      id: "legacy-initialize",
      request: () => legacyRequest(4, "initialize"),
      requestOptions: exactOptions,
      expectedHttpStatus: 200,
      expectedJsonRpcCode: null,
      expectedSdkDispatchCount: 1,
      expectedProviderDispatchCount: 0,
      validate(body) {
        expectSuccess(body);
        const result = resultOf(body, "protocol_conformance_legacy_initialize_failed");
        if (result.protocolVersion !== LEGACY_PROTOCOL_VERSION) {
          fail("protocol_conformance_legacy_initialize_mismatch");
        }
      },
    },
    {
      id: "legacy-list",
      request: () => legacyRequest(5, "tools/list"),
      requestOptions: exactOptions,
      expectedHttpStatus: 200,
      expectedJsonRpcCode: null,
      expectedSdkDispatchCount: 1,
      expectedProviderDispatchCount: 0,
      validate(body) {
        expectSuccess(body);
        const result = resultOf(body, "protocol_conformance_legacy_list_failed");
        if (
          result.resultType !== undefined ||
          result.ttlMs !== undefined ||
          result.cacheScope !== undefined
        ) {
          fail("protocol_conformance_legacy_envelope_mismatch");
        }
        legacyTools = result.tools;
      },
    },
    {
      id: "auth-absent-modern",
      request: () => modernRequest(modernBody(6, "server/discover")),
      expectedHttpStatus: 403,
      expectedJsonRpcCode: INVALID_PARAMS,
      expectedSdkDispatchCount: 0,
      expectedProviderDispatchCount: 0,
      validate: expectError,
    },
    {
      id: "auth-absent-legacy",
      request: () => legacyRequest(7, "initialize"),
      expectedHttpStatus: 403,
      expectedJsonRpcCode: INVALID_PARAMS,
      expectedSdkDispatchCount: 0,
      expectedProviderDispatchCount: 0,
      validate: expectError,
    },
    {
      id: "scope-missing",
      request: () => modernRequest(modernBody(8, "tools/list")),
      requestOptions: authInfoWith(baseAuth, {
        scopes: ["things.read", "things.write"],
      }),
      expectedHttpStatus: 403,
      expectedJsonRpcCode: INVALID_PARAMS,
      expectedSdkDispatchCount: 0,
      expectedProviderDispatchCount: 0,
      validate: expectError,
    },
    {
      id: "scope-extra",
      request: () => legacyRequest(9, "tools/list"),
      requestOptions: authInfoWith(baseAuth, {
        scopes: [
          "things.read",
          "things.write",
          "things.admin",
          "things.extra",
        ],
      }),
      expectedHttpStatus: 403,
      expectedJsonRpcCode: INVALID_PARAMS,
      expectedSdkDispatchCount: 0,
      expectedProviderDispatchCount: 0,
      validate: expectError,
    },
    {
      id: "resource-mismatch",
      request: () => modernRequest(modernBody(10, "server/discover")),
      requestOptions: authInfoWith(baseAuth, {
        resource: "https://example.invalid/mcp/things",
      }),
      expectedHttpStatus: 403,
      expectedJsonRpcCode: INVALID_PARAMS,
      expectedSdkDispatchCount: 0,
      expectedProviderDispatchCount: 0,
      validate: expectError,
    },
    {
      id: "credential-class-mismatch",
      request: () => legacyRequest(11, "initialize"),
      requestOptions: authInfoWith(baseAuth, {
        credentialClass: oppositeCredentialClass,
      }),
      expectedHttpStatus: 403,
      expectedJsonRpcCode: INVALID_PARAMS,
      expectedSdkDispatchCount: 0,
      expectedProviderDispatchCount: 0,
      validate: expectError,
    },
    {
      id: "principal-invalid",
      request: () => modernRequest(modernBody(12, "tools/list")),
      requestOptions: authInfoWith(baseAuth, { principal: "" }),
      expectedHttpStatus: 403,
      expectedJsonRpcCode: INVALID_PARAMS,
      expectedSdkDispatchCount: 0,
      expectedProviderDispatchCount: 0,
      validate: expectError,
    },
    {
      id: "client-invalid",
      request: () => legacyRequest(13, "tools/list"),
      requestOptions: authInfoWith(baseAuth, { clientId: "" }),
      expectedHttpStatus: 403,
      expectedJsonRpcCode: INVALID_PARAMS,
      expectedSdkDispatchCount: 0,
      expectedProviderDispatchCount: 0,
      validate: expectError,
    },
    {
      id: "session-id-forbidden",
      request: () =>
        modernRequest(modernBody(14, "tools/list"), {
          "mcp-session-id": "forbidden",
        }),
      requestOptions: exactOptions,
      expectedHttpStatus: 400,
      expectedJsonRpcCode: HEADER_MISMATCH,
      expectedSdkDispatchCount: 0,
      expectedProviderDispatchCount: 0,
      validate: expectError,
    },
    {
      id: "last-event-id-forbidden",
      request: () =>
        modernRequest(modernBody(15, "tools/list"), {
          "last-event-id": "forbidden",
        }),
      requestOptions: exactOptions,
      expectedHttpStatus: 400,
      expectedJsonRpcCode: HEADER_MISMATCH,
      expectedSdkDispatchCount: 0,
      expectedProviderDispatchCount: 0,
      validate: expectError,
    },
    {
      id: "get-method-forbidden",
      request: () => new Request(LOCAL_THINGS_RESOURCE),
      requestOptions: exactOptions,
      expectedHttpStatus: 405,
      expectedJsonRpcCode: INVALID_REQUEST,
      expectedSdkDispatchCount: 0,
      expectedProviderDispatchCount: 0,
      validate: expectError,
    },
    {
      id: "method-mismatch",
      request: () =>
        modernRequest(modernBody(17, "server/discover"), {
          [MCP_METHOD_HEADER]: "tools/list",
        }),
      requestOptions: exactOptions,
      expectedHttpStatus: 400,
      expectedJsonRpcCode: HEADER_MISMATCH,
      expectedSdkDispatchCount: 0,
      expectedProviderDispatchCount: 0,
      validate: expectError,
    },
    {
      id: "name-mismatch",
      request: () =>
        modernRequest(callBody, {
          [MCP_NAME_HEADER]: "things_core__wrong",
        }),
      requestOptions: callOptions,
      expectedHttpStatus: 400,
      expectedJsonRpcCode: HEADER_MISMATCH,
      expectedSdkDispatchCount: 0,
      expectedProviderDispatchCount: 0,
      validate: expectError,
    },
    {
      id: "missing-client-capabilities",
      request: () => modernRequest(missingCapabilitiesBody),
      requestOptions: exactOptions,
      expectedHttpStatus: 400,
      expectedJsonRpcCode: MISSING_REQUIRED_CLIENT_CAPABILITY,
      expectedSdkDispatchCount: 0,
      expectedProviderDispatchCount: 0,
      validate: expectError,
    },
    {
      id: "unsupported-version",
      request: () =>
        modernRequest(unsupportedBody, {
          [MCP_PROTOCOL_VERSION_HEADER]: "2099-01-01",
        }),
      requestOptions: exactOptions,
      expectedHttpStatus: 400,
      expectedJsonRpcCode: UNSUPPORTED_PROTOCOL_VERSION,
      expectedSdkDispatchCount: 0,
      expectedProviderDispatchCount: 0,
      validate: expectError,
    },
    {
      id: "unknown-modern-method",
      request: () => modernRequest(modernBody(21, "things/unknown")),
      requestOptions: exactOptions,
      expectedHttpStatus: 404,
      expectedJsonRpcCode: METHOD_NOT_FOUND,
      expectedSdkDispatchCount: 1,
      expectedProviderDispatchCount: 0,
      validate: expectError,
    },
    {
      id: "parse-error",
      request: () =>
        new Request(LOCAL_THINGS_RESOURCE, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: "{",
        }),
      requestOptions: exactOptions,
      expectedHttpStatus: 400,
      expectedJsonRpcCode: PARSE_ERROR,
      expectedSdkDispatchCount: 0,
      expectedProviderDispatchCount: 0,
      validate: expectError,
    },
  ];

  if (
    canonicalJson(definitions.map((entry) => entry.id)) !==
    canonicalJson(PROTOCOL_CONFORMANCE_CASE_IDS)
  ) {
    fail("protocol_conformance_case_universe_mismatch");
  }
  const executed: ExecutedCase[] = [];
  for (const definition of definitions) {
    executed.push(await executeCase(handler, definition));
  }
  if (
    canonicalJson(modernTools) !== canonicalJson(legacyTools) ||
    canonicalJson(modernTools) !== canonicalJson(handler.catalog.tools)
  ) {
    fail("protocol_conformance_catalog_mismatch");
  }
  return buildProtocolConformanceReport(
    handler.catalog,
    executed.map((entry) => entry.result),
  );
}
