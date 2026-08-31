#!/usr/bin/env node

import { createHash, timingSafeEqual } from "node:crypto";
import {
  chmod,
  lstat,
  open,
  readFile,
  readlink,
  rename,
  unlink,
} from "node:fs/promises";
import { constants as fsConstants } from "node:fs";
import path from "node:path";

const DIGEST = /^[0-9a-f]{64}$/;
const DISTRIBUTION_DIGEST = /^sha256-[0-9a-f]{64}$/;
const RECEIPT_KEYS = [
  "schemaVersion",
  "status",
  "mode",
  "noSecrets",
  "createdAt",
  "expiresAt",
  "publicOrigin",
  "publicResource",
  "registrationMode",
  "remotePublicReady",
  "toolDispatchEnabled",
  "tunnelAllowed",
  "bindings",
];
const BINDING_KEYS = [
  "auditManifestSha256",
  "distributionDigest",
  "capabilityManifestSha256",
  "settingsSha256",
  "routeManifestSha256",
  "cloudflaredConfigSha256",
  "catalogSha256",
  "scopeMapSha256",
  "manifestProjectionSha256",
  "oauthPolicySha256",
  "oauthLoginCredentialSha256",
  "observedWireEvidenceSha256",
  "conformanceResultSha256",
];
const PUBLIC_ORIGIN = "https://mcp.w4w.dev";
const PUBLIC_RESOURCE = `${PUBLIC_ORIGIN}/mcp/things`;
const REMOTE_ORIGIN = "http://127.0.0.1:46684";
const ZERO_DIGEST = "0".repeat(64);
const MAX_CAPTURE_TTL_MS = 30 * 60 * 1_000;
const MAX_PUBLIC_TTL_MS = 24 * 60 * 60 * 1_000;
const MAX_CLOCK_SKEW_MS = 5_000;
const OBSERVED_WIRE_KEYS = [
  "$schema",
  "schemaVersion",
  "status",
  "capturedAt",
  "expiresAt",
  "publicResource",
  "registrationMode",
  "redirectUri",
  "redirectUriSha256",
  "mcpProtocolVersion",
  "modernDiscoveryObserved",
  "requiredIndependentScopes",
  "offlineAccessRequested",
  "offlineAccessSemantics",
  "resourceIndicatorObserved",
  "pkceS256Observed",
  "captureReceiptSha256",
  "routeStatuses",
  "secretFree",
  "redactionsVerified",
  "prohibitedDataAbsent",
  "evidenceDigestSha256",
];
const OBSERVED_ROUTE_STATUS_KEYS = [
  "mcp",
  "protectedResourceMetadata",
  "authorizationServerMetadata",
  "authorization",
  "registration",
];
const CHATGPT_REDIRECT_URI = "https://chatgpt.com/connector_platform_oauth_redirect";
const RFC3339 = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/;
const ROUTE_MANIFEST = Object.freeze({
  schemaVersion: 1,
  hostname: "mcp.w4w.dev",
  publicOrigin: PUBLIC_ORIGIN,
  publicResource: PUBLIC_RESOURCE,
  origin: REMOTE_ORIGIN,
  allowedPaths: Object.freeze([
    "/",
    "/mcp/things",
    "/.well-known/oauth-protected-resource/mcp/things",
    "/.well-known/oauth-authorization-server",
    "/.well-known/oauth-authorization-server/mcp/things",
    "/oauth/authorize",
    "/oauth/token",
    "/oauth/register",
    "/oauth/revoke",
    "/oauth/login",
    "/oauth/session/logout",
    "/oauth/assets/login.css",
  ]),
  fallback: "http_status:404",
});
const CLOUDFLARED_PATH_PATTERN = String.raw`^/($|mcp/things|\.well-known/oauth-protected-resource/mcp/things|\.well-known/oauth-authorization-server(?:/mcp/things)?|oauth/authorize|oauth/token|oauth/register|oauth/revoke|oauth/login|oauth/session/logout|oauth/assets/login\.css)$`;

function invariant(condition, message) {
  if (!condition) throw new Error(message);
}

function currentUid() {
  invariant(typeof process.getuid === "function", "POSIX owner checks are required");
  return process.getuid();
}

function exactKeys(value, expected, label) {
  invariant(value !== null && typeof value === "object" && !Array.isArray(value), `${label} must be an object`);
  invariant(
    JSON.stringify(Object.keys(value).sort()) === JSON.stringify([...expected].sort()),
    `${label} keys are invalid`,
  );
}

