import { canonicalJson } from "../protocol/canonical-json.js";
import { parseThingsManifestProjection } from "../protocol/catalog-validation.js";
import type { ThingsManifestProjection } from "../protocol/types.js";
import { readOwnerOnlyRuntimeFile } from "./secure-file.js";

const GROUP_ID = "3b94a096-b95f-586c-b2e7-e69ed177eb5a";
const NORMALIZED_CATALOG_SHA256 = "0c48616453e929a8f9d287bb7a4bb59f0d587df3e7008506bfdd7c52472b066e";
const SERVERS = ["things-core", "things-shortcuts", "things-native"] as const;

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function fail(): never {
  throw new Error("runtime_settings_contract_invalid");
}

function failSmartRoutingEnvironment(): never {
  throw new Error("runtime_smart_routing_environment_invalid");
}

function object(value: unknown): Record<string, unknown> {
  return isRecord(value) ? value : fail();
}

function array(value: unknown): readonly unknown[] {
  return Array.isArray(value) ? value : fail();
}

function equal(left: unknown, right: unknown): boolean {
  return canonicalJson(left) === canonicalJson(right);
}

function expectedApprovalMode(risk: unknown): "never" | "per-call" {
  return risk === "read-only" ? "never" : "per-call";
}

function groupMemberName(value: unknown): string {
  const name = typeof value === "string" ? value : object(value).name;
  return typeof name === "string" && name.length > 0 ? name : fail();
}

export function assertSettingsSmartRoutingDisabled(settings: unknown): void {
  const systemConfig = object(object(settings).systemConfig);
  if (systemConfig.nameSeparator !== "-") fail();
  const smartRouting = object(systemConfig.smartRouting);
  if (smartRouting.enabled !== false) fail();
}

export function assertInheritedSmartRoutingDisabled(value: string | undefined): void {
  if (value !== undefined && value !== "false") {
    failSmartRoutingEnvironment();
  }
}

function protocolToolFromManifest(value: unknown): Record<string, unknown> {
  const entry = object(value);
  return {
    server: entry.server,
    serverToolName: entry.serverToolName,
    publicToolName: entry.publicToolName,
    expectedMcphubQualifiedName: entry.expectedMcphubQualifiedName,
    qualifiedCapabilityId: entry.qualifiedCapabilityId,
    minimumIndependentScope: entry.minimumIndependentScope,
    risk: entry.risk,
    annotations: entry.annotations,
    schemaContractId: entry.schemaContractId,
    adaptedSchemaHashes: entry.adaptedSchemaHashes,
    auditedUpstreamSchemaHashes: entry.auditedUpstreamSchemaHashes ?? null,
    backendPrerequisites: entry.backendPrerequisites,
    implementationKind: entry.implementationKind,
    testIds: entry.testIds,
  };
}

export function projectThingsManifestForRuntime(manifestValue: unknown): ThingsManifestProjection {
  const manifest = object(manifestValue);
  const group = object(manifest.group);
  return parseThingsManifestProjection({
    schemaVersion: 1,
    group: {
      name: group.name,
      localPath: group.localPath,
      remotePath: group.remotePath,
      localResource: group.localResource,
      remoteResource: group.remoteResource,
      servers: group.servers,
    },
    counts: manifest.counts,
    tools: array(manifest.tools).map(protocolToolFromManifest),
  });
}

export interface ValidatedRuntimeSettingsContract {
  readonly capabilityManifestSha256: string;
  readonly projection: ThingsManifestProjection;
  readonly settingsSha256: string;
}

export function loadAndValidateRuntimeSettingsContract(input: {
  readonly capabilityManifestPath: string;
  readonly settingsPath: string;
}): ValidatedRuntimeSettingsContract {
  const manifestFile = readOwnerOnlyRuntimeFile(input.capabilityManifestPath);
  const settingsFile = readOwnerOnlyRuntimeFile(input.settingsPath);
  const manifestBytes = manifestFile.bytes;
  const settingsBytes = settingsFile.bytes;
  const manifest = object(JSON.parse(manifestBytes.toString("utf8")) as unknown);
  const settings = object(JSON.parse(settingsBytes.toString("utf8")) as unknown);
  assertSettingsSmartRoutingDisabled(settings);
  const projection = projectThingsManifestForRuntime(manifest);
  const contract = object(settings.thingsContract);
  const contractTools = array(contract.tools);
  const manifestTools = array(manifest.tools);
  const expectedContractTools = manifestTools.map((value) => {
    const entry = object(value);
    return { ...entry, approvalMode: expectedApprovalMode(entry.risk) };
  });
  if (
    contract.version !== 1 ||
    contract.group !== "things" ||
    contract.groupId !== GROUP_ID ||
    contract.manifestSha256 !== manifestFile.sha256 ||
    contract.normalizedCatalogSha256 !== NORMALIZED_CATALOG_SHA256 ||
    !equal(contract.counts, manifest.counts) ||
    !equal(contract.scopes, manifest.scopes) ||
    !equal(contractTools, expectedContractTools) ||
    !equal(contract.approvalPolicy, {
      default: "per-call",
      readOnlyRisk: "never",
      otherwise: "per-call",
    })
  ) {
    return fail();
  }

  const servers = object(settings.mcpServers);
  const toolsByServer = new Map<string, Record<string, unknown>[]>();
  for (const server of SERVERS) toolsByServer.set(server, []);
  for (const value of manifestTools) {
    const entry = object(value);
    const server = String(entry.server);
    const list = toolsByServer.get(server);
    if (list === undefined) return fail();
    list.push(entry);
  }
  for (const server of SERVERS) {
    const entry = object(servers[server]);
    const tools = toolsByServer.get(server) ?? [];
    const names = tools.map((value) => value.serverToolName);
    const approvals = Object.fromEntries(
      tools.map((value) => [String(value.serverToolName), expectedApprovalMode(value.risk)]),
    );
    if (
      entry.groupOnly !== true ||
      !equal(entry.tools, names) ||
      !equal(entry.toolApprovals, approvals)
    ) {
      return fail();
    }
  }

  const groups = array(settings.groups);
  const thingsGroups = groups.filter((value) => {
    const entry = object(value);
    return entry.name === "things";
  });
  if (thingsGroups.length !== 1) return fail();
  const thingsGroup = object(thingsGroups[0]);
  const thingsMembers = array(thingsGroup.servers).map((value) => object(value));
  const marker = object(thingsGroup.contract);
  if (
    thingsGroup.id !== GROUP_ID ||
    thingsMembers.some((member) => "alias" in member) ||
    !equal(thingsMembers.map((member) => member.name), SERVERS) ||
    !equal(marker, {
      groupId: GROUP_ID,
      normalizedCatalogSha256: NORMALIZED_CATALOG_SHA256,
      toolCount: 70,
      approvalPolicy: contract.approvalPolicy,
    })
  ) {
    return fail();
  }
  for (const value of groups) {
    const group = object(value);
    if (group.name === "things") continue;
    const names = array(group.servers).map(groupMemberName);
    if (names.some((name) => SERVERS.includes(name as (typeof SERVERS)[number]))) {
      return fail();
    }
  }
  return Object.freeze({
    capabilityManifestSha256: manifestFile.sha256,
    projection,
    settingsSha256: settingsFile.sha256,
  });
}

export function loadAndValidateRuntimeSettings(input: {
  readonly capabilityManifestPath: string;
  readonly settingsPath: string;
}): ThingsManifestProjection {
  return loadAndValidateRuntimeSettingsContract(input).projection;
}
