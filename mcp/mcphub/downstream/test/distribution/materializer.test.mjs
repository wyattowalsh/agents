import assert from "node:assert/strict";
import { createHash, generateKeyPairSync, sign } from "node:crypto";
import { spawnSync } from "node:child_process";
import { gzipSync } from "node:zlib";
import { chmod, cp, mkdir, mkdtemp, readFile, readdir, realpath, rename, rm, symlink, writeFile, lstat } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { DatabaseSync } from "node:sqlite";
import test from "node:test";

import { bundleRuntime, transformLockedMcpHubSourceForUnitTest } from "../../src/materializer/bundle.mjs";
import { canonicalJson, sha1Bytes, sha256Bytes, sha512Sri } from "../../src/materializer/canonical.mjs";
import { verifyLockedDependencyClosure } from "../../src/materializer/dependency-closure.mjs";
import { validatePnpmCacheDirectory } from "../../src/materializer/gate.mjs";
import { readSafeRegularFile } from "../../src/materializer/safe-file.mjs";
import { collectUpstreamPackageAssets, publishSealCandidate, validateCapabilityManifest } from "../../src/materializer/seal.mjs";
import { assertSafeProcessEnvironment, checkLaunch, launchDistribution, resolveCurrentDistribution } from "../../src/materializer/launch.mjs";
import { computeDerivationDigest, computeDistributionDigest, safeRelativePath, validateLockedDependencyClosure } from "../../src/materializer/manifest.mjs";
import {
  checkMaterializationForUnitTest,
  materializeDistribution,
  materializeDistributionForUnitTest,
} from "../../src/materializer/materialize.mjs";
import { importSelfContainedModule, SEALED_MODULE_POLICY_SHA256 } from "../../src/materializer/sealed-module.mjs";
import { REVOKED_DISTRIBUTION_DIGESTS } from "../../src/materializer/revocations.mjs";
import { verifyUpstreamTarballBytes } from "../../src/materializer/tarball.mjs";
import {
  checkSelection,
  rollbackDistribution,
  selectDistribution,
} from "../../../../../scripts/mcphub/downstream-select.mjs";

const TARBALL_SHA = "4cb58d4cb11c7d036bde169504f0ddbe9849159e40fe764950ad62853d1502bb";
const TARBALL_SRI = "sha512-k0csMxsrZZOmh1Cef4WF/KGwFBtusJGPhCq5d1xTlhTfxy6qd61sGzU9ImoagquJZnnIaGp5SOWBv3xASNT5Tw==";
const SIGNING_KEY_ID = "SHA256:DhQ8wR5APBvFHLF/+Tc+AYvPOdTpcIDqOhxsBHRwC7U";
const ARCHIVE_INVENTORY = "de78c552b9e90a9a46e78bf10974eb0861cd270f4ca05c7bfdbeb73677de04fe";
const REPO_ROOT = path.resolve(import.meta.dirname, "../../../../..");
const MATERIALIZE_CLI = path.join(REPO_ROOT, "scripts/mcphub/downstream-materialize.mjs");
const LAUNCH_CLI = path.join(REPO_ROOT, "scripts/mcphub/downstream-launch.mjs");
const SELECT_CLI = path.join(REPO_ROOT, "scripts/mcphub/downstream-select.mjs");
const LOCKED_MCPHUB_ROOT = path.join(REPO_ROOT, "mcp/mcphub/downstream/node_modules/@samanhappy/mcphub");
const MCPHUB_SSRF_RELATIVE_PATH = "node_modules/@samanhappy/mcphub/dist/utils/ssrf.js";
const MCPHUB_SSRF_SHA256 = "d7fc7ac44dd23e74f599538c1bb92e698f5280311cfa6ed7582695abdd423e0e";
const MCPHUB_MCP_SERVICE_RELATIVE_PATH = "node_modules/@samanhappy/mcphub/dist/services/mcpService.js";
const MCPHUB_MCP_SERVICE_SHA256 = "e7a8f7d0b566ff4fb3988add3fa01bd7f6a058b0ad2e4fcdabc5ea5cd894f87e";
const FAILED_CUTOVER_DIGEST = "sha256-7369fbfd45eebe415500d41cbb9de5c55b2d95338932344ed09820d7e72a7262";
const QUARANTINED_DIGEST = "sha256-bda99d286dd44377d37a7c9500fea8d3f9005c426c59ce92b4a0018bebce0182";

const VERIFIED_UPSTREAM = Object.freeze({
  tarballSha256: TARBALL_SHA,
  tarballIntegrity: TARBALL_SRI,
  signatureKeyId: SIGNING_KEY_ID,
  archiveFileCount: 469,
  archiveUnpackedBytes: 9_706_506,
  archiveInventorySha256: ARCHIVE_INVENTORY,
});

function writeOctal(buffer, offset, length, value) {
  const encoded = `${value.toString(8).padStart(length - 1, "0")}\0`;
  buffer.write(encoded, offset, length, "ascii");
}

function tarMember(name, bytes, type = "0") {
  const header = Buffer.alloc(512);
  header.write(name, 0, 100, "utf8");
  writeOctal(header, 100, 8, 0o644);
  writeOctal(header, 108, 8, 0);
  writeOctal(header, 116, 8, 0);
  writeOctal(header, 124, 12, bytes.byteLength);
  writeOctal(header, 136, 12, 0);
  header.fill(0x20, 148, 156);
  header.write(type, 156, 1, "ascii");
  header.write("ustar\0", 257, 6, "binary");
  header.write("00", 263, 2, "ascii");
  const checksum = header.reduce((total, byte) => total + byte, 0);
  header.write(`${checksum.toString(8).padStart(6, "0")}\0 `, 148, 8, "ascii");
  const padding = Buffer.alloc(Math.ceil(bytes.byteLength / 512) * 512 - bytes.byteLength);
  return Buffer.concat([header, bytes, padding]);
}

function signedSyntheticTarball({ forbiddenMember = false } = {}) {
  const packageJson = Buffer.from(JSON.stringify({ name: "@test/mcphub", version: "1.0.0" }), "utf8");
  const members = [tarMember("package/package.json", packageJson)];
  if (forbiddenMember) members.push(tarMember("package/link", Buffer.alloc(0), "2"));
  const bytes = gzipSync(Buffer.concat([...members, Buffer.alloc(1024)]));
  const { privateKey, publicKey } = generateKeyPairSync("ec", { namedCurve: "P-256" });
  const publicKeySpkiBase64 = publicKey.export({ format: "der", type: "spki" }).toString("base64");
  const npmIntegrity = sha512Sri(bytes);
  const signedMessage = `@test/mcphub@1.0.0:${npmIntegrity}`;
  const signatureBase64 = sign("sha256", Buffer.from(signedMessage), privateKey).toString("base64");
  const policy = {
    packageName: "@test/mcphub",
    version: "1.0.0",
    tarballSha256: sha256Bytes(bytes),
    npmSha1: sha1Bytes(bytes),
    npmIntegrity,
    keyId: "TEST-PINNED-P256-KEY",
    signatureBase64,
    publicKeySpkiBase64,
    archiveFileCount: 1,
    archiveUnpackedBytes: packageJson.byteLength,
    archiveInventorySha256: null,
  };
  const provenance = {
    package: {
      name: policy.packageName,
      version: policy.version,
      tarballSha256: policy.tarballSha256,
      npmSha1: policy.npmSha1,
      npmIntegrity: policy.npmIntegrity,
      fileCount: policy.archiveFileCount,
      unpackedSize: policy.archiveUnpackedBytes,
    },
    signature: {
      verified: true,
      algorithm: "ecdsa-sha2-nistp256",
      signedMessage,
      keyId: policy.keyId,
      signatureBase64,
      publicKeySpkiBase64,
    },
  };
  return { bytes, policy, provenance };
}

