import { randomBytes } from "node:crypto";
import { chmod, lstat, mkdir, readdir, rename, rm, writeFile } from "node:fs/promises";
import path from "node:path";

import { canonicalJson, sha256Bytes } from "./canonical.mjs";
import {
  computeDerivationDigest,
  computeDistributionDigest,
  parseDistributionDigestReceipt,
  validateAuditManifest,
  validateLockedDependencyClosure,
  validateMaterializedOutputInventory,
  validateOwnedSourcesManifest,
  validatePatchManifest,
} from "./manifest.mjs";
import { readSafeRegularFile } from "./safe-file.mjs";
import { assertSelfContainedModule, SEALED_MODULE_POLICY_SHA256 } from "./sealed-module.mjs";

const CAPABILITY_SOURCE = "openspec/changes/replace-supathings-with-things-plus-plus/capability-manifest.json";
const CAPABILITY_OUTPUT = "dist/things-capability-manifest.json";
const ENTRY_SOURCE = "dist/runtime/main.mjs";
const FINAL_RECEIPTS = Object.freeze([
  "owned-sources.json",
  "patch-manifest.json",
  "materialized-output-inventory.json",
  "audit-manifest.json",
  "distribution-digest.json",
]);

function invariant(condition, message) {
  if (!condition) throw new Error(message);
}

function codeUnitCompare(left, right) {
  return left < right ? -1 : left > right ? 1 : 0;
}

function canonicalBytes(value) {
  return Buffer.from(`${canonicalJson(value)}\n`, "utf8");
}

function parseJson(bytes, label) {
  try {
    return JSON.parse(bytes.toString("utf8"));
  } catch (error) {
    throw new Error(`${label} is not valid JSON`, { cause: error });
  }
}

async function readInput(root, relativePath, options = {}) {
  invariant(path.isAbsolute(root), "seal input root must be absolute");
  return readSafeRegularFile(path.join(root, ...relativePath.split("/")), {
    label: relativePath,
    ...options,
  });
}

async function writeOwnerFile(root, relativePath, bytes) {
  const destination = path.join(root, ...relativePath.split("/"));
  await mkdir(path.dirname(destination), { recursive: true, mode: 0o700 });
  await chmod(path.dirname(destination), 0o700);
  await writeFile(destination, bytes, { flag: "wx", mode: 0o600 });
  await chmod(destination, 0o600);
}

export async function collectUpstreamPackageAssets(packageRoot) {
  invariant(path.isAbsolute(packageRoot), "upstream package root must be absolute");
  const rootStats = await lstat(packageRoot);
  invariant(rootStats.isDirectory() && !rootStats.isSymbolicLink(), "upstream package root must be a non-symlink directory");
  const relativePaths = ["package.json", "servers.json"];
  const frontendRoot = path.join(packageRoot, "frontend/dist");
  async function visit(current, relative) {
    const entries = await readdir(current, { withFileTypes: true });
    entries.sort((left, right) => codeUnitCompare(left.name, right.name));
    for (const entry of entries) {
      const childRelative = `${relative}/${entry.name}`;
      const child = path.join(current, entry.name);
      const stats = await lstat(child);
      invariant(!stats.isSymbolicLink(), `upstream frontend asset is a symlink: ${childRelative}`);
      if (stats.isDirectory()) await visit(child, childRelative);
      else {
        invariant(stats.isFile(), `upstream frontend asset is not regular: ${childRelative}`);
        relativePaths.push(childRelative);
      }
    }
  }
  await visit(frontendRoot, "frontend/dist");
  invariant(relativePaths.includes("frontend/dist/index.html"), "upstream frontend index.html is absent");
  invariant(relativePaths.some((relativePath) => relativePath.startsWith("frontend/dist/assets/")), "upstream hashed frontend assets are absent");
  const records = [];
  for (const relativePath of relativePaths.sort(codeUnitCompare)) {
    const opened = await readSafeRegularFile(path.join(packageRoot, ...relativePath.split("/")), { label: `upstream package asset ${relativePath}` });
    records.push(Object.freeze({
      logicalSourcePath: `node_modules/@samanhappy/mcphub/${relativePath}`,
      outputPath: `dist/package/${relativePath}`,
      bytes: opened.bytes,
    }));
  }
  const packageJson = parseJson(records.find((record) => record.outputPath === "dist/package/package.json").bytes, "upstream package metadata");
  invariant(packageJson.name === "@samanhappy/mcphub" && packageJson.version === "1.0.32", "upstream package metadata identity is invalid");
  const servers = parseJson(records.find((record) => record.outputPath === "dist/package/servers.json").bytes, "upstream servers.json");
  invariant(Object.keys(servers).length > 0, "upstream servers.json must contain populated market data");
  return records;
}

