import { canonicalJson, constantTimeTextEqual, sha256 } from "../common/crypto.js";
import { OAuthSecurityError } from "../common/errors.js";
import {
  requireExactResource,
  requireObservedRegistrationMode,
  type RegistrationMode,
} from "../../policy/oauth-policy.js";
import {
  assertSafeHttpsUrl,
  requireApprovedCallback,
  validateApprovedCallbacks,
} from "./callbacks.js";

const DIGEST_PATTERN = /^[a-f0-9]{64}$/;
const IDENTIFIER_PATTERN = /^[A-Za-z0-9._~:/-]{1,512}$/;
const CIMD_MAX_BYTES = 64 * 1_024;
const CIMD_CACHE_TTL_MS = 5 * 60 * 1_000;
const CIMD_LOAD_TIMEOUT_MS = 3_000;

export type CimdAuthenticationMethod = "none" | "private_key_jwt";

export interface ApprovedClientPolicy {
  readonly registrationMode: RegistrationMode | null;
  readonly approvedClientId: string | null;
  readonly approvedCallbacks: readonly string[];
  readonly approvedMetadataDigest: string | null;
}

export type ApprovedJwk =
  | {
      readonly alg: "RS256";
      readonly e: string;
      readonly kid: string;
      readonly kty: "RSA";
      readonly n: string;
      readonly use: "sig";
    }
  | {
      readonly alg: "ES256";
      readonly crv: "P-256";
      readonly kid: string;
      readonly kty: "EC";
      readonly use: "sig";
      readonly x: string;
      readonly y: string;
    };

export interface ValidatedCimdClient {
  readonly clientId: string;
  readonly redirectUri: string;
  readonly metadataDigest: string;
  readonly tokenEndpointAuthMethod: CimdAuthenticationMethod;
  readonly jwks: readonly ApprovedJwk[];
}

export interface ValidatedDcrMetadata {
  readonly clientName: string;
  readonly redirectUri: string;
  readonly metadataDigest: string;
  readonly tokenEndpointAuthMethod: "client_secret_basic";
}

interface CimdLoadResult {
  readonly body: Uint8Array;
  readonly contentType: string;
  readonly finalUrl: string;
  readonly status: number;
}

export type CimdLoader = (clientId: string, signal: AbortSignal) => Promise<CimdLoadResult>;

interface CacheEntry {
  readonly binding: string;
  readonly documentJson: string;
  readonly expiresAt: number;
  readonly value: ValidatedCimdClient;
}

function policyCacheKey(policy: ApprovedClientPolicy): string {
  return sha256(
    canonicalJson({
      approvedCallbacks: policy.approvedCallbacks,
      approvedClientId: policy.approvedClientId,
      approvedMetadataDigest: policy.approvedMetadataDigest,
      registrationMode: policy.registrationMode,
    }),
  );
}

function cacheBinding(policy: ApprovedClientPolicy, value: ValidatedCimdClient): string {
  return sha256(
    canonicalJson({
      callbacks: policy.approvedCallbacks,
      clientId: value.clientId,
      jwks: value.jwks,
      metadataDigest: value.metadataDigest,
      mode: policy.registrationMode,
      redirectUri: value.redirectUri,
      tokenEndpointAuthMethod: value.tokenEndpointAuthMethod,
    }),
  );
}

function objectValue(value: unknown): Record<string, unknown> {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw new OAuthSecurityError("oauth_client_metadata_invalid", { oauthError: "invalid_client" });
  }
  return value as Record<string, unknown>;
}

function stringValue(record: Record<string, unknown>, key: string): string {
  const value = record[key];
  if (typeof value !== "string") {
    throw new OAuthSecurityError("oauth_client_metadata_invalid", { oauthError: "invalid_client" });
  }
  return value;
}

function stringArray(record: Record<string, unknown>, key: string): readonly string[] {
  const value = record[key];
  if (!Array.isArray(value) || value.some((item) => typeof item !== "string")) {
    throw new OAuthSecurityError("oauth_client_metadata_invalid", { oauthError: "invalid_client" });
  }
  return value;
}

function exactArray(actual: readonly string[], expected: readonly string[]): boolean {
  return actual.length === expected.length && actual.every((value, index) => value === expected[index]);
}