async function fixture({ entrySource: suppliedEntrySource } = {}) {
  const temporary = await realpath(await mkdtemp(path.join(os.tmpdir(), "mcphub-distribution-")));
  const evidenceRoot = path.join(temporary, "evidence");
  const sourceRoot = path.join(temporary, "source");
  const runtimeRoot = path.join(temporary, "runtime");
  await mkdir(path.join(evidenceRoot, "provenance"), { mode: 0o700, recursive: true });
  await mkdir(sourceRoot, { mode: 0o700 });
  await mkdir(runtimeRoot, { mode: 0o700 });
  for (const directory of [evidenceRoot, path.join(evidenceRoot, "provenance"), sourceRoot, runtimeRoot]) await chmod(directory, 0o700);

  const entrySource = suppliedEntrySource ?? [
    "export async function main(context) {",
    "  globalThis.__MCPHUB_DOWNSTREAM_TEST_LAUNCH__ = { argv: context.argv, digest: context.auditManifest.distribution.digest };",
    "}",
    "",
  ].join("\n");
  const sourcePath = path.join(sourceRoot, "dist/runtime/main.mjs");
  await mkdir(path.dirname(sourcePath), { mode: 0o700, recursive: true });
  await writeFile(sourcePath, entrySource, { mode: 0o600 });
  await chmod(sourcePath, 0o600);

  const evidence = {
    "provenance/upstream.json": "{\"upstream\":true}\n",
    "provenance/dependency-graph.json": "{\"graph\":true}\n",
    "package.json": "{\"private\":true}\n",
    "pnpm-lock.yaml": "lockfileVersion: '9.0'\n",
  };
  const evidenceDigests = {};
  for (const [relativePath, content] of Object.entries(evidence)) {
    const filePath = path.join(evidenceRoot, ...relativePath.split("/"));
    await writeFile(filePath, content, { mode: 0o600 });
    await chmod(filePath, 0o600);
    evidenceDigests[relativePath] = sha256Bytes(Buffer.from(content));
  }

  const distributionFile = {
    sourcePath: "dist/runtime/main.mjs",
    path: "runtime/main.mjs",
    sha256: sha256Bytes(Buffer.from(entrySource)),
    size: Buffer.byteLength(entrySource),
    mode: 0o600,
    role: "entrypoint",
  };
  const capabilitySource = "{\"schemaVersion\":\"1.0.0\",\"group\":{\"name\":\"things\"}}\n";
  const capabilitySourcePath = path.join(sourceRoot, "dist/things-capability-manifest.json");
  await writeFile(capabilitySourcePath, capabilitySource, { mode: 0o600 });
  await chmod(capabilitySourcePath, 0o600);
  const capabilityFile = {
    sourcePath: "dist/things-capability-manifest.json",
    path: "things-capability-manifest.json",
    sha256: sha256Bytes(Buffer.from(capabilitySource)),
    size: Buffer.byteLength(capabilitySource),
    mode: 0o600,
    role: "asset",
  };
  const lockedModuleBytes = Buffer.from("export default class AppServer {}\n", "utf8");
  const lockedModuleSha256 = sha256Bytes(lockedModuleBytes);
  const lockedModuleSha512 = createHash("sha512").update(lockedModuleBytes).digest("hex");
  const mcphubIntegrity = TARBALL_SRI;
  const mcphubLockKey = "@samanhappy/mcphub@1.0.32";
  const packageIndexKey = `${mcphubIntegrity}\t${mcphubLockKey}`;
  const packageIndexRow = Buffer.from("synthetic-pnpm-v11-package-index-row", "utf8");
  const modules = [{
    path: "node_modules/@samanhappy/mcphub/dist/server.js",
    sha256: lockedModuleSha256,
    size: lockedModuleBytes.byteLength,
    kind: "locked-dependency",
  }, {
    path: "src/runtime/main.ts",
    sha256: sha256Bytes(Buffer.from(entrySource)),
    size: Buffer.byteLength(entrySource),
    kind: "owned-source",
  }];
  const moduleInventorySha256 = sha256Bytes(Buffer.from(canonicalJson(modules)));
  const transformEvents = [];
  const transformEventsSha256 = sha256Bytes(Buffer.from(canonicalJson(transformEvents)));
  const buildAttestation = {
    schemaVersion: 1,
    astValidated: true,
    entrySha256: distributionFile.sha256,
    validatorPolicySha256: SEALED_MODULE_POLICY_SHA256,
    transformEventsSha256,
    moduleInventorySha256,
  };
  const buildAttestationSha256 = sha256Bytes(Buffer.from(canonicalJson(buildAttestation)));
  const lockedDependencyClosurePayload = {
    schemaVersion: 1,
    status: "verified",
    method: "fresh-offline-copy-install+pnpm-v11-cafs-sha512",
    lockfileSha256: evidenceDigests["pnpm-lock.yaml"],
    lifecycleScriptsExecuted: false,
    networkResolution: false,
    packageImportMethod: "copy",
    storeFormat: "v11",
    pnpm: {
      version: "11.22.0",
      executableSha256: sha256Bytes(Buffer.from("synthetic-pnpm-11.22.0", "utf8")),
      executableSize: Buffer.byteLength("synthetic-pnpm-11.22.0"),
    },
    storeIndexSha256: sha256Bytes(Buffer.from("synthetic-pnpm-v11-index", "utf8")),
    packageCount: 1,
    moduleCount: 1,
    packages: [{
      package: "@samanhappy/mcphub",
      version: "1.0.32",
      lockIntegrity: mcphubIntegrity,
      packageIndexKey,
      packageIndexRowSha256: sha256Bytes(packageIndexRow),
      packageIndexRowSize: packageIndexRow.byteLength,
      moduleCount: 1,
    }],
    modules: [{
      modulePath: "node_modules/@samanhappy/mcphub/dist/server.js",
      package: "@samanhappy/mcphub",
      version: "1.0.32",
      packageRelativePath: "dist/server.js",
      lockKey: mcphubLockKey,
      lockIntegrity: mcphubIntegrity,
      sha256: lockedModuleSha256,
      size: lockedModuleBytes.byteLength,
      installedMode: 0o644,
      cafsSha512: lockedModuleSha512,
      cafsPath: `files/${lockedModuleSha512.slice(0, 2)}/${lockedModuleSha512.slice(2)}`,
      packageIndexKey,
      packageIndexRowSha256: sha256Bytes(packageIndexRow),
      packageIndexRowSize: packageIndexRow.byteLength,
    }],
  };
  const lockedDependencyClosure = {
    ...lockedDependencyClosurePayload,
    inventorySha256: sha256Bytes(Buffer.from(canonicalJson(lockedDependencyClosurePayload))),
  };
  const assets = [{
    sourcePath: "openspec/changes/replace-supathings-with-things-plus-plus/capability-manifest.json",
    sourceSha256: capabilityFile.sha256,
    outputPath: capabilityFile.sourcePath,
    outputSha256: capabilityFile.sha256,
    size: capabilityFile.size,
    mode: 0o600,
  }];
  const distributionFiles = [distributionFile, capabilityFile];
  const sealAttestation = {
    schemaVersion: 1,
    buildAttestationSha256,
    lockedDependencyClosureSha256: lockedDependencyClosure.inventorySha256,
    assetInventorySha256: sha256Bytes(Buffer.from(canonicalJson(assets))),
    distributionFileInventorySha256: sha256Bytes(Buffer.from(canonicalJson(distributionFiles))),
  };
  const sealAttestationSha256 = sha256Bytes(Buffer.from(canonicalJson(sealAttestation)));
  const outputInventory = {
    schemaVersion: 1,
    status: "sealed",
    bundler: {
      name: "rolldown",
      version: "1.2.6",
      entry: "src/runtime/main.ts",
      output: "dist/runtime/main.mjs",
      format: "esm",
      platform: "node",
      codeSplitting: false,
      sourcemap: false,
      minify: "dce-only",
      comments: false,
      polyfillRequire: false,
      emittedChunks: 1,
      emittedAssets: 0,
    },
    modules,
    transformations: [],
    transformEvents,
    transformEventsSha256,
    validatorPolicySha256: SEALED_MODULE_POLICY_SHA256,
    buildAttestation,
    buildAttestationSha256,
    lockedDependencyClosure,
    sealAttestation,
    sealAttestationSha256,
    assets,
    files: distributionFiles,
  };
  const ownedSourcesContent = `${canonicalJson({
    schemaVersion: 1,
    status: "sealed",
    exhaustive: true,
    entry: "src/runtime/main.ts",
    modules,
    moduleCount: modules.length,
    moduleInventorySha256,
    lockedDependencyClosureSha256: lockedDependencyClosure.inventorySha256,
    assets,
  })}\n`;
  const patchManifestContent = `${canonicalJson({
    schemaVersion: 1,
    status: "sealed",
    bundler: { name: "rolldown", version: "1.2.6" },
    productionLoaderTransformations: [],
    validatorPolicySha256: SEALED_MODULE_POLICY_SHA256,
    events: transformEvents,
    eventCount: transformEvents.length,
    eventsSha256: transformEventsSha256,
    buildAttestation,
    buildAttestationSha256,
  })}\n`;
  for (const [relativePath, content] of [
    ["provenance/owned-sources.json", ownedSourcesContent],
    ["provenance/patch-manifest.json", patchManifestContent],
  ]) {
    const filePath = path.join(evidenceRoot, ...relativePath.split("/"));
    await writeFile(filePath, content, { mode: 0o600 });
    await chmod(filePath, 0o600);
    evidenceDigests[relativePath] = sha256Bytes(Buffer.from(content));
  }
  const outputInventoryContent = `${canonicalJson(outputInventory)}\n`;
  const outputInventoryPath = path.join(evidenceRoot, "provenance/materialized-output-inventory.json");
  await writeFile(outputInventoryPath, outputInventoryContent, { mode: 0o600 });
  await chmod(outputInventoryPath, 0o600);
  evidenceDigests["provenance/materialized-output-inventory.json"] = sha256Bytes(Buffer.from(outputInventoryContent));

  const manifest = {
    schemaVersion: 1,
    status: "sealed",
    provenance: {
      upstreamManifestSha256: evidenceDigests["provenance/upstream.json"],
      upstreamTarballSha256: TARBALL_SHA,
      upstreamTarballIntegrity: TARBALL_SRI,
      upstreamSignatureKeyId: SIGNING_KEY_ID,
      upstreamArchiveFileCount: 469,
      upstreamArchiveUnpackedBytes: 9_706_506,
      upstreamArchiveInventorySha256: ARCHIVE_INVENTORY,
      dependencyGraphSha256: evidenceDigests["provenance/dependency-graph.json"],
      packageJsonSha256: evidenceDigests["package.json"],
      lockfileSha256: evidenceDigests["pnpm-lock.yaml"],
    },
    dependencies: {
      publicEdge: { server: "2.0.0", core: "2.0.0", node: null },
      privateBackendClient: { sdk: "1.29.0" },
      schemaValidator: {
        package: "@cfworker/json-schema",
        version: "4.1.1",
        integrity: "sha512-gAmrUZSGtKc3AiBL71iNWxDsyUC5uMaKKGdvzYsBoTW/xi42JQHl7eKV2OYzCUqvc+D2RCcf7EXY2iCyFIk6og==",
        tarballSha256: "f3a8076b450505f0671fa78a6efb5e7726883e2c6dfb13b29261872803610203",
        signatureKeyId: SIGNING_KEY_ID,
      },
      v1V2BleedRejected: true,
    },
    sourceClosure: {
      exhaustive: true,
      ownedSourcesManifestSha256: evidenceDigests["provenance/owned-sources.json"],
      patchManifestSha256: evidenceDigests["provenance/patch-manifest.json"],
      derivationSha256: "0".repeat(64),
      productionLoaderTransformations: [],
    },
    build: {
      commands: ["pnpm install --frozen-lockfile --offline --ignore-workspace --ignore-scripts", "pnpm run build"],
      nodeVersion: process.version,
      packageManager: "pnpm@11.22.0",
      outputInventoryComplete: true,
      outputInventorySha256: evidenceDigests["provenance/materialized-output-inventory.json"],
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
      files: distributionFiles,
    },
  };
  manifest.sourceClosure.derivationSha256 = computeDerivationDigest(manifest);
  manifest.distribution.digest = computeDistributionDigest(manifest);
  const manifestPath = path.join(temporary, "audit.json");
  const manifestContent = `${canonicalJson(manifest)}\n`;
  await writeFile(manifestPath, manifestContent, { mode: 0o600 });
  await chmod(manifestPath, 0o600);
  const digestReceipt = {
    schemaVersion: 1,
    status: "sealed",
    auditManifestSha256: sha256Bytes(Buffer.from(manifestContent)),
    outputInventorySha256: manifest.build.outputInventorySha256,
    distributionDigest: manifest.distribution.digest,
    entryPoint: manifest.distribution.entryPoint,
    entryExport: manifest.distribution.entryExport,
    fileCount: manifest.distribution.files.length,
  };
  const digestReceiptPath = path.join(evidenceRoot, "provenance/distribution-digest.json");
  await writeFile(digestReceiptPath, `${canonicalJson(digestReceipt)}\n`, { mode: 0o600 });
  await chmod(digestReceiptPath, 0o600);
  const options = { manifestPath, evidenceRoot, sourceRoot, runtimeRoot };
  return { temporary, evidenceRoot, sourceRoot, runtimeRoot, sourcePath, manifestPath, manifest, options };
}

function materializeFixture(options) {
  return materializeDistributionForUnitTest(options, VERIFIED_UPSTREAM);
}

function checkFixture(options) {
  return checkMaterializationForUnitTest(options, VERIFIED_UPSTREAM);
}

async function withFixture(run, settings) {
  const state = await fixture(settings);
  try {
    await run(state);
  } finally {
    delete globalThis.__MCPHUB_DOWNSTREAM_TEST_LAUNCH__;
    await rm(state.temporary, { recursive: true, force: true });
  }
}

async function copyFixtureSealCandidate(state, candidateRoot) {
  await mkdir(candidateRoot, { recursive: true, mode: 0o700 });
  await chmod(candidateRoot, 0o700);
  await cp(path.join(state.sourceRoot, "dist"), path.join(candidateRoot, "dist"), { recursive: true, force: false });
  await cp(path.join(state.evidenceRoot, "provenance"), path.join(candidateRoot, "provenance"), { recursive: true, force: false });
  await cp(state.manifestPath, path.join(candidateRoot, "provenance/audit-manifest.json"), { force: false });
}

async function rewriteManifestAndDigestReceipt({ manifest, manifestPath, evidenceRoot }) {
  const manifestContent = `${canonicalJson(manifest)}\n`;
  await writeFile(manifestPath, manifestContent, { mode: 0o600 });
  await chmod(manifestPath, 0o600);
  const receipt = {
    schemaVersion: 1,
    status: "sealed",
    auditManifestSha256: sha256Bytes(Buffer.from(manifestContent)),
    outputInventorySha256: manifest.build.outputInventorySha256,
    distributionDigest: manifest.distribution.digest,
    entryPoint: manifest.distribution.entryPoint,
    entryExport: manifest.distribution.entryExport,
    fileCount: manifest.distribution.files.length,
  };
  const receiptPath = path.join(evidenceRoot, "provenance/distribution-digest.json");
  await writeFile(receiptPath, `${canonicalJson(receipt)}\n`, { mode: 0o600 });
  await chmod(receiptPath, 0o600);
}