export function validateCapabilityManifest(value) {
  invariant(value !== null && typeof value === "object" && !Array.isArray(value), "capability manifest must be an object");
  invariant(value.schemaVersion === "1.0.0", "capability manifest schemaVersion is invalid");
  invariant(value.group?.name === "things", "capability manifest must own exactly the things group");
  invariant(canonicalJson(value.group.servers) === canonicalJson(["things-core", "things-shortcuts", "things-native"]), "capability manifest group server set or order is invalid");
  invariant(value.group.localPath === "/mcp/things" && value.group.remotePath === "/mcp/things", "capability manifest routes must be /mcp/things");
  invariant(Array.isArray(value.tools) && value.tools.length === 70, "capability manifest must contain exactly 70 tools");
  invariant(
    canonicalJson(value.counts) === canonicalJson({
      tools: 70,
      coreTools: 41,
      shortcutTools: 21,
      nativeTools: 8,
      supaOutcomes: 37,
      workflows: 17,
      legacyEvalIds: 25,
      newEvalIds: 16,
    }),
    "capability manifest expanded counts are invalid",
  );
  const counts = new Map();
  const capabilityIds = new Set();
  const publicNames = new Set();
  const serverNames = new Set();
  for (const tool of value.tools) {
    invariant(tool !== null && typeof tool === "object" && !Array.isArray(tool), "capability manifest tool rows must be objects");
    invariant(typeof tool.qualifiedCapabilityId === "string" && tool.qualifiedCapabilityId.length > 0, "capability manifest tool ID is invalid");
    invariant(["things-core", "things-shortcuts", "things-native"].includes(tool.server), `capability manifest tool server is invalid for ${tool.qualifiedCapabilityId}`);
    invariant(tool.qualifiedCapabilityId === `${tool.server}/${tool.serverToolName}`, `capability manifest qualified ID mismatch for ${tool.qualifiedCapabilityId}`);
    const expectedPublicName = `${tool.server.replaceAll("-", "_")}__${tool.serverToolName}`;
    invariant(tool.publicToolName === expectedPublicName && tool.expectedMcphubQualifiedName === expectedPublicName, `capability manifest public-name normalization mismatch for ${tool.qualifiedCapabilityId}`);
    invariant(!capabilityIds.has(tool.qualifiedCapabilityId), `duplicate capability manifest qualified ID: ${tool.qualifiedCapabilityId}`);
    invariant(!publicNames.has(tool.publicToolName), `duplicate capability manifest public name: ${tool.publicToolName}`);
    invariant(!serverNames.has(`${tool.server}\0${tool.serverToolName}`), `duplicate capability manifest server tool: ${tool.qualifiedCapabilityId}`);
    capabilityIds.add(tool.qualifiedCapabilityId);
    publicNames.add(tool.publicToolName);
    serverNames.add(`${tool.server}\0${tool.serverToolName}`);
    invariant(tool.adaptedSchemaHashes?.status === "frozen", `adapted schema hashes are not frozen for ${tool.qualifiedCapabilityId}`);
    invariant(/^[0-9a-f]{64}$/.test(tool.adaptedSchemaHashes?.inputSchemaSha256), `adapted input schema hash is invalid for ${tool.qualifiedCapabilityId}`);
    invariant(/^[0-9a-f]{64}$/.test(tool.adaptedSchemaHashes?.outputSchemaSha256), `adapted output schema hash is invalid for ${tool.qualifiedCapabilityId}`);
    counts.set(tool.server, (counts.get(tool.server) ?? 0) + 1);
  }
  invariant(counts.size === 3 && counts.get("things-core") === 41 && counts.get("things-shortcuts") === 21 && counts.get("things-native") === 8, "capability manifest server expansion is not exactly 41/21/8");
  for (const key of ["exactToolUnion", "zeroRemoved", "zeroUnmapped", "netNewGreaterThanZero", "oneThingsGroupOnly"]) {
    invariant(value.invariants?.[key] === true, `capability manifest invariant ${key} is not true`);
  }
  invariant(Array.isArray(value.netNewOutcomeIds) && value.netNewOutcomeIds.length > 0, "capability manifest must contain net-new outcomes");
  return value;
}

