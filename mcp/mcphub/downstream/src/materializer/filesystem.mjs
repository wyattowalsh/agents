import { lstat, opendir, realpath } from "node:fs/promises";
import path from "node:path";

import { readSafeRegularFile } from "./safe-file.mjs";

function invariant(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function currentUid() {
  invariant(typeof process.getuid === "function", "owner validation requires a POSIX runtime");
  return process.getuid();
}

async function validateTrustedDirectory(rootPath, label, { ownerOnly }) {
  invariant(path.isAbsolute(rootPath), `${label} must be absolute`);
  const stats = await lstat(rootPath);
  invariant(stats.isDirectory() && !stats.isSymbolicLink(), `${label} must be a non-symlink directory`);
  invariant(stats.uid === currentUid(), `${label} must be owned by the current user`);
  invariant((stats.mode & 0o022) === 0, `${label} must not be group- or other-writable`);
  if (ownerOnly) {
    invariant((stats.mode & 0o077) === 0, `${label} must not grant group or other permissions`);
  }
  invariant(await realpath(rootPath) === path.resolve(rootPath), `${label} must not traverse a symlink`);
  return stats;
}

export async function validateOwnerDirectory(rootPath, label) {
  return validateTrustedDirectory(rootPath, label, { ownerOnly: true });
}

async function resolveTrustedFile(rootPath, relativePath, label) {
  await validateTrustedDirectory(rootPath, `${label} root`, { ownerOnly: false });
  const rootReal = await realpath(rootPath);
  let current = rootPath;
  const segments = relativePath.split("/");
  for (const segment of segments.slice(0, -1)) {
    current = path.join(current, segment);
    const stats = await lstat(current);
    invariant(stats.isDirectory() && !stats.isSymbolicLink(), `${label} parent must be a non-symlink directory`);
    invariant(stats.uid === currentUid(), `${label} parent owner mismatch`);
    invariant((stats.mode & 0o022) === 0, `${label} parent must not be group- or other-writable`);
  }
  const candidate = path.join(rootPath, ...segments);
  const parentReal = await realpath(path.dirname(candidate));
  invariant(parentReal === rootReal || parentReal.startsWith(`${rootReal}${path.sep}`), `${label} parent escapes its root`);
  return candidate;
}

export async function validateSourceFile(sourceRoot, record) {
  const candidate = await resolveTrustedFile(sourceRoot, record.sourcePath, "source file");
  return readSafeRegularFile(candidate, {
    label: "source file",
    expectedSize: record.size,
    expectedSha256: record.sha256,
  });
}

export async function validateEvidenceFile(evidenceRoot, relativePath, expectedSha256) {
  const candidate = await resolveTrustedFile(evidenceRoot, relativePath, "evidence file");
  return readSafeRegularFile(candidate, { label: "evidence file", expectedSha256 });
}

async function walk(rootPath, relative = "") {
  const records = [];
  const directory = await opendir(relative ? path.join(rootPath, relative) : rootPath);
  for await (const entry of directory) {
    const child = relative ? `${relative}/${entry.name}` : entry.name;
    const childPath = path.join(rootPath, ...child.split("/"));
    const stats = await lstat(childPath);
    invariant(!stats.isSymbolicLink(), `materialized distribution contains a symlink: ${child}`);
    if (stats.isDirectory()) {
      invariant(stats.uid === currentUid(), `materialized directory owner mismatch: ${child}`);
      invariant((stats.mode & 0o077) === 0, `materialized directory is not owner-only: ${child}`);
      records.push({ path: child, kind: "directory" });
      records.push(...await walk(rootPath, child));
    } else {
      invariant(stats.isFile(), `materialized distribution contains a non-file: ${child}`);
      records.push({ path: child, kind: "file" });
    }
  }
  return records;
}

export async function verifyMaterializedFiles(distributionRoot, manifest) {
  await validateOwnerDirectory(distributionRoot, "distribution root");
  const expected = new Map(manifest.distribution.files.map((record) => [record.path, record]));
  expected.set("audit-manifest.json", null);
  const actual = await walk(distributionRoot);
  const actualNames = actual.filter((record) => record.kind === "file").map((record) => record.path).sort();
  const expectedNames = [...expected.keys()].sort();
  invariant(JSON.stringify(actualNames) === JSON.stringify(expectedNames), "materialized file inventory does not match the sealed manifest");

  const expectedDirectories = new Set();
  for (const name of expectedNames) {
    const parts = name.split("/").slice(0, -1);
    for (let index = 1; index <= parts.length; index += 1) {
      expectedDirectories.add(parts.slice(0, index).join("/"));
    }
  }
  const actualDirectories = actual.filter((record) => record.kind === "directory").map((record) => record.path).sort();
  invariant(JSON.stringify(actualDirectories) === JSON.stringify([...expectedDirectories].sort()), "materialized directory inventory does not match the sealed manifest");

  const fileBytes = new Map();
  for (const relativePath of actualNames) {
    const record = expected.get(relativePath);
    const filePath = path.join(distributionRoot, ...relativePath.split("/"));
    if (record === null) {
      const opened = await readSafeRegularFile(filePath, {
        label: "materialized audit manifest",
        expectedMode: 0o600,
        ownerOnly: true,
      });
      invariant(opened.bytes.byteLength > 0, "materialized audit manifest is empty");
      fileBytes.set(relativePath, opened.bytes);
      continue;
    }
    invariant(record !== undefined, `unexpected materialized file: ${relativePath}`);
    const opened = await readSafeRegularFile(filePath, {
      label: "materialized file",
      expectedMode: record.mode,
      expectedSize: record.size,
      expectedSha256: record.sha256,
      ownerOnly: true,
    });
    fileBytes.set(relativePath, opened.bytes);
  }
  return { fileCount: manifest.distribution.files.length, digest: manifest.distribution.digest, fileBytes };
}

export async function fileExists(filePath) {
  try {
    await lstat(filePath);
    return true;
  } catch (error) {
    if (error && error.code === "ENOENT") {
      return false;
    }
    throw error;
  }
}