async function syntheticBundleWorkspace(mainSource, extras = {}) {
  const temporary = await realpath(await mkdtemp(path.join(os.tmpdir(), "mcphub-bundle-")));
  const entryPath = path.join(temporary, "src/runtime/main.ts");
  const outputPath = path.join(temporary, "dist/runtime/main.mjs");
  await mkdir(path.dirname(entryPath), { mode: 0o700, recursive: true });
  await writeFile(entryPath, mainSource, { mode: 0o600 });
  for (const [relativePath, content] of Object.entries(extras)) {
    const target = path.join(temporary, ...relativePath.split("/"));
    await mkdir(path.dirname(target), { mode: 0o700, recursive: true });
    await writeFile(target, content, { mode: 0o600 });
  }
  return { temporary, entryPath, outputPath };
}

test("materializes owner-only bytes once with fail-closed revoked and green non-revoked selection", async () => {
  await withFixture(async ({ options, runtimeRoot, manifest, temporary }) => {
    assert.equal(Object.isFrozen(REVOKED_DISTRIBUTION_DIGESTS), true);
    assert.deepEqual(REVOKED_DISTRIBUTION_DIGESTS, [FAILED_CUTOVER_DIGEST, QUARANTINED_DIGEST]);
    assert.equal(REVOKED_DISTRIBUTION_DIGESTS.includes(manifest.distribution.digest), false);

    for (const [index, digest] of REVOKED_DISTRIBUTION_DIGESTS.entries()) {
      const receiptPath = path.join(temporary, `revoked-selection-${index}.json`);
      await assert.rejects(
        selectDistribution({ runtimeRoot, digest, receiptPath }),
        /distribution digest is revoked/,
      );
      await assert.rejects(lstat(path.join(runtimeRoot, "current")), { code: "ENOENT" });
      await assert.rejects(lstat(receiptPath), { code: "ENOENT" });

      const currentPath = path.join(runtimeRoot, "current");
      await symlink(digest, currentPath);
      await assert.rejects(checkSelection({ runtimeRoot }), /distribution digest is revoked/);

      const rollbackReceiptPath = path.join(temporary, `revoked-current-rollback-${index}.json`);
      const rollbackReceipt = {
        schemaVersion: 1,
        kind: "mcphub-downstream-selection",
        runtimeRoot,
        selectedDigest: manifest.distribution.digest,
        previous: { state: "absent" },
        rolledBack: false,
      };
      await writeFile(rollbackReceiptPath, `${JSON.stringify(rollbackReceipt)}\n`, { mode: 0o600 });
      await assert.rejects(
        rollbackDistribution({ runtimeRoot, receiptPath: rollbackReceiptPath }),
        /distribution digest is revoked/,
      );
      assert.equal((await lstat(currentPath)).isSymbolicLink(), true);
      assert.equal(JSON.parse(await readFile(rollbackReceiptPath, "utf8")).rolledBack, false);
      await rm(currentPath);
      await rm(rollbackReceiptPath);

      const revokedPreviousReceiptPath = path.join(temporary, `revoked-previous-rollback-${index}.json`);
      const revokedPreviousReceipt = {
        ...rollbackReceipt,
        previous: { state: "present", digest },
      };
      await writeFile(revokedPreviousReceiptPath, `${JSON.stringify(revokedPreviousReceipt)}\n`, { mode: 0o600 });
      await assert.rejects(
        rollbackDistribution({ runtimeRoot, receiptPath: revokedPreviousReceiptPath }),
        /distribution digest is revoked/,
      );
      await assert.rejects(lstat(currentPath), { code: "ENOENT" });
      assert.equal(JSON.parse(await readFile(revokedPreviousReceiptPath, "utf8")).rolledBack, false);
      await rm(revokedPreviousReceiptPath);
    }

    const first = await materializeFixture(options);
    assert.deepEqual(first, { digest: manifest.distribution.digest, evidenceCount: 8, fileCount: 2, upstreamArchiveInventorySha256: ARCHIVE_INVENTORY, published: true });
    const digestRoot = path.join(runtimeRoot, manifest.distribution.digest);
    assert.equal((await lstat(digestRoot)).mode & 0o777, 0o700);
    assert.equal((await lstat(path.join(digestRoot, "runtime/main.mjs"))).mode & 0o777, 0o600);
    await assert.rejects(lstat(path.join(runtimeRoot, "current")), { code: "ENOENT" });
    const check = await checkFixture(options);
    assert.deepEqual(check, { mode: "check", digest: manifest.distribution.digest, evidenceCount: 8, fileCount: 2, upstreamArchiveInventorySha256: ARCHIVE_INVENTORY, publishRequired: false });
    assert.equal((await materializeFixture(options)).published, false);

    const receiptPath = path.join(temporary, "selection.json");
    assert.deepEqual(
      await selectDistribution({ runtimeRoot, digest: manifest.distribution.digest, receiptPath }),
      { operation: "select", selectedDigest: manifest.distribution.digest, previousState: "absent" },
    );
    assert.deepEqual(await checkSelection({ runtimeRoot }), {
      operation: "check",
      selectedDigest: manifest.distribution.digest,
    });
    assert.deepEqual(await rollbackDistribution({ runtimeRoot, receiptPath }), {
      operation: "rollback",
      restoredState: "absent",
    });
    assert.equal(JSON.parse(await readFile(receiptPath, "utf8")).rolledBack, true);
    await assert.rejects(lstat(path.join(runtimeRoot, "current")), { code: "ENOENT" });
  });
});

test("launcher rejects unflagged imports and executes flagged descriptor-read bundle bytes", async () => {
  await withFixture(async ({ options, runtimeRoot, manifest }) => {
    for (const digest of REVOKED_DISTRIBUTION_DIGESTS) {
      const currentPath = path.join(runtimeRoot, "current");
      await symlink(digest, currentPath);
      await assert.rejects(resolveCurrentDistribution(runtimeRoot), /distribution digest is revoked/);
      await assert.rejects(checkLaunch({ runtimeRoot }), /distribution digest is revoked/);
      await assert.rejects(launchDistribution({ runtimeRoot }), /distribution digest is revoked/);
      await assert.rejects(lstat(path.join(runtimeRoot, digest)), { code: "ENOENT" });
      await rm(currentPath);
    }

    await materializeFixture(options);
    await symlink(manifest.distribution.digest, path.join(runtimeRoot, "current"));
    assert.equal((await checkLaunch({ runtimeRoot })).digest, manifest.distribution.digest);

    const environment = { ...process.env };
    delete environment.NODE_OPTIONS;
    delete environment.NODE_PATH;
    const unflagged = spawnSync(process.execPath, [LAUNCH_CLI, "--runtime-root", runtimeRoot], {
      encoding: "utf8",
      env: environment,
    });
    assert.equal(unflagged.status, 1);
    assert.equal(unflagged.stdout, "");
    assert.deepEqual(JSON.parse(unflagged.stderr), {
      status: "error",
      reasonCode: "MCPHUB_DOWNSTREAM_LAUNCH_FAILED",
    });
    const flagged = spawnSync(
      process.execPath,
      ["--disallow-code-generation-from-strings", LAUNCH_CLI, "--runtime-root", runtimeRoot, "--", "--fixture-child"],
      { encoding: "utf8", env: environment },
    );
    assert.equal(flagged.status, 0, flagged.stderr);
    assert.deepEqual(JSON.parse(flagged.stdout), {
      digest: manifest.distribution.digest,
      entryPoint: manifest.distribution.entryPoint,
    });
    assert.equal(flagged.stderr, "");

    await launchDistribution({ runtimeRoot, argv: ["--fixture"] });
    assert.deepEqual(globalThis.__MCPHUB_DOWNSTREAM_TEST_LAUNCH__, { argv: ["--fixture"], digest: manifest.distribution.digest });
    assert.throws(() => process.getBuiltinModule("node:path"), /runtime capability is forbidden/);
    assert.throws(() => process.binding("module_wrap"), /process\.binding capability is forbidden/);
    assert.equal(typeof process.binding("buffer").kStringMaxLength, "number");
    const DynamicFunction = (() => {}).constructor;
    assert.throws(() => DynamicFunction("return 42")(), /Code generation from strings disallowed/);
  });
});

test("CLIs emit content-free reports and stable content-free failure reason codes", async () => {
  await withFixture(async ({ options, runtimeRoot, manifest, temporary, manifestPath, evidenceRoot, sourceRoot, sourcePath }) => {
    await materializeFixture(options);
    await symlink(manifest.distribution.digest, path.join(runtimeRoot, "current"));
    const environment = { ...process.env };
    delete environment.NODE_OPTIONS;
    delete environment.NODE_PATH;
    const launchCheck = spawnSync(process.execPath, [LAUNCH_CLI, "--check", "--runtime-root", runtimeRoot], { encoding: "utf8", env: environment });
    assert.equal(launchCheck.status, 0, launchCheck.stderr);
    assert.equal(launchCheck.stdout.includes(temporary), false);
    const selectionReceiptPath = path.join(temporary, "revoked-cli-selection.json");
    const revokedSelection = spawnSync(process.execPath, [
      SELECT_CLI,
      "select",
      "--runtime-root",
      runtimeRoot,
      "--digest",
      FAILED_CUTOVER_DIGEST,
      "--receipt",
      selectionReceiptPath,
    ], { encoding: "utf8", env: environment });
    assert.equal(revokedSelection.status, 1);
    assert.equal(revokedSelection.stdout, "");
    assert.deepEqual(JSON.parse(revokedSelection.stderr), {
      status: "error",
      reasonCode: "MCPHUB_DOWNSTREAM_SELECTION_FAILED",
    });
    assert.equal(revokedSelection.stderr.includes(temporary), false);
    assert.equal(revokedSelection.stderr.includes(FAILED_CUTOVER_DIGEST), false);
    await assert.rejects(lstat(selectionReceiptPath), { code: "ENOENT" });
    assert.equal((await checkLaunch({ runtimeRoot })).digest, manifest.distribution.digest);
    const failed = spawnSync(process.execPath, [MATERIALIZE_CLI, "--check", "--manifest", manifestPath, "--evidence-root", evidenceRoot, "--source-root", sourceRoot, "--runtime-root", runtimeRoot, "--upstream-tarball", sourcePath], { encoding: "utf8", env: environment });
    assert.equal(failed.status, 1);
    assert.deepEqual(JSON.parse(failed.stderr), { status: "error", reasonCode: "MCPHUB_DOWNSTREAM_MATERIALIZATION_FAILED" });
    assert.equal(failed.stderr.includes(temporary), false);
    const invalid = spawnSync(process.execPath, [MATERIALIZE_CLI, "--unknown", temporary], { encoding: "utf8", env: environment });
    assert.equal(invalid.status, 2);
    assert.deepEqual(JSON.parse(invalid.stderr), { status: "error", reasonCode: "MCPHUB_DOWNSTREAM_ARGUMENT_INVALID" });
  });
});

test("rejects tampered source and evidence bytes before publication", async () => {
  await withFixture(async ({ options, sourcePath, evidenceRoot, runtimeRoot, manifest }) => {
    await writeFile(sourcePath, "tampered\n", { mode: 0o600 });
    await assert.rejects(materializeFixture(options), /source file (size|hash) mismatch/);
    await assert.rejects(lstat(path.join(runtimeRoot, manifest.distribution.digest)), { code: "ENOENT" });
    await writeFile(sourcePath, "x".repeat(manifest.distribution.files[0].size), { mode: 0o600 });
    await writeFile(path.join(evidenceRoot, "provenance/upstream.json"), "{\"tampered\":true}\n", { mode: 0o600 });
    await assert.rejects(materializeFixture(options), /evidence file hash mismatch/);
  });
});

