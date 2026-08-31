import assert from "node:assert/strict";
import {
  chmod,
  link,
  lstat,
  mkdtemp,
  readFile,
  realpath,
  rename,
  rm,
  symlink,
  writeFile,
} from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import {
  BUILD_PUBLICATION_LOCK_NAME,
  withBuildPublicationLock,
} from "../../src/materializer/build-lock.mjs";

async function fixture(t) {
  const rootPath = await realpath(await mkdtemp(path.join(os.tmpdir(), "mcphub-build-lock-")));
  await chmod(rootPath, 0o700);
  t.after(() => rm(rootPath, { recursive: true, force: true }));
  return {
    lockPath: path.join(rootPath, BUILD_PUBLICATION_LOCK_NAME),
    rootPath,
  };
}

async function assertAbsent(filePath) {
  await assert.rejects(lstat(filePath), { code: "ENOENT" });
}

test("an acquired publication lock excludes a concurrent attempt", async (t) => {
  const state = await fixture(t);
  let markAcquired;
  let releaseFirst;
  const acquired = new Promise((resolve) => {
    markAcquired = resolve;
  });
  const hold = new Promise((resolve) => {
    releaseFirst = resolve;
  });

  const first = withBuildPublicationLock(state.rootPath, async () => {
    markAcquired();
    await hold;
    return "published";
  });
  await acquired;
  await assert.rejects(
    withBuildPublicationLock(state.rootPath, async () => "must-not-run"),
    /could not be acquired safely/,
  );
  releaseFirst();
  assert.equal(await first, "published");
  await assertAbsent(state.lockPath);
});

test("success returns the callback value and removes the exact owner-only lock", async (t) => {
  const state = await fixture(t);
  const value = await withBuildPublicationLock(state.rootPath, async () => {
    const stats = await lstat(state.lockPath);
    assert.ok(stats.isFile() && !stats.isSymbolicLink());
    assert.equal(stats.uid, process.getuid());
    assert.equal(stats.mode & 0o777, 0o600);
    assert.equal(stats.nlink, 1);
    return Object.freeze({ fresh: true });
  });
  assert.deepEqual(value, { fresh: true });
  await assertAbsent(state.lockPath);
});

test("callback failure is preserved after exact lock cleanup", async (t) => {
  const state = await fixture(t);
  const callbackError = new Error("synthetic callback failure");
  await assert.rejects(
    withBuildPublicationLock(state.rootPath, async () => {
      throw callbackError;
    }),
    (error) => error === callbackError,
  );
  await assertAbsent(state.lockPath);
});

test("a stale regular lock is refused and preserved", async (t) => {
  const state = await fixture(t);
  await writeFile(state.lockPath, "stale\n", { flag: "wx", mode: 0o600 });
  await assert.rejects(
    withBuildPublicationLock(state.rootPath, async () => undefined),
    /could not be acquired safely/,
  );
  assert.equal(await readFile(state.lockPath, "utf8"), "stale\n");
});

test("a symlink lock is refused without changing its target", async (t) => {
  const state = await fixture(t);
  const targetPath = path.join(state.rootPath, "symlink-target");
  await writeFile(targetPath, "target\n", { mode: 0o600 });
  await symlink(targetPath, state.lockPath);
  await assert.rejects(
    withBuildPublicationLock(state.rootPath, async () => undefined),
    /could not be acquired safely/,
  );
  assert.ok((await lstat(state.lockPath)).isSymbolicLink());
  assert.equal(await readFile(targetPath, "utf8"), "target\n");
});

test("a pre-existing hardlink lock is refused and preserved", async (t) => {
  const state = await fixture(t);
  const targetPath = path.join(state.rootPath, "hardlink-target");
  await writeFile(targetPath, "target\n", { mode: 0o600 });
  await link(targetPath, state.lockPath);
  await assert.rejects(
    withBuildPublicationLock(state.rootPath, async () => undefined),
    /could not be acquired safely/,
  );
  assert.equal((await lstat(targetPath)).nlink, 2);
  assert.equal((await lstat(state.lockPath)).ino, (await lstat(targetPath)).ino);
});

test("a hardlink added while held prevents release of either name", async (t) => {
  const state = await fixture(t);
  const aliasPath = path.join(state.rootPath, "held-lock-alias");
  await assert.rejects(
    withBuildPublicationLock(state.rootPath, async () => {
      await link(state.lockPath, aliasPath);
    }),
    /could not be released safely/,
  );
  const lockStats = await lstat(state.lockPath);
  const aliasStats = await lstat(aliasPath);
  assert.equal(lockStats.ino, aliasStats.ino);
  assert.equal(lockStats.nlink, 2);
});

test("a replacement is detected and never removed", async (t) => {
  const state = await fixture(t);
  const displacedPath = path.join(state.rootPath, "displaced-lock");
  await assert.rejects(
    withBuildPublicationLock(state.rootPath, async () => {
      await rename(state.lockPath, displacedPath);
      await writeFile(state.lockPath, "replacement\n", { flag: "wx", mode: 0o600 });
    }),
    /could not be released safely/,
  );
  assert.equal(await readFile(state.lockPath, "utf8"), "replacement\n");
  assert.ok((await lstat(displacedPath)).isFile());
  assert.notEqual((await lstat(state.lockPath)).ino, (await lstat(displacedPath)).ino);
});

test("a symlink replacement is detected and left untouched", async (t) => {
  const state = await fixture(t);
  const displacedPath = path.join(state.rootPath, "displaced-lock");
  const targetPath = path.join(state.rootPath, "replacement-target");
  await writeFile(targetPath, "target\n", { mode: 0o600 });
  await assert.rejects(
    withBuildPublicationLock(state.rootPath, async () => {
      await rename(state.lockPath, displacedPath);
      await symlink(targetPath, state.lockPath);
    }),
    /could not be released safely/,
  );
  assert.ok((await lstat(state.lockPath)).isSymbolicLink());
  assert.equal(await readFile(targetPath, "utf8"), "target\n");
});

test("an unsafe publication root is rejected before creating a lock", async (t) => {
  const state = await fixture(t);
  await chmod(state.rootPath, 0o777);
  await assert.rejects(
    withBuildPublicationLock(state.rootPath, async () => undefined),
    /must not be group- or other-writable/,
  );
  await assertAbsent(state.lockPath);
});
