import assert from "node:assert/strict";
import { chmod, lstat, mkdir, mkdtemp, readFile, readlink, realpath, rm, symlink, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import {
  rollbackDistributionForUnitTest,
  selectDistributionForUnitTest,
} from "../../../../../scripts/mcphub/downstream-select.mjs";

const digestA = `sha256-${"a".repeat(64)}`;
const digestB = `sha256-${"b".repeat(64)}`;

async function fixture() {
  const runtimeRoot = await mkdtemp(path.join(await realpath(os.tmpdir()), "mcphub-selector-"));
  await chmod(runtimeRoot, 0o700);
  await mkdir(path.join(runtimeRoot, digestA), { mode: 0o700 });
  await mkdir(path.join(runtimeRoot, digestB), { mode: 0o700 });
  const verifyTarget = async (root, digest) => {
    assert.equal(root, runtimeRoot);
    assert.ok([digestA, digestB].includes(digest));
    assert.ok((await lstat(path.join(root, digest))).isDirectory());
    return { digest, fileCount: 1 };
  };
  return { runtimeRoot, receiptPath: path.join(runtimeRoot, "selection.json"), verifyTarget };
}

test("selection from absence and rollback are exact and receipt-bound", async (t) => {
  const state = await fixture();
  t.after(() => rm(state.runtimeRoot, { recursive: true, force: true }));

  assert.deepEqual(
    await selectDistributionForUnitTest(
      { runtimeRoot: state.runtimeRoot, digest: digestA, receiptPath: state.receiptPath },
      state.verifyTarget,
    ),
    { operation: "select", selectedDigest: digestA, previousState: "absent" },
  );
  assert.equal(await readlink(path.join(state.runtimeRoot, "current")), digestA);
  assert.equal((await lstat(state.receiptPath)).mode & 0o077, 0);
  const receipt = JSON.parse(await readFile(state.receiptPath, "utf8"));
  assert.deepEqual(receipt.previous, { state: "absent" });

  assert.deepEqual(
    await rollbackDistributionForUnitTest(
      { runtimeRoot: state.runtimeRoot, receiptPath: state.receiptPath },
      state.verifyTarget,
    ),
    { operation: "rollback", restoredState: "absent" },
  );
  await assert.rejects(lstat(path.join(state.runtimeRoot, "current")), { code: "ENOENT" });
  await assert.rejects(
    rollbackDistributionForUnitTest(
      { runtimeRoot: state.runtimeRoot, receiptPath: state.receiptPath },
      state.verifyTarget,
    ),
    /already consumed/,
  );
});

test("rollback restores only the recorded verified previous target", async (t) => {
  const state = await fixture();
  t.after(() => rm(state.runtimeRoot, { recursive: true, force: true }));
  await symlink(digestA, path.join(state.runtimeRoot, "current"));

  await selectDistributionForUnitTest(
    { runtimeRoot: state.runtimeRoot, digest: digestB, receiptPath: state.receiptPath },
    state.verifyTarget,
  );
  await rollbackDistributionForUnitTest(
    { runtimeRoot: state.runtimeRoot, receiptPath: state.receiptPath },
    state.verifyTarget,
  );
  assert.equal(await readlink(path.join(state.runtimeRoot, "current")), digestA);
});

test("rollback fails closed when current or receipt state drifts", async (t) => {
  const state = await fixture();
  t.after(() => rm(state.runtimeRoot, { recursive: true, force: true }));
  await selectDistributionForUnitTest(
    { runtimeRoot: state.runtimeRoot, digest: digestA, receiptPath: state.receiptPath },
    state.verifyTarget,
  );
  await rm(path.join(state.runtimeRoot, "current"));
  await symlink(digestB, path.join(state.runtimeRoot, "current"));
  await assert.rejects(
    rollbackDistributionForUnitTest(
      { runtimeRoot: state.runtimeRoot, receiptPath: state.receiptPath },
      state.verifyTarget,
    ),
    /no longer matches/,
  );

  await writeFile(state.receiptPath, "{}\n", { mode: 0o600 });
  await assert.rejects(
    rollbackDistributionForUnitTest(
      { runtimeRoot: state.runtimeRoot, receiptPath: state.receiptPath },
      state.verifyTarget,
    ),
    /keys are invalid/,
  );
});

test("selection rejects non-digest targets and unsafe runtime roots", async (t) => {
  const state = await fixture();
  t.after(() => rm(state.runtimeRoot, { recursive: true, force: true }));
  await assert.rejects(
    selectDistributionForUnitTest(
      { runtimeRoot: state.runtimeRoot, digest: "sha256-not-a-digest", receiptPath: state.receiptPath },
      state.verifyTarget,
    ),
    /one exact sha256 basename/,
  );
  await chmod(state.runtimeRoot, 0o777);
  await assert.rejects(
    selectDistributionForUnitTest(
      { runtimeRoot: state.runtimeRoot, digest: digestA, receiptPath: state.receiptPath },
      state.verifyTarget,
    ),
    /group- or other-writable/,
  );
});
