import { constants } from "node:fs";
import { lstat, open, realpath, unlink } from "node:fs/promises";
import path from "node:path";

export const BUILD_PUBLICATION_LOCK_NAME = ".dist-build.lock";

const LOCK_MODE = 0o600n;
const PERMISSION_MASK = 0o777n;

function invariant(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function currentUid() {
  invariant(typeof process.getuid === "function", "build publication locking requires a POSIX runtime");
  return BigInt(process.getuid());
}

function sameInode(left, right) {
  return left.dev === right.dev && left.ino === right.ino;
}

function assertLockMetadata(stats, expectedIdentity = null) {
  invariant(stats.isFile(), "build publication lock must be a regular file");
  invariant(stats.uid === currentUid(), "build publication lock owner mismatch");
  invariant((stats.mode & PERMISSION_MASK) === LOCK_MODE, "build publication lock mode mismatch");
  invariant(stats.nlink === 1n, "build publication lock must have exactly one link");
  if (expectedIdentity !== null) {
    invariant(sameInode(stats, expectedIdentity), "build publication lock identity changed");
  }
}

async function validateRoot(rootPath, expectedIdentity = null) {
  invariant(typeof rootPath === "string" && path.isAbsolute(rootPath), "build publication root must be absolute");
  invariant(path.resolve(rootPath) === rootPath, "build publication root must be normalized");
  const stats = await lstat(rootPath, { bigint: true });
  invariant(stats.isDirectory() && !stats.isSymbolicLink(), "build publication root must be a non-symlink directory");
  invariant(stats.uid === currentUid(), "build publication root owner mismatch");
  const permissions = stats.mode & PERMISSION_MASK;
  invariant((permissions & 0o022n) === 0n, "build publication root must not be group- or other-writable");
  invariant((permissions & 0o300n) === 0o300n, "build publication root must be owner-writable and searchable");
  invariant(await realpath(rootPath) === rootPath, "build publication root must not traverse a symlink");
  if (expectedIdentity !== null) {
    invariant(sameInode(stats, expectedIdentity), "build publication root identity changed");
  }
  return stats;
}

async function acquireBuildPublicationLock(rootPath) {
  const rootIdentity = await validateRoot(rootPath);
  invariant(Number.isInteger(constants.O_NOFOLLOW) && constants.O_NOFOLLOW !== 0, "O_NOFOLLOW is required");
  const lockPath = path.join(rootPath, BUILD_PUBLICATION_LOCK_NAME);
  let handle;
  try {
    handle = await open(
      lockPath,
      constants.O_CREAT | constants.O_EXCL | constants.O_RDWR | constants.O_NOFOLLOW,
      Number(LOCK_MODE),
    );
  } catch {
    throw new Error("build publication lock could not be acquired safely");
  }

  try {
    const descriptorIdentity = await handle.stat({ bigint: true });
    assertLockMetadata(descriptorIdentity);
    await validateRoot(rootPath, rootIdentity);
    const pathIdentity = await lstat(lockPath, { bigint: true });
    assertLockMetadata(pathIdentity, descriptorIdentity);
    return Object.freeze({ descriptorIdentity, handle, lockPath, rootIdentity, rootPath });
  } catch (error) {
    await handle.close();
    throw error;
  }
}

async function releaseBuildPublicationLock(lock) {
  let releaseError = null;
  try {
    await validateRoot(lock.rootPath, lock.rootIdentity);
    const descriptorBefore = await lock.handle.stat({ bigint: true });
    assertLockMetadata(descriptorBefore, lock.descriptorIdentity);
    const pathIdentity = await lstat(lock.lockPath, { bigint: true });
    assertLockMetadata(pathIdentity, lock.descriptorIdentity);
    await unlink(lock.lockPath);
    const descriptorAfter = await lock.handle.stat({ bigint: true });
    invariant(sameInode(descriptorAfter, lock.descriptorIdentity), "build publication lock descriptor identity changed");
    invariant(descriptorAfter.uid === currentUid(), "build publication lock descriptor owner changed");
    invariant((descriptorAfter.mode & PERMISSION_MASK) === LOCK_MODE, "build publication lock descriptor mode changed");
    invariant(descriptorAfter.nlink === 0n, "build publication lock unlink was not exact");
  } catch {
    releaseError = new Error("build publication lock could not be released safely");
  }

  try {
    await lock.handle.close();
  } catch {
    releaseError ??= new Error("build publication lock descriptor could not be closed safely");
  }
  if (releaseError !== null) {
    throw releaseError;
  }
}

/**
 * Serialize publication into one package root. The callback begins only after
 * an owner-only exclusive lock is descriptor- and pathname-verified, and the
 * lock remains held until the callback settles.
 */
export async function withBuildPublicationLock(rootPath, operation) {
  invariant(typeof operation === "function", "build publication operation must be a function");
  const lock = await acquireBuildPublicationLock(rootPath);
  try {
    return await operation();
  } finally {
    await releaseBuildPublicationLock(lock);
  }
}