function normalizedAbsolute(value, label) {
  invariant(typeof value === "string" && value.length > 0 && !value.includes("\0"), `${label} is invalid`);
  invariant(path.isAbsolute(value) && path.normalize(value) === value, `${label} must be normalized and absolute`);
  return value;
}

function safeScalar(value, pattern, label) {
  invariant(typeof value === "string" && pattern.test(value), `${label} is invalid`);
  return value;
}

function canonicalJson(value) {
  if (value === null || typeof value === "string" || typeof value === "boolean") return JSON.stringify(value);
  if (typeof value === "number") {
    invariant(Number.isFinite(value), "canonical JSON forbids non-finite numbers");
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) return `[${value.map((entry) => canonicalJson(entry)).join(",")}]`;
  invariant(typeof value === "object", "canonical JSON value is unsupported");
  return `{${Object.keys(value)
    .sort()
    .map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`)
    .join(",")}}`;
}

function sha256(bytes) {
  return createHash("sha256").update(bytes).digest("hex");
}

function equalBytes(left, right) {
  return left.byteLength === right.byteLength && timingSafeEqual(left, right);
}

async function validateOwnedDirectory(directory, label) {
  normalizedAbsolute(directory, label);
  const stats = await lstat(directory);
  invariant(stats.isDirectory() && !stats.isSymbolicLink(), `${label} must be a real directory`);
  invariant(stats.uid === currentUid(), `${label} owner mismatch`);
  invariant((stats.mode & 0o022) === 0, `${label} must not be group/world writable`);
}

async function validateCredentialMetadata(filePath) {
  normalizedAbsolute(filePath, "Cloudflare credentials path");
  const stats = await lstat(filePath);
  invariant(stats.isFile() && !stats.isSymbolicLink() && stats.nlink === 1, "Cloudflare credentials must be one regular file");
  invariant(stats.uid === currentUid(), "Cloudflare credentials owner mismatch");
  invariant((stats.mode & 0o077) === 0, "Cloudflare credentials must be owner-only");
}

async function readOwnedStable(filePath, { label, maximumBytes = 16 * 1024 * 1024, ownerOnly = false }) {
  normalizedAbsolute(filePath, label);
  const before = await lstat(filePath);
  invariant(before.isFile() && !before.isSymbolicLink() && before.nlink === 1, `${label} must be one regular file`);
  invariant(before.uid === currentUid(), `${label} owner mismatch`);
  invariant((before.mode & 0o022) === 0, `${label} must not be group/world writable`);
  if (ownerOnly) invariant((before.mode & 0o077) === 0, `${label} must be owner-only`);
  invariant(before.size > 0 && before.size <= maximumBytes, `${label} size is invalid`);
  const handle = await open(filePath, fsConstants.O_RDONLY | fsConstants.O_NOFOLLOW);
  try {
    const opened = await handle.stat();
    invariant(opened.dev === before.dev && opened.ino === before.ino && opened.size === before.size, `${label} identity changed`);
    const bytes = await handle.readFile();
    const after = await lstat(filePath);
    invariant(
      after.dev === opened.dev && after.ino === opened.ino && after.size === opened.size && bytes.byteLength === opened.size,
      `${label} changed while reading`,
    );
    return bytes;
  } finally {
    await handle.close();
  }
}

async function writePrivateAtomic(output, bytes, { exclusive }) {
  normalizedAbsolute(output, "output path");
  await validateOwnedDirectory(path.dirname(output), "output parent");
  if (exclusive) {
    const handle = await open(output, fsConstants.O_CREAT | fsConstants.O_EXCL | fsConstants.O_WRONLY, 0o600);
    try {
      await handle.writeFile(bytes);
      await handle.sync();
    } finally {
      await handle.close();
    }
    await chmod(output, 0o600);
  } else {
    const temporary = `${output}.tmp-${process.pid}-${Date.now()}`;
    const handle = await open(temporary, fsConstants.O_CREAT | fsConstants.O_EXCL | fsConstants.O_WRONLY, 0o600);
    try {
      await handle.writeFile(bytes);
      await handle.sync();
    } finally {
      await handle.close();
    }
    try {
      await chmod(temporary, 0o600);
      await rename(temporary, output);
    } finally {
      await unlink(temporary).catch((error) => {
        if (error?.code !== "ENOENT") throw error;
      });
    }
  }
  const actual = await readOwnedStable(output, { label: "published output", ownerOnly: true });
  invariant(equalBytes(actual, bytes), "published output readback mismatch");
}

function renderCloudflaredConfig(tunnelName, credentialsFile) {
  safeScalar(tunnelName, /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/, "tunnel name");
  normalizedAbsolute(credentialsFile, "Cloudflare credentials path");
  return Buffer.from(
    `tunnel: ${tunnelName}\n` +
      `credentials-file: ${credentialsFile}\n\n` +
      "ingress:\n" +
      "  - hostname: mcp.w4w.dev\n" +
      `    path: '${CLOUDFLARED_PATH_PATTERN}'\n` +
      "    service: http://127.0.0.1:46684\n" +
      "    originRequest:\n" +
      "      httpHostHeader: mcp.w4w.dev\n" +
      "      connectTimeout: 10s\n" +
      "  - service: http_status:404\n",
    "utf8",
  );
}

async function renderConfig(options) {
  const output = normalizedAbsolute(options.output, "config output");
  await validateCredentialMetadata(options.credentials_file);
  const bytes = renderCloudflaredConfig(options.tunnel_name, options.credentials_file);
  await writePrivateAtomic(output, bytes, { exclusive: false });
  return { cloudflaredConfigSha256: sha256(bytes), output };
}

async function verifyConfig(options) {
  await validateCredentialMetadata(options.credentials_file);
  const expected = renderCloudflaredConfig(options.tunnel_name, options.credentials_file);
  const actual = await readOwnedStable(options.input, { label: "Cloudflare ingress config", ownerOnly: true });
  invariant(equalBytes(actual, expected), "Cloudflare ingress config is not the exact 46684-only manifest");
  return { cloudflaredConfigSha256: sha256(actual) };
}

async function selectedDistribution(runtimeRoot) {
  normalizedAbsolute(runtimeRoot, "runtime root");
  await validateOwnedDirectory(runtimeRoot, "runtime root");
  const pointer = path.join(runtimeRoot, "current");
  const stats = await lstat(pointer);
  invariant(stats.isSymbolicLink() && stats.uid === currentUid(), "selected distribution pointer is invalid");
  const distributionDigest = await readlink(pointer);
  invariant(DISTRIBUTION_DIGEST.test(distributionDigest), "selected distribution digest is invalid");
  const distributionRoot = path.join(runtimeRoot, distributionDigest);
  invariant(path.dirname(distributionRoot) === runtimeRoot, "selected distribution escaped runtime root");
  await validateOwnedDirectory(distributionRoot, "selected distribution");
  return { distributionDigest, distributionRoot };
}

function observedTimestamp(value, label) {
  invariant(typeof value === "string" && RFC3339.test(value), `${label} must be RFC3339`);
  const timestamp = Date.parse(value);
  invariant(Number.isSafeInteger(timestamp), `${label} is invalid`);
  return timestamp;
}

function validateObservedWireEvidence(bytes, { captureReceipt, registrationMode, requiredUntil }) {
  const record = JSON.parse(bytes.toString("utf8"));
  exactKeys(record, OBSERVED_WIRE_KEYS, "observed-wire evidence");
  exactKeys(record.routeStatuses, OBSERVED_ROUTE_STATUS_KEYS, "observed-wire route statuses");
  invariant(record.$schema === "./observed-wire-record.schema.json", "observed-wire schema reference is invalid");
  invariant(record.schemaVersion === "1.1.0" && record.status === "observed-pass", "observed-wire status is not a v1.1 pass");
  invariant(record.publicResource === PUBLIC_RESOURCE, "observed-wire public resource drifted");
  const expectedRegistrationMode =
    registrationMode === "cimd" ? "client-id-metadata-document" : "dynamic-client-registration";
  invariant(record.registrationMode === expectedRegistrationMode, "observed-wire registration mode mismatched");
  invariant(record.redirectUri === CHATGPT_REDIRECT_URI, "observed-wire callback is invalid");
  invariant(
    record.redirectUriSha256 === sha256(Buffer.from(CHATGPT_REDIRECT_URI, "utf8")),
    "observed-wire callback digest is invalid",
  );
  invariant(
    record.mcpProtocolVersion === "2026-07-28" || record.mcpProtocolVersion === "2025-11-25",
    "observed-wire MCP protocol era is unsupported",
  );
  invariant(typeof record.modernDiscoveryObserved === "boolean", "observed-wire discovery flag is invalid");
  if (record.mcpProtocolVersion === "2026-07-28") {
    invariant(record.modernDiscoveryObserved === true, "observed-wire modern discovery was not observed");
  }
  invariant(
    JSON.stringify(record.requiredIndependentScopes) ===
      JSON.stringify(["things.read", "things.write", "things.admin"]),
    "observed-wire independent Things scopes are invalid",
  );
  invariant(record.offlineAccessRequested === true, "observed-wire offline_access was not requested");
  invariant(
    record.offlineAccessSemantics === "refresh-only-no-things-authorization",
    "observed-wire offline_access semantics drifted",
  );
  invariant(record.resourceIndicatorObserved === true, "observed-wire resource indicator was not observed");
  invariant(record.pkceS256Observed === true, "observed-wire PKCE S256 was not observed");
  invariant(
    DIGEST.test(record.captureReceiptSha256) && record.captureReceiptSha256 === captureReceipt.sha256,
    "observed-wire capture receipt digest is invalid",
  );
  invariant(
    record.routeStatuses.mcp === 401 &&
      record.routeStatuses.protectedResourceMetadata === 200 &&
      record.routeStatuses.authorizationServerMetadata === 200 &&
      record.routeStatuses.authorization === 503,
    "observed-wire route observations are invalid",
  );
  invariant(
    record.routeStatuses.registration === (registrationMode === "dcr" ? 503 : null),
    "observed-wire registration route observation mismatched",
  );
  invariant(
    record.secretFree === true && record.redactionsVerified === true && record.prohibitedDataAbsent === true,
    "observed-wire privacy attestations are incomplete",
  );
  invariant(DIGEST.test(record.evidenceDigestSha256), "observed-wire evidence digest is invalid");
  const evidenceWithoutDigest = { ...record };
  delete evidenceWithoutDigest.evidenceDigestSha256;
  invariant(
    record.evidenceDigestSha256 === sha256(Buffer.from(canonicalJson(evidenceWithoutDigest), "utf8")),
    "observed-wire internal evidence digest mismatched",
  );
  const capturedAt = observedTimestamp(record.capturedAt, "observed-wire capturedAt");
  const expiresAt = observedTimestamp(record.expiresAt, "observed-wire expiresAt");
  const now = Date.now();
  invariant(capturedAt <= now + MAX_CLOCK_SKEW_MS, "observed-wire capture is from the future");
  invariant(expiresAt > now && expiresAt > capturedAt, "observed-wire evidence is expired");
  invariant(expiresAt - capturedAt <= MAX_PUBLIC_TTL_MS, "observed-wire evidence TTL exceeds public freshness limit");
  invariant(
    capturedAt >= captureReceipt.receipt.createdAt &&
      capturedAt <= captureReceipt.receipt.expiresAt,
    "observed-wire timestamps are not bound to the capture receipt",
  );
  invariant(expiresAt >= requiredUntil, "observed-wire evidence expires before the public activation receipt");
}

async function currentBindings(options, { publicMode, receiptBindings, registrationMode, requiredUntil }) {
  const { distributionDigest, distributionRoot } = await selectedDistribution(options.runtime_root);
  const auditBytes = await readOwnedStable(path.join(distributionRoot, "audit-manifest.json"), {
    label: "selected audit manifest",
    ownerOnly: true,
  });
  const capabilityBytes = await readOwnedStable(path.join(distributionRoot, "things-capability-manifest.json"), {
    label: "selected capability manifest",
    ownerOnly: true,
  });
  const settingsBytes = await readOwnedStable(options.settings, { label: "runtime settings", ownerOnly: true });
  const configBytes = await readOwnedStable(options.cloudflared_config, {
    label: "Cloudflare ingress config",
    ownerOnly: true,
  });
  const conformanceBytes = await readOwnedStable(options.conformance_result, { label: "conformance result" });
  const conformanceCatalog = parseConformance(conformanceBytes);
  const computed = {
    auditManifestSha256: sha256(Buffer.from(canonicalJson(JSON.parse(auditBytes.toString("utf8"))), "utf8")),
    distributionDigest,
    capabilityManifestSha256: sha256(capabilityBytes),
    settingsSha256: sha256(settingsBytes),
    routeManifestSha256: sha256(Buffer.from(canonicalJson(ROUTE_MANIFEST), "utf8")),
    cloudflaredConfigSha256: sha256(configBytes),
    catalogSha256: conformanceCatalog.catalogSha256,
    scopeMapSha256: conformanceCatalog.scopeMapSha256,
    manifestProjectionSha256: conformanceCatalog.manifestProjectionSha256,
    conformanceResultSha256: sha256(conformanceBytes),
  };
  if (publicMode) {
    const captureReceipt = await verifyReceipt({
      ...options,
      allow_expired_capture: true,
      expect_mode: "capture",
      receipt: options.capture_receipt,
    });
    const policyBytes = await readOwnedStable(options.oauth_policy, { label: "OAuth policy", ownerOnly: true });
    const loginBytes = await readOwnedStable(options.oauth_login_credential, {
      label: "OAuth login credential",
      ownerOnly: true,
    });
    computed.oauthPolicySha256 = sha256(policyBytes);
    computed.oauthLoginCredentialSha256 = sha256(loginBytes);
    const observedBytes = await readOwnedStable(options.observed_wire_evidence, { label: "observed-wire evidence" });
    validateObservedWireEvidence(observedBytes, { captureReceipt, registrationMode, requiredUntil });
    computed.observedWireEvidenceSha256 = sha256(observedBytes);
  } else {
    computed.oauthPolicySha256 = ZERO_DIGEST;
    computed.oauthLoginCredentialSha256 = ZERO_DIGEST;
    computed.observedWireEvidenceSha256 = ZERO_DIGEST;
  }
  if (receiptBindings !== undefined) {
    for (const [key, value] of Object.entries(computed)) {
      invariant(receiptBindings[key] === value, `activation receipt ${key} drifted`);
    }
  }
  return computed;
}

function parseConformance(bytes) {
  const report = JSON.parse(bytes.toString("utf8"));
  exactKeys(report.catalog, ["toolCount", "serverCounts", "catalogSha256", "scopeMapSha256", "manifestProjectionSha256"], "conformance catalog");
  invariant(report.execution?.status === "passed", "conformance execution did not pass");
  for (const key of ["catalogSha256", "scopeMapSha256", "manifestProjectionSha256"]) {
    invariant(DIGEST.test(report.catalog[key]), `conformance ${key} is invalid`);
  }
  return report.catalog;
}

async function issueReceipt(options) {
  const mode = options.mode;
  invariant(mode === "capture" || mode === "public", "activation mode is invalid");
  const publicMode = mode === "public";
  const ttlSeconds = Number(options.ttl_seconds);
  invariant(Number.isInteger(ttlSeconds) && ttlSeconds > 0, "TTL must be positive whole seconds");
  const ttlMs = ttlSeconds * 1_000;
  invariant(ttlMs <= (publicMode ? MAX_PUBLIC_TTL_MS : MAX_CAPTURE_TTL_MS), "activation TTL exceeds its mode limit");
  const registrationMode = publicMode ? options.registration_mode : null;
  invariant(!publicMode || registrationMode === "cimd" || registrationMode === "dcr", "public registration mode must be cimd or dcr");
  invariant(publicMode || options.registration_mode === undefined, "capture mode forbids a registration mode");

  const createdAt = Date.now();
  const expiresAt = createdAt + ttlMs;
  const configReport = await verifyConfig({
    input: options.cloudflared_config,
    tunnel_name: options.tunnel_name,
    credentials_file: options.credentials_file,
  });
  const computed = await currentBindings(options, {
    publicMode,
    registrationMode,
    requiredUntil: expiresAt,
  });
  invariant(computed.cloudflaredConfigSha256 === configReport.cloudflaredConfigSha256, "Cloudflare config verification digest drifted");
  const bindings = { ...computed };
  exactKeys(bindings, BINDING_KEYS, "activation bindings");
  const receipt = {
    schemaVersion: 1,
    status: "pass",
    mode,
    noSecrets: true,
    createdAt,
    expiresAt,
    publicOrigin: PUBLIC_ORIGIN,
    publicResource: PUBLIC_RESOURCE,
    registrationMode,
    remotePublicReady: publicMode,
    toolDispatchEnabled: publicMode,
    tunnelAllowed: true,
    bindings,
  };
  exactKeys(receipt, RECEIPT_KEYS, "activation receipt");
  await writePrivateAtomic(options.receipt, Buffer.from(`${canonicalJson(receipt)}\n`, "utf8"), { exclusive: true });
  return { mode, distributionDigest: bindings.distributionDigest, expiresAt: receipt.expiresAt };
}

function validateBindingShapes(bindings) {
  exactKeys(bindings, BINDING_KEYS, "activation bindings");
  invariant(DISTRIBUTION_DIGEST.test(bindings.distributionDigest), "activation distribution digest is invalid");
  for (const key of BINDING_KEYS) {
    if (key === "distributionDigest") continue;
    invariant(DIGEST.test(bindings[key]), `activation ${key} is invalid`);
  }
}

function decodeReceiptIdentity(bytes, options = {}) {
  const receipt = JSON.parse(bytes.toString("utf8"));
  exactKeys(receipt, RECEIPT_KEYS, "activation receipt");
  validateBindingShapes(receipt.bindings);
  invariant(receipt.schemaVersion === 1 && receipt.status === "pass" && receipt.noSecrets === true, "activation receipt status is invalid");
  invariant(receipt.mode === "capture" || receipt.mode === "public", "activation receipt mode is invalid");
  invariant(receipt.publicOrigin === PUBLIC_ORIGIN && receipt.publicResource === PUBLIC_RESOURCE, "activation receipt public route drifted");
  invariant(receipt.tunnelAllowed === true, "activation receipt tunnel gate is invalid");
  invariant(Number.isSafeInteger(receipt.createdAt) && Number.isSafeInteger(receipt.expiresAt), "activation receipt timestamps are invalid");
  const now = Date.now();
  const maximumTtl = receipt.mode === "public" ? MAX_PUBLIC_TTL_MS : MAX_CAPTURE_TTL_MS;
  invariant(receipt.createdAt <= now + MAX_CLOCK_SKEW_MS, "activation receipt is from the future");
  invariant(receipt.expiresAt > receipt.createdAt, "activation receipt timestamps are invalid");
  if (!(options.allow_expired_capture === true && receipt.mode === "capture")) {
    invariant(receipt.expiresAt > now, "activation receipt expired");
  }
  invariant(receipt.expiresAt - receipt.createdAt <= maximumTtl, "activation receipt TTL is invalid");
  const publicMode = receipt.mode === "public";
  if (publicMode) {
    invariant(receipt.registrationMode === "cimd" || receipt.registrationMode === "dcr", "public registration mode is invalid");
    invariant(receipt.remotePublicReady === true && receipt.toolDispatchEnabled === true, "public activation gates are not all enabled");
    for (const key of [
      "catalogSha256",
      "scopeMapSha256",
      "manifestProjectionSha256",
      "oauthPolicySha256",
      "oauthLoginCredentialSha256",
      "observedWireEvidenceSha256",
      "conformanceResultSha256",
    ]) {
      invariant(receipt.bindings[key] !== ZERO_DIGEST, `public activation ${key} cannot be zero`);
    }
  } else {
    invariant(receipt.registrationMode === null, "capture registration mode must be null");
    invariant(receipt.remotePublicReady === false && receipt.toolDispatchEnabled === false, "capture activation cannot dispatch tools");
    for (const key of ["oauthPolicySha256", "oauthLoginCredentialSha256", "observedWireEvidenceSha256"]) {
      invariant(receipt.bindings[key] === ZERO_DIGEST, `capture activation ${key} must be zero`);
    }
  }
  invariant(receipt.bindings.routeManifestSha256 === sha256(Buffer.from(canonicalJson(ROUTE_MANIFEST), "utf8")), "route manifest digest drifted");
  if (options.expect_mode !== undefined) invariant(receipt.mode === options.expect_mode, "activation mode does not match expectation");
  return receipt;
}

async function readReceiptIdentity(options) {
  const bytes = await readOwnedStable(options.receipt, {
    label: "remote activation receipt",
    ownerOnly: true,
    maximumBytes: 16_384,
  });
  const receipt = decodeReceiptIdentity(bytes, options);
  return { bytes, receipt, sha256: sha256(bytes) };
}

async function verifyReceipt(options) {
  const identity = await readReceiptIdentity(options);
  const publicMode = identity.receipt.mode === "public";
  await currentBindings(options, {
    publicMode,
    receiptBindings: identity.receipt.bindings,
    registrationMode: identity.receipt.registrationMode,
    requiredUntil: identity.receipt.expiresAt,
  });
  return identity;
}

async function snapshotCaptureReceipt(options) {
  const verified = await verifyReceipt({ ...options, expect_mode: "capture" });
  await writePrivateAtomic(options.output, verified.bytes, { exclusive: true });
  const snapshot = await readOwnedStable(options.output, {
    label: "capture receipt snapshot",
    ownerOnly: true,
    maximumBytes: 16_384,
  });
  invariant(sha256(snapshot) === verified.sha256, "capture receipt snapshot digest drifted");
  return { captureReceiptSha256: verified.sha256, expiresAt: verified.receipt.expiresAt };
}

async function revokeReceipt(options) {
  normalizedAbsolute(options.receipt, "receipt path");
  let bytes;
  try {
    bytes = await readOwnedStable(options.receipt, {
      label: "remote activation receipt",
      ownerOnly: true,
      maximumBytes: 16_384,
    });
  } catch (error) {
    if (error?.code === "ENOENT") return;
    throw error;
  }
  await validateOwnedDirectory(path.dirname(options.receipt), "receipt parent");
  if (options.expected_sha256 !== undefined) {
    invariant(DIGEST.test(options.expected_sha256), "expected activation receipt digest is invalid");
    invariant(sha256(bytes) === options.expected_sha256, "activation receipt identity changed before revoke");
  }
  await unlink(options.receipt);
  try {
    await lstat(options.receipt);
    throw new Error("activation receipt remained after revoke");
  } catch (error) {
    if (error?.code !== "ENOENT") throw error;
  }
}

async function receiptDigest(options) {
  const bytes = await readOwnedStable(options.receipt, {
    label: "remote activation receipt",
    ownerOnly: true,
    maximumBytes: 16_384,
  });
  return sha256(bytes);
}

function parseArgs(argv) {
  const [operation, ...rest] = argv;
  invariant(
    [
      "issue",
      "receipt-digest",
      "render-config",
      "revoke",
      "route-digest",
      "snapshot-capture",
      "unexpired",
      "verify",
      "verify-config",
    ].includes(operation),
    "operation is invalid",
  );
  const options = {};
  for (let index = 0; index < rest.length; index += 2) {
    const argument = rest[index];
    const value = rest[index + 1];
    invariant(argument?.startsWith("--") && value !== undefined, "argument pair is invalid");
    const name = argument.slice(2).replaceAll("-", "_");
    invariant(options[name] === undefined, "duplicate argument is invalid");
    options[name] = value;
  }
  return { operation, options };
}

async function main() {
  const { operation, options } = parseArgs(process.argv.slice(2));
  if (operation === "render-config") {
    process.stdout.write(`${JSON.stringify(await renderConfig(options))}\n`);
  } else if (operation === "verify-config") {
    process.stdout.write(`${JSON.stringify(await verifyConfig(options))}\n`);
  } else if (operation === "issue") {
    process.stdout.write(`${JSON.stringify(await issueReceipt(options))}\n`);
  } else if (operation === "snapshot-capture") {
    process.stdout.write(`${JSON.stringify(await snapshotCaptureReceipt(options))}\n`);
  } else if (operation === "verify") {
    const verified = await verifyReceipt(options);
    process.stdout.write(`${verified.receipt.mode}\n`);
  } else if (operation === "unexpired") {
    invariant(options.expect_mode === "capture" || options.expect_mode === "public", "unexpired expect-mode is invalid");
    const identity = await readReceiptIdentity(options);
    process.stdout.write(`${identity.receipt.mode}\n`);
  } else if (operation === "revoke") {
    await revokeReceipt(options);
    process.stdout.write('{"status":"revoked"}\n');
  } else if (operation === "receipt-digest") {
    process.stdout.write(`${await receiptDigest(options)}\n`);
  } else {
    process.stdout.write(`${sha256(Buffer.from(canonicalJson(ROUTE_MANIFEST), "utf8"))}\n`);
  }
}

try {
  await main();
} catch {
  process.stderr.write('{"status":"error","reasonCode":"MCPHUB_REMOTE_ACTIVATION_INVALID"}\n');
  process.exitCode = 1;
}
