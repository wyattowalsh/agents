import {
  closeSync,
  constants,
  fchmodSync,
  fstatSync,
  fsyncSync,
  lstatSync,
  mkdirSync,
  openSync,
  readSync,
  type Stats,
  writeFileSync,
} from "node:fs";
import path from "node:path";

import { OAuthSecurityError } from "./errors.js";

const DIRECTORY_MODE = 0o700;
const FILE_MODE = 0o600;

function unsafe(): never {
  throw new OAuthSecurityError("oauth_database_unsafe", { httpStatus: 503 });
}

function currentUid(): number {
  if (typeof process.getuid !== "function") {
    return unsafe();
  }
  return process.getuid();
}

function permissions(stat: Stats): number {
  return stat.mode & 0o777;
}

function sameFile(left: Stats, right: Stats): boolean {
  return left.dev === right.dev && left.ino === right.ino;
}

function assertSafeDirectoryStat(stat: Stats): void {
  if (
    !stat.isDirectory() ||
    stat.isSymbolicLink() ||
    stat.uid !== currentUid() ||
    permissions(stat) !== DIRECTORY_MODE
  ) {
    unsafe();
  }
}

function assertSafeFileStat(stat: Stats): void {
  if (
    !stat.isFile() ||
    stat.isSymbolicLink() ||
    stat.uid !== currentUid() ||
    permissions(stat) !== FILE_MODE ||
    stat.nlink !== 1
  ) {
    unsafe();
  }
}

function requireAbsoluteNormalized(target: string): void {
  if (!path.isAbsolute(target) || path.normalize(target) !== target || target.includes("\0")) {
    unsafe();
  }
}

function pathStat(target: string): Stats {
  try {
    return lstatSync(target);
  } catch {
    return unsafe();
  }
}

export interface FileIdentity {
  readonly device: bigint;
  readonly inode: bigint;
}

export interface RetainedSecureDescriptor {
  readonly fd: number;
  readonly identity: FileIdentity;
  readonly path: string;
  readonly type: "directory" | "file";
}

function identityFromStat(stat: ReturnType<typeof fstatSync>): FileIdentity {
  const value = stat as unknown as { readonly dev: bigint; readonly ino: bigint };
  return Object.freeze({ device: value.dev, inode: value.ino });
}

function identityMatches(stat: ReturnType<typeof fstatSync>, expected: FileIdentity): boolean {
  const value = stat as unknown as { readonly dev: bigint; readonly ino: bigint };
  return value.dev === expected.device && value.ino === expected.inode;
}

export function ensureSecureStateDirectory(stateDirectory: string): string {
  requireAbsoluteNormalized(stateDirectory);
  try {
    mkdirSync(stateDirectory, { mode: DIRECTORY_MODE });
  } catch (error) {
    const code = error instanceof Error && "code" in error ? error.code : undefined;
    if (code !== "EEXIST") {
      unsafe();
    }
  }
  const descriptor = retainSecureDirectory(stateDirectory);
  closeSecureDescriptor(descriptor);
  return stateDirectory;
}

export function retainSecureDirectory(stateDirectory: string): RetainedSecureDescriptor {
  requireAbsoluteNormalized(stateDirectory);
  const before = pathStat(stateDirectory);
  assertSafeDirectoryStat(before);
  let fd: number;
  try {
    fd = openSync(stateDirectory, constants.O_RDONLY | constants.O_DIRECTORY | constants.O_NOFOLLOW);
  } catch {
    return unsafe();
  }
  try {
    const opened = fstatSync(fd, { bigint: true });
    const openedCompat = fstatSync(fd);
    const after = pathStat(stateDirectory);
    assertSafeDirectoryStat(openedCompat);
    assertSafeDirectoryStat(after);
    if (!sameFile(before, openedCompat) || !sameFile(openedCompat, after)) {
      unsafe();
    }
    return Object.freeze({
      fd,
      identity: identityFromStat(opened),
      path: stateDirectory,
      type: "directory" as const,
    });
  } catch (error) {
    closeSync(fd);
    throw error;
  }
}