test("rejects unlisted materialized files and directories", async () => {
  await withFixture(async ({ options, runtimeRoot, manifest }) => {
    await materializeFixture(options);
    const digestRoot = path.join(runtimeRoot, manifest.distribution.digest);
    await writeFile(path.join(digestRoot, "unlisted.js"), "export {};\n", { mode: 0o600 });
    await symlink(manifest.distribution.digest, path.join(runtimeRoot, "current"));
    await assert.rejects(checkLaunch({ runtimeRoot }), /file inventory does not match/);
    await rm(path.join(digestRoot, "unlisted.js"));
    await mkdir(path.join(digestRoot, "unlisted"), { mode: 0o700 });
    await assert.rejects(checkLaunch({ runtimeRoot }), /directory inventory does not match/);
  });
});

test("rejects candidate closure and source symlinks", async () => {
  await withFixture(async ({ options, manifestPath, sourcePath, sourceRoot, evidenceRoot, manifest }) => {
    manifest.status = "candidate";
    manifest.sourceClosure.exhaustive = false;
    manifest.sourceClosure.derivationSha256 = null;
    manifest.build.outputInventoryComplete = false;
    manifest.distribution.digest = computeDistributionDigest(manifest);
    await rewriteManifestAndDigestReceipt({ manifest, manifestPath, evidenceRoot });
    await assert.rejects(materializeFixture(options), /requires a sealed audit manifest/);

    manifest.status = "sealed";
    manifest.sourceClosure.exhaustive = true;
    manifest.build.outputInventoryComplete = true;
    manifest.sourceClosure.derivationSha256 = computeDerivationDigest(manifest);
    manifest.distribution.digest = computeDistributionDigest(manifest);
    await rewriteManifestAndDigestReceipt({ manifest, manifestPath, evidenceRoot });
    await rm(sourcePath);
    const realEntry = path.join(sourceRoot, "real-entry.mjs");
    await writeFile(realEntry, "export async function main() {}\n", { mode: 0o600 });
    await symlink(realEntry, sourcePath);
    await assert.rejects(materializeFixture(options), /could not be opened safely/);
  });
});

test("rejects preload, loader, NODE_PATH, and npx execution environments", () => {
  assert.throws(() => assertSafeProcessEnvironment({ env: { NODE_OPTIONS: "--import=hook.mjs" }, execArgv: [], argv: ["node", "launcher.mjs"] }), /NODE_OPTIONS is forbidden/);
  assert.throws(() => assertSafeProcessEnvironment({ env: { NODE_PATH: "/tmp/cache" }, execArgv: [], argv: ["node", "launcher.mjs"] }), /NODE_PATH is forbidden/);
  assert.throws(() => assertSafeProcessEnvironment({ env: {}, execArgv: ["--loader=hook.mjs"], argv: ["node", "launcher.mjs"] }), /preload argument/);
  assert.throws(() => assertSafeProcessEnvironment({ env: {}, execArgv: [], argv: ["node", "/tmp/_npx/a/launcher.mjs"] }), /npx execution is forbidden/);
});

test("production materialization requires actual tarball bytes and rejects missing, swapped, and symlink inputs", async () => {
  await withFixture(async ({ options, sourcePath, temporary }) => {
    const production = { ...options };
    await assert.rejects(materializeDistribution(production), /audited upstream tarball path is required/);
    await assert.rejects(materializeDistribution({ ...production, upstreamTarballPath: sourcePath }), /hash mismatch/);
    const link = path.join(temporary, "upstream.tgz");
    await symlink(sourcePath, link);
    await assert.rejects(materializeDistribution({ ...production, upstreamTarballPath: link }), /could not be opened safely/);
  });
});

test("verifies SHA256, SRI SHA512, pinned ECDSA signature, and extracted archive inventory", () => {
  const synthetic = signedSyntheticTarball();
  const verified = verifyUpstreamTarballBytes(synthetic.bytes, synthetic.provenance, synthetic.policy);
  assert.equal(verified.archiveFileCount, 1);
  assert.equal(verified.archiveUnpackedBytes, Buffer.byteLength(JSON.stringify({ name: "@test/mcphub", version: "1.0.0" })));
  assert.match(verified.archiveInventorySha256, /^[0-9a-f]{64}$/);
});

test("rejects wrong SRI even when other provenance is well formed", () => {
  const synthetic = signedSyntheticTarball();
  synthetic.provenance.package.npmIntegrity = `sha512-${Buffer.alloc(64).toString("base64")}`;
  assert.throws(() => verifyUpstreamTarballBytes(synthetic.bytes, synthetic.provenance, synthetic.policy), /provenance SRI mismatch/);
});

test("rejects swapped registry signature bytes and signing-key substitution", () => {
  const synthetic = signedSyntheticTarball();
  synthetic.provenance.signature.signatureBase64 = Buffer.from("wrong").toString("base64");
  assert.throws(() => verifyUpstreamTarballBytes(synthetic.bytes, synthetic.provenance, synthetic.policy), /signature bytes mismatch/);
  const second = signedSyntheticTarball();
  second.provenance.signature.keyId = "SUBSTITUTED";
  assert.throws(() => verifyUpstreamTarballBytes(second.bytes, second.provenance, second.policy), /key ID mismatch/);
});

test("rejects symlink and other non-regular members during independent extraction", () => {
  const synthetic = signedSyntheticTarball({ forbiddenMember: true });
  assert.throws(() => verifyUpstreamTarballBytes(synthetic.bytes, synthetic.provenance, synthetic.policy), /forbidden non-regular member/);
});

test("descriptor reads bind bytes to one stable inode across hostile pathname replacement", async () => {
  const temporary = await realpath(await mkdtemp(path.join(os.tmpdir(), "mcphub-safe-open-")));
  try {
    const original = path.join(temporary, "input");
    const moved = path.join(temporary, "moved");
    await writeFile(original, "trusted", { mode: 0o600 });
    const opened = await readSafeRegularFile(original, { label: "fixture", expectedSha256: sha256Bytes(Buffer.from("trusted")) });
    await rename(original, moved);
    await writeFile(original, "hostile", { mode: 0o600 });
    assert.equal(opened.bytes.toString("utf8"), "trusted");
    assert.notEqual((await readFile(original, "utf8")), opened.bytes.toString("utf8"));
    await rm(original);
    await symlink(moved, original);
    await assert.rejects(readSafeRegularFile(original), /could not be opened safely/);
  } finally {
    await rm(temporary, { recursive: true, force: true });
  }
});

test("rejects bare-package and dynamic imports before ancestor node_modules can resolve", async () => {
  await withFixture(async ({ options, temporary }) => {
    const packageRoot = path.join(temporary, "node_modules/poison");
    await mkdir(packageRoot, { recursive: true, mode: 0o700 });
    await writeFile(path.join(packageRoot, "package.json"), "{\"type\":\"module\",\"exports\":\"./index.js\"}\n", { mode: 0o600 });
    await writeFile(path.join(packageRoot, "index.js"), "globalThis.__POISON_EXECUTED__=true;\n", { mode: 0o600 });
    await assert.rejects(materializeFixture(options), /imports must be static node: built-ins/);
    assert.equal(globalThis.__POISON_EXECUTED__, undefined);
  }, { entrySource: 'import "poison"; export async function main() {}\n' });
  await withFixture(async ({ options }) => {
    await assert.rejects(materializeFixture(options), /dynamic import/);
  }, { entrySource: 'export async function main() { await import("node:fs"); }\n' });
  const computedBuiltin = Buffer.from('export function main(){ return process[`getBuiltin${"Module"}`]("node:path").sep; }\n');
  await assert.rejects(importSelfContainedModule(computedBuiltin), /computed process or global member access/);
  const aliasedBuiltin = Buffer.from('export function main(){ const runtimeProcess = process; const name = "getBuiltin" + "Module"; return runtimeProcess[name]("node:path").sep; }\n');
  await assert.rejects(importSelfContainedModule(aliasedBuiltin), /computed process or global member access/);
  const globalProcessAlias = Buffer.from('export function main(){ const p=globalThis.process; const key=["getBuiltin","Module"].join(""); return p[key]("node:path").sep; }\n');
  await assert.rejects(importSelfContainedModule(globalProcessAlias), /computed process or global member access/);
  const destructuredGlobalProcessAlias = Buffer.from('export function main(){ const root=globalThis; const {process:p0}=root; const p1=p0; const key=["getBuiltin","Module"].join(""); return p1[key]("node:path").sep; }\n');
  await assert.rejects(importSelfContainedModule(destructuredGlobalProcessAlias), /computed process or global member access/);
  const escapedBuiltin = Buffer.from('export function main(){ return process.get\\u0042uiltinModule("node:path").sep; }\n');
  await assert.rejects(importSelfContainedModule(escapedBuiltin), /mutable module resolution/);
  const moduleNamespace = Buffer.from('import * as nm from "node:module"; export function main(){ const load=nm["create"+"Require"](process.cwd()+"/sealed-entry.mjs"); return load("rolldown").VERSION; }\n');
  await assert.rejects(importSelfContainedModule(moduleNamespace), /computed createRequire|node:module import is forbidden/);
  const vmNamespace = Buffer.from('import * as vm from "node:vm"; export function main(){ return vm.runInThisContext("1+1"); }\n');
  await assert.rejects(importSelfContainedModule(vmNamespace), /node:vm import is forbidden/);
  const computedEval = Buffer.from('export function main(){ return globalThis["e"+"val"]("1+1"); }\n');
  await assert.rejects(importSelfContainedModule(computedEval), /computed eval|computed process or global member access/);
  const computedFunction = Buffer.from('export function main(){ return globalThis["Fun"+"ction"]("return 2")(); }\n');
  await assert.rejects(importSelfContainedModule(computedFunction), /computed Function|computed process or global member access/);
  const directDlopen = Buffer.from('export function main(){ return process.dlopen({}, "/private/tmp/addon.node"); }\n');
  await assert.rejects(importSelfContainedModule(directDlopen), /native module loading|process\.dlopen/);
  const computedDlopen = Buffer.from('export function main(){ return process["dlo"+"pen"]({}, "/private/tmp/addon.node"); }\n');
  await assert.rejects(importSelfContainedModule(computedDlopen), /computed process or global member access/);
  const destructuredDlopen = Buffer.from('export function main(){ const { dl\\u006fpen: load } = process; return typeof load; }\n');
  await assert.rejects(importSelfContainedModule(destructuredDlopen), /native module loading/);
  const constructorCodegen = Buffer.from('export function main(){ return (()=>{}).constructor("return 73")(); }\n');
  await assert.rejects(importSelfContainedModule(constructorCodegen), /inline function constructor/);
  const aliasedConstructorCodegen = Buffer.from('export function main(){ const f=()=>{}; return f.constructor("return 74")(); }\n');
  await assert.rejects(importSelfContainedModule(aliasedConstructorCodegen), /callable constructor/);
  const extractedConstructorCodegen = Buffer.from('const C = Function.call.bind(Object.prototype.hasOwnProperty).constructor; export function main(){ return C("return 75")(); }\n');
  await assert.rejects(importSelfContainedModule(extractedConstructorCodegen), /dynamic code generation|constructor access/);
  for (const source of [
    'function f(){} const C=f.constructor; export function main(){ return C("return 42")(); }\n',
    'const f=()=>{}; const C=f["constructor"]; export function main(){ return new C("return 43")(); }\n',
    'const {constructor:C}=function f(){}; export function main(){ return C.call(null,"return 44")(); }\n',
    'const C=Reflect.get(Array,"constructor"); export function main(){ return C.bind(null,"return 45")()(); }\n',
    'const {get}=Reflect; const C=get(Array,"constructor"); export function main(){ return C("return 46")(); }\n',
    'const C=Object.getOwnPropertyDescriptor(Object.getPrototypeOf(function f(){}),"constructor").value; export function main(){ return C("return 47")(); }\n',
  ]) {
    try {
      const loaded = await importSelfContainedModule(Buffer.from(source));
      assert.throws(() => loaded.main(), /Code generation from strings disallowed/);
    } catch (error) {
      assert.match(String(error), /constructor|code generation|descriptor/);
    }
  }
  for (const source of [
    'const {["process"]:p}=globalThis; const k=["Module","getBuiltin"].reverse().join(""); export function main(){ return p[k]("node:path").sep; }\n',
    'const p=globalThis["process"]; const k=["Module","getBuiltin"].reverse().join(""); export function main(){ return p[k]("node:path").sep; }\n',
    'const R=Reflect; const p=R.get(globalThis,["pro","cess"].join("")); const k=["Module","getBuiltin"].reverse().join(""); export function main(){ return R.get(p,k)("node:path").sep; }\n',
    'const getProcess=()=>process; const p=getProcess(); const k=["Module","getBuiltin"].reverse().join(""); export function main(){ return p[k]("node:path").sep; }\n',
    'const p=Object.getOwnPropertyDescriptor(globalThis,"process").value; const k=["Module","getBuiltin"].reverse().join(""); export function main(){ return p[k]("node:path").sep; }\n',
  ]) {
    await assert.rejects(importSelfContainedModule(Buffer.from(source)), /process|global|reflect|descriptor|computed/);
  }
  const constructorName = Buffer.from('export function main(value){ return value.constructor.name; }\n');
  const constructorNameModule = await importSelfContainedModule(constructorName);
  assert.equal(constructorNameModule.main(new Map()), "Map");
  const optionalConstructorName = Buffer.from('export function main(value){ return value?.constructor?.name; }\n');
  const optionalConstructorNameModule = await importSelfContainedModule(optionalConstructorName);
  assert.equal(optionalConstructorNameModule.main(new Set()), "Set");
  const importedProcess = Buffer.from('import proc from "node:process"; export function main(){ const key=["Module","getBuiltin"].reverse().join(""); return proc[key]("node:path").sep; }\n');
  await assert.rejects(importSelfContainedModule(importedProcess), /node:process import is forbidden/);
  for (const pseudoGlobal of ["__dirname", "__filename"]) {
    await assert.rejects(
      importSelfContainedModule(Buffer.from(`export function main(){ return ${pseudoGlobal}; }\n`)),
      /CommonJS pseudo-global/,
    );
  }
  const inertPseudoGlobals = await importSelfContainedModule(Buffer.from('export function main(){ return "__dirname __filename"; }\n'));
  assert.equal(inertPseudoGlobals.main(), "__dirname __filename");
  const templateImport = Buffer.from('export async function main(target){ return `${await import(target)}`; }\n');
  await assert.rejects(importSelfContainedModule(templateImport), /dynamic import/);
  const regexTemplateBypass = Buffer.from('export function main(){ return `${/}/.test("}") && process.getBuiltinModule("node:path").sep}`; }\n');
  await assert.rejects(importSelfContainedModule(regexTemplateBypass), /mutable module resolution/);
  const inertTokens = Buffer.from('// import(target), process.dlopen, and createRequire are inert here\nexport function main(){ return "Set globalThis.File to import(\'node:buffer\').File; eval Function getBuiltinModule"; }\n');
  const inertLoaded = await importSelfContainedModule(inertTokens);
  assert.equal(inertLoaded.main(), "Set globalThis.File to import('node:buffer').File; eval Function getBuiltinModule");
  const inertRequireKey = Buffer.from('export function main(){ return { require: "disabled" }; }\n');
  const inertRequireKeyLoaded = await importSelfContainedModule(inertRequireKey);
  assert.deepEqual(inertRequireKeyLoaded.main(), { require: "disabled" });
  const runtimeDerivedConstructor = Buffer.from('const prototype=Object.getPrototypeOf(()=>{}); const key=Object.getOwnPropertyNames(prototype).find((value)=>typeof value==="string"&&value.endsWith("structor")); const DynamicFunction=prototype[key]; export function main(){ return DynamicFunction("return 42")(); }\n');
  const runtimeDerivedConstructorModule = await importSelfContainedModule(runtimeDerivedConstructor);
  assert.throws(() => runtimeDerivedConstructorModule.main(), /Code generation from strings disallowed/);
  const runtimeDerivedProcess = Buffer.from('const descriptors=Object.getOwnPropertyDescriptors(globalThis); const values=Object.values(descriptors).map((entry)=>{try{return "value" in entry?entry.value:entry.get?.call(globalThis)}catch{return undefined}}); const p=values.find((value)=>value&&typeof value==="object"&&Object.getOwnPropertyNames(value).some((key)=>key.endsWith("BuiltinModule"))); const loaderKey=Object.getOwnPropertyNames(p).find((value)=>value.endsWith("BuiltinModule")); export function main(){ return p[loaderKey]("node:path"); }\n');
  const runtimeDerivedProcessModule = await importSelfContainedModule(runtimeDerivedProcess);
  assert.throws(() => runtimeDerivedProcessModule.main(), /runtime capability is forbidden/);
});

