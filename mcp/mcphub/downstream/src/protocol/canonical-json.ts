import { createHash } from "node:crypto";

import type { JsonValue } from "./types.js";

function isPlainObject(value: unknown): value is Record<string, unknown> {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    return false;
  }
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

function canonicalize(value: unknown, seen: Set<object>): string {
  if (value === null) {
    return "null";
  }
  if (typeof value === "string" || typeof value === "boolean") {
    return JSON.stringify(value);
  }
  if (typeof value === "number") {
    if (!Number.isFinite(value)) {
      throw new TypeError("canonical_json_non_finite_number");
    }
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    if (seen.has(value)) {
      throw new TypeError("canonical_json_cycle");
    }
    seen.add(value);
    const encoded = `[${value.map((entry) => canonicalize(entry, seen)).join(",")}]`;
    seen.delete(value);
    return encoded;
  }
  if (isPlainObject(value)) {
    if (seen.has(value)) {
      throw new TypeError("canonical_json_cycle");
    }
    seen.add(value);
    const encoded = `{${Object.keys(value)
      .sort()
      .map((key) => {
        const entry = value[key];
        if (entry === undefined) {
          throw new TypeError("canonical_json_undefined");
        }
        return `${JSON.stringify(key)}:${canonicalize(entry, seen)}`;
      })
      .join(",")}}`;
    seen.delete(value);
    return encoded;
  }
  throw new TypeError("canonical_json_invalid_value");
}

export function canonicalJson(value: JsonValue | unknown): string {
  return canonicalize(value, new Set());
}

export function canonicalSha256(value: JsonValue | unknown): string {
  return createHash("sha256").update(canonicalJson(value), "utf8").digest("hex");
}

