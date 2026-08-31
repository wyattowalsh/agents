#!/usr/bin/env node

import { randomBytes } from "node:crypto";
import {
  chmod,
  lstat,
  open,
  readFile,
  readlink,
  realpath,
  rename,
  symlink,
  unlink,
} from "node:fs/promises";
import path from "node:path";

import { validateOwnerDirectory, verifyMaterializedFiles } from "../../mcp/mcphub/downstream/src/materializer/filesystem.mjs";
import { readAuditManifest } from "../../mcp/mcphub/downstream/src/materializer/manifest.mjs";
import { assertDistributionDigestNotRevoked } from "../../mcp/mcphub/downstream/src/materializer/revocations.mjs";
import { assertSelfContainedModule } from "../../mcp/mcphub/downstream/src/materializer/sealed-module.mjs";

const DIGEST = /^sha256-[0-9a-f]{64}$/;
const RECEIPT_KIND = "mcphub-downstream-selection";
const RECEIPT_VERSION = 1;

function invariant(condition, message) {
  if (!condition) throw new Error(message);
}

function currentUid() {
  invariant(typeof process.getuid === "function", "owner validation requires a POSIX runtime");
  return process.getuid();
}

function exactKeys(value, expected, label) {
  invariant(value !== null && typeof value === "object" && !Array.isArray(value), `${label} must be an object`);
  const actual = Object.keys(value).sort();
  invariant(JSON.stringify(actual) === JSON.stringify([...expected].sort()), `${label} keys are invalid`);
}

async function missing(filePath) {
  try {
    await lstat(filePath);
    return false;
  } catch (error) {
    if (error && error.code === "ENOENT") return true;
    throw error;
  }
}

async function verifyDistributionTarget(runtimeRoot, digest) {
  invariant(path.isAbsolute(runtimeRoot), "runtime root must be absolute");
  invariant(DIGEST.test(digest), "digest must be one exact sha256 basename");
  assertDistributionDigestNotRevoked(digest);
  await validateOwnerDirectory(runtimeRoot, "runtime root");
  const distributionRoot = path.join(runtimeRoot, digest);
  invariant(path.dirname(distributionRoot) === runtimeRoot, "distribution must be a direct runtime-root child");
  invariant(await realpath(distributionRoot) === distributionRoot, "distribution target must not traverse a symlink");
  const manifest = await readAuditManifest(path.join(distributionRoot, "audit-manifest.json"), { requireSealed: true });
  invariant(manifest.distribution.digest === digest, "distribution digest does not match its sealed manifest");
  const verification = await verifyMaterializedFiles(distributionRoot, manifest);
  const entryBytes = verification.fileBytes.get(manifest.distribution.entryPoint);
  invariant(entryBytes !== undefined, "verified entrypoint bytes are missing");
  assertSelfContainedModule(entryBytes);
  return { digest, fileCount: manifest.distribution.files.length };
}

async function inspectCurrent(runtimeRoot, verifyTarget, { allowAbsent = true } = {}) {
  await validateOwnerDirectory(runtimeRoot, "runtime root");
  const pointerPath = path.join(runtimeRoot, "current");
  if (await missing(pointerPath)) {
    invariant(allowAbsent, "current pointer is absent");
    return Object.freeze({ state: "absent" });
  }
  const stats = await lstat(pointerPath);
  invariant(stats.isSymbolicLink(), "current must be a symbolic-link pointer");
  invariant(stats.uid === currentUid(), "current pointer owner mismatch");
  const digest = await readlink(pointerPath);
  invariant(DIGEST.test(digest), "current pointer target is invalid");
  assertDistributionDigestNotRevoked(digest);
  await verifyTarget(runtimeRoot, digest);
  return Object.freeze({ state: "present", digest });
}

function temporaryPointerPath(runtimeRoot) {
  return path.join(runtimeRoot, `.current-${process.pid}-${randomBytes(8).toString("hex")}`);
}

async function atomicSetPointer(runtimeRoot, digest, verifyTarget) {
  assertDistributionDigestNotRevoked(digest);
  await verifyTarget(runtimeRoot, digest);
  const temporary = temporaryPointerPath(runtimeRoot);
  invariant(await missing(temporary), "temporary pointer already exists");
  try {
    await symlink(digest, temporary);
    const temporaryStats = await lstat(temporary);
    invariant(temporaryStats.isSymbolicLink(), "temporary pointer is not a symlink");
    invariant(temporaryStats.uid === currentUid(), "temporary pointer owner mismatch");
    invariant(await readlink(temporary) === digest, "temporary pointer target drifted");
    await verifyTarget(runtimeRoot, digest);
    await rename(temporary, path.join(runtimeRoot, "current"));
  } finally {
    if (!(await missing(temporary))) await unlink(temporary);
  }
  const selected = await inspectCurrent(runtimeRoot, verifyTarget, { allowAbsent: false });
  invariant(selected.state === "present" && selected.digest === digest, "selected pointer verification failed");
}

