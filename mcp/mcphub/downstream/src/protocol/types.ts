import type {
  AuthInfo,
  CallToolResult,
  McpHandlerRequestOptions,
  McpHttpHandler,
} from "@modelcontextprotocol/server";

import type {
  ThingsCredentialClass,
  ThingsResource,
  ThingsServerName,
} from "./constants.js";

export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonObject | readonly JsonValue[];
export interface JsonObject {
  readonly [key: string]: JsonValue;
}

export interface ClosedJsonObjectSchema extends JsonObject {
  readonly type: "object";
  readonly additionalProperties: false;
}

export type ThingsScope = "things.read" | "things.write" | "things.admin";
export type ThingsRisk =
  | "read-only"
  | "ui-handoff"
  | "ui-visible"
  | "single-write"
  | "bulk-write"
  | "destructive-write";

export interface ThingsToolAnnotations {
  readonly readOnlyHint: boolean;
  readonly destructiveHint: boolean;
  readonly idempotentHint: boolean;
  readonly openWorldHint: boolean;
}

export interface ThingsPublicTool {
  readonly name: string;
  readonly description: string;
  readonly inputSchema: ClosedJsonObjectSchema;
  readonly outputSchema: ClosedJsonObjectSchema;
  readonly annotations: ThingsToolAnnotations;
  readonly _meta: JsonObject;
}

export interface AdaptedSchemaHashes {
  readonly inputSchemaSha256: string;
  readonly outputSchemaSha256: string;
  readonly status: "frozen";
}

export interface AuditedUpstreamSchemaHashes {
  readonly inputSchemaSha256: string;
  readonly outputSchemaSha256: string;
}

export type ThingsImplementationKind =
  | "upstream-security-adapter"
  | "fixed-shortcut-protocol"
  | "fixed-applescript"
  | "fixed-things-url-scheme";

export interface ThingsManifestToolContract {
  readonly server: ThingsServerName;
  readonly serverToolName: string;
  readonly publicToolName: string;
  readonly expectedMcphubQualifiedName: string;
  readonly qualifiedCapabilityId: string;
  readonly minimumIndependentScope: ThingsScope;
  readonly risk: ThingsRisk;
  readonly annotations: ThingsToolAnnotations;
  readonly schemaContractId: string;
  readonly adaptedSchemaHashes: AdaptedSchemaHashes;
  readonly auditedUpstreamSchemaHashes: AuditedUpstreamSchemaHashes | null;
  readonly backendPrerequisites: readonly string[];
  readonly implementationKind: ThingsImplementationKind;
  readonly testIds: readonly string[];
}

export interface ThingsManifestProjection {
  readonly schemaVersion: 1;
  readonly group: {
    readonly name: "things";
    readonly localPath: "/mcp/things";
    readonly remotePath: "/mcp/things";
    readonly localResource: ThingsResource;
    readonly remoteResource: ThingsResource;
    readonly servers: readonly ThingsServerName[];
  };
  readonly counts: {
    readonly tools: 70;
    readonly coreTools: 41;
    readonly shortcutTools: 21;
    readonly nativeTools: 8;
    readonly supaOutcomes: 37;
    readonly workflows: 17;
    readonly legacyEvalIds: 25;
    readonly newEvalIds: 16;
  };
  readonly tools: readonly ThingsManifestToolContract[];
}

export interface ThingsCatalogSnapshot {
  readonly tools: readonly ThingsPublicTool[];
}

export interface ThingsCallContext {
  readonly principal: string;
  readonly clientId: string;
  readonly resource: ThingsResource;
  readonly scopes: ReadonlySet<ThingsScope>;
  readonly signal: AbortSignal;
}

export interface ThingsProviderCall {
  readonly server: ThingsServerName;
  readonly serverToolName: string;
  readonly publicToolName: string;
  readonly arguments: Readonly<Record<string, unknown>>;
  readonly context: ThingsCallContext;
}