test("sealed entry bytes remain the executed bytes after hostile rename and symlink swap", async () => {
  await withFixture(async ({ options, runtimeRoot, manifest }) => {
    await materializeFixture(options);
    await symlink(manifest.distribution.digest, path.join(runtimeRoot, "current"));
    const resolved = await resolveCurrentDistribution(runtimeRoot);
    const entryPath = path.join(resolved.distributionRoot, "runtime/main.mjs");
    const moved = path.join(resolved.distributionRoot, "runtime/original.mjs");
    await rename(entryPath, moved);
    await symlink(moved, entryPath);
    const loaded = await importSelfContainedModule(resolved.entryBytes);
    await loaded.main({ argv: ["--sealed"], auditManifest: manifest });
    assert.deepEqual(globalThis.__MCPHUB_DOWNSTREAM_TEST_LAUNCH__, { argv: ["--sealed"], digest: manifest.distribution.digest });
    await assert.rejects(checkLaunch({ runtimeRoot }), /symlink/);
  });
});

test("JSON Schema relativePath pattern is exactly aligned with safeRelativePath", async () => {
  const schema = JSON.parse(await readFile(path.join(REPO_ROOT, "config/schemas/mcphub-downstream-audit.schema.json"), "utf8"));
  const pattern = new RegExp(schema.$defs.relativePath.pattern, "u");
  const corpus = ["a", "a/b", "a.b/c-d_1", "Δ/文件", "a\nb", "", "/a", "a/", "a//b", ".", "..", "./a", "a/.", "a/../b", "a\\b", "a\0b"];
  for (const value of corpus) {
    let runtime = true;
    try { safeRelativePath(value); } catch { runtime = false; }
    const schemaAccepts = typeof value === "string" && value.length >= 1 && pattern.test(value);
    assert.equal(schemaAccepts, runtime, `relativePath parity mismatch for ${JSON.stringify(value)}`);
  }
});

test("seal rejects duplicated capability rows and wrong Things group servers", async () => {
  const capabilityPath = path.join(REPO_ROOT, "openspec/changes/replace-supathings-with-things-plus-plus/capability-manifest.json");
  const canonical = JSON.parse(await readFile(capabilityPath, "utf8"));
  assert.equal(validateCapabilityManifest(canonical), canonical);
  const duplicate = structuredClone(canonical);
  duplicate.tools[1] = structuredClone(duplicate.tools[0]);
  assert.throws(() => validateCapabilityManifest(duplicate), /duplicate capability manifest/);
  const wrongGroup = structuredClone(canonical);
  wrongGroup.group.servers[2] = "things-generic";
  assert.throws(() => validateCapabilityManifest(wrongGroup), /group server set/);
  const contractedCounts = structuredClone(canonical);
  delete contractedCounts.counts.supaOutcomes;
  assert.throws(() => validateCapabilityManifest(contractedCounts), /expanded counts/);
  const driftedWorkflowCount = structuredClone(canonical);
  driftedWorkflowCount.counts.workflows -= 1;
  assert.throws(() => validateCapabilityManifest(driftedWorkflowCount), /expanded counts/);
});

test("locked package attestations are exact, module-derived, and tamper-evident", async () => {
  await withFixture(async ({ evidenceRoot }) => {
    const inventory = JSON.parse(await readFile(path.join(evidenceRoot, "provenance/materialized-output-inventory.json"), "utf8"));
    const closure = inventory.lockedDependencyClosure;
    assert.equal(validateLockedDependencyClosure(closure), closure);
    assert.equal(closure.packages[0].moduleCount, 1);
    assert.equal(closure.packages[0].lockIntegrity, TARBALL_SRI);

    const countTamper = structuredClone(closure);
    countTamper.packages[0].moduleCount = 2;
    assert.throws(() => validateLockedDependencyClosure(countTamper), /sum to the exact module count/);

    const rowTamper = structuredClone(closure);
    rowTamper.packages[0].packageIndexRowSha256 = "f".repeat(64);
    assert.throws(() => validateLockedDependencyClosure(rowTamper), /package_index receipt differs/);
  });
});

test("sealed package-root assets preserve metadata, market data, and hashed frontend files", async () => {
  const temporary = await realpath(await mkdtemp(path.join(os.tmpdir(), "mcphub-package-assets-")));
  try {
    await mkdir(path.join(temporary, "frontend/dist/assets"), { recursive: true, mode: 0o700 });
    await writeFile(path.join(temporary, "package.json"), '{"name":"@samanhappy/mcphub","version":"1.0.32"}\n', { mode: 0o600 });
    await writeFile(path.join(temporary, "servers.json"), '{"github":{"name":"GitHub"}}\n', { mode: 0o600 });
    await writeFile(path.join(temporary, "frontend/dist/index.html"), '<script src="/assets/app-deadbeef.js"></script>\n', { mode: 0o600 });
    await writeFile(path.join(temporary, "frontend/dist/assets/app-deadbeef.js"), "export {};\n", { mode: 0o600 });
    const assets = await collectUpstreamPackageAssets(temporary);
    assert.deepEqual(assets.map((record) => record.outputPath), [
      "dist/package/frontend/dist/assets/app-deadbeef.js",
      "dist/package/frontend/dist/index.html",
      "dist/package/package.json",
      "dist/package/servers.json",
    ]);
    await writeFile(path.join(temporary, "servers.json"), "{}\n", { mode: 0o600 });
    await assert.rejects(collectUpstreamPackageAssets(temporary), /populated market data/);
  } finally {
    await rm(temporary, { recursive: true, force: true });
  }
});

test("offline seal accepts an absolute owner-controlled pnpm metadata cache", async () => {
  const temporary = await realpath(await mkdtemp(path.join(os.tmpdir(), "mcphub-pnpm-cache-positive-")));
  try {
    const cacheRoot = path.join(temporary, "metadata-cache");
    await mkdir(cacheRoot, { mode: 0o700 });
    assert.equal(await validatePnpmCacheDirectory(cacheRoot), cacheRoot);
  } finally {
    await rm(temporary, { recursive: true, force: true });
  }
});

test("offline seal rejects absent, relative, missing, writable, and symlinked pnpm caches", async () => {
  await assert.rejects(validatePnpmCacheDirectory(undefined), /is required/);
  await assert.rejects(validatePnpmCacheDirectory("relative/cache"), /must be absolute/);
  await assert.rejects(validatePnpmCacheDirectory(path.join(os.tmpdir(), "missing-mcphub-pnpm-cache")), /existing directory/);

  const temporary = await realpath(await mkdtemp(path.join(os.tmpdir(), "mcphub-pnpm-cache-negative-")));
  try {
    const cacheRoot = path.join(temporary, "metadata-cache");
    await mkdir(cacheRoot, { mode: 0o700 });
    await chmod(cacheRoot, 0o722);
    await assert.rejects(validatePnpmCacheDirectory(cacheRoot), /group- or other-writable/);
    await chmod(cacheRoot, 0o700);

    const directLink = path.join(temporary, "direct-link");
    await symlink(cacheRoot, directLink);
    await assert.rejects(validatePnpmCacheDirectory(directLink), /non-symlink directory/);

    const parentRoot = path.join(temporary, "parent");
    const nestedCache = path.join(parentRoot, "cache");
    await mkdir(nestedCache, { recursive: true, mode: 0o700 });
    const parentLink = path.join(temporary, "parent-link");
    await symlink(parentRoot, parentLink);
    await assert.rejects(validatePnpmCacheDirectory(path.join(parentLink, "cache")), /must not resolve through a symlink/);
  } finally {
    await rm(temporary, { recursive: true, force: true });
  }
});

