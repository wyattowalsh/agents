import { canonicalSha256 } from "../protocol/canonical-json.js";
import type { RegistrationMode } from "../policy/oauth-policy.js";
import { readOwnerOnlyRuntimeFile } from "./secure-file.js";

export type RemoteRuntimeMode = "disabled" | "capture" | "public";

const SHA256 = /^[a-f0-9]{64}$/u;
const DISTRIBUTION_DIGEST = /^sha256-[a-f0-9]{64}$/u;
const ZERO_SHA256 = "0".repeat(64);
const MAX_CAPTURE_TTL_MS = 30 * 60 * 1_000;
const MAX_PUBLIC_TTL_MS = 24 * 60 * 60 * 1_000;
const CLOCK_SKEW_MS = 5 * 60 * 1_000;

const BINDING_KEYS = Object.freeze([
  "auditManifestSha256",
  "capabilityManifestSha256",
  "catalogSha256",
  "cloudflaredConfigSha256",
  "conformanceResultSha256",
  "distributionDigest",
  "manifestProjectionSha256",
  "oauthLoginCredentialSha256",
  "oauthPolicySha256",
  "observedWireEvidenceSha256",
  "routeManifestSha256",
  "scopeMapSha256",
  "settingsSha256",
] as const);

export interface RemoteActivationBindings {
  readonly auditManifestSha256: string;
  readonly capabilityManifestSha256: string;
  readonly catalogSha256: string;
  readonly cloudflaredConfigSha256: string;
  readonly conformanceResultSha256: string;
  readonly distributionDigest: string;
  readonly manifestProjectionSha256: string;
  readonly oauthLoginCredentialSha256: string;
  readonly oauthPolicySha256: string;
  readonly observedWireEvidenceSha256: string;
  readonly routeManifestSha256: string;
  readonly scopeMapSha256: string;
  readonly settingsSha256: string;
}

export interface ValidatedRemoteActivationReceipt {
  readonly bindings: RemoteActivationBindings;
  readonly createdAt: number;
  readonly expiresAt: number;
  readonly mode: Exclude<RemoteRuntimeMode, "disabled">;
  readonly noSecrets: true;
  readonly publicOrigin: "https://mcp.w4w.dev";
  readonly publicResource: "https://mcp.w4w.dev/mcp/things";
  readonly receiptSha256: string;
  readonly registrationMode: RegistrationMode | null;
  readonly remotePublicReady: boolean;
  readonly status: "pass";
  readonly toolDispatchEnabled: boolean;
  readonly tunnelAllowed: true;
}

export interface RuntimeActivation {
  readonly bindRemoteListener: boolean;
  readonly mode: RemoteRuntimeMode;
  readonly remotePublicReady: boolean;
  readonly remoteToolDispatchEnabled: boolean;
  readonly receiptSha256: string | null;
  readonly tunnelAllowed: boolean;
}

function fail(code = "remote_activation_receipt_invalid"): never {
  throw new Error(code);
}

function record(value: unknown): Record<string, unknown> {
  if (value === null || typeof value !== "object" || Array.isArray(value)) return fail();
  const prototype = Object.getPrototypeOf(value);
  if (prototype !== Object.prototype && prototype !== null) return fail();
  return value as Record<string, unknown>;
}

function exactKeys(value: Record<string, unknown>, expected: readonly string[]): void {
  const actual = Object.keys(value).sort();
  const required = [...expected].sort();
  if (actual.length !== required.length || actual.some((key, index) => key !== required[index])) {
    fail();
  }
}

function digest(value: unknown, allowZero = false): string {
  if (
    typeof value !== "string" ||
    !SHA256.test(value) ||
    (!allowZero && value === ZERO_SHA256)
  ) {
    return fail();
  }
  return value;
}

function distributionDigest(value: unknown): string {
  return typeof value === "string" && DISTRIBUTION_DIGEST.test(value) ? value : fail();
}

function safeInteger(value: unknown): number {
  return typeof value === "number" && Number.isSafeInteger(value) ? value : fail();
}

function parseBindings(value: unknown, mode: "capture" | "public"): RemoteActivationBindings {
  const source = record(value);
  exactKeys(source, BINDING_KEYS);
  const capturePlaceholder = mode === "capture";
  return Object.freeze({
    auditManifestSha256: digest(source.auditManifestSha256),
    capabilityManifestSha256: digest(source.capabilityManifestSha256),
    catalogSha256: digest(source.catalogSha256),
    cloudflaredConfigSha256: digest(source.cloudflaredConfigSha256),
    conformanceResultSha256: digest(source.conformanceResultSha256),
    distributionDigest: distributionDigest(source.distributionDigest),
    manifestProjectionSha256: digest(source.manifestProjectionSha256),
    oauthLoginCredentialSha256: digest(
      source.oauthLoginCredentialSha256,
      capturePlaceholder,
    ),
    oauthPolicySha256: digest(source.oauthPolicySha256, capturePlaceholder),
    observedWireEvidenceSha256: digest(
      source.observedWireEvidenceSha256,
      capturePlaceholder,
    ),
    routeManifestSha256: digest(source.routeManifestSha256),
    scopeMapSha256: digest(source.scopeMapSha256),
    settingsSha256: digest(source.settingsSha256),
  });
}

function bindingsEqual(
  actual: RemoteActivationBindings,
  expected: RemoteActivationBindings,
): boolean {
  return BINDING_KEYS.every((key) => actual[key] === expected[key]);
}

