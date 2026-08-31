import { createHash, randomBytes } from "node:crypto";
import {
  closeSync,
  constants,
  fstatSync,
  fsyncSync,
  linkSync,
  lstatSync,
  openSync,
  unlinkSync,
  writeSync,
} from "node:fs";
import path from "node:path";

import { canonicalJson, canonicalSha256 } from "../protocol/canonical-json.js";
import {
  OAUTH_SCOPES,
  THINGS_RESOURCE,
  THINGS_SCOPES,
  type RegistrationMode,
} from "../policy/oauth-policy.js";
import type { IngressRouteId } from "./route-policy.js";

const SCHEMA_PATH = "./observed-wire-record.schema.json" as const;
const SCHEMA_VERSION = "1.1.0" as const;
const OFFLINE_ACCESS_SEMANTICS = "refresh-only-no-things-authorization" as const;
const MAX_CAPTURE_TTL_MS = 30 * 60 * 1_000;
const EVIDENCE_FRESHNESS_TTL_MS = 24 * 60 * 60 * 1_000;
const CLOCK_SKEW_MS = 5 * 60 * 1_000;
const SHA256 = /^[a-f0-9]{64}$/u;
const OPAQUE = /^[A-Za-z0-9_-]{43,128}$/u;
const DOCUMENTED_CIMD_CLIENT_ID = "https://chatgpt.com/oauth/client.json";
const DOCUMENTED_REDIRECT_URI =
  "https://chatgpt.com/connector_platform_oauth_redirect" as const;
const MODERN_PROTOCOL = "2026-07-28" as const;
const LEGACY_PROTOCOL = "2025-11-25" as const;

type CapturedProtocol = typeof MODERN_PROTOCOL | typeof LEGACY_PROTOCOL;
type ObservedRegistrationMode =
  | "client-id-metadata-document"
  | "dynamic-client-registration";

export interface CaptureRouteStatuses {
  readonly authorization: 503 | null;
  readonly authorizationServerMetadata: 200 | null;
  readonly mcp: 401 | null;
  readonly protectedResourceMetadata: 200 | null;
  readonly registration: 503 | null;
}

export interface CaptureEvidenceRecord {
  readonly $schema: typeof SCHEMA_PATH;
  readonly captureReceiptSha256: string;
  readonly capturedAt: string;
  readonly evidenceDigestSha256: string;
  readonly expiresAt: string;
  readonly mcpProtocolVersion: CapturedProtocol | null;
  readonly modernDiscoveryObserved: boolean;
  readonly offlineAccessRequested: boolean;
  readonly offlineAccessSemantics: typeof OFFLINE_ACCESS_SEMANTICS;
  readonly pkceS256Observed: boolean;
  readonly prohibitedDataAbsent: true;
  readonly publicResource: typeof THINGS_RESOURCE;
  readonly redactionsVerified: true;
  readonly redirectUri: typeof DOCUMENTED_REDIRECT_URI | null;
  readonly redirectUriSha256: string | null;
  readonly registrationMode: ObservedRegistrationMode | null;
  readonly requiredIndependentScopes: typeof THINGS_SCOPES;
  readonly resourceIndicatorObserved: boolean;
  readonly routeStatuses: CaptureRouteStatuses;
  readonly schemaVersion: typeof SCHEMA_VERSION;
  readonly secretFree: true;
  readonly status: "observed-fail" | "observed-pass";
}

interface CaptureState {
  ambiguous: boolean;
  mcpProtocolVersion: CapturedProtocol | null;
  modernDiscoveryObserved: boolean;
  offlineAccessRequested: boolean;
  pkceS256Observed: boolean;
  redirectUri: typeof DOCUMENTED_REDIRECT_URI | null;
  registrationMode: RegistrationMode | null;
  requiredScopesObserved: boolean;
  resourceIndicatorObserved: boolean;
  routeStatuses: {
    authorization: 503 | null;
    authorizationServerMetadata: 200 | null;
    mcp: 401 | null;
    protectedResourceMetadata: 200 | null;
    registration: 503 | null;
  };
}

interface CaptureFacts {
  readonly mcpProtocolVersion?: CapturedProtocol;
  readonly modernDiscoveryObserved?: boolean;
  readonly offlineAccessRequested?: boolean;
  readonly pkceS256Observed?: boolean;
  readonly redirectUri?: typeof DOCUMENTED_REDIRECT_URI;
  readonly registrationMode?: RegistrationMode;
  readonly requiredScopesObserved?: boolean;
  readonly resourceIndicatorObserved?: boolean;
}