function validateJwk(value: unknown): ApprovedJwk {
  const record = objectValue(value);
  const kid = stringValue(record, "kid");
  const kty = stringValue(record, "kty");
  const alg = stringValue(record, "alg");
  const use = record.use;
  if (
    !IDENTIFIER_PATTERN.test(kid) ||
    (use !== undefined && use !== "sig") ||
    (kty !== "RSA" && kty !== "EC") ||
    (alg !== "RS256" && alg !== "ES256") ||
    (kty === "RSA" && alg !== "RS256") ||
    (kty === "EC" && alg !== "ES256")
  ) {
    throw new OAuthSecurityError("oauth_client_metadata_invalid", { oauthError: "invalid_client" });
  }
  if (kty === "RSA") {
    const n = stringValue(record, "n");
    const e = stringValue(record, "e");
    if (n.length < 342 || e.length === 0) {
      throw new OAuthSecurityError("oauth_client_metadata_invalid", { oauthError: "invalid_client" });
    }
    return Object.freeze({ alg: "RS256", e, kid, kty: "RSA", n, use: "sig" });
  }
  const crv = stringValue(record, "crv");
  const x = stringValue(record, "x");
  const y = stringValue(record, "y");
  if (crv !== "P-256" || x.length !== 43 || y.length !== 43) {
    throw new OAuthSecurityError("oauth_client_metadata_invalid", { oauthError: "invalid_client" });
  }
  return Object.freeze({ alg: "ES256", crv, kid, kty: "EC", use: "sig", x, y });
}

function validatePolicy(policy: ApprovedClientPolicy, requestedMode: RegistrationMode): {
  readonly approvedCallbacks: ReadonlySet<string>;
  readonly metadataDigest: string;
} {
  requireObservedRegistrationMode(policy.registrationMode, requestedMode);
  const approvedCallbacks = validateApprovedCallbacks(policy.approvedCallbacks);
  const metadataDigest = policy.approvedMetadataDigest;
  if (metadataDigest === null || !DIGEST_PATTERN.test(metadataDigest)) {
    throw new OAuthSecurityError("oauth_client_metadata_invalid", { oauthError: "invalid_client" });
  }
  return { approvedCallbacks, metadataDigest };
}

export function validateCimdDocument(
  document: unknown,
  policy: ApprovedClientPolicy,
): ValidatedCimdClient {
  const policyValues = validatePolicy(policy, "cimd");
  const clientId = policy.approvedClientId;
  if (clientId === null) {
    throw new OAuthSecurityError("oauth_client_metadata_invalid", { oauthError: "invalid_client" });
  }
  assertSafeHttpsUrl(clientId);
  const record = objectValue(document);
  if (stringValue(record, "client_id") !== clientId) {
    throw new OAuthSecurityError("oauth_client_metadata_invalid", { oauthError: "invalid_client" });
  }
  const redirectUris = stringArray(record, "redirect_uris");
  if (redirectUris.length !== 1) {
    throw new OAuthSecurityError("oauth_callback_not_allowed");
  }
  const redirectUri = redirectUris[0];
  if (redirectUri === undefined) {
    throw new OAuthSecurityError("oauth_callback_not_allowed");
  }
  requireApprovedCallback(redirectUri, policyValues.approvedCallbacks);
  const method = stringValue(record, "token_endpoint_auth_method");
  if (method !== "none" && method !== "private_key_jwt") {
    throw new OAuthSecurityError("oauth_client_metadata_invalid", { oauthError: "invalid_client" });
  }
  const digest = sha256(canonicalJson(document));
  if (digest !== policyValues.metadataDigest) {
    throw new OAuthSecurityError("oauth_client_metadata_invalid", { oauthError: "invalid_client" });
  }
  let jwks: readonly ApprovedJwk[] = [];
  if (method === "private_key_jwt") {
    const jwksRecord = objectValue(record.jwks);
    const keys = jwksRecord.keys;
    if (!Array.isArray(keys) || keys.length === 0 || keys.length > 5) {
      throw new OAuthSecurityError("oauth_client_metadata_invalid", { oauthError: "invalid_client" });
    }
    jwks = Object.freeze(keys.map(validateJwk));
    if (new Set(jwks.map((key) => key.kid)).size !== jwks.length) {
      throw new OAuthSecurityError("oauth_client_metadata_invalid", { oauthError: "invalid_client" });
    }
  } else if (record.jwks !== undefined) {
    throw new OAuthSecurityError("oauth_client_metadata_invalid", { oauthError: "invalid_client" });
  }
  return Object.freeze({
    clientId,
    redirectUri,
    metadataDigest: digest,
    tokenEndpointAuthMethod: method,
    jwks,
  });
}

