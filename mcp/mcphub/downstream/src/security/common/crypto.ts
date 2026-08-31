import { createHash, randomBytes, timingSafeEqual } from "node:crypto";

import { OAuthSecurityError } from "./errors.js";

function canonicalize(value: unknown, seen: Set<object>): unknown {
  if (value === null || typeof value === "string" || typeof value === "boolean") {
    return value;
  }
  if (typeof value === "number") {
    if (!Number.isFinite(value)) {
      throw new OAuthSecurityError("oauth_client_metadata_invalid");
    }
    return value;
  }
  if (Array.isArray(value)) {
    if (seen.has(value)) {
      throw new OAuthSecurityError("oauth_client_metadata_invalid");
    }
    seen.add(value);
    const result = value.map((item) => canonicalize(item, seen));
    seen.delete(value);
    return result;
  }
  if (typeof value === "object") {
    if (seen.has(value)) {
      throw new OAuthSecurityError("oauth_client_metadata_invalid");
    }
    seen.add(value);
    const record = value as Record<string, unknown>;
    const result: Record<string, unknown> = {};
    for (const key of Object.keys(record).sort()) {
      const item = record[key];
      if (item === undefined) {
        throw new OAuthSecurityError("oauth_client_metadata_invalid");
      }
      result[key] = canonicalize(item, seen);
    }
    seen.delete(value);
    return result;
  }
  throw new OAuthSecurityError("oauth_client_metadata_invalid");
}

export function canonicalJson(value: unknown): string {
  return JSON.stringify(canonicalize(value, new Set()));
}

export function sha256(value: string | Uint8Array): string {
  return createHash("sha256").update(value).digest("hex");
}

export function hashOpaque(value: string): string {
  return sha256(Buffer.from(value, "utf8"));
}

export function randomOpaque(bytes = 32): string {
  if (!Number.isInteger(bytes) || bytes < 32) {
    throw new OAuthSecurityError("oauth_token_invalid");
  }
  return randomBytes(bytes).toString("base64url");
}

export function constantTimeTextEqual(left: string, right: string): boolean {
  const leftDigest = createHash("sha256").update(left, "utf8").digest();
  const rightDigest = createHash("sha256").update(right, "utf8").digest();
  return timingSafeEqual(leftDigest, rightDigest);
}
