import { createHash } from "node:crypto";

function normalizeJson(value) {
  if (value === null || typeof value === "string" || typeof value === "boolean") {
    return value;
  }
  if (typeof value === "number") {
    if (!Number.isFinite(value)) {
      throw new TypeError("canonical JSON does not permit non-finite numbers");
    }
    return value;
  }
  if (Array.isArray(value)) {
    return value.map(normalizeJson);
  }
  if (typeof value === "object") {
    const normalized = {};
    for (const key of Object.keys(value).sort()) {
      const child = value[key];
      if (child === undefined) {
        throw new TypeError(`canonical JSON does not permit undefined at ${key}`);
      }
      normalized[key] = normalizeJson(child);
    }
    return normalized;
  }
  throw new TypeError(`canonical JSON does not permit ${typeof value}`);
}

export function canonicalJson(value) {
  return JSON.stringify(normalizeJson(value));
}

export function sha256Bytes(value) {
  return createHash("sha256").update(value).digest("hex");
}

export function sha1Bytes(value) {
  return createHash("sha1").update(value).digest("hex");
}

export function sha512Sri(value) {
  return `sha512-${createHash("sha512").update(value).digest("base64")}`;
}