test("seal publication verifies the exact pair and restores both generations on second-swap failure", async () => {
  await withFixture(async (state) => {
    const candidateRoot = path.join(state.temporary, "candidate-success");
    const downstreamRoot = path.join(state.temporary, "downstream-success");
    await mkdir(downstreamRoot, { mode: 0o700 });
    await copyFixtureSealCandidate(state, candidateRoot);
    const result = await publishSealCandidate({
      candidateRoot,
      downstreamRoot,
      withPublicationLock: async (operation) => operation(),
    });
    assert.deepEqual(result, { published: true, receiptCount: 5 });
    assert.equal((await readFile(path.join(downstreamRoot, "dist/runtime/main.mjs"), "utf8")).includes("export async function main"), true);
  });

  await withFixture(async (state) => {
    const candidateRoot = path.join(state.temporary, "candidate-rollback");
    const downstreamRoot = path.join(state.temporary, "downstream-rollback");
    await mkdir(path.join(downstreamRoot, "dist"), { recursive: true, mode: 0o700 });
    await mkdir(path.join(downstreamRoot, "provenance"), { recursive: true, mode: 0o700 });
    await writeFile(path.join(downstreamRoot, "dist/old.txt"), "old-dist\n", { mode: 0o600 });
    await writeFile(path.join(downstreamRoot, "provenance/old.txt"), "old-provenance\n", { mode: 0o600 });
    await copyFixtureSealCandidate(state, candidateRoot);
    await assert.rejects(publishSealCandidate({
      candidateRoot,
      downstreamRoot,
      withPublicationLock: async (operation) => operation(),
      testOnlyAfterFirstSwap: async () => { throw new Error("injected second swap failure"); },
    }), /injected second swap failure/);
    assert.equal(await readFile(path.join(downstreamRoot, "dist/old.txt"), "utf8"), "old-dist\n");
    assert.equal(await readFile(path.join(downstreamRoot, "provenance/old.txt"), "utf8"), "old-provenance\n");
  });

  await withFixture(async (state) => {
    const candidateRoot = path.join(state.temporary, "candidate-stray");
    const downstreamRoot = path.join(state.temporary, "downstream-stray");
    await mkdir(downstreamRoot, { mode: 0o700 });
    await copyFixtureSealCandidate(state, candidateRoot);
    await writeFile(path.join(candidateRoot, "dist/stray.txt"), "stray\n", { mode: 0o600 });
    await assert.rejects(publishSealCandidate({
      candidateRoot,
      downstreamRoot,
      withPublicationLock: async (operation) => operation(),
    }), /unlisted files/);
  });
});

test("content ID changes when exact patch, source, or output derivation inventory changes", async () => {
  await withFixture(async ({ manifest }) => {
    const originalDerivation = manifest.sourceClosure.derivationSha256;
    const originalDistribution = manifest.distribution.digest;
    manifest.sourceClosure.patchManifestSha256 = "f".repeat(64);
    assert.notEqual(computeDerivationDigest(manifest), originalDerivation);
    manifest.sourceClosure.derivationSha256 = computeDerivationDigest(manifest);
    assert.notEqual(computeDistributionDigest(manifest), originalDistribution);
  });
});

test("enforces output-inventory and distribution-digest receipts", async () => {
  await withFixture(async ({ options, evidenceRoot }) => {
    const inventoryPath = path.join(evidenceRoot, "provenance/materialized-output-inventory.json");
    await writeFile(inventoryPath, "{}\n", { mode: 0o600 });
    await assert.rejects(materializeFixture(options), /evidence file hash mismatch/);
  });
  await withFixture(async ({ options, evidenceRoot }) => {
    const receiptPath = path.join(evidenceRoot, "provenance/distribution-digest.json");
    const receipt = JSON.parse(await readFile(receiptPath, "utf8"));
    receipt.auditManifestSha256 = "f".repeat(64);
    await writeFile(receiptPath, `${canonicalJson(receipt)}\n`, { mode: 0o600 });
    await assert.rejects(materializeFixture(options), /does not bind the exact audit manifest bytes/);
  });
});

test("rejects every production loader transformation", async () => {
  await withFixture(async ({ options, manifest, manifestPath, evidenceRoot }) => {
    manifest.sourceClosure.productionLoaderTransformations.push("legacy-esm-hook");
    manifest.sourceClosure.derivationSha256 = computeDerivationDigest(manifest);
    manifest.distribution.digest = computeDistributionDigest(manifest);
    await rewriteManifestAndDigestReceipt({ manifest, manifestPath, evidenceRoot });
    await assert.rejects(materializeFixture(options), /production loader transformations are forbidden/);
  });
});

test("pinned rolldown emits one deterministic self-contained ESM chunk", async () => {
  const workspace = await syntheticBundleWorkspace(
    'export async function main() { const loaded = await import("./helper.ts"); return loaded.value; }\n',
    { "src/runtime/helper.ts": "export const value = 42;\n" },
  );
  try {
    const first = await bundleRuntime({ ...workspace, inventoryRoot: workspace.temporary });
    const firstBytes = await readFile(workspace.outputPath);
    assert.deepEqual(await readdir(path.dirname(workspace.outputPath)), ["main.mjs"]);
    assert.equal(first.bundler.version, "1.2.6");
    assert.equal(first.bundler.emittedChunks, 1);
    assert.equal(first.bundler.emittedAssets, 0);
    assert.equal(first.imports.every((specifier) => specifier.startsWith("node:")), true);
    assert.deepEqual(first.modules.map((record) => record.path), ["src/runtime/helper.ts", "src/runtime/main.ts"]);
    await rm(path.dirname(workspace.outputPath), { recursive: true, force: true });
    const second = await bundleRuntime({ ...workspace, inventoryRoot: workspace.temporary });
    assert.deepEqual(await readFile(workspace.outputPath), firstBytes);
    assert.equal(second.entrySha256, first.entrySha256);
    assert.deepEqual(second.modules, first.modules);
  } finally {
    await rm(workspace.temporary, { recursive: true, force: true });
  }
  await assertMcpHubSsrfCorrection();
  await assertMcpHubTransportIsolation();
});

test("rolldown graph inspection accepts TypeScript type-only imports", async () => {
  const workspace = await syntheticBundleWorkspace(
    [
      'import type { RuntimeContext } from "./types.ts";',
      'import { value } from "./helper.ts";',
      "export async function main(context: RuntimeContext) { return { context, value }; }",
      "",
    ].join("\n"),
    {
      "src/runtime/helper.ts": "export const value = 42;\n",
      "src/runtime/types.ts": "export interface RuntimeContext { readonly argv: readonly string[]; }\n",
    },
  );
  try {
    const inventory = await bundleRuntime({ ...workspace, inventoryRoot: workspace.temporary });
    assert.deepEqual(inventory.modules.map((record) => record.path), ["src/runtime/helper.ts", "src/runtime/main.ts"]);
    assert.equal(inventory.imports.every((specifier) => specifier.startsWith("node:")), true);
    assert.equal((await readFile(workspace.outputPath, "utf8")).includes("import type"), false);
  } finally {
    await rm(workspace.temporary, { recursive: true, force: true });
  }
});

async function assertMcpHubSsrfCorrection() {
  const source = await readFile(path.join(LOCKED_MCPHUB_ROOT, "dist/utils/ssrf.js"), "utf8");
  assert.equal(sha256Bytes(Buffer.from(source, "utf8")), MCPHUB_SSRF_SHA256);
  const transformed = transformLockedMcpHubSourceForUnitTest({
    code: source,
    relativePath: MCPHUB_SSRF_RELATIVE_PATH,
  });
  assert.deepEqual(transformed.transformations, ["mcphub-ssrf-rfc6598-cgnat-range-v1"]);
  assert.deepEqual(
    transformed.transformEvents.map(({ name, kind, target, count }) => ({ name, kind, target, count })),
    [{
      name: "mcphub-ssrf-rfc6598-cgnat-range-v1",
      kind: "replacement",
      target: MCPHUB_SSRF_RELATIVE_PATH,
      count: 1,
    }],
  );
  assert.equal(transformed.code.split("[0x64000000, 0x657fffff]").length - 1, 0);
  assert.equal(transformed.code.split("[0x64400000, 0x647fffff]").length - 1, 1);

  const workspace = await syntheticBundleWorkspace(
    [
      'import { assertSafeUrl, isBlockedIp } from "./ssrf.ts";',
      "export async function main() {",
      "  const ranges = [",
      '    "99.255.255.255",',
      '    "100.23.203.190",',
      '    "100.63.255.255",',
      '    "100.64.0.0",',
      '    "100.127.255.255",',
      '    "100.128.0.0",',
      '    "101.0.0.0",',
      "  ].map((ip) => ({ ip, blocked: isBlockedIp(ip) }));",
      "  await assertSafeUrl('https://mcp.deepwiki.com/mcp', { lookup: async () => ['100.23.203.190'] });",
      "  let cgnatLookupRejected = false;",
      "  try {",
      "    await assertSafeUrl('https://cgnat.invalid/mcp', { lookup: async () => ['100.64.0.0'] });",
      "  } catch (error) {",
      "    cgnatLookupRejected = error?.name === 'UnsafeUrlError';",
      "  }",
      "  return { ranges, publicLookupAllowed: true, cgnatLookupRejected };",
      "}",
      "",
    ].join("\n"),
    { "src/runtime/ssrf.ts": transformed.code },
  );
  try {
    await bundleRuntime({ ...workspace, inventoryRoot: workspace.temporary });
    const loaded = await importSelfContainedModule(await readFile(workspace.outputPath));
    assert.deepEqual(await loaded.main(), {
      ranges: [
        { ip: "99.255.255.255", blocked: false },
        { ip: "100.23.203.190", blocked: false },
        { ip: "100.63.255.255", blocked: false },
        { ip: "100.64.0.0", blocked: true },
        { ip: "100.127.255.255", blocked: true },
        { ip: "100.128.0.0", blocked: false },
        { ip: "101.0.0.0", blocked: false },
      ],
      publicLookupAllowed: true,
      cgnatLookupRejected: true,
    });
  } finally {
    await rm(workspace.temporary, { recursive: true, force: true });
  }

  assert.throws(
    () => transformLockedMcpHubSourceForUnitTest({
      code: source.replace("[0x64000000, 0x657fffff]", "[0x64400000, 0x647fffff]"),
      relativePath: MCPHUB_SSRF_RELATIVE_PATH,
    }),
    /MCPHub SSRF source drift/,
  );
  assert.throws(
    () => transformLockedMcpHubSourceForUnitTest({
      code: `${source}\n`,
      relativePath: MCPHUB_SSRF_RELATIVE_PATH,
    }),
    /MCPHub SSRF source drift/,
  );
}