function validateBundleReport(report, bundleBytes) {
  invariant(report?.schemaVersion === 1, "bundle report schemaVersion is invalid");
  invariant(report.bundler?.name === "rolldown" && report.bundler.version === "1.2.6", "bundle report is not pinned rolldown 1.2.6");
  invariant(report.bundler.entry === "src/runtime/main.ts" && report.bundler.output === ENTRY_SOURCE, "bundle report entry/output pair is invalid");
  invariant(report.bundler.emittedChunks === 1 && report.bundler.emittedAssets === 0, "bundle report must contain one emitted chunk and no emitted assets");
  invariant(Array.isArray(report.modules) && report.modules.length > 0, "bundle report module closure is empty");
  invariant(Array.isArray(report.transformEvents), "bundle report transform events are absent");
  invariant(report.transformEvents.every((event) => event.count === 1), "bundle report transform event count is not exact");
  invariant(report.transformEventsSha256 === sha256Bytes(Buffer.from(canonicalJson(report.transformEvents), "utf8")), "bundle report transform-event digest mismatch");
  invariant(report.validatorPolicySha256 === SEALED_MODULE_POLICY_SHA256, "bundle report validator policy digest mismatch");
  invariant(report.entrySha256 === sha256Bytes(bundleBytes) && report.entrySize === bundleBytes.byteLength, "bundle report does not bind exact entry bytes");
  const sealed = assertSelfContainedModule(bundleBytes);
  invariant(sealed.policySha256 === report.validatorPolicySha256, "bundle report and launch policy digests differ");
  invariant(report.buildAttestation?.astValidated === true, "bundle report lacks authoritative AST attestation");
  invariant(report.buildAttestation.entrySha256 === report.entrySha256, "bundle report AST attestation does not bind entry bytes");
  invariant(report.buildAttestation.validatorPolicySha256 === report.validatorPolicySha256, "bundle report AST attestation does not bind validator policy");
  invariant(report.buildAttestation.transformEventsSha256 === report.transformEventsSha256, "bundle report AST attestation does not bind transform events");
  invariant(report.buildAttestation.moduleInventorySha256 === sha256Bytes(Buffer.from(canonicalJson(report.modules), "utf8")), "bundle report AST attestation does not bind module inventory");
  invariant(report.buildAttestationSha256 === sha256Bytes(Buffer.from(canonicalJson(report.buildAttestation), "utf8")), "bundle report AST attestation digest mismatch");
  invariant(report.imports.every((specifier) => specifier.startsWith("node:") && !["node:module", "node:process", "node:vm"].includes(specifier)), "bundle report contains a forbidden external import");
  invariant(report.exports.includes("main"), "bundle report does not export main");
  return report;
}

function validateDependencyClosure(value, report, lockSha256) {
  const closure = validateLockedDependencyClosure(value, "dependency closure", { requireAuditedMcphub: true });
  invariant(closure.lockfileSha256 === lockSha256, "dependency closure does not bind the frozen lockfile");
  const lockedModules = report.modules.filter((record) => record.kind === "locked-dependency");
  invariant(closure.modules.length === lockedModules.length, "dependency closure does not cover every locked bundle module");
  for (let index = 0; index < lockedModules.length; index += 1) {
    const expected = lockedModules[index];
    const actual = closure.modules[index];
    invariant(actual.modulePath === expected.path && actual.sha256 === expected.sha256 && actual.size === expected.size, `dependency closure differs from bundle module ${expected.path}`);
  }
  return closure;
}