async function atomicRemovePointer(runtimeRoot, expectedDigest, verifyTarget) {
  const current = await inspectCurrent(runtimeRoot, verifyTarget, { allowAbsent: false });
  invariant(current.state === "present" && current.digest === expectedDigest, "current pointer changed before rollback");
  const displaced = temporaryPointerPath(runtimeRoot);
  invariant(await missing(displaced), "temporary rollback pointer already exists");
  await rename(path.join(runtimeRoot, "current"), displaced);
  try {
    invariant(await missing(path.join(runtimeRoot, "current")), "current pointer remained after rollback");
    const stats = await lstat(displaced);
    invariant(stats.isSymbolicLink() && stats.uid === currentUid(), "displaced pointer identity changed");
    invariant(await readlink(displaced) === expectedDigest, "displaced pointer target changed");
  } finally {
    if (!(await missing(displaced))) await unlink(displaced);
  }
}

function receiptPayload(runtimeRoot, selectedDigest, previous) {
  return Object.freeze({
    schemaVersion: RECEIPT_VERSION,
    kind: RECEIPT_KIND,
    runtimeRoot,
    selectedDigest,
    previous,
    rolledBack: false,
  });
}

async function validateReceiptParent(receiptPath) {
  invariant(path.isAbsolute(receiptPath), "receipt path must be absolute");
  await validateOwnerDirectory(path.dirname(receiptPath), "receipt parent");
}

async function createReceipt(receiptPath, payload) {
  await validateReceiptParent(receiptPath);
  const handle = await open(receiptPath, "wx", 0o600);
  try {
    await handle.writeFile(`${JSON.stringify(payload)}\n`, "utf8");
    await handle.sync();
  } finally {
    await handle.close();
  }
  await chmod(receiptPath, 0o600);
}

function parsePrevious(value) {
  invariant(value !== null && typeof value === "object" && !Array.isArray(value), "receipt previous state is invalid");
  if (value.state === "absent") {
    exactKeys(value, ["state"], "absent previous state");
    return Object.freeze({ state: "absent" });
  }
  exactKeys(value, ["state", "digest"], "present previous state");
  invariant(value.state === "present" && DIGEST.test(value.digest), "recorded previous digest is invalid");
  assertDistributionDigestNotRevoked(value.digest);
  return Object.freeze({ state: "present", digest: value.digest });
}

async function readReceipt(receiptPath) {
  await validateReceiptParent(receiptPath);
  const stats = await lstat(receiptPath);
  invariant(stats.isFile() && !stats.isSymbolicLink(), "selection receipt must be a regular file");
  invariant(stats.uid === currentUid(), "selection receipt owner mismatch");
  invariant((stats.mode & 0o077) === 0, "selection receipt must be owner-only");
  invariant(stats.size > 0 && stats.size <= 16_384, "selection receipt size is invalid");
  const payload = JSON.parse(await readFile(receiptPath, "utf8"));
  exactKeys(
    payload,
    ["schemaVersion", "kind", "runtimeRoot", "selectedDigest", "previous", "rolledBack"],
    "selection receipt",
  );
  invariant(payload.schemaVersion === RECEIPT_VERSION && payload.kind === RECEIPT_KIND, "selection receipt contract is invalid");
  invariant(path.isAbsolute(payload.runtimeRoot), "receipt runtime root must be absolute");
  invariant(DIGEST.test(payload.selectedDigest), "receipt selected digest is invalid");
  assertDistributionDigestNotRevoked(payload.selectedDigest);
  invariant(payload.rolledBack === false, "selection receipt is already consumed");
  return Object.freeze({ ...payload, previous: parsePrevious(payload.previous) });
}

async function consumeReceipt(receiptPath, payload) {
  const temporary = `${receiptPath}.consumed-${process.pid}-${randomBytes(8).toString("hex")}`;
  invariant(await missing(temporary), "temporary receipt already exists");
  try {
    const handle = await open(temporary, "wx", 0o600);
    try {
      await handle.writeFile(`${JSON.stringify({ ...payload, rolledBack: true })}\n`, "utf8");
      await handle.sync();
    } finally {
      await handle.close();
    }
    await chmod(temporary, 0o600);
    await rename(temporary, receiptPath);
  } finally {
    if (!(await missing(temporary))) await unlink(temporary);
  }
}

