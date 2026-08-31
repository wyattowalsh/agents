import { isIP } from "node:net";

import { OAuthSecurityError } from "../common/errors.js";

const LOCAL_HOSTS = new Set(["localhost", "localhost.localdomain"]);

function reject(): never {
  throw new OAuthSecurityError("oauth_callback_not_allowed");
}

function canonicalHost(value: string): { readonly host: string; readonly ipVersion: 0 | 4 | 6 } {
  let host = value.toLowerCase();
  if (host.startsWith("[") && host.endsWith("]")) {
    host = host.slice(1, -1);
  }
  if (host.includes("%")) {
    return reject();
  }
  const initialVersion = isIP(host);
  if (initialVersion === 0 && host.endsWith(".")) {
    host = host.slice(0, -1);
  }
  const version = isIP(host);
  return { host, ipVersion: version as 0 | 4 | 6 };
}

function ipv4Octets(host: string): readonly number[] {
  const values = host.split(".").map((part) => Number(part));
  if (
    values.length !== 4 ||
    values.some((value) => !Number.isInteger(value) || value < 0 || value > 255)
  ) {
    return reject();
  }
  return values;
}

function prohibitedIpv4(host: string): boolean {
  const octets = ipv4Octets(host);
  const first = octets[0];
  const second = octets[1];
  if (first === undefined || second === undefined) {
    return true;
  }
  return (
    first === 0 ||
    first === 10 ||
    first === 127 ||
    (first === 100 && second >= 64 && second <= 127) ||
    (first === 169 && second === 254) ||
    (first === 172 && second >= 16 && second <= 31) ||
    (first === 192 && second === 168) ||
    (first === 198 && (second === 18 || second === 19)) ||
    first >= 224
  );
}

function ipv6Words(host: string): readonly number[] {
  const halves = host.split("::");
  if (halves.length > 2) {
    return reject();
  }
  const parseParts = (text: string): number[] => {
    if (text.length === 0) {
      return [];
    }
    const result: number[] = [];
    for (const part of text.split(":")) {
      if (part.includes(".")) {
        const octets = ipv4Octets(part);
        result.push((octets[0]! << 8) | octets[1]!, (octets[2]! << 8) | octets[3]!);
      } else if (!/^[a-f0-9]{1,4}$/u.test(part)) {
        return reject();
      } else {
        result.push(Number.parseInt(part, 16));
      }
    }
    return result;
  };
  const left = parseParts(halves[0] ?? "");
  const right = parseParts(halves[1] ?? "");
  if (halves.length === 1) {
    if (left.length !== 8) {
      return reject();
    }
    return left;
  }
  const missing = 8 - left.length - right.length;
  if (missing < 1) {
    return reject();
  }
  return [...left, ...Array.from({ length: missing }, () => 0), ...right];
}

function prohibitedIpv6(host: string): boolean {
  const words = ipv6Words(host);
  const first = words[0] ?? 0;
  const unspecified = words.every((word) => word === 0);
  const loopback = words.slice(0, 7).every((word) => word === 0) && words[7] === 1;
  const linkLocal = (first & 0xffc0) === 0xfe80;
  const uniqueLocal = (first & 0xfe00) === 0xfc00;
  const multicast = (first & 0xff00) === 0xff00;
  const mappedIpv4 =
    words.slice(0, 5).every((word) => word === 0) &&
    words[5] === 0xffff &&
    words[6] !== undefined &&
    words[7] !== undefined;
  if (mappedIpv4) {
    const address = `${words[6]! >> 8}.${words[6]! & 0xff}.${words[7]! >> 8}.${words[7]! & 0xff}`;
    return prohibitedIpv4(address);
  }
  return unspecified || loopback || linkLocal || uniqueLocal || multicast;
}

function assertPublicHost(hostname: string): void {
  const { host, ipVersion } = canonicalHost(hostname);
  if (
    host.length === 0 ||
    LOCAL_HOSTS.has(host) ||
    host.endsWith(".localhost") ||
    (ipVersion === 4 && prohibitedIpv4(host)) ||
    (ipVersion === 6 && prohibitedIpv6(host))
  ) {
    reject();
  }
}

export function assertSafeHttpsUrl(value: string): URL {
  if (value.length === 0 || value.length > 2_048 || /[\u0000-\u001f\u007f]/u.test(value)) {
    return reject();
  }
  let parsed: URL;
  try {
    parsed = new URL(value);
  } catch {
    return reject();
  }
  assertPublicHost(parsed.hostname);
  if (
    parsed.protocol !== "https:" ||
    parsed.username.length > 0 ||
    parsed.password.length > 0 ||
    parsed.hash.length > 0 ||
    parsed.port.length > 0 ||
    parsed.href !== value
  ) {
    return reject();
  }
  return parsed;
}

export function validateApprovedCallbacks(callbacks: readonly string[]): ReadonlySet<string> {
  if (callbacks.length !== 1 || new Set(callbacks).size !== callbacks.length) {
    return reject();
  }
  for (const callback of callbacks) {
    assertSafeHttpsUrl(callback);
  }
  return new Set(callbacks);
}

export function requireApprovedCallback(callback: string, approved: ReadonlySet<string>): void {
  assertSafeHttpsUrl(callback);
  if (!approved.has(callback)) {
    throw new OAuthSecurityError("oauth_callback_not_allowed", {
      oauthError: "access_denied",
    });
  }
}