function validateDependencyGraph(value, packageJson, lockSha256) {
  invariant(value?.schemaVersion === 1, "dependency graph schemaVersion is invalid");
  invariant(value.lockfile?.sha256 === lockSha256, "dependency graph does not bind the current frozen lockfile");
  invariant(value.runtime?.packageManager === "pnpm@11.22.0", "dependency graph package manager is not frozen");
  invariant(canonicalJson(value.directDependencies?.production) === canonicalJson(packageJson.dependencies), "dependency graph direct production dependencies differ from package.json");
  invariant(value.directDependencies.production["@cfworker/json-schema"] === "4.1.1", "dependency graph omits the exact CfWorker validator dependency");
  return value;
}

export async function stageSealCandidate({
  repoRoot,
  downstreamRoot,
  candidateRoot,
  bundleReport,
  bundlePath,
  upstreamPackageRoot,
  dependencyClosure,
  buildCommands = [
    "pnpm install --frozen-lockfile --offline --ignore-workspace --ignore-scripts",
    "node src/materializer/gate.mjs seal",
  ],
}) {
  invariant(path.isAbsolute(repoRoot) && path.isAbsolute(downstreamRoot) && path.isAbsolute(candidateRoot), "seal roots must be absolute");
  await mkdir(candidateRoot, { mode: 0o700, recursive: true });
  await chmod(candidateRoot, 0o700);

  const bundle = await readSafeRegularFile(path.resolve(bundlePath), { label: "sealed runtime bundle", expectedMode: 0o600, ownerOnly: true });
  const report = validateBundleReport(bundleReport, bundle.bytes);
  const capability = await readInput(repoRoot, CAPABILITY_SOURCE);
  validateCapabilityManifest(parseJson(capability.bytes, "capability manifest"));
  const upstreamPackageAssets = await collectUpstreamPackageAssets(upstreamPackageRoot);
  const upstream = await readInput(downstreamRoot, "provenance/upstream.json");
  const dependencyGraph = await readInput(downstreamRoot, "provenance/dependency-graph.json");
  const packageFile = await readInput(downstreamRoot, "package.json");
  const lockfile = await readInput(downstreamRoot, "pnpm-lock.yaml");
  const packageJson = parseJson(packageFile.bytes, "downstream package.json");
  invariant(packageJson.packageManager === "pnpm@11.22.0", "downstream package manager is not pinned");
  invariant(packageJson.dependencies?.["@cfworker/json-schema"] === "4.1.1", "downstream CfWorker dependency is not exact 4.1.1");
  const graph = validateDependencyGraph(parseJson(dependencyGraph.bytes, "dependency graph"), packageJson, sha256Bytes(lockfile.bytes));
  const lockedDependencyClosure = validateDependencyClosure(dependencyClosure, report, sha256Bytes(lockfile.bytes));
  const upstreamJson = parseJson(upstream.bytes, "upstream provenance");

  await writeOwnerFile(candidateRoot, ENTRY_SOURCE, bundle.bytes);
  await writeOwnerFile(candidateRoot, CAPABILITY_OUTPUT, capability.bytes);
  const stagedAssets = [{
    logicalSourcePath: CAPABILITY_SOURCE,
    outputPath: CAPABILITY_OUTPUT,
    bytes: capability.bytes,
  }, ...upstreamPackageAssets];
  for (const asset of upstreamPackageAssets) await writeOwnerFile(candidateRoot, asset.outputPath, asset.bytes);
  const assets = stagedAssets.map((asset) => ({
    sourcePath: asset.logicalSourcePath,
    sourceSha256: sha256Bytes(asset.bytes),
    outputPath: asset.outputPath,
    outputSha256: sha256Bytes(asset.bytes),
    size: asset.bytes.byteLength,
    mode: 0o600,
  })).sort((left, right) => codeUnitCompare(left.outputPath, right.outputPath));
  const files = [{
    sourcePath: ENTRY_SOURCE,
    path: "runtime/main.mjs",
    sha256: report.entrySha256,
    size: report.entrySize,
    mode: 0o600,
    role: "entrypoint",
  }, ...stagedAssets.map((asset) => ({
    sourcePath: asset.outputPath,
    path: asset.outputPath.slice("dist/".length),
    sha256: sha256Bytes(asset.bytes),
    size: asset.bytes.byteLength,
    mode: 0o600,
    role: "asset",
  }))].sort((left, right) => codeUnitCompare(left.path, right.path));

  const ownedSources = validateOwnedSourcesManifest({
    schemaVersion: 1,
    status: "sealed",
    exhaustive: true,
    entry: "src/runtime/main.ts",
    modules: report.modules,
    moduleCount: report.modules.length,
    moduleInventorySha256: report.buildAttestation.moduleInventorySha256,
    lockedDependencyClosureSha256: lockedDependencyClosure.inventorySha256,
    assets,
  });
  const patchManifest = validatePatchManifest({
    schemaVersion: 1,
    status: "sealed",
    bundler: { name: report.bundler.name, version: report.bundler.version },
    productionLoaderTransformations: [],
    validatorPolicySha256: report.validatorPolicySha256,
    events: report.transformEvents,
    eventCount: report.transformEvents.length,
    eventsSha256: report.transformEventsSha256,
    buildAttestation: report.buildAttestation,
    buildAttestationSha256: report.buildAttestationSha256,
  });
  const ownedBytes = canonicalBytes(ownedSources);
  const patchBytes = canonicalBytes(patchManifest);
  const sealAttestation = {
    schemaVersion: 1,
    buildAttestationSha256: report.buildAttestationSha256,
    lockedDependencyClosureSha256: lockedDependencyClosure.inventorySha256,
    assetInventorySha256: sha256Bytes(Buffer.from(canonicalJson(assets), "utf8")),
    distributionFileInventorySha256: sha256Bytes(Buffer.from(canonicalJson(files), "utf8")),
  };
  const sealAttestationSha256 = sha256Bytes(Buffer.from(canonicalJson(sealAttestation), "utf8"));
  const outputInventory = {
    schemaVersion: 1,
    status: "sealed",
    bundler: report.bundler,
    modules: report.modules,
    transformations: report.transformations,
    transformEvents: report.transformEvents,
    transformEventsSha256: report.transformEventsSha256,
    validatorPolicySha256: report.validatorPolicySha256,
    buildAttestation: report.buildAttestation,
    buildAttestationSha256: report.buildAttestationSha256,
    lockedDependencyClosure,
    sealAttestation,
    sealAttestationSha256,
    assets,
    files,
  };
  const outputBytes = canonicalBytes(outputInventory);

  const auditManifest = {
    schemaVersion: 1,
    status: "sealed",
    provenance: {
      upstreamManifestSha256: sha256Bytes(upstream.bytes),
      upstreamTarballSha256: upstreamJson.package.tarballSha256,
      upstreamTarballIntegrity: upstreamJson.package.npmIntegrity,
      upstreamSignatureKeyId: upstreamJson.signature.keyId,
      upstreamArchiveFileCount: upstreamJson.package.fileCount,
      upstreamArchiveUnpackedBytes: upstreamJson.package.unpackedSize,
      upstreamArchiveInventorySha256: upstreamJson.archiveInventory.canonicalInventorySha256,
      dependencyGraphSha256: sha256Bytes(dependencyGraph.bytes),
      packageJsonSha256: sha256Bytes(packageFile.bytes),
      lockfileSha256: sha256Bytes(lockfile.bytes),
    },
    dependencies: {
      publicEdge: { server: "2.0.0", core: "2.0.0", node: null },
      privateBackendClient: { sdk: "1.29.0" },
      schemaValidator: {
        package: "@cfworker/json-schema",
        version: "4.1.1",
        integrity: "sha512-gAmrUZSGtKc3AiBL71iNWxDsyUC5uMaKKGdvzYsBoTW/xi42JQHl7eKV2OYzCUqvc+D2RCcf7EXY2iCyFIk6og==",
        tarballSha256: "f3a8076b450505f0671fa78a6efb5e7726883e2c6dfb13b29261872803610203",
        signatureKeyId: "SHA256:DhQ8wR5APBvFHLF/+Tc+AYvPOdTpcIDqOhxsBHRwC7U",
      },
      v1V2BleedRejected: true,
    },
    sourceClosure: {
      exhaustive: true,
      ownedSourcesManifestSha256: sha256Bytes(ownedBytes),
      patchManifestSha256: sha256Bytes(patchBytes),
      derivationSha256: "0".repeat(64),
      productionLoaderTransformations: [],
    },
    build: {
      commands: buildCommands,
      nodeVersion: process.version,
      packageManager: "pnpm@11.22.0",
      outputInventoryComplete: true,
      outputInventorySha256: sha256Bytes(outputBytes),
      sealAttestationSha256,
    },
    constraints: {
      offlineBuild: true,
      frozenLockfile: true,
      sameProcessLaunch: true,
      rejectUnlistedFiles: true,
      ownerOnlyRuntime: true,
      npx: false,
      liveRegistryResolution: false,
      versionRanges: false,
      mutablePackageCache: false,
      nodeOptions: false,
      esmLoaderHooks: false,
      networkAtMaterialization: false,
      networkDependencyResolution: false,
      entryBundleSelfContained: true,
      barePackageImports: false,
      dynamicImports: false,
      ancestorNodeModulesResolution: false,
    },
    distribution: {
      digest: `sha256-${"0".repeat(64)}`,
      entryPoint: "runtime/main.mjs",
      entryExport: "main",
      files,
    },
  };
  auditManifest.sourceClosure.derivationSha256 = computeDerivationDigest(auditManifest);
  auditManifest.distribution.digest = computeDistributionDigest(auditManifest);
  validateAuditManifest(auditManifest, { requireSealed: true });
  validateMaterializedOutputInventory(outputInventory, auditManifest);
  const auditBytes = canonicalBytes(auditManifest);
  const digestReceipt = {
    schemaVersion: 1,
    status: "sealed",
    auditManifestSha256: sha256Bytes(auditBytes),
    outputInventorySha256: sha256Bytes(outputBytes),
    distributionDigest: auditManifest.distribution.digest,
    entryPoint: auditManifest.distribution.entryPoint,
    entryExport: auditManifest.distribution.entryExport,
    fileCount: files.length,
  };

  const receipts = new Map([
    ["owned-sources.json", ownedBytes],
    ["patch-manifest.json", patchBytes],
    ["materialized-output-inventory.json", outputBytes],
    ["audit-manifest.json", auditBytes],
    ["distribution-digest.json", canonicalBytes(digestReceipt)],
  ]);
  for (const [name, bytes] of receipts) await writeOwnerFile(candidateRoot, `provenance/${name}`, bytes);
  await writeOwnerFile(candidateRoot, "provenance/upstream.json", upstream.bytes);
  await writeOwnerFile(candidateRoot, "provenance/dependency-graph.json", dependencyGraph.bytes);
  invariant(FINAL_RECEIPTS.every((name) => receipts.has(name)), "seal candidate omitted a required receipt");
  return Object.freeze({
    auditManifest,
    outputInventory,
    ownedSources,
    patchManifest,
    digestReceipt,
    receiptCount: receipts.size,
    dependencyGraph: graph,
  });
}

