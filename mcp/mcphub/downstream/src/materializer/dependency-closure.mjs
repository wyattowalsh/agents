import { createHash } from "node:crypto";
import { lstat } from "node:fs/promises";
import path from "node:path";
import { DatabaseSync } from "node:sqlite";
import { pathToFileURL } from "node:url";

import { canonicalJson, sha256Bytes } from "./canonical.mjs";
import { readSafeRegularFile } from "./safe-file.mjs";

function invariant(condition, message) {
  if (!condition) throw new Error(message);
}

function codeUnitCompare(left, right) {
  return left < right ? -1 : left > right ? 1 : 0;
}

function unquoteYamlScalar(value) {
  if ((value.startsWith("'") && value.endsWith("'")) || (value.startsWith('"') && value.endsWith('"'))) {
    return value.slice(1, -1);
  }
  return value;
}

function isMissingFileError(error) {
  return error?.cause?.code === "ENOENT";
}

async function readPnpmCafsFile(storeRoot, cafsPath, expectedSize) {
  const candidates = [cafsPath, `${cafsPath}-exec`];
  let missing;
  for (const relative of candidates) {
    try {
      return await readSafeRegularFile(path.join(storeRoot, ...relative.split("/")), {
        label: `pnpm CAFS content ${relative}`,
        expectedSize,
      });
    } catch (error) {
      if (!isMissingFileError(error)) throw error;
      missing = error;
    }
  }
  throw missing;
}

export function parseLockPackageIntegrities(lockBytes) {
  invariant(Buffer.isBuffer(lockBytes), "lockfile must be descriptor-read bytes");
  const source = lockBytes.toString("utf8");
  invariant(Buffer.from(source, "utf8").equals(lockBytes), "lockfile must be valid UTF-8");
  const records = new Map();
  let inPackages = false;
  let currentKey = null;
  for (const line of source.split("\n")) {
    if (line === "packages:") {
      inPackages = true;
      currentKey = null;
      continue;
    }
    if (!inPackages) continue;
    if (/^[A-Za-z]/.test(line)) break;
    const keyMatch = line.match(/^  (.+):$/);
    if (keyMatch) {
      currentKey = unquoteYamlScalar(keyMatch[1]);
      continue;
    }
    const integrityMatch = line.match(/^    resolution: \{integrity: (sha512-[A-Za-z0-9+/=]+)\}$/);
    if (integrityMatch && currentKey !== null) {
      invariant(!records.has(currentKey), `duplicate lock package integrity: ${currentKey}`);
      records.set(currentKey, integrityMatch[1]);
    }
  }
  invariant(records.size > 0, "lockfile package-integrity inventory is empty");
  return records;
}

