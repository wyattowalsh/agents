import { scryptSync, timingSafeEqual } from "node:crypto";

import type { LoginProofVerifier } from "../oauth/service.js";
import type { RegistrationMode } from "../policy/oauth-policy.js";
import { constantTimeTextEqual } from "../security/common/crypto.js";
import {
  CimdMetadataResolver,
  type ApprovedClientPolicy,
  type CimdLoader,
} from "../security/oauth/clients.js";
import { readOwnerOnlyRuntimeFile } from "./secure-file.js";

const SHA256 = /^[a-f0-9]{64}$/u;
const BOUNDED_IDENTIFIER = /^[^\u0000-\u001f\u007f]{1,512}$/u;
const BASE64URL = /^[A-Za-z0-9_-]+$/u;
const CIMD_MAX_BYTES = 64 * 1024;
const SCRYPT_KEY_BYTES = 32;
const SCRYPT_OPTIONS = Object.freeze({ N: 16_384, r: 8, p: 1, maxmem: 32 * 1024 * 1024 });

interface LoginCredential {
  readonly accountKey: string;
  readonly derivedKey: Buffer;
  readonly principal: string;
  readonly salt: Buffer;
}

export interface LoadedOAuthRuntimeConfig {
  readonly cimdResolver: CimdMetadataResolver | null;
  readonly clientPolicy: ApprovedClientPolicy;
  readonly credentialSha256: string;
  readonly policySha256: string;
  readonly registrationPrincipal: string;
  readonly verifyLoginProof: LoginProofVerifier;
}

function fail(): never {
  throw new Error("runtime_oauth_config_invalid");
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

function parseJson(bytes: Uint8Array): unknown {
  try {
    return JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes)) as unknown;
  } catch {
    return fail();
  }
}

function identifier(value: unknown): string {
  return typeof value === "string" && BOUNDED_IDENTIFIER.test(value) ? value : fail();
}

function base64urlBytes(value: unknown, expectedBytes: number): Buffer {
  if (typeof value !== "string" || !BASE64URL.test(value)) return fail();
  const bytes = Buffer.from(value, "base64url");
  if (bytes.byteLength !== expectedBytes || bytes.toString("base64url") !== value) return fail();
  return bytes;
}

function parsePolicy(value: unknown): Readonly<{
  clientPolicy: ApprovedClientPolicy;
  registrationPrincipal: string;
}> {
  const source = record(value);
  exactKeys(source, ["client", "registrationPrincipal", "schemaVersion"]);
  if (source.schemaVersion !== 1) return fail();
  const client = record(source.client);
  exactKeys(client, [
    "approvedCallbacks",
    "approvedClientId",
    "approvedMetadataDigest",
    "registrationMode",
  ]);
  const rawRegistrationMode = client.registrationMode;
  if (rawRegistrationMode !== "cimd" && rawRegistrationMode !== "dcr") return fail();
  const registrationMode: RegistrationMode = rawRegistrationMode;
  const rawApprovedClientId = client.approvedClientId;
  let approvedClientId: string | null = null;
  if (registrationMode === "cimd") {
    if (
      typeof rawApprovedClientId !== "string" ||
      !rawApprovedClientId.startsWith("https://")
    ) {
      return fail();
    }
    approvedClientId = rawApprovedClientId;
  } else if (rawApprovedClientId !== null) {
    return fail();
  }
  const approvedCallbacks = client.approvedCallbacks;
  if (!Array.isArray(approvedCallbacks) || approvedCallbacks.length !== 1) {
    return fail();
  }
  const approvedCallback = approvedCallbacks[0];
  if (typeof approvedCallback !== "string") return fail();
  const approvedMetadataDigest = client.approvedMetadataDigest;
  if (typeof approvedMetadataDigest !== "string" || !SHA256.test(approvedMetadataDigest)) {
    return fail();
  }
  return Object.freeze({
    clientPolicy: Object.freeze({
      registrationMode,
      approvedClientId,
      approvedCallbacks: Object.freeze([approvedCallback]),
      approvedMetadataDigest,
    }),
    registrationPrincipal: identifier(source.registrationPrincipal),
  });
}