async function moveAsideIfPresent(source, backup) {
  try {
    await rename(source, backup);
    return true;
  } catch (error) {
    if (error.code === "ENOENT") return false;
    throw error;
  }
}

async function treeFileInventory(root) {
  const results = [];
  async function visit(current, prefix) {
    const entries = await readdir(current, { withFileTypes: true });
    entries.sort((left, right) => codeUnitCompare(left.name, right.name));
    for (const entry of entries) {
      const absolute = path.join(current, entry.name);
      const relative = prefix === "" ? entry.name : `${prefix}/${entry.name}`;
      const stats = await lstat(absolute);
      invariant(!stats.isSymbolicLink(), `sealed tree contains a symlink: ${relative}`);
      if (stats.isDirectory()) await visit(absolute, relative);
      else {
        invariant(stats.isFile(), `sealed tree contains a non-regular entry: ${relative}`);
        results.push(relative);
      }
    }
  }
  await visit(root, "");
  return results.sort(codeUnitCompare);
}

async function verifySealPair(root) {
  const auditOpened = await readSafeRegularFile(path.join(root, "provenance/audit-manifest.json"), {
    label: "sealed audit manifest",
    expectedMode: 0o600,
    ownerOnly: true,
  });
  const auditManifest = validateAuditManifest(parseJson(auditOpened.bytes, "sealed audit manifest"), { requireSealed: true });
  const expectedProvenance = ["upstream.json", "dependency-graph.json", ...FINAL_RECEIPTS].sort(codeUnitCompare);
  invariant(canonicalJson(await treeFileInventory(path.join(root, "provenance"))) === canonicalJson(expectedProvenance), "sealed provenance tree contains missing or unlisted files");
  const expectedDist = auditManifest.distribution.files.map((record) => record.sourcePath.slice("dist/".length)).sort(codeUnitCompare);
  invariant(auditManifest.distribution.files.every((record) => record.sourcePath.startsWith("dist/")), "sealed distribution source path is outside dist");
  invariant(canonicalJson(await treeFileInventory(path.join(root, "dist"))) === canonicalJson(expectedDist), "sealed dist tree contains missing or unlisted files");
  const upstreamOpened = await readSafeRegularFile(path.join(root, "provenance/upstream.json"), { label: "sealed upstream provenance", expectedMode: 0o600, ownerOnly: true });
  const dependencyOpened = await readSafeRegularFile(path.join(root, "provenance/dependency-graph.json"), { label: "sealed dependency graph", expectedMode: 0o600, ownerOnly: true });
  invariant(sha256Bytes(upstreamOpened.bytes) === auditManifest.provenance.upstreamManifestSha256, "published upstream provenance digest mismatch");
  invariant(sha256Bytes(dependencyOpened.bytes) === auditManifest.provenance.dependencyGraphSha256, "published dependency graph digest mismatch");
  const ownedOpened = await readSafeRegularFile(path.join(root, "provenance/owned-sources.json"), { label: "sealed owned-sources manifest", expectedMode: 0o600, ownerOnly: true });
  const patchOpened = await readSafeRegularFile(path.join(root, "provenance/patch-manifest.json"), { label: "sealed patch manifest", expectedMode: 0o600, ownerOnly: true });
  const outputOpened = await readSafeRegularFile(path.join(root, "provenance/materialized-output-inventory.json"), { label: "sealed output inventory", expectedMode: 0o600, ownerOnly: true });
  invariant(sha256Bytes(ownedOpened.bytes) === auditManifest.sourceClosure.ownedSourcesManifestSha256, "published owned-sources digest mismatch");
  invariant(sha256Bytes(patchOpened.bytes) === auditManifest.sourceClosure.patchManifestSha256, "published patch-manifest digest mismatch");
  invariant(sha256Bytes(outputOpened.bytes) === auditManifest.build.outputInventorySha256, "published output-inventory digest mismatch");
  const ownedSources = validateOwnedSourcesManifest(parseJson(ownedOpened.bytes, "sealed owned-sources manifest"));
  const patchManifest = validatePatchManifest(parseJson(patchOpened.bytes, "sealed patch manifest"));
  const outputInventory = validateMaterializedOutputInventory(parseJson(outputOpened.bytes, "sealed output inventory"), auditManifest);
  invariant(canonicalJson(ownedSources.modules) === canonicalJson(outputInventory.modules), "published owned/output module closures differ");
  invariant(canonicalJson(ownedSources.assets) === canonicalJson(outputInventory.assets), "published owned/output asset closures differ");
  invariant(canonicalJson(patchManifest.events) === canonicalJson(outputInventory.transformEvents), "published patch/output event closures differ");
  const receiptOpened = await readSafeRegularFile(path.join(root, "provenance/distribution-digest.json"), { label: "sealed distribution digest receipt", expectedMode: 0o600, ownerOnly: true });
  parseDistributionDigestReceipt(receiptOpened.bytes, auditManifest, sha256Bytes(auditOpened.bytes));
  for (const record of auditManifest.distribution.files) {
    const opened = await readSafeRegularFile(path.join(root, ...record.sourcePath.split("/")), {
      label: `sealed distribution source ${record.sourcePath}`,
      expectedSha256: record.sha256,
      expectedSize: record.size,
      expectedMode: record.mode,
      ownerOnly: true,
    });
    if (record.role === "entrypoint") {
      const sealed = assertSelfContainedModule(opened.bytes);
      invariant(sealed.sha256 === outputInventory.buildAttestation.entrySha256, "published entry differs from AST-attested bytes");
      invariant(sealed.policySha256 === outputInventory.validatorPolicySha256, "published entry policy differs from AST-attested policy");
    }
  }
  return Object.freeze({ auditManifest, outputInventory });
}