async function assertMcpHubTransportIsolation() {
  const source = await readFile(path.join(LOCKED_MCPHUB_ROOT, "dist/services/mcpService.js"), "utf8");
  assert.equal(sha256Bytes(Buffer.from(source, "utf8")), MCPHUB_MCP_SERVICE_SHA256);
  const transformed = transformLockedMcpHubSourceForUnitTest({
    code: source,
    relativePath: MCPHUB_MCP_SERVICE_RELATIVE_PATH,
  });
  assert.deepEqual(transformed.transformations, ["mcphub-transport-construction-isolation-v1"]);
  assert.deepEqual(
    transformed.transformEvents.map(({ name, kind, target, count }) => ({ name, kind, target, count })),
    [{
      name: "mcphub-transport-construction-isolation-v1",
      kind: "replacement",
      target: MCPHUB_MCP_SERVICE_RELATIVE_PATH,
      count: 1,
    }],
  );
  const isolatedStart = transformed.code.indexOf([
    "            else {",
    "                try {",
    "                    transport = await createTransportFromConfig(name, expandedConf);",
  ].join("\n"));
  const isolatedEnd = transformed.code.indexOf("            const serverInfoRef = {};", isolatedStart);
  assert.notEqual(isolatedStart, -1);
  assert.notEqual(isolatedEnd, -1);
  const isolatedBranch = transformed.code.slice(isolatedStart, isolatedEnd).trimEnd();
  assert.equal(isolatedBranch.split("continue;").length - 1, 1);

  const workspace = await syntheticBundleWorkspace([
    "const logger = { error() {} };",
    "const summarizeErrorForLogging = (error) => ({ message: error.message });",
    "const formatErrorForLogging = (error) => error.message;",
    "const createTransportFromConfig = async (name, config) => {",
    "  if (config.unsafe === true) throw new Error('blocked-by-ssrf');",
    "  return { name };",
    "};",
    "export async function main() {",
    "  const allServers = [",
    "    { name: 'unrelated-unsafe', type: 'streamable-http', unsafe: true, enabled: true },",
    "    { name: 'things-core', type: 'stdio', enabled: true },",
    "    { name: 'things-shortcuts', type: 'stdio', enabled: true },",
    "    { name: 'things-native', type: 'stdio', enabled: true },",
    "  ];",
    "  const nextServerInfos = [];",
    "  for (const expandedConf of allServers) {",
    "    const { name } = expandedConf;",
    "    let transport;",
    "    if (expandedConf.type === 'openapi') {",
    "      throw new Error('unused synthetic OpenAPI branch');",
    "    }",
    isolatedBranch,
    "    nextServerInfos.push({ name, status: 'connected', error: null, transport, config: expandedConf });",
    "  }",
    "  return nextServerInfos.map((serverInfo) => ({",
    "    name: serverInfo.name,",
    "    status: serverInfo.status,",
    "    error: serverInfo.error,",
    "    hasTransport: Object.hasOwn(serverInfo, 'transport'),",
    "    configName: serverInfo.config.name,",
    "    toolCount: serverInfo.tools?.length ?? null,",
    "  }));",
    "}",
    "",
  ].join("\n"));
  try {
    await bundleRuntime({ ...workspace, inventoryRoot: workspace.temporary });
    const loaded = await importSelfContainedModule(await readFile(workspace.outputPath));
    assert.deepEqual(await loaded.main(), [
      {
        name: "unrelated-unsafe",
        status: "disconnected",
        error: "Failed to construct transport: blocked-by-ssrf",
        hasTransport: false,
        configName: "unrelated-unsafe",
        toolCount: 0,
      },
      { name: "things-core", status: "connected", error: null, hasTransport: true, configName: "things-core", toolCount: null },
      { name: "things-shortcuts", status: "connected", error: null, hasTransport: true, configName: "things-shortcuts", toolCount: null },
      { name: "things-native", status: "connected", error: null, hasTransport: true, configName: "things-native", toolCount: null },
    ]);
  } finally {
    await rm(workspace.temporary, { recursive: true, force: true });
  }

  assert.throws(
    () => transformLockedMcpHubSourceForUnitTest({
      code: source.replace(
        "transport = await createTransportFromConfig(name, expandedConf);",
        "transport =  await createTransportFromConfig(name, expandedConf);",
      ),
      relativePath: MCPHUB_MCP_SERVICE_RELATIVE_PATH,
    }),
    /MCPHub MCP service source drift/,
  );
  assert.throws(
    () => transformLockedMcpHubSourceForUnitTest({
      code: `${source}\n`,
      relativePath: MCPHUB_MCP_SERVICE_RELATIVE_PATH,
    }),
    /MCPHub MCP service source drift/,
  );
}

test("sealed MCPHub module directory uses the verified materialized runtime path and rejects anchor drift", async () => {
  const entrySource = [
    'import path from "node:path";',
    'import McpHubAppServer from "@samanhappy/mcphub/dist/server.js";',
    "interface SealedMainInput { readonly argv: readonly string[]; readonly distributionRoot: string; }",
    "export async function main(input: SealedMainInput): Promise<void> {",
    "  if (input.argv.length !== 0 || !path.isAbsolute(input.distributionRoot)) throw new Error('invalid input');",
    "  const upstream = new McpHubAppServer();",
    "  globalThis.__MCPHUB_SEALED_MODULE_DIR_TEST__ = upstream.currentModuleDir();",
    "}",
    "",
  ].join("\n");
  const moduleDirSource = [
    "import { fileURLToPath } from 'url';",
    "import path from 'path';",
    "export function getCurrentModuleDir() {",
    "    const currentModuleFile = fileURLToPath(import.meta.url);",
    "    return path.dirname(currentModuleFile);",
    "}",
    "",
  ].join("\n");
  const extras = {
    "node_modules/@samanhappy/mcphub/package.json": JSON.stringify({ name: "@samanhappy/mcphub", version: "1.0.32", type: "module" }),
    "node_modules/@samanhappy/mcphub/dist/server.js": [
      'import { getCurrentModuleDir } from "./utils/moduleDir.js";',
      "export default class AppServer { currentModuleDir() { return getCurrentModuleDir(); } }",
      "",
    ].join("\n"),
    "node_modules/@samanhappy/mcphub/dist/utils/moduleDir.js": moduleDirSource,
  };
  const workspace = await syntheticBundleWorkspace(entrySource, extras);
  try {
    const inventory = await bundleRuntime({ ...workspace, inventoryRoot: workspace.temporary });
    assert.deepEqual(inventory.transformations, [
      "mcphub-module-dir-sealed-runtime-v1",
      "owned-runtime-module-dir-injection-v1",
    ]);
    const bundleBytes = await readFile(workspace.outputPath);
    assert.equal(bundleBytes.includes(Buffer.from("import.meta")), false);
    const loaded = await importSelfContainedModule(bundleBytes);
    const distributionRoot = path.join(workspace.temporary, "sealed-distribution");
    await loaded.main({ argv: [], distributionRoot });
    assert.equal(globalThis.__MCPHUB_SEALED_MODULE_DIR_TEST__, path.join(distributionRoot, "package", "dist", "utils"));
  } finally {
    delete globalThis.__MCPHUB_SEALED_MODULE_DIR_TEST__;
    await rm(workspace.temporary, { recursive: true, force: true });
  }

  const drifted = await syntheticBundleWorkspace(entrySource, {
    ...extras,
    "node_modules/@samanhappy/mcphub/dist/utils/moduleDir.js": moduleDirSource.replace("currentModuleFile", "currentFile"),
  });
  try {
    await assert.rejects(
      bundleRuntime({ ...drifted, inventoryRoot: drifted.temporary }),
      /MCPHub module-directory source .* anchor drift/,
    );
  } finally {
    await rm(drifted.temporary, { recursive: true, force: true });
  }

  {
  const ownedSurface = await readFile(path.join(REPO_ROOT, "mcp/mcphub/downstream/src/materializer/typeorm-mcphub-surface.mjs"), "utf8");
  const ownedDriverFactory = await readFile(path.join(REPO_ROOT, "mcp/mcphub/downstream/src/materializer/typeorm-postgres-driver-factory.mjs"), "utf8");
  const ownedOtelNoop = await readFile(path.join(REPO_ROOT, "mcp/mcphub/downstream/src/materializer/optional-opentelemetry-noop.mjs"), "utf8");
  const entrySource = [
    'import { value } from "../../node_modules/@samanhappy/mcphub/dist/db/connection.js";',
    'import { traced } from "../../node_modules/@better-auth/core/dist/instrumentation/api.mjs";',
    "export async function main() { return [value, traced]; }",
    "",
  ].join("\n");
  const extras = {
    "src/materializer/typeorm-mcphub-surface.mjs": ownedSurface,
    "src/materializer/typeorm-postgres-driver-factory.mjs": ownedDriverFactory,
    "src/materializer/optional-opentelemetry-noop.mjs": ownedOtelNoop,
    "node_modules/@samanhappy/mcphub/package.json": JSON.stringify({ name: "@samanhappy/mcphub", version: "1.0.32", type: "module" }),
    "node_modules/@samanhappy/mcphub/dist/db/connection.js": 'import { DataSource } from "typeorm"; export const value = typeof DataSource;\n',
    "node_modules/@better-auth/core/dist/instrumentation/api.mjs": 'import { trace } from "@opentelemetry/api"; export const traced = typeof trace.getTracer;\n',
    "node_modules/typeorm/package.json": JSON.stringify({ name: "typeorm", version: "0.3.28", type: "module", exports: { ".": "./index.mjs" } }),
    "node_modules/typeorm/index.mjs": "export const sentinel = true;\n",
    "node_modules/typeorm/data-source/DataSource.js": 'import { DriverFactory } from "../driver/DriverFactory.js"; export class DataSource { static DriverFactory = DriverFactory; }\n',
    "node_modules/typeorm/decorator/entity/Entity.js": "export const Entity = () => {};\n",
    "node_modules/typeorm/decorator/columns/Column.js": "export const Column = () => {};\n",
    "node_modules/typeorm/decorator/columns/PrimaryGeneratedColumn.js": "export const PrimaryGeneratedColumn = () => {};\n",
    "node_modules/typeorm/decorator/columns/CreateDateColumn.js": "export const CreateDateColumn = () => {};\n",
    "node_modules/typeorm/decorator/columns/UpdateDateColumn.js": "export const UpdateDateColumn = () => {};\n",
    "node_modules/typeorm/decorator/columns/PrimaryColumn.js": "export const PrimaryColumn = () => {};\n",
    "node_modules/typeorm/decorator/Index.js": "export const Index = () => {};\n",
    "node_modules/typeorm/decorator/listeners/EventSubscriber.js": "export const EventSubscriber = () => {};\n",
    "node_modules/typeorm/find-options/operator/MoreThan.js": "export const MoreThan = (value) => value;\n",
    "node_modules/typeorm/find-options/operator/Between.js": "export const Between = (left, right) => [left, right];\n",
    "node_modules/typeorm/find-options/operator/Like.js": "export const Like = (value) => value;\n",
    "node_modules/typeorm/error/MissingDriverError.js": "export class MissingDriverError extends Error {}\n",
    "node_modules/typeorm/driver/postgres/PostgresDriver.js": "export class PostgresDriver {}\n",
  };
  const workspace = await syntheticBundleWorkspace(entrySource, extras);
  try {
    const inventory = await bundleRuntime({ ...workspace, inventoryRoot: workspace.temporary });
    assert.equal(inventory.transformations.includes("typeorm-mcphub-import-surface-v1"), true);
    assert.equal(inventory.transformations.includes("typeorm-postgres-driver-factory-v1"), true);
    assert.equal(inventory.transformations.includes("optional-opentelemetry-noop-v1"), true);
    assert.equal(inventory.modules.some((record) => record.path === "src/materializer/typeorm-mcphub-surface.mjs"), true);
    assert.equal(inventory.modules.some((record) => record.path === "src/materializer/typeorm-postgres-driver-factory.mjs"), true);
    assert.equal(inventory.modules.some((record) => record.path === "src/materializer/optional-opentelemetry-noop.mjs"), true);
    assert.equal(
      inventory.transformEvents
        .filter((event) => event.kind === "resolution" && event.target?.startsWith("src/materializer/"))
        .every((event) => !event.target.startsWith("../")),
      true,
    );
  } finally {
    await rm(workspace.temporary, { recursive: true, force: true });
  }

  const unapproved = await syntheticBundleWorkspace(
    'import { trace } from "@opentelemetry/api"; export async function main() { return trace; }\n',
    { "src/materializer/optional-opentelemetry-noop.mjs": ownedOtelNoop },
  );
  try {
    await assert.rejects(
      bundleRuntime({ ...unapproved, inventoryRoot: unapproved.temporary }),
      /optional OpenTelemetry import is forbidden outside the frozen optional-instrumentation set/,
    );
  } finally {
    await rm(unapproved.temporary, { recursive: true, force: true });
  }
  }
});