const TOP_LEVEL_KEYS = Object.freeze([
  "$schema",
  "captureReceiptSha256",
  "capturedAt",
  "evidenceDigestSha256",
  "expiresAt",
  "mcpProtocolVersion",
  "modernDiscoveryObserved",
  "offlineAccessRequested",
  "offlineAccessSemantics",
  "pkceS256Observed",
  "prohibitedDataAbsent",
  "publicResource",
  "redactionsVerified",
  "redirectUri",
  "redirectUriSha256",
  "registrationMode",
  "requiredIndependentScopes",
  "resourceIndicatorObserved",
  "routeStatuses",
  "schemaVersion",
  "secretFree",
  "status",
] as const);

const ROUTE_STATUS_KEYS = Object.freeze([
  "authorization",
  "authorizationServerMetadata",
  "mcp",
  "protectedResourceMetadata",
  "registration",
] as const);

function fail(code = "capture_evidence_invalid"): never {
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

function sha256(value: string): string {
  return createHash("sha256").update(value, "utf8").digest("hex");
}

function secureParent(pathname: string): void {
  if (
    !path.isAbsolute(pathname) ||
    path.normalize(pathname) !== pathname ||
    pathname.includes("\0") ||
    path.basename(pathname) === "." ||
    path.basename(pathname) === ".."
  ) {
    fail("capture_evidence_path_invalid");
  }
  let parent: ReturnType<typeof lstatSync>;
  try {
    parent = lstatSync(path.dirname(pathname));
  } catch {
    return fail("capture_evidence_path_invalid");
  }
  if (
    !parent.isDirectory() ||
    parent.isSymbolicLink() ||
    (typeof process.getuid === "function" && parent.uid !== process.getuid()) ||
    (parent.mode & 0o077) !== 0
  ) {
    fail("capture_evidence_path_invalid");
  }
}

function pathDoesNotExist(pathname: string): boolean {
  try {
    lstatSync(pathname);
    return false;
  } catch (error) {
    return error instanceof Error && "code" in error && error.code === "ENOENT";
  }
}

function atomicOwnerOnlyCreate(pathname: string, bytes: Buffer): void {
  secureParent(pathname);
  if (!pathDoesNotExist(pathname)) fail("capture_evidence_path_exists");
  const temporary = path.join(
    path.dirname(pathname),
    `.${path.basename(pathname)}.${process.pid}.${randomBytes(16).toString("hex")}.tmp`,
  );
  let descriptor: number | undefined;
  try {
    descriptor = openSync(
      temporary,
      constants.O_WRONLY | constants.O_CREAT | constants.O_EXCL | constants.O_NOFOLLOW,
      0o600,
    );
    let offset = 0;
    while (offset < bytes.byteLength) {
      const count = writeSync(descriptor, bytes, offset, bytes.byteLength - offset);
      if (count < 1) fail("capture_evidence_write_failed");
      offset += count;
    }
    fsyncSync(descriptor);
    const opened = fstatSync(descriptor);
    if (
      !opened.isFile() ||
      opened.nlink !== 1 ||
      opened.size !== bytes.byteLength ||
      (typeof process.getuid === "function" && opened.uid !== process.getuid()) ||
      (opened.mode & 0o077) !== 0
    ) {
      fail("capture_evidence_path_invalid");
    }
    closeSync(descriptor);
    descriptor = undefined;
    if (!pathDoesNotExist(pathname)) fail("capture_evidence_path_exists");
    try {
      linkSync(temporary, pathname);
    } catch (error) {
      if (error instanceof Error && "code" in error && error.code === "EEXIST") {
        fail("capture_evidence_path_exists");
      }
      throw error;
    }
    unlinkSync(temporary);
    const materialized = lstatSync(pathname);
    if (
      !materialized.isFile() ||
      materialized.isSymbolicLink() ||
      materialized.nlink !== 1 ||
      materialized.size !== bytes.byteLength ||
      (typeof process.getuid === "function" && materialized.uid !== process.getuid()) ||
      (materialized.mode & 0o077) !== 0
    ) {
      fail("capture_evidence_path_invalid");
    }
  } catch (error) {
    if (descriptor !== undefined) closeSync(descriptor);
    try {
      unlinkSync(temporary);
    } catch {
      // The successful link-and-unlink path no longer has a temporary pathname.
    }
    if (error instanceof Error && error.message.startsWith("capture_evidence_")) throw error;
    fail("capture_evidence_write_failed");
  }
}

function exactOAuthScopes(scopes: readonly string[]): boolean {
  return (
    scopes.length === OAUTH_SCOPES.length &&
    new Set(scopes).size === OAUTH_SCOPES.length &&
    OAUTH_SCOPES.every((scope) => scopes.includes(scope))
  );
}

function authorizeFacts(request: Request): CaptureFacts {
  if (request.method !== "GET") return Object.freeze({});
  const params = new URL(request.url).searchParams;
  const clientId = params.get("client_id");
  const redirectUri = params.get("redirect_uri");
  const rawScopes = params.get("scope")?.split(" ") ?? [];
  const challenge = params.get("code_challenge");
  const facts: {
    offlineAccessRequested: boolean;
    pkceS256Observed: boolean;
    redirectUri?: typeof DOCUMENTED_REDIRECT_URI;
    registrationMode?: RegistrationMode;
    requiredScopesObserved: boolean;
    resourceIndicatorObserved: boolean;
  } = {
    offlineAccessRequested:
      rawScopes.includes("offline_access") && exactOAuthScopes(rawScopes),
    pkceS256Observed:
      params.get("code_challenge_method") === "S256" &&
      challenge !== null &&
      OPAQUE.test(challenge),
    requiredScopesObserved: exactOAuthScopes(rawScopes),
    resourceIndicatorObserved: params.get("resource") === THINGS_RESOURCE,
  };
  if (clientId === DOCUMENTED_CIMD_CLIENT_ID) facts.registrationMode = "cimd";
  else if (
    clientId !== null &&
    clientId.startsWith("dcr_") &&
    OPAQUE.test(clientId.slice("dcr_".length))
  ) {
    facts.registrationMode = "dcr";
  }
  if (redirectUri === DOCUMENTED_REDIRECT_URI) facts.redirectUri = DOCUMENTED_REDIRECT_URI;
  return Object.freeze(facts);
}

async function registrationFacts(request: Request): Promise<CaptureFacts> {
  if (request.method !== "POST") return Object.freeze({});
  let metadata: Record<string, unknown>;
  try {
    metadata = record(JSON.parse(await request.text()) as unknown);
  } catch {
    return Object.freeze({});
  }
  const redirects = metadata.redirect_uris;
  return Object.freeze({
    ...(Array.isArray(redirects) &&
    redirects.length === 1 &&
    redirects[0] === DOCUMENTED_REDIRECT_URI
      ? { redirectUri: DOCUMENTED_REDIRECT_URI }
      : {}),
    registrationMode: "dcr" as const,
  });
}

async function mcpFacts(request: Request): Promise<CaptureFacts> {
  if (request.method !== "POST") return Object.freeze({});
  const headerVersion = request.headers.get("mcp-protocol-version");
  const headerMethod = request.headers.get("mcp-method");
  let body: Record<string, unknown>;
  try {
    body = record(JSON.parse(await request.text()) as unknown);
  } catch {
    return Object.freeze({});
  }
  if (headerVersion === MODERN_PROTOCOL && headerMethod === "server/discover") {
    try {
      const metadata = record(record(body.params)._meta);
      if (
        body.jsonrpc === "2.0" &&
        body.method === "server/discover" &&
        metadata["io.modelcontextprotocol/protocolVersion"] === MODERN_PROTOCOL
      ) {
        return Object.freeze({
          mcpProtocolVersion: MODERN_PROTOCOL,
          modernDiscoveryObserved: true,
        });
      }
    } catch {
      return Object.freeze({});
    }
  }
  if (
    headerVersion === LEGACY_PROTOCOL &&
    (headerMethod === null || headerMethod === "initialize")
  ) {
    try {
      const params = record(body.params);
      if (
        body.jsonrpc === "2.0" &&
        body.method === "initialize" &&
        params.protocolVersion === LEGACY_PROTOCOL
      ) {
        return Object.freeze({
          mcpProtocolVersion: LEGACY_PROTOCOL,
          modernDiscoveryObserved: false,
        });
      }
    } catch {
      return Object.freeze({});
    }
  }
  return Object.freeze({});
}

async function captureFacts(request: Request, route: IngressRouteId): Promise<CaptureFacts> {
  if (route === "things-mcp") return await mcpFacts(request);
  if (route === "oauth-authorize") return authorizeFacts(request);
  if (route === "oauth-register") return await registrationFacts(request);
  return Object.freeze({});
}

function observeRouteStatus(
  state: CaptureState,
  route: IngressRouteId,
  status: number,
): void {
  const merge = <K extends keyof CaptureState["routeStatuses"]>(
    key: K,
    expected: NonNullable<CaptureState["routeStatuses"][K]>,
  ): void => {
    if (status !== expected) {
      state.ambiguous = true;
      return;
    }
    const previous = state.routeStatuses[key];
    if (previous !== null && previous !== expected) state.ambiguous = true;
    else state.routeStatuses[key] = expected;
  };
  if (route === "things-mcp") merge("mcp", 401);
  else if (route === "oauth-protected-resource") merge("protectedResourceMetadata", 200);
  else if (route === "oauth-authorization-server") merge("authorizationServerMetadata", 200);
  else if (route === "oauth-authorize") merge("authorization", 503);
  else if (route === "oauth-register") merge("registration", 503);
}

function mergeFacts(state: CaptureState, facts: CaptureFacts): void {
  if (facts.mcpProtocolVersion !== undefined) {
    if (
      state.mcpProtocolVersion !== null &&
      state.mcpProtocolVersion !== facts.mcpProtocolVersion
    ) {
      state.ambiguous = true;
    } else {
      state.mcpProtocolVersion = facts.mcpProtocolVersion;
    }
  }
  if (facts.registrationMode !== undefined) {
    if (state.registrationMode !== null && state.registrationMode !== facts.registrationMode) {
      state.ambiguous = true;
    } else {
      state.registrationMode = facts.registrationMode;
    }
  }
  if (facts.redirectUri !== undefined) state.redirectUri = facts.redirectUri;
  if (facts.modernDiscoveryObserved === true) state.modernDiscoveryObserved = true;
  if (facts.requiredScopesObserved === true) state.requiredScopesObserved = true;
  if (facts.offlineAccessRequested === true) state.offlineAccessRequested = true;
  if (facts.resourceIndicatorObserved === true) state.resourceIndicatorObserved = true;
  if (facts.pkceS256Observed === true) state.pkceS256Observed = true;
}

function isPassing(state: CaptureState): boolean {
  const routes = state.routeStatuses;
  return (
    !state.ambiguous &&
    state.registrationMode !== null &&
    state.redirectUri === DOCUMENTED_REDIRECT_URI &&
    state.mcpProtocolVersion !== null &&
    (state.mcpProtocolVersion !== MODERN_PROTOCOL || state.modernDiscoveryObserved) &&
    state.requiredScopesObserved &&
    state.offlineAccessRequested &&
    state.resourceIndicatorObserved &&
    state.pkceS256Observed &&
    routes.mcp === 401 &&
    routes.protectedResourceMetadata === 200 &&
    routes.authorizationServerMetadata === 200 &&
    routes.authorization === 503 &&
    (state.registrationMode === "cimd"
      ? routes.registration === null
      : routes.registration === 503)
  );
}

function observedMode(mode: RegistrationMode | null): ObservedRegistrationMode | null {
  if (mode === "cimd") return "client-id-metadata-document";
  if (mode === "dcr") return "dynamic-client-registration";
  return null;
}

function unsignedEvidence(input: {
  readonly captureReceiptSha256: string;
  readonly capturedAt: number;
  readonly expiresAt: number;
  readonly state: CaptureState;
}): Omit<CaptureEvidenceRecord, "evidenceDigestSha256"> {
  return Object.freeze({
    $schema: SCHEMA_PATH,
    schemaVersion: SCHEMA_VERSION,
    status: isPassing(input.state) ? "observed-pass" : "observed-fail",
    capturedAt: new Date(input.capturedAt).toISOString(),
    expiresAt: new Date(input.expiresAt).toISOString(),
    publicResource: THINGS_RESOURCE,
    registrationMode: observedMode(input.state.registrationMode),
    redirectUri: input.state.redirectUri,
    redirectUriSha256:
      input.state.redirectUri === null ? null : sha256(input.state.redirectUri),
    mcpProtocolVersion: input.state.mcpProtocolVersion,
    modernDiscoveryObserved: input.state.modernDiscoveryObserved,
    requiredIndependentScopes: THINGS_SCOPES,
    offlineAccessRequested: input.state.offlineAccessRequested,
    offlineAccessSemantics: OFFLINE_ACCESS_SEMANTICS,
    resourceIndicatorObserved: input.state.resourceIndicatorObserved,
    pkceS256Observed: input.state.pkceS256Observed,
    captureReceiptSha256: input.captureReceiptSha256,
    routeStatuses: Object.freeze({ ...input.state.routeStatuses }),
    secretFree: true,
    redactionsVerified: true,
    prohibitedDataAbsent: true,
  });
}

function evidence(input: {
  readonly captureReceiptSha256: string;
  readonly capturedAt: number;
  readonly expiresAt: number;
  readonly state: CaptureState;
}): CaptureEvidenceRecord {
  const unsigned = unsignedEvidence(input);
  return Object.freeze({
    ...unsigned,
    evidenceDigestSha256: canonicalSha256(unsigned),
  });
}

export class CaptureEvidenceRecorder {
  readonly #captureReceiptSha256: string;
  readonly #captureExpiresAt: number;
  readonly #now: () => number;
  readonly #path: string;
  readonly #state: CaptureState;
  #materialized = false;
  #queue: Promise<void> = Promise.resolve();

  public constructor(input: {
    readonly captureReceiptSha256: string;
    readonly createdAt: number;
    readonly expiresAt: number;
    readonly now?: () => number;
    readonly path: string;
  }) {
    this.#now = input.now ?? Date.now;
    const now = this.#now();
    if (
      !SHA256.test(input.captureReceiptSha256) ||
      !Number.isSafeInteger(input.createdAt) ||
      !Number.isSafeInteger(input.expiresAt) ||
      input.createdAt > now + CLOCK_SKEW_MS ||
      input.expiresAt <= now ||
      input.expiresAt <= input.createdAt ||
      input.expiresAt - input.createdAt > MAX_CAPTURE_TTL_MS
    ) {
      fail();
    }
    secureParent(input.path);
    if (!pathDoesNotExist(input.path)) fail("capture_evidence_path_exists");
    this.#captureReceiptSha256 = input.captureReceiptSha256;
    this.#captureExpiresAt = input.expiresAt;
    this.#path = input.path;
    this.#state = {
      ambiguous: false,
      mcpProtocolVersion: null,
      modernDiscoveryObserved: false,
      offlineAccessRequested: false,
      pkceS256Observed: false,
      redirectUri: null,
      registrationMode: null,
      requiredScopesObserved: false,
      resourceIndicatorObserved: false,
      routeStatuses: {
        authorization: null,
        authorizationServerMetadata: null,
        mcp: null,
        protectedResourceMetadata: null,
        registration: null,
      },
    };
  }

  public observe(request: Request, route: IngressRouteId, responseStatus: number): Promise<void> {
    const task = this.#queue.then(async () => {
      if (this.#materialized) return;
      const now = this.#now();
      if (now >= this.#captureExpiresAt) fail("capture_evidence_expired");
      const facts = await captureFacts(request, route);
      observeRouteStatus(this.#state, route, responseStatus);
      mergeFacts(this.#state, facts);
      if (!this.#state.ambiguous && !isPassing(this.#state)) return;
      const materialized = evidence({
        captureReceiptSha256: this.#captureReceiptSha256,
        capturedAt: now,
        expiresAt: now + EVIDENCE_FRESHNESS_TTL_MS,
        state: this.#state,
      });
      atomicOwnerOnlyCreate(
        this.#path,
        Buffer.from(`${canonicalJson(materialized)}\n`, "utf8"),
      );
      this.#materialized = true;
    });
    this.#queue = task.catch(() => undefined);
    return task;
  }
}

function canonicalTimestamp(value: unknown): number {
  if (typeof value !== "string") return fail();
  const timestamp = Date.parse(value);
  if (!Number.isSafeInteger(timestamp) || new Date(timestamp).toISOString() !== value) return fail();
  return timestamp;
}

export function parseCaptureEvidenceRecord(input: {
  readonly bytes: Uint8Array;
  readonly captureReceiptSha256: string;
  readonly now?: number;
}): CaptureEvidenceRecord {
  let parsed: unknown;
  try {
    parsed = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(input.bytes)) as unknown;
  } catch {
    return fail();
  }
  const source = record(parsed);
  exactKeys(source, TOP_LEVEL_KEYS);
  const routes = record(source.routeStatuses);
  exactKeys(routes, ROUTE_STATUS_KEYS);
  const capturedAt = canonicalTimestamp(source.capturedAt);
  const expiresAt = canonicalTimestamp(source.expiresAt);
  const scopes = source.requiredIndependentScopes;
  const mode = source.registrationMode;
  const protocol = source.mcpProtocolVersion;
  if (
    source.$schema !== SCHEMA_PATH ||
    source.schemaVersion !== SCHEMA_VERSION ||
    (source.status !== "observed-pass" && source.status !== "observed-fail") ||
    source.captureReceiptSha256 !== input.captureReceiptSha256 ||
    !SHA256.test(input.captureReceiptSha256) ||
    capturedAt >= expiresAt ||
    expiresAt <= (input.now ?? Date.now()) ||
    expiresAt - capturedAt > EVIDENCE_FRESHNESS_TTL_MS ||
    source.publicResource !== THINGS_RESOURCE ||
    (mode !== null &&
      mode !== "client-id-metadata-document" &&
      mode !== "dynamic-client-registration") ||
    (protocol !== null && protocol !== MODERN_PROTOCOL && protocol !== LEGACY_PROTOCOL) ||
    typeof source.modernDiscoveryObserved !== "boolean" ||
    typeof source.offlineAccessRequested !== "boolean" ||
    source.offlineAccessSemantics !== OFFLINE_ACCESS_SEMANTICS ||
    typeof source.resourceIndicatorObserved !== "boolean" ||
    typeof source.pkceS256Observed !== "boolean" ||
    source.secretFree !== true ||
    source.redactionsVerified !== true ||
    source.prohibitedDataAbsent !== true ||
    !Array.isArray(scopes) ||
    scopes.length !== THINGS_SCOPES.length ||
    !THINGS_SCOPES.every((scope, index) => scopes[index] === scope) ||
    !([null, 503] as unknown[]).includes(routes.authorization) ||
    !([null, 200] as unknown[]).includes(routes.authorizationServerMetadata) ||
    !([null, 401] as unknown[]).includes(routes.mcp) ||
    !([null, 200] as unknown[]).includes(routes.protectedResourceMetadata) ||
    !([null, 503] as unknown[]).includes(routes.registration)
  ) {
    return fail();
  }
  const redirect = source.redirectUri;
  const redirectDigest = source.redirectUriSha256;
  if (
    !(
      (redirect === null && redirectDigest === null) ||
      (redirect === DOCUMENTED_REDIRECT_URI &&
        redirectDigest === sha256(DOCUMENTED_REDIRECT_URI))
    )
  ) {
    return fail();
  }
  const { evidenceDigestSha256, ...unsigned } = source;
  if (
    typeof evidenceDigestSha256 !== "string" ||
    !SHA256.test(evidenceDigestSha256) ||
    evidenceDigestSha256 !== canonicalSha256(unsigned)
  ) {
    return fail();
  }
  if (source.status === "observed-pass") {
    const expectedRegistration =
      mode === "client-id-metadata-document" ? null : 503;
    if (
      mode === null ||
      redirect !== DOCUMENTED_REDIRECT_URI ||
      protocol === null ||
      (protocol === MODERN_PROTOCOL && source.modernDiscoveryObserved !== true) ||
      source.offlineAccessRequested !== true ||
      source.resourceIndicatorObserved !== true ||
      source.pkceS256Observed !== true ||
      routes.mcp !== 401 ||
      routes.protectedResourceMetadata !== 200 ||
      routes.authorizationServerMetadata !== 200 ||
      routes.authorization !== 503 ||
      routes.registration !== expectedRegistration
    ) {
      return fail();
    }
  }
  return parsed as CaptureEvidenceRecord;
}

export function validateCaptureEvidenceForPublic(input: {
  readonly bytes: Uint8Array;
  readonly expectedRegistrationMode: RegistrationMode;
  readonly now?: number;
}): CaptureEvidenceRecord {
  let untrusted: Record<string, unknown>;
  try {
    untrusted = record(
      JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(input.bytes)) as unknown,
    );
  } catch {
    return fail();
  }
  const receipt = untrusted.captureReceiptSha256;
  if (typeof receipt !== "string" || !SHA256.test(receipt)) return fail();
  const evidenceRecord = parseCaptureEvidenceRecord({
    bytes: input.bytes,
    captureReceiptSha256: receipt,
    ...(input.now === undefined ? {} : { now: input.now }),
  });
  const expectedMode =
    input.expectedRegistrationMode === "cimd"
      ? "client-id-metadata-document"
      : "dynamic-client-registration";
  if (
    evidenceRecord.status !== "observed-pass" ||
    evidenceRecord.registrationMode !== expectedMode
  ) {
    return fail();
  }
  return evidenceRecord;
}