export function createSecureFile(filePath: string, bytes: string | Uint8Array = ""): void {
  requireAbsoluteNormalized(filePath);
  let fd: number;
  try {
    fd = openSync(
      filePath,
      constants.O_CREAT | constants.O_EXCL | constants.O_RDWR | constants.O_NOFOLLOW,
      FILE_MODE,
    );
  } catch {
    return unsafe();
  }
  try {
    fchmodSync(fd, FILE_MODE);
    if (typeof bytes === "string") {
      writeFileSync(fd, bytes, { encoding: "utf8" });
    } else {
      writeFileSync(fd, bytes);
    }
    fsyncSync(fd);
  } catch (error) {
    throw error instanceof OAuthSecurityError
      ? error
      : new OAuthSecurityError("oauth_database_unsafe", { httpStatus: 503 });
  } finally {
    closeSync(fd);
  }
}

export function retainSecureFile(filePath: string): RetainedSecureDescriptor {
  requireAbsoluteNormalized(filePath);
  const before = pathStat(filePath);
  assertSafeFileStat(before);
  let fd: number;
  try {
    fd = openSync(filePath, constants.O_RDWR | constants.O_NOFOLLOW);
  } catch {
    return unsafe();
  }
  try {
    const opened = fstatSync(fd, { bigint: true });
    const openedCompat = fstatSync(fd);
    const after = pathStat(filePath);
    assertSafeFileStat(openedCompat);
    assertSafeFileStat(after);
    if (!sameFile(before, openedCompat) || !sameFile(openedCompat, after)) {
      unsafe();
    }
    return Object.freeze({
      fd,
      identity: identityFromStat(opened),
      path: filePath,
      type: "file" as const,
    });
  } catch (error) {
    closeSync(fd);
    throw error;
  }
}

export function assertRetainedSecureDescriptor(descriptor: RetainedSecureDescriptor): void {
  let opened: ReturnType<typeof fstatSync>;
  let current: Stats;
  try {
    opened = fstatSync(descriptor.fd, { bigint: true });
    current = lstatSync(descriptor.path);
  } catch {
    return unsafe();
  }
  const openedCompat = fstatSync(descriptor.fd);
  if (descriptor.type === "directory") {
    assertSafeDirectoryStat(openedCompat);
    assertSafeDirectoryStat(current);
  } else {
    assertSafeFileStat(openedCompat);
    assertSafeFileStat(current);
  }
  if (!identityMatches(opened, descriptor.identity)) {
    unsafe();
  }
  const currentIdentity = lstatSync(descriptor.path, { bigint: true });
  if (currentIdentity.dev !== descriptor.identity.device || currentIdentity.ino !== descriptor.identity.inode) {
    unsafe();
  }
}

export function readRetainedSecureFile(descriptor: RetainedSecureDescriptor, maxBytes = 8_192): string {
  if (descriptor.type !== "file") {
    return unsafe();
  }
  assertRetainedSecureDescriptor(descriptor);
  const stat = fstatSync(descriptor.fd);
  if (stat.size <= 0 || stat.size > maxBytes) {
    return unsafe();
  }
  try {
    const buffer = Buffer.alloc(stat.size);
    const read = readSync(descriptor.fd, buffer, 0, stat.size, 0);
    if (read !== stat.size) {
      return unsafe();
    }
    return buffer.toString("utf8");
  } catch {
    return unsafe();
  }
}

export function closeSecureDescriptor(descriptor: RetainedSecureDescriptor): void {
  try {
    closeSync(descriptor.fd);
  } catch {
    // Closing is best-effort; no content is included in errors or logs.
  }
}

export interface OAuthStatePaths {
  readonly stateDirectory: string;
  readonly databasePath: string;
  readonly initializationReceiptPath: string;
}

export function resolveOAuthStatePaths(environment: NodeJS.ProcessEnv = process.env): OAuthStatePaths {
  const configured = environment.MCPHUB_OAUTH_STATE_DIR;
  if (configured === undefined || configured.length === 0 || configured.includes("\0")) {
    return unsafe();
  }
  const stateDirectory = ensureSecureStateDirectory(configured);
  return Object.freeze({
    stateDirectory,
    databasePath: path.join(stateDirectory, "oauth.sqlite3"),
    initializationReceiptPath: path.join(stateDirectory, "oauth.sqlite3.init-receipt.json"),
  });
}