export function auditManifestIdentity(value: unknown): Readonly<{
  auditManifestSha256: string;
  distributionDigest: string;
}> {
  const manifest = record(value);
  if (manifest.schemaVersion !== 1 || manifest.status !== "sealed") return fail();
  const distribution = record(manifest.distribution);
  const selectedDigest = distributionDigest(distribution.digest);
  return Object.freeze({
    auditManifestSha256: canonicalSha256(value),
    distributionDigest: selectedDigest,
  });
}

export function parseRemoteActivationReceipt(input: {
  readonly bytes: Uint8Array;
  readonly expectedBindings: RemoteActivationBindings;
  readonly expectedMode: "capture" | "public";
  readonly expectedRegistrationMode: RegistrationMode | null;
  readonly now?: number;
  readonly receiptSha256: string;
}): ValidatedRemoteActivationReceipt {
  let parsed: unknown;
  try {
    parsed = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(input.bytes)) as unknown;
  } catch {
    return fail();
  }
  const source = record(parsed);
  exactKeys(source, [
    "bindings",
    "createdAt",
    "expiresAt",
    "mode",
    "noSecrets",
    "publicOrigin",
    "publicResource",
    "registrationMode",
    "remotePublicReady",
    "schemaVersion",
    "status",
    "toolDispatchEnabled",
    "tunnelAllowed",
  ]);
  if (
    source.schemaVersion !== 1 ||
    source.status !== "pass" ||
    source.mode !== input.expectedMode ||
    source.noSecrets !== true ||
    source.publicOrigin !== "https://mcp.w4w.dev" ||
    source.publicResource !== "https://mcp.w4w.dev/mcp/things" ||
    source.registrationMode !== input.expectedRegistrationMode ||
    source.tunnelAllowed !== true ||
    !SHA256.test(input.receiptSha256)
  ) {
    return fail();
  }
  const createdAt = safeInteger(source.createdAt);
  const expiresAt = safeInteger(source.expiresAt);
  const now = input.now ?? Date.now();
  const maximumTtl = input.expectedMode === "capture" ? MAX_CAPTURE_TTL_MS : MAX_PUBLIC_TTL_MS;
  if (
    createdAt > now + CLOCK_SKEW_MS ||
    expiresAt <= now ||
    expiresAt <= createdAt ||
    expiresAt - createdAt > maximumTtl
  ) {
    return fail();
  }
  const expectedReady = input.expectedMode === "public";
  if (
    source.remotePublicReady !== expectedReady ||
    source.toolDispatchEnabled !== expectedReady
  ) {
    return fail();
  }
  const bindings = parseBindings(source.bindings, input.expectedMode);
  if (!bindingsEqual(bindings, input.expectedBindings)) return fail();
  return Object.freeze({
    bindings,
    createdAt,
    expiresAt,
    mode: input.expectedMode,
    noSecrets: true,
    publicOrigin: "https://mcp.w4w.dev",
    publicResource: "https://mcp.w4w.dev/mcp/things",
    receiptSha256: input.receiptSha256,
    registrationMode: input.expectedRegistrationMode,
    remotePublicReady: expectedReady,
    status: "pass",
    toolDispatchEnabled: expectedReady,
    tunnelAllowed: true,
  });
}

export function loadRemoteActivationReceipt(input: {
  readonly expectedBindings: RemoteActivationBindings;
  readonly expectedMode: "capture" | "public";
  readonly expectedRegistrationMode: RegistrationMode | null;
  readonly now?: number;
  readonly path: string;
}): ValidatedRemoteActivationReceipt {
  const file = readOwnerOnlyRuntimeFile(input.path, 32 * 1024);
  return parseRemoteActivationReceipt({
    bytes: file.bytes,
    expectedBindings: input.expectedBindings,
    expectedMode: input.expectedMode,
    expectedRegistrationMode: input.expectedRegistrationMode,
    ...(input.now === undefined ? {} : { now: input.now }),
    receiptSha256: file.sha256,
  });
}

export function evaluateRuntimeActivation(input: {
  readonly mode: RemoteRuntimeMode;
  readonly receipt: ValidatedRemoteActivationReceipt | null;
}): RuntimeActivation {
  if (input.mode === "disabled") {
    return Object.freeze({
      bindRemoteListener: false,
      mode: input.mode,
      remotePublicReady: false,
      remoteToolDispatchEnabled: false,
      receiptSha256: null,
      tunnelAllowed: false,
    });
  }
  if (input.receipt === null || input.receipt.mode !== input.mode) {
    return fail(input.mode === "capture" ? "capture_mode_not_ready" : "remote_public_not_ready");
  }
  if (input.mode === "capture") {
    if (input.receipt.remotePublicReady || input.receipt.toolDispatchEnabled) {
      return fail("capture_mode_not_ready");
    }
    return Object.freeze({
      bindRemoteListener: true,
      mode: input.mode,
      remotePublicReady: false,
      remoteToolDispatchEnabled: false,
      receiptSha256: input.receipt.receiptSha256,
      tunnelAllowed: input.receipt.tunnelAllowed,
    });
  }
  if (!input.receipt.remotePublicReady || !input.receipt.toolDispatchEnabled) {
    return fail("remote_public_not_ready");
  }
  return Object.freeze({
    bindRemoteListener: true,
    mode: input.mode,
    remotePublicReady: true,
    remoteToolDispatchEnabled: true,
    receiptSha256: input.receipt.receiptSha256,
    tunnelAllowed: input.receipt.tunnelAllowed,
  });
}