function parseLoginCredential(value: unknown): LoginCredential {
  const source = record(value);
  exactKeys(source, ["accountKey", "password", "principal", "schemaVersion"]);
  if (source.schemaVersion !== 1) return fail();
  const password = record(source.password);
  exactKeys(password, ["algorithm", "derivedKey", "salt"]);
  if (password.algorithm !== "scrypt-v1") return fail();
  return Object.freeze({
    accountKey: identifier(source.accountKey),
    derivedKey: base64urlBytes(password.derivedKey, SCRYPT_KEY_BYTES),
    principal: identifier(source.principal),
    salt: base64urlBytes(password.salt, 16),
  });
}

function loginProofVerifier(credential: LoginCredential): LoginProofVerifier {
  return async (proof, expectedNonce) => {
    const source = record(proof);
    exactKeys(source, ["accountKey", "nonce", "password"]);
    const accountKey = identifier(source.accountKey);
    const nonce = identifier(source.nonce);
    const password = source.password;
    if (
      typeof password !== "string" ||
      password.length < 1 ||
      password.length > 1_024 ||
      /[\u0000\r\n]/u.test(password)
    ) {
      return fail();
    }
    const candidate = scryptSync(password, credential.salt, SCRYPT_KEY_BYTES, SCRYPT_OPTIONS);
    if (
      !timingSafeEqual(candidate, credential.derivedKey) ||
      !constantTimeTextEqual(accountKey, credential.accountKey) ||
      !constantTimeTextEqual(nonce, expectedNonce)
    ) {
      return fail();
    }
    return Object.freeze({
      accountKey: credential.accountKey,
      principal: credential.principal,
    });
  };
}

async function boundedResponseBody(response: Response): Promise<Uint8Array> {
  const declared = response.headers.get("content-length");
  if (declared !== null && (!/^\d+$/u.test(declared) || Number(declared) > CIMD_MAX_BYTES)) {
    return fail();
  }
  if (response.body === null) return fail();
  const reader = response.body.getReader();
  const chunks: Uint8Array[] = [];
  let total = 0;
  try {
    while (true) {
      const item = await reader.read();
      if (item.done) break;
      total += item.value.byteLength;
      if (total > CIMD_MAX_BYTES) return fail();
      chunks.push(item.value);
    }
  } finally {
    reader.releaseLock();
  }
  const body = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    body.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return body;
}

const cimdLoader: CimdLoader = async (clientId, signal) => {
  const response = await fetch(clientId, {
    cache: "no-store",
    credentials: "omit",
    headers: { accept: "application/json" },
    redirect: "error",
    referrerPolicy: "no-referrer",
    signal,
  });
  return Object.freeze({
    body: await boundedResponseBody(response),
    contentType: response.headers.get("content-type") ?? "",
    finalUrl: response.url,
    status: response.status,
  });
};

export function loadOAuthRuntimeConfig(input: {
  readonly credentialPath: string;
  readonly policyPath: string;
}): LoadedOAuthRuntimeConfig {
  const policyFile = readOwnerOnlyRuntimeFile(input.policyPath, 64 * 1024);
  const credentialFile = readOwnerOnlyRuntimeFile(input.credentialPath, 16 * 1024);
  const policy = parsePolicy(parseJson(policyFile.bytes));
  const credential = parseLoginCredential(parseJson(credentialFile.bytes));
  return Object.freeze({
    cimdResolver:
      policy.clientPolicy.registrationMode === "cimd"
        ? new CimdMetadataResolver(cimdLoader)
        : null,
    clientPolicy: policy.clientPolicy,
    credentialSha256: credentialFile.sha256,
    policySha256: policyFile.sha256,
    registrationPrincipal: policy.registrationPrincipal,
    verifyLoginProof: loginProofVerifier(credential),
  });
}

export function registrationModeOf(
  config: LoadedOAuthRuntimeConfig,
): RegistrationMode {
  const mode = config.clientPolicy.registrationMode;
  return mode === "cimd" || mode === "dcr" ? mode : fail();
}