export function validateDcrMetadata(
  document: unknown,
  resource: string,
  policy: ApprovedClientPolicy,
): ValidatedDcrMetadata {
  requireExactResource(resource);
  const policyValues = validatePolicy(policy, "dcr");
  const record = objectValue(document);
  const redirectUris = stringArray(record, "redirect_uris");
  if (redirectUris.length !== 1) {
    throw new OAuthSecurityError("oauth_callback_not_allowed");
  }
  const redirectUri = redirectUris[0];
  if (redirectUri === undefined) {
    throw new OAuthSecurityError("oauth_callback_not_allowed");
  }
  requireApprovedCallback(redirectUri, policyValues.approvedCallbacks);
  if (
    stringValue(record, "token_endpoint_auth_method") !== "client_secret_basic" ||
    !exactArray(stringArray(record, "grant_types"), ["authorization_code", "refresh_token"]) ||
    !exactArray(stringArray(record, "response_types"), ["code"])
  ) {
    throw new OAuthSecurityError("oauth_client_metadata_invalid", { oauthError: "invalid_client" });
  }
  const clientName = stringValue(record, "client_name");
  if (!/^[A-Za-z0-9][A-Za-z0-9 ._-]{0,79}$/.test(clientName)) {
    throw new OAuthSecurityError("oauth_client_metadata_invalid", { oauthError: "invalid_client" });
  }
  const digest = sha256(canonicalJson(document));
  if (digest !== policyValues.metadataDigest) {
    throw new OAuthSecurityError("oauth_client_metadata_invalid", { oauthError: "invalid_client" });
  }
  return Object.freeze({
    clientName,
    redirectUri,
    metadataDigest: digest,
    tokenEndpointAuthMethod: "client_secret_basic",
  });
}

export class CimdMetadataResolver {
  readonly #loader: CimdLoader;
  readonly #cache = new Map<string, CacheEntry>();

  constructor(loader: CimdLoader) {
    this.#loader = loader;
  }

  async resolve(policy: ApprovedClientPolicy, now = Date.now()): Promise<ValidatedCimdClient> {
    const clientId = policy.approvedClientId;
    if (clientId === null) {
      throw new OAuthSecurityError("oauth_client_metadata_invalid", { oauthError: "invalid_client" });
    }
    const cacheKey = policyCacheKey(policy);
    const cached = this.#cache.get(cacheKey);
    if (cached !== undefined && cached.expiresAt > now) {
      let document: unknown;
      try {
        document = JSON.parse(cached.documentJson);
      } catch {
        throw new OAuthSecurityError("oauth_client_metadata_invalid", { oauthError: "invalid_client" });
      }
      const revalidated = validateCimdDocument(document, policy);
      if (!constantTimeTextEqual(cached.binding, cacheBinding(policy, revalidated))) {
        throw new OAuthSecurityError("oauth_client_metadata_invalid", { oauthError: "invalid_client" });
      }
      return revalidated;
    }
    const controller = new AbortController();
    let rejectTimeout: ((reason: Error) => void) | null = null;
    const timeoutFailure = new Promise<never>((_resolve, reject) => {
      rejectTimeout = reject;
    });
    const timeout = setTimeout(() => {
      controller.abort();
      rejectTimeout?.(new Error("cimd_timeout"));
    }, CIMD_LOAD_TIMEOUT_MS);
    timeout.unref();
    let response: CimdLoadResult;
    try {
      response = await Promise.race([this.#loader(clientId, controller.signal), timeoutFailure]);
    } catch {
      throw new OAuthSecurityError("oauth_client_metadata_invalid", {
        httpStatus: 503,
        oauthError: "temporarily_unavailable",
      });
    } finally {
      clearTimeout(timeout);
    }
    if (
      response.status !== 200 ||
      response.finalUrl !== clientId ||
      response.body.byteLength === 0 ||
      response.body.byteLength > CIMD_MAX_BYTES ||
      !/^application\/(?:[a-z0-9.+-]*\+)?json(?:\s*;|$)/iu.test(response.contentType)
    ) {
      throw new OAuthSecurityError("oauth_client_metadata_invalid", { oauthError: "invalid_client" });
    }
    let document: unknown;
    try {
      const text = new TextDecoder("utf-8", { fatal: true }).decode(response.body);
      document = JSON.parse(text);
    } catch {
      throw new OAuthSecurityError("oauth_client_metadata_invalid", { oauthError: "invalid_client" });
    }
    const value = validateCimdDocument(document, policy);
    const documentJson = canonicalJson(document);
    this.#cache.set(cacheKey, {
      binding: cacheBinding(policy, value),
      documentJson,
      value,
      expiresAt: now + CIMD_CACHE_TTL_MS,
    });
    return value;
  }
}