test("rolldown rejects computed dynamic imports and native modules", async () => {
  const computed = await syntheticBundleWorkspace(
    'export async function main(target) { return import(target); }\n',
    { "src/runtime/late.ts": "export const value = 1;\n" },
  );
  try {
    await assert.rejects(bundleRuntime({ ...computed, inventoryRoot: computed.temporary }), /emitted unresolved dynamic import/);
  } finally {
    await rm(computed.temporary, { recursive: true, force: true });
  }
  const native = await syntheticBundleWorkspace(
    'import native from "./addon.node"; export async function main() { return native; }\n',
    { "src/runtime/addon.node": "not-a-native-binary\n" },
  );
  try {
    await assert.rejects(bundleRuntime({ ...native, inventoryRoot: native.temporary }), /native module/);
  } finally {
    await rm(native.temporary, { recursive: true, force: true });
  }
  for (const source of [
    'export function main(){ const p=globalThis.process; const key=["getBuiltin","Module"].join(""); return p[key]("node:path").sep; }\n',
    'export function main(){ const { process: p }=globalThis; const key="getBuiltin"+"Module"; return p[key]("node:path").sep; }\n',
    'export function main(){ const root=globalThis; const p0=root.process; const p1=p0; const key=["getBuiltin","Module"].join(""); return p1[key]("node:path").sep; }\n',
  ]) {
    const aliasedProcess = await syntheticBundleWorkspace(source);
    try {
      await assert.rejects(
        bundleRuntime({ ...aliasedProcess, inventoryRoot: aliasedProcess.temporary }),
        /computed process\/global access|mutable module resolution property getBuiltinModule/,
      );
    } finally {
      await rm(aliasedProcess.temporary, { recursive: true, force: true });
    }
  }
  const importedProcess = await syntheticBundleWorkspace(
    'import proc from "node:process"; export function main(){ const key=["Module","getBuiltin"].reverse().join(""); return proc[key]("node:path").sep; }\n',
  );
  try {
    await assert.rejects(
      bundleRuntime({ ...importedProcess, inventoryRoot: importedProcess.temporary }),
      /node:process|forbidden mutable loader/,
    );
  } finally {
    await rm(importedProcess.temporary, { recursive: true, force: true });
  }
  const aliasedConstructor = await syntheticBundleWorkspace(
    'export function main(){ const f=()=>{}; return f.constructor("return 74")(); }\n',
  );
  try {
    await assert.rejects(
      bundleRuntime({ ...aliasedConstructor, inventoryRoot: aliasedConstructor.temporary }),
      /callable constructor access/,
    );
  } finally {
    await rm(aliasedConstructor.temporary, { recursive: true, force: true });
  }
  const extractedConstructor = await syntheticBundleWorkspace(
    'const hasOwn = Function.call.bind(Object.prototype.hasOwnProperty); const C = hasOwn.constructor; export function main(){ return C("return 75")(); }\n',
  );
  try {
    await assert.rejects(
      bundleRuntime({ ...extractedConstructor, inventoryRoot: extractedConstructor.temporary }),
      /constructor (?:access|extraction)/,
    );
  } finally {
    await rm(extractedConstructor.temporary, { recursive: true, force: true });
  }
  for (const source of [
    'function f(){} const C=f.constructor; export function main(){ return C("return 42")(); }\n',
    'const f=()=>{}; const C=f["constructor"]; export function main(){ return new C("return 43")(); }\n',
    'const {constructor:C}=function f(){}; export function main(){ return C.call(null,"return 44")(); }\n',
    'const C=Reflect.get(Array,"constructor"); export function main(){ return C.bind(null,"return 45")()(); }\n',
    'const {["process"]:p}=globalThis; const k=["Module","getBuiltin"].reverse().join(""); export function main(){ return p[k]("node:path").sep; }\n',
    'const R=Reflect; const p=R.get(globalThis,["pro","cess"].join("")); const k=["Module","getBuiltin"].reverse().join(""); export function main(){ return R.get(p,k)("node:path").sep; }\n',
    'const getProcess=()=>process; const p=getProcess(); const k=["Module","getBuiltin"].reverse().join(""); export function main(){ return p[k]("node:path").sep; }\n',
  ]) {
    const adversarial = await syntheticBundleWorkspace(source);
    try {
      try {
        await bundleRuntime({ ...adversarial, inventoryRoot: adversarial.temporary });
        const loaded = await importSelfContainedModule(await readFile(adversarial.outputPath));
        assert.throws(() => loaded.main(), /Code generation from strings disallowed|runtime capability is forbidden/);
      } catch (error) {
        assert.match(String(error), /constructor|code-generation|computed global destructuring|process\/global|computed process\/global|mutable module resolution|Code generation from strings disallowed|runtime capability is forbidden/);
      }
    } finally {
      await rm(adversarial.temporary, { recursive: true, force: true });
    }
  }
  const runtimeDerived = await syntheticBundleWorkspace(
    'const prototype=Object.getPrototypeOf(()=>{}); const key=Object.getOwnPropertyNames(prototype).find((value)=>typeof value==="string"&&value.endsWith("structor")); const DynamicFunction=prototype[key]; export function main(){ return DynamicFunction("return 42")(); }\n',
  );
  try {
    await bundleRuntime({ ...runtimeDerived, inventoryRoot: runtimeDerived.temporary });
    const loaded = await importSelfContainedModule(await readFile(runtimeDerived.outputPath));
    assert.throws(() => loaded.main(), /Code generation from strings disallowed/);
  } finally {
    await rm(runtimeDerived.temporary, { recursive: true, force: true });
  }
});

test("sealed output permits only statically named Symbol.for global slots", async () => {
  const safe = await syntheticBundleWorkspace(
    'export function main(value) { const hasOwn = Function.call.bind(Object.prototype.hasOwnProperty); return [globalThis[Symbol.for("sealed-static-slot")], hasOwn(value, "x")]; }\n',
  );
  try {
    await bundleRuntime({ ...safe, inventoryRoot: safe.temporary });
  } finally {
    await rm(safe.temporary, { recursive: true, force: true });
  }
  const safeAlias = await syntheticBundleWorkspace(
    'const slot = Symbol.for("sealed-static-slot"); const isInstance = Function.call.bind(Function.prototype[Symbol.hasInstance]); export function main(value) { return [globalThis[slot], isInstance(Object, value)]; }\n',
  );
  try {
    await bundleRuntime({ ...safeAlias, inventoryRoot: safeAlias.temporary });
  } finally {
    await rm(safeAlias.temporary, { recursive: true, force: true });
  }
  const safeConstructorComparison = await syntheticBundleWorkspace(
    'export function main(value) { return Object.getPrototypeOf(value).constructor === Object; }\n',
  );
  try {
    await bundleRuntime({ ...safeConstructorComparison, inventoryRoot: safeConstructorComparison.temporary });
  } finally {
    await rm(safeConstructorComparison.temporary, { recursive: true, force: true });
  }

  const unresolved = await syntheticBundleWorkspace(
    "export function main(symbol) { return globalThis[symbol]; }\n",
  );
  try {
    await assert.rejects(
      bundleRuntime({ ...unresolved, inventoryRoot: unresolved.temporary }),
      /unresolved computed global access/,
    );
  } finally {
    await rm(unresolved.temporary, { recursive: true, force: true });
  }
});

test("rolldown canonicalizes bare built-ins and rejects unresolved imports", async () => {
  const bare = await syntheticBundleWorkspace('import fs from "fs"; export async function main() { return fs; }\n');
  try {
    const inventory = await bundleRuntime({ ...bare, inventoryRoot: bare.temporary });
    assert.deepEqual(inventory.imports, ["node:fs"]);
  } finally {
    await rm(bare.temporary, { recursive: true, force: true });
  }
  const commonJs = await syntheticBundleWorkspace(
    'import legacy from "./legacy.cjs"; export async function main() { const crypto = await import("node:crypto"); return [legacy, crypto.randomUUID]; }\n',
    { "src/runtime/legacy.cjs": 'module.exports = require("node:fs").constants;\n' },
  );
  try {
    const inventory = await bundleRuntime({ ...commonJs, inventoryRoot: commonJs.temporary });
    assert.equal(inventory.imports.includes("node:crypto"), true);
    assert.equal(inventory.imports.includes("node:fs"), true);
    assert.equal(inventory.imports.every((specifier) => specifier.startsWith("node:")), true);
    assert.equal(inventory.transformations.includes("emitted-node-builtins-static-import-v1"), true);
    const output = await readFile(commonJs.outputPath, "utf8");
    assert.doesNotMatch(output, /\brequire\s*\(|\bimport\s*\(/u);
  } finally {
    await rm(commonJs.temporary, { recursive: true, force: true });
  }
  const commonJsProcess = await syntheticBundleWorkspace(
    'import readPlatform from "./platform.cjs"; export function main(process) { return readPlatform(process); }\n',
    { "src/runtime/platform.cjs": 'module.exports = function readPlatform(process) { return require("process").platform; };\n' },
  );
  try {
    const inventory = await bundleRuntime({ ...commonJsProcess, inventoryRoot: commonJsProcess.temporary });
    assert.equal(inventory.imports.includes("node:process"), false);
    const output = await readFile(commonJsProcess.outputPath, "utf8");
    assert.equal(output.includes('from "node:process"'), false);
    const loaded = await importSelfContainedModule(Buffer.from(output));
    assert.equal(loaded.main({ platform: "shadowed" }), globalThis.process.platform);
  } finally {
    await rm(commonJsProcess.temporary, { recursive: true, force: true });
  }
  const unresolved = await syntheticBundleWorkspace('import "./missing.ts"; export async function main() {}\n');
  try {
    await assert.rejects(bundleRuntime({ ...unresolved, inventoryRoot: unresolved.temporary }));
  } finally {
    await rm(unresolved.temporary, { recursive: true, force: true });
  }
});

test("package gates have no pending-success, pass-without-tests, or lifecycle-script escape", async () => {
  const packageJson = JSON.parse(await readFile(path.join(REPO_ROOT, "mcp/mcphub/downstream/package.json"), "utf8"));
  const gateSource = await readFile(path.join(REPO_ROOT, "mcp/mcphub/downstream/src/materializer/gate.mjs"), "utf8");
  const scripts = Object.entries(packageJson.scripts);
  assert.equal(scripts.some(([name]) => /^(pre|post)/.test(name)), false);
  assert.equal(scripts.some(([, command]) => command.includes("passWithNoTests") || command.includes("pending") || command.includes("if [")), false);
  assert.equal(packageJson.scripts["test:protocol"], "node src/materializer/gate.mjs protocol");
  assert.equal(gateSource.includes("minimum-release-age=0") || gateSource.includes("minimum_release_age: \"0\""), false);
  assert.equal(gateSource.includes("--config.cache-dir=<verified-pnpm-cache>"), true);
});