export async function publishSealCandidate({
  candidateRoot,
  downstreamRoot,
  withPublicationLock,
  testOnlyAfterFirstSwap = undefined,
}) {
  invariant(path.isAbsolute(candidateRoot) && path.isAbsolute(downstreamRoot), "seal publication roots must be absolute");
  invariant(typeof withPublicationLock === "function", "seal publication requires the singleton build/publication lock");
  if (testOnlyAfterFirstSwap !== undefined) {
    invariant(process.env.NODE_TEST_CONTEXT !== undefined, "publication fault injection is forbidden outside node:test");
    invariant(typeof testOnlyAfterFirstSwap === "function", "publication fault injection must be a function");
  }
  return withPublicationLock(async () => {
    await verifySealPair(candidateRoot);
    const candidateProvenance = path.join(candidateRoot, "provenance");
    const candidateDist = path.join(candidateRoot, "dist");
    const destinationProvenance = path.join(downstreamRoot, "provenance");
    const destinationDist = path.join(downstreamRoot, "dist");
    const transactionId = `${process.pid}-${randomBytes(6).toString("hex")}`;
    const backupProvenance = path.join(downstreamRoot, `.provenance.backup-${transactionId}`);
    const backupDist = path.join(downstreamRoot, `.dist.backup-${transactionId}`);
    let oldProvenance = false;
    let oldDist = false;
    let newProvenance = false;
    let newDist = false;
    try {
      oldDist = await moveAsideIfPresent(destinationDist, backupDist);
      oldProvenance = await moveAsideIfPresent(destinationProvenance, backupProvenance);
      await rename(candidateDist, destinationDist);
      newDist = true;
      if (testOnlyAfterFirstSwap !== undefined) await testOnlyAfterFirstSwap();
      await rename(candidateProvenance, destinationProvenance);
      newProvenance = true;
      await verifySealPair(downstreamRoot);
      if (oldDist) await rm(backupDist, { recursive: true, force: true });
      if (oldProvenance) await rm(backupProvenance, { recursive: true, force: true });
      await rm(candidateRoot, { recursive: true, force: true });
      return Object.freeze({ published: true, receiptCount: FINAL_RECEIPTS.length });
    } catch (error) {
      if (newProvenance) await rm(destinationProvenance, { recursive: true, force: true });
      if (newDist) await rm(destinationDist, { recursive: true, force: true });
      if (oldProvenance) await rename(backupProvenance, destinationProvenance);
      if (oldDist) await rename(backupDist, destinationDist);
      throw error;
    }
  });
}
