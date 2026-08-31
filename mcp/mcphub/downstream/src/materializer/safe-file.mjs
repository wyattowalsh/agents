import { constants } from "node:fs";
import { open } from "node:fs/promises";
import path from "node:path";

import { sha256Bytes } from "./canonical.mjs";

function invariant(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function currentUid() {
  invariant(typeof process.getuid === "function", "safe file reads require a POSIX runtime");
  return BigInt(process.getuid());
}

function stableIdentity(before, after) {
  for (const field of ["dev", "ino", "size", "mode", "uid", "gid", "nlink", "mtimeNs", "ctimeNs"]) {
    invariant(before[field] === after[field], `safe file identity changed during read: ${field}`);
  }
}

/**
 * Open once with O_NOFOLLOW, validate the descriptor, read from that descriptor,
 * and revalidate the same inode. Callers consume bytes, never a pathname that
 * would be reopened after validation.
 */
export async function readSafeRegularFile(
  filePath,
  { label = "input file", expectedSha256 = null, expectedSize = null, expectedMode = null, ownerOnly = false, requireSingleLink = true } = {},
) {
  invariant(path.isAbsolute(filePath), `${label} path must be absolute`);
  invariant(Number.isInteger(constants.O_NOFOLLOW) && constants.O_NOFOLLOW !== 0, "O_NOFOLLOW is required");
  let handle;
  try {
    handle = await open(filePath, constants.O_RDONLY | constants.O_NOFOLLOW);
  } catch (error) {
    throw new Error(`${label} could not be opened safely`, { cause: error });
  }
  try {
    const before = await handle.stat({ bigint: true });
    invariant(before.isFile(), `${label} must be a regular file`);
    if (requireSingleLink) invariant(before.nlink === 1n, `${label} must have exactly one link`);
    invariant(before.uid === currentUid(), `${label} must be owned by the current user`);
    const permissions = before.mode & 0o777n;
    invariant((permissions & 0o022n) === 0n, `${label} must not be group- or other-writable`);
    if (ownerOnly) {
      invariant((permissions & 0o077n) === 0n, `${label} must be owner-only`);
    }
    if (expectedMode !== null) {
      invariant(permissions === BigInt(expectedMode), `${label} mode mismatch`);
    }
    if (expectedSize !== null) {
      invariant(before.size === BigInt(expectedSize), `${label} size mismatch`);
    }
    const bytes = await handle.readFile();
    const after = await handle.stat({ bigint: true });
    stableIdentity(before, after);
    invariant(BigInt(bytes.byteLength) === before.size, `${label} short read`);
    if (expectedSha256 !== null) {
      invariant(sha256Bytes(bytes) === expectedSha256, `${label} hash mismatch`);
    }
    return Object.freeze({
      bytes,
      identity: Object.freeze({ dev: before.dev, ino: before.ino, size: before.size }),
      mode: Number(permissions),
    });
  } finally {
    await handle.close();
  }
}