async function selectDistributionWithVerifier({ runtimeRoot, digest, receiptPath }, verifyTarget) {
  invariant(path.isAbsolute(runtimeRoot), "runtime root must be absolute");
  invariant(DIGEST.test(digest), "digest must be one exact sha256 basename");
  assertDistributionDigestNotRevoked(digest);
  await validateOwnerDirectory(runtimeRoot, "runtime root");
  await validateReceiptParent(receiptPath);
  invariant(await missing(receiptPath), "selection receipt already exists");
  const previous = await inspectCurrent(runtimeRoot, verifyTarget);
  await atomicSetPointer(runtimeRoot, digest, verifyTarget);
  const receipt = receiptPayload(runtimeRoot, digest, previous);
  try {
    await createReceipt(receiptPath, receipt);
  } catch (error) {
    if (previous.state === "present") {
      await atomicSetPointer(runtimeRoot, previous.digest, verifyTarget);
    } else {
      await atomicRemovePointer(runtimeRoot, digest, verifyTarget);
    }
    throw error;
  }
  return Object.freeze({ operation: "select", selectedDigest: digest, previousState: previous.state });
}

async function rollbackDistributionWithVerifier({ runtimeRoot, receiptPath }, verifyTarget) {
  invariant(path.isAbsolute(runtimeRoot), "runtime root must be absolute");
  const receipt = await readReceipt(receiptPath);
  invariant(receipt.runtimeRoot === runtimeRoot, "selection receipt is bound to another runtime root");
  const current = await inspectCurrent(runtimeRoot, verifyTarget, { allowAbsent: false });
  invariant(
    current.state === "present" && current.digest === receipt.selectedDigest,
    "current pointer no longer matches the recorded selection",
  );
  if (receipt.previous.state === "present") {
    await atomicSetPointer(runtimeRoot, receipt.previous.digest, verifyTarget);
  } else {
    await atomicRemovePointer(runtimeRoot, receipt.selectedDigest, verifyTarget);
  }
  await consumeReceipt(receiptPath, receipt);
  return Object.freeze({ operation: "rollback", restoredState: receipt.previous.state });
}

export async function selectDistribution(options) {
  return selectDistributionWithVerifier(options, verifyDistributionTarget);
}

export async function rollbackDistribution(options) {
  return rollbackDistributionWithVerifier(options, verifyDistributionTarget);
}

export async function checkSelection({ runtimeRoot }) {
  const current = await inspectCurrent(runtimeRoot, verifyDistributionTarget, { allowAbsent: false });
  invariant(current.state === "present", "current pointer is absent");
  return Object.freeze({ operation: "check", selectedDigest: current.digest });
}

export async function selectDistributionForUnitTest(options, verifyTarget) {
  invariant(process.env.NODE_TEST_CONTEXT !== undefined, "test-only selector is unavailable outside node:test");
  return selectDistributionWithVerifier(options, verifyTarget);
}

export async function rollbackDistributionForUnitTest(options, verifyTarget) {
  invariant(process.env.NODE_TEST_CONTEXT !== undefined, "test-only rollback is unavailable outside node:test");
  return rollbackDistributionWithVerifier(options, verifyTarget);
}

function parseArgs(argv) {
  const [operation, ...rest] = argv;
  invariant(["check", "rollback", "select"].includes(operation), "operation is required");
  const options = { operation };
  for (let index = 0; index < rest.length; index += 1) {
    const argument = rest[index];
    invariant(["--digest", "--receipt", "--runtime-root"].includes(argument), "unknown argument");
    const value = rest[index + 1];
    invariant(value !== undefined, "argument value is missing");
    if (argument !== "--digest") invariant(path.isAbsolute(value), `${argument} must be absolute`);
    options[argument.slice(2).replaceAll("-", "_")] = value;
    index += 1;
  }
  invariant(options.runtime_root !== undefined, "runtime root is required");
  if (operation === "select") invariant(options.digest !== undefined && options.receipt !== undefined, "select arguments are incomplete");
  if (operation === "rollback") invariant(options.receipt !== undefined && options.digest === undefined, "rollback arguments are invalid");
  if (operation === "check") invariant(options.receipt === undefined && options.digest === undefined, "check arguments are invalid");
  return options;
}

async function main() {
  let args;
  try {
    args = parseArgs(process.argv.slice(2));
  } catch {
    process.stderr.write('{"status":"error","reasonCode":"MCPHUB_DOWNSTREAM_SELECTION_ARGUMENT_INVALID"}\n');
    process.exitCode = 2;
    return;
  }
  try {
    const report = args.operation === "select"
      ? await selectDistribution({ runtimeRoot: args.runtime_root, digest: args.digest, receiptPath: args.receipt })
      : args.operation === "rollback"
        ? await rollbackDistribution({ runtimeRoot: args.runtime_root, receiptPath: args.receipt })
        : await checkSelection({ runtimeRoot: args.runtime_root });
    process.stdout.write(`${JSON.stringify({ status: "ok", ...report })}\n`);
  } catch {
    process.stderr.write('{"status":"error","reasonCode":"MCPHUB_DOWNSTREAM_SELECTION_FAILED"}\n');
    process.exitCode = 1;
  }
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
