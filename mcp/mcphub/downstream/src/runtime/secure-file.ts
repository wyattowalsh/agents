import { createHash } from "node:crypto";
import {
  closeSync,
  constants,
  fstatSync,
  lstatSync,
  openSync,
  readFileSync,
} from "node:fs";
import path from "node:path";

export interface OwnerOnlyRuntimeFile {
  readonly bytes: Buffer;
  readonly sha256: string;
}

function fail(): never {
  throw new Error("runtime_secure_file_invalid");
}

export function readOwnerOnlyRuntimeFile(
  pathname: string,
  maximumBytes = 8 * 1024 * 1024,
): OwnerOnlyRuntimeFile {
  if (
    !path.isAbsolute(pathname) ||
    path.normalize(pathname) !== pathname ||
    pathname.includes("\0") ||
    !Number.isSafeInteger(maximumBytes) ||
    maximumBytes < 1
  ) {
    return fail();
  }
  let before: ReturnType<typeof lstatSync>;
  try {
    before = lstatSync(pathname);
  } catch {
    return fail();
  }
  if (
    !before.isFile() ||
    before.isSymbolicLink() ||
    before.nlink !== 1 ||
    (typeof process.getuid === "function" && before.uid !== process.getuid()) ||
    (before.mode & 0o077) !== 0 ||
    before.size < 1 ||
    before.size > maximumBytes
  ) {
    return fail();
  }
  let descriptor: number;
  try {
    descriptor = openSync(pathname, constants.O_RDONLY | constants.O_NOFOLLOW);
  } catch {
    return fail();
  }
  try {
    const opened = fstatSync(descriptor);
    if (
      !opened.isFile() ||
      opened.dev !== before.dev ||
      opened.ino !== before.ino ||
      opened.size !== before.size ||
      opened.nlink !== 1 ||
      (opened.mode & 0o077) !== 0
    ) {
      return fail();
    }
    const bytes = readFileSync(descriptor);
    const after = lstatSync(pathname);
    if (
      after.dev !== opened.dev ||
      after.ino !== opened.ino ||
      after.size !== opened.size ||
      after.nlink !== 1 ||
      bytes.byteLength !== opened.size
    ) {
      return fail();
    }
    return Object.freeze({
      bytes,
      sha256: createHash("sha256").update(bytes).digest("hex"),
    });
  } catch {
    return fail();
  } finally {
    closeSync(descriptor);
  }
}