export interface ThingsToolProvider {
  snapshot(): Promise<ThingsCatalogSnapshot>;
  call(request: ThingsProviderCall): Promise<CallToolResult>;
}

export interface ValidatedThingsRoute {
  readonly contract: ThingsManifestToolContract;
  readonly tool: ThingsPublicTool;
}

export interface ValidatedThingsCatalog {
  readonly tools: readonly ThingsPublicTool[];
  readonly routesByName: ReadonlyMap<string, ValidatedThingsRoute>;
  readonly serverCounts: Readonly<Record<ThingsServerName, number>>;
  readonly catalogSha256: string;
  readonly scopeMapSha256: string;
  readonly manifestProjectionSha256: string;
}

export interface ProtocolEvent {
  readonly code:
    | "protocol_rejected"
    | "protocol_internal_error"
    | "provider_rejected";
}

export type ProtocolEventSink = (event: ProtocolEvent) => void;

export interface ThingsProtocolOptions {
  readonly maxRequestBodySize?: number;
  readonly eventSink?: ProtocolEventSink;
}

export interface ThingsProtocolHandler extends McpHttpHandler {
  fetch(
    request: Request,
    options?: McpHandlerRequestOptions,
  ): Promise<Response>;
  readonly catalog: ValidatedThingsCatalog;
}

export interface ProtocolAuthIdentity {
  readonly authInfo: AuthInfo;
  readonly principal: string;
  readonly clientId: string;
  readonly resource: ThingsResource;
  readonly credentialClass: ThingsCredentialClass;
  readonly scopes: ReadonlySet<ThingsScope>;
}

export interface ProtocolConformanceCaseResult {
  readonly id: ProtocolConformanceCaseId;
  readonly status: "passed";
  readonly httpStatus: number;
  readonly jsonRpcCode: number | null;
  readonly sdkDispatchCount: number;
  readonly providerDispatchCount: number;
  readonly resultSha256: string;
}

export type ProtocolConformanceCaseId =
  | "modern-discover"
  | "modern-list"
  | "modern-call"
  | "legacy-initialize"
  | "legacy-list"
  | "auth-absent-modern"
  | "auth-absent-legacy"
  | "scope-missing"
  | "scope-extra"
  | "resource-mismatch"
  | "credential-class-mismatch"
  | "principal-invalid"
  | "client-invalid"
  | "session-id-forbidden"
  | "last-event-id-forbidden"
  | "get-method-forbidden"
  | "method-mismatch"
  | "name-mismatch"
  | "missing-client-capabilities"
  | "unsupported-version"
  | "unknown-modern-method"
  | "parse-error";

export interface ProtocolConformanceReport {
  readonly schemaVersion: 1;
  readonly protocol: {
    readonly modern: "2026-07-28";
    readonly legacy: "2025-11-25";
    readonly discoverySupportedVersions: readonly ["2026-07-28"];
    readonly stateless: true;
    readonly sessionsAccepted: false;
    readonly getStreamAccepted: false;
  };
  readonly catalog: {
    readonly toolCount: 70;
    readonly serverCounts: Readonly<Record<ThingsServerName, number>>;
    readonly catalogSha256: string;
    readonly scopeMapSha256: string;
    readonly manifestProjectionSha256: string;
  };
  readonly isolation: {
    readonly publicSdkPackage: "@modelcontextprotocol/server";
    readonly publicSdkVersion: "2.0.0";
    readonly privateV1ImportsInProtocol: 0;
  };
  readonly execution: {
    readonly status: "passed";
    readonly caseCount: 22;
    readonly passedCaseCount: 22;
    readonly caseIds: readonly ProtocolConformanceCaseId[];
    readonly cases: readonly ProtocolConformanceCaseResult[];
    readonly sdkDispatchCount: 6;
    readonly providerDispatchCount: 1;
    readonly errorMatrixSha256: string;
    readonly errorMatrixResultsSha256: string;
    readonly resultBundleSha256: string;
  };
}