async function nearestPackageIdentity(inventoryRoot, modulePath, cache) {
  let current = path.dirname(modulePath);
  while (current.startsWith(`${inventoryRoot}${path.sep}`)) {
    if (cache.has(current)) return cache.get(current);
    if (current.includes(`${path.sep}node_modules${path.sep}`)) {
      const packageJsonPath = path.join(current, "package.json");
      try {
        const opened = await readSafeRegularFile(packageJsonPath, { label: `locked package metadata ${packageJsonPath}` });
        const value = JSON.parse(opened.bytes.toString("utf8"));
        if (typeof value.name === "string" && typeof value.version === "string") {
          const identity = Object.freeze({ root: current, name: value.name, version: value.version });
          cache.set(current, identity);
          return identity;
        }
      } catch (error) {
        if (error.cause?.code !== "ENOENT" && error.code !== "ENOENT" && !String(error.message).includes("could not be opened safely")) throw error;
      }
    }
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  throw new Error(`locked dependency module has no exact package identity: ${modulePath}`);
}

function readStoreIndexRows(storeRoot, packageKeys) {
  const indexUrl = pathToFileURL(path.join(storeRoot, "index.db"));
  indexUrl.searchParams.set("immutable", "1");
  const database = new DatabaseSync(indexUrl.href);
  try {
    const statement = database.prepare("SELECT key, data FROM package_index WHERE key = ?");
    const rows = new Map();
    for (const packageKey of packageKeys) {
      const matches = statement.all(packageKey);
      invariant(matches.length === 1, `pnpm package_index row is missing or non-unique: ${packageKey}`);
      const row = matches[0];
      invariant(row.key === packageKey && row.data instanceof Uint8Array && row.data.byteLength > 0, `pnpm package_index row is invalid: ${packageKey}`);
      rows.set(packageKey, Buffer.from(row.data));
    }
    return rows;
  } finally {
    database.close();
  }
}

export async function verifyLockedDependencyClosure({ inventoryRoot, modules, lockBytes, storeRoot, pnpm }) {
  invariant(path.isAbsolute(inventoryRoot) && path.isAbsolute(storeRoot), "dependency closure roots must be absolute");
  const inventoryStats = await lstat(inventoryRoot);
  invariant(inventoryStats.isDirectory() && !inventoryStats.isSymbolicLink(), "dependency inventory root must be a non-symlink directory");
  const storeStats = await lstat(storeRoot);
  invariant(storeStats.isDirectory() && !storeStats.isSymbolicLink(), "pnpm store root must be a non-symlink directory");
  invariant(path.basename(storeRoot) === "v11", "pnpm store format must be v11");
  invariant(pnpm?.version === "11.22.0", "dependency closure requires pnpm 11.22.0 readback");
  invariant(/^[0-9a-f]{64}$/.test(pnpm.executableSha256) && Number.isSafeInteger(pnpm.executableSize) && pnpm.executableSize > 0, "pnpm executable identity is invalid");
  const integrities = parseLockPackageIntegrities(lockBytes);
  const packageCache = new Map();
  const pendingModules = [];
  for (const module of modules.filter((record) => record.kind === "locked-dependency")) {
    const absolutePath = path.join(inventoryRoot, ...module.path.split("/"));
    const opened = await readSafeRegularFile(absolutePath, {
      label: `locked dependency module ${module.path}`,
      expectedSha256: module.sha256,
      expectedSize: module.size,
    });
    const identity = await nearestPackageIdentity(inventoryRoot, absolutePath, packageCache);
    const lockKey = `${identity.name}@${identity.version}`;
    const integrity = integrities.get(lockKey);
    invariant(typeof integrity === "string", `locked dependency package has no integrity-bound lock record: ${lockKey}`);
    const cafsSha512 = createHash("sha512").update(opened.bytes).digest("hex");
    const cafsPath = `files/${cafsSha512.slice(0, 2)}/${cafsSha512.slice(2)}`;
    const cafs = await readPnpmCafsFile(storeRoot, cafsPath, opened.bytes.byteLength);
    invariant(cafs.bytes.equals(opened.bytes), `installed dependency bytes differ from content-addressed pnpm store: ${module.path}`);
    const packageRelativePath = path.relative(identity.root, absolutePath).split(path.sep).join("/");
    invariant(packageRelativePath.length > 0 && !packageRelativePath.startsWith("../") && packageRelativePath !== "..", `locked dependency module is outside its package root: ${module.path}`);
    pendingModules.push(Object.freeze({
      modulePath: module.path,
      package: identity.name,
      version: identity.version,
      packageRelativePath,
      lockKey,
      lockIntegrity: integrity,
      sha256: module.sha256,
      size: module.size,
      installedMode: opened.mode,
      cafsSha512,
      cafsPath,
    }));
  }
  pendingModules.sort((left, right) => codeUnitCompare(left.modulePath, right.modulePath));
  const indexBefore = await readSafeRegularFile(path.join(storeRoot, "index.db"), { label: "pnpm v11 package index" });
  const packageIndexKeys = [...new Set(pendingModules.map((record) => `${record.lockIntegrity}\t${record.lockKey}`))].sort(codeUnitCompare);
  const indexRows = readStoreIndexRows(storeRoot, packageIndexKeys);
  const indexAfter = await readSafeRegularFile(path.join(storeRoot, "index.db"), {
    label: "pnpm v11 package index after query",
    expectedSha256: sha256Bytes(indexBefore.bytes),
    expectedSize: indexBefore.bytes.byteLength,
  });
  invariant(indexAfter.bytes.equals(indexBefore.bytes), "pnpm package index changed during closure verification");
  const moduleRecords = pendingModules.map((record) => {
    const packageIndexKey = `${record.lockIntegrity}\t${record.lockKey}`;
    const packageIndexRow = indexRows.get(packageIndexKey);
    invariant(packageIndexRow !== undefined, `pnpm package_index row was not captured: ${packageIndexKey}`);
    return Object.freeze({
      ...record,
      packageIndexKey,
      packageIndexRowSha256: sha256Bytes(packageIndexRow),
      packageIndexRowSize: packageIndexRow.byteLength,
    });
  });
  invariant(moduleRecords.length > 0, "locked dependency module closure is empty");
  invariant(moduleRecords.length === modules.filter((record) => record.kind === "locked-dependency").length, "locked dependency closure is incomplete");
  const packageMap = new Map();
  for (const record of moduleRecords) {
    const key = `${record.package}\0${record.version}`;
    const current = packageMap.get(key) ?? {
      package: record.package,
      version: record.version,
      lockIntegrity: record.lockIntegrity,
      packageIndexKey: record.packageIndexKey,
      packageIndexRowSha256: record.packageIndexRowSha256,
      packageIndexRowSize: record.packageIndexRowSize,
      moduleCount: 0,
    };
    invariant(current.lockIntegrity === record.lockIntegrity, `package integrity differs within module closure: ${record.lockKey}`);
    invariant(current.packageIndexKey === record.packageIndexKey && current.packageIndexRowSha256 === record.packageIndexRowSha256 && current.packageIndexRowSize === record.packageIndexRowSize, `package_index evidence differs within module closure: ${record.lockKey}`);
    current.moduleCount += 1;
    packageMap.set(key, current);
  }
  const packages = [...packageMap.values()].sort((left, right) => codeUnitCompare(`${left.package}@${left.version}`, `${right.package}@${right.version}`));
  const mcphub = packages.find((record) => record.package === "@samanhappy/mcphub" && record.version === "1.0.32");
  invariant(mcphub?.lockIntegrity === "sha512-k0csMxsrZZOmh1Cef4WF/KGwFBtusJGPhCq5d1xTlhTfxy6qd61sGzU9ImoagquJZnnIaGp5SOWBv3xASNT5Tw==", "MCPHub dependency closure does not bind the audited archive SRI");
  const closure = {
    schemaVersion: 1,
    status: "verified",
    method: "fresh-offline-copy-install+pnpm-v11-cafs-sha512",
    lockfileSha256: sha256Bytes(lockBytes),
    lifecycleScriptsExecuted: false,
    networkResolution: false,
    packageImportMethod: "copy",
    storeFormat: "v11",
    pnpm,
    storeIndexSha256: sha256Bytes(indexBefore.bytes),
    packageCount: packages.length,
    moduleCount: moduleRecords.length,
    packages,
    modules: moduleRecords,
  };
  return Object.freeze({
    ...closure,
    inventorySha256: sha256Bytes(Buffer.from(canonicalJson(closure), "utf8")),
  });
}
