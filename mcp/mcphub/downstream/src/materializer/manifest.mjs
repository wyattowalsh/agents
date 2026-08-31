import path from "node:path";

import { canonicalJson, sha256Bytes } from "./canonical.mjs";
import { readSafeRegularFile } from "./safe-file.mjs";

const SHA256 = /^[0-9a-f]{64}$/;
const DIGEST = /^sha256-[0-9a-f]{64}$/;
const ALLOWED_ROLES = new Set(["entrypoint", "runtime", "asset", "dependency"]);
const MODULE_KINDS = new Set(["owned-source", "locked-dependency", "build-input"]);

function invariant(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function object(value, label) {
  invariant(value !== null && typeof value === "object" && !Array.isArray(value), `${label} must be an object`);
  return value;
}

function exactKeys(value, allowed, label) {
  const actual = Object.keys(value).sort();
  const expected = [...allowed].sort();
  invariant(JSON.stringify(actual) === JSON.stringify(expected), `${label} contains missing or unknown fields`);
}

function validateModuleRecords(value, label) {
  invariant(Array.isArray(value) && value.length > 0, `${label} must be a non-empty array`);
  let previous = "";
  for (const [index, rawRecord] of value.entries()) {
    const record = object(rawRecord, `${label}[${index}]`);
    exactKeys(record, ["path", "sha256", "size", "kind"], `${label}[${index}]`);
    const modulePath = safeRelativePath(record.path, `${label}[${index}].path`);
    invariant(modulePath > previous, `${label} must be strictly sorted by path`);
    previous = modulePath;
    invariant(SHA256.test(record.sha256), `invalid module sha256 for ${modulePath}`);
    invariant(Number.isSafeInteger(record.size) && record.size > 0, `invalid module size for ${modulePath}`);
    invariant(MODULE_KINDS.has(record.kind), `invalid module kind for ${modulePath}`);
  }
  return value;
}

function validateAssetRecords(value, label) {
  invariant(Array.isArray(value) && value.length > 0, `${label} must be a non-empty array`);
  let previous = "";
  for (const [index, rawRecord] of value.entries()) {
    const record = object(rawRecord, `${label}[${index}]`);
    exactKeys(record, ["sourcePath", "sourceSha256", "outputPath", "outputSha256", "size", "mode"], `${label}[${index}]`);
    safeRelativePath(record.sourcePath, `${label}[${index}].sourcePath`);
    const outputPath = safeRelativePath(record.outputPath, `${label}[${index}].outputPath`);
    invariant(outputPath > previous, `${label} must be strictly sorted by output path`);
    previous = outputPath;
    invariant(SHA256.test(record.sourceSha256) && SHA256.test(record.outputSha256), `${label}[${index}] hashes are invalid`);
    invariant(record.sourceSha256 === record.outputSha256, `${label}[${index}] is not exact-byte staged`);
    invariant(Number.isSafeInteger(record.size) && record.size > 0, `${label}[${index}] size is invalid`);
    invariant(record.mode === 0o600, `${label}[${index}] mode must be 0600`);
  }
  return value;
}

function validateTransformEvents(value, label) {
  invariant(Array.isArray(value), `${label} must be an array`);
  let previous = "";
  for (const [index, rawEvent] of value.entries()) {
    const event = object(rawEvent, `${label}[${index}]`);
    exactKeys(event, ["name", "kind", "source", "importer", "target", "preimageSha256", "postimageSha256", "count"], `${label}[${index}]`);
    invariant(typeof event.name === "string" && event.name.length > 0, `${label}[${index}].name is invalid`);
    invariant(typeof event.kind === "string" && event.kind.length > 0, `${label}[${index}].kind is invalid`);
    invariant(event.source === null || (typeof event.source === "string" && event.source.length > 0), `${label}[${index}].source is invalid`);
    invariant(event.importer === null || (typeof event.importer === "string" && event.importer.length > 0), `${label}[${index}].importer is invalid`);
    invariant(event.target === null || (typeof event.target === "string" && event.target.length > 0), `${label}[${index}].target is invalid`);
    invariant(SHA256.test(event.preimageSha256) && SHA256.test(event.postimageSha256), `${label}[${index}] hashes are invalid`);
    invariant(event.count === 1, `${label}[${index}].count must be one`);
    const canonical = canonicalJson(event);
    invariant(canonical > previous, `${label} must be strictly code-unit sorted by canonical event JSON`);
    previous = canonical;
  }
  return value;
}

function validateBuildAttestation(value, label) {
  const attestation = object(value, label);
  exactKeys(attestation, ["schemaVersion", "astValidated", "entrySha256", "validatorPolicySha256", "transformEventsSha256", "moduleInventorySha256"], label);
  invariant(attestation.schemaVersion === 1 && attestation.astValidated === true, `${label} is not an authoritative AST attestation`);
  for (const key of ["entrySha256", "validatorPolicySha256", "transformEventsSha256", "moduleInventorySha256"]) {
    invariant(SHA256.test(attestation[key]), `${label}.${key} is invalid`);
  }
  return attestation;
}

export function validateLockedDependencyClosure(value, label = "locked dependency closure", { requireAuditedMcphub = true } = {}) {
  const closure = object(value, label);
  exactKeys(closure, [
    "schemaVersion",
    "status",
    "method",
    "lockfileSha256",
    "lifecycleScriptsExecuted",
    "networkResolution",
    "packageImportMethod",
    "storeFormat",
    "pnpm",
    "storeIndexSha256",
    "packageCount",
    "moduleCount",
    "packages",
    "modules",
    "inventorySha256",
  ], label);
  invariant(closure.schemaVersion === 1 && closure.status === "verified", `${label} is not verified`);
  invariant(closure.method === "fresh-offline-copy-install+pnpm-v11-cafs-sha512", `${label} method is invalid`);
  invariant(SHA256.test(closure.lockfileSha256) && SHA256.test(closure.storeIndexSha256) && SHA256.test(closure.inventorySha256), `${label} digests are invalid`);
  invariant(closure.lifecycleScriptsExecuted === false && closure.networkResolution === false && closure.packageImportMethod === "copy" && closure.storeFormat === "v11", `${label} isolation flags are invalid`);
  const pnpm = object(closure.pnpm, `${label}.pnpm`);
  exactKeys(pnpm, ["version", "executableSha256", "executableSize"], `${label}.pnpm`);
  invariant(pnpm.version === "11.22.0" && SHA256.test(pnpm.executableSha256) && Number.isSafeInteger(pnpm.executableSize) && pnpm.executableSize > 0, `${label}.pnpm identity is invalid`);
  invariant(Array.isArray(closure.packages) && closure.packageCount === closure.packages.length, `${label} package count mismatch`);
  invariant(Array.isArray(closure.modules) && closure.moduleCount === closure.modules.length, `${label} module count mismatch`);
  const packageRecords = new Map();
  let previousPackage = "";
  let packageModuleCount = 0;
  for (const [index, rawRecord] of closure.packages.entries()) {
    const record = object(rawRecord, `${label}.packages[${index}]`);
    exactKeys(record, ["package", "version", "lockIntegrity", "packageIndexKey", "packageIndexRowSha256", "packageIndexRowSize", "moduleCount"], `${label}.packages[${index}]`);
    invariant(typeof record.package === "string" && record.package.length > 0 && typeof record.version === "string" && record.version.length > 0, `${label}.packages[${index}] identity is invalid`);
    const key = `${record.package}@${record.version}`;
    invariant(key > previousPackage, `${label} packages must be strictly code-unit sorted and unique`);
    previousPackage = key;
    invariant(/^sha512-[A-Za-z0-9+/=]+$/.test(record.lockIntegrity), `${label}.packages[${index}] lock integrity is invalid`);
    invariant(record.packageIndexKey === `${record.lockIntegrity}\t${key}`, `${label}.packages[${index}] package_index key mismatch`);
    invariant(SHA256.test(record.packageIndexRowSha256) && Number.isSafeInteger(record.packageIndexRowSize) && record.packageIndexRowSize > 0, `${label}.packages[${index}] package_index receipt is invalid`);
    invariant(Number.isSafeInteger(record.moduleCount) && record.moduleCount > 0, `${label}.packages[${index}] module count is invalid`);
    packageModuleCount += record.moduleCount;
    packageRecords.set(key, record);
  }
  invariant(packageModuleCount === closure.moduleCount, `${label} package rows do not sum to the exact module count`);
  let previousModule = "";
  const derivedPackageCounts = new Map();
  for (const [index, rawRecord] of closure.modules.entries()) {
    const record = object(rawRecord, `${label}.modules[${index}]`);
    exactKeys(record, ["modulePath", "package", "version", "packageRelativePath", "lockKey", "lockIntegrity", "sha256", "size", "installedMode", "cafsSha512", "cafsPath", "packageIndexKey", "packageIndexRowSha256", "packageIndexRowSize"], `${label}.modules[${index}]`);
    safeRelativePath(record.modulePath, `${label}.modules[${index}].modulePath`);
    safeRelativePath(record.packageRelativePath, `${label}.modules[${index}].packageRelativePath`);
    invariant(record.modulePath > previousModule, `${label} modules must be strictly sorted`);
    previousModule = record.modulePath;
    invariant(typeof record.package === "string" && record.package.length > 0 && typeof record.version === "string" && record.version.length > 0, `${label}.modules[${index}] package identity is invalid`);
    invariant(record.lockKey === `${record.package}@${record.version}`, `${label}.modules[${index}] lock key mismatch`);
    invariant(/^sha512-[A-Za-z0-9+/=]+$/.test(record.lockIntegrity), `${label}.modules[${index}] lock integrity is invalid`);
    invariant(SHA256.test(record.sha256) && /^[0-9a-f]{128}$/.test(record.cafsSha512), `${label}.modules[${index}] content digests are invalid`);
    invariant(record.cafsPath === `files/${record.cafsSha512.slice(0, 2)}/${record.cafsSha512.slice(2)}`, `${label}.modules[${index}] CAFS path mismatch`);
    invariant(Number.isSafeInteger(record.size) && record.size > 0, `${label}.modules[${index}] size is invalid`);
    invariant(Number.isSafeInteger(record.installedMode) && record.installedMode >= 0 && record.installedMode <= 0o777, `${label}.modules[${index}] installed mode is invalid`);
    const packageRecord = packageRecords.get(record.lockKey);
    invariant(packageRecord !== undefined, `${label}.modules[${index}] has no package attestation row`);
    invariant(record.lockIntegrity === packageRecord.lockIntegrity, `${label}.modules[${index}] lock integrity differs from its package row`);
    invariant(record.packageIndexKey === packageRecord.packageIndexKey && record.packageIndexRowSha256 === packageRecord.packageIndexRowSha256 && record.packageIndexRowSize === packageRecord.packageIndexRowSize, `${label}.modules[${index}] package_index receipt differs from its package row`);
    derivedPackageCounts.set(record.lockKey, (derivedPackageCounts.get(record.lockKey) ?? 0) + 1);
  }
  for (const [key, record] of packageRecords) invariant(derivedPackageCounts.get(key) === record.moduleCount, `${label} package row is not derived from its exact modules: ${key}`);
  if (requireAuditedMcphub) {
    const mcphub = packageRecords.get("@samanhappy/mcphub@1.0.32");
    invariant(mcphub?.lockIntegrity === "sha512-k0csMxsrZZOmh1Cef4WF/KGwFBtusJGPhCq5d1xTlhTfxy6qd61sGzU9ImoagquJZnnIaGp5SOWBv3xASNT5Tw==", `${label} does not bind the audited MCPHub 1.0.32 SRI`);
  }
  const payload = structuredClone(closure);
  delete payload.inventorySha256;
  invariant(closure.inventorySha256 === sha256Bytes(Buffer.from(canonicalJson(payload), "utf8")), `${label} inventory digest mismatch`);
  return closure;
}

function validateSealAttestation(value, label) {
  const attestation = object(value, label);
  exactKeys(attestation, ["schemaVersion", "buildAttestationSha256", "lockedDependencyClosureSha256", "assetInventorySha256", "distributionFileInventorySha256"], label);
  invariant(attestation.schemaVersion === 1, `${label} schemaVersion is invalid`);
  for (const key of ["buildAttestationSha256", "lockedDependencyClosureSha256", "assetInventorySha256", "distributionFileInventorySha256"]) {
    invariant(SHA256.test(attestation[key]), `${label}.${key} is invalid`);
  }
  return attestation;
}

export function safeRelativePath(value, label = "path") {
  invariant(typeof value === "string" && value.length > 0, `${label} must be a non-empty string`);
  invariant(!value.includes("\\") && !value.includes("\0"), `${label} contains a forbidden character`);
  invariant(!path.posix.isAbsolute(value), `${label} must be relative`);
  invariant(path.posix.normalize(value) === value, `${label} must be normalized`);
  invariant(!value.split("/").some((part) => part === "" || part === "." || part === ".."), `${label} contains an unsafe segment`);
  return value;
}

export function manifestDigestPayload(manifest) {
  const payload = structuredClone(manifest);
  object(payload.distribution, "distribution");
  delete payload.distribution.digest;
  return payload;
}

export function computeDistributionDigest(manifest) {
  return `sha256-${sha256Bytes(Buffer.from(canonicalJson(manifestDigestPayload(manifest)), "utf8"))}`;
}

export function computeDerivationDigest(manifest) {
  const payload = {
    upstream: {
      tarballSha256: manifest.provenance.upstreamTarballSha256,
      tarballIntegrity: manifest.provenance.upstreamTarballIntegrity,
      signatureKeyId: manifest.provenance.upstreamSignatureKeyId,
      archiveFileCount: manifest.provenance.upstreamArchiveFileCount,
      archiveUnpackedBytes: manifest.provenance.upstreamArchiveUnpackedBytes,
      archiveInventorySha256: manifest.provenance.upstreamArchiveInventorySha256,
    },
    ownedSourcesManifestSha256: manifest.sourceClosure.ownedSourcesManifestSha256,
    patchManifestSha256: manifest.sourceClosure.patchManifestSha256,
    productionLoaderTransformations: manifest.sourceClosure.productionLoaderTransformations,
    outputInventorySha256: manifest.build.outputInventorySha256,
    outputs: manifest.distribution.files,
  };
  return sha256Bytes(Buffer.from(canonicalJson(payload), "utf8"));
}

export function validateAuditManifest(value, { requireSealed = true } = {}) {
  const manifest = object(value, "audit manifest");
  exactKeys(manifest, ["schemaVersion", "status", "provenance", "dependencies", "sourceClosure", "build", "constraints", "distribution"], "audit manifest");
  invariant(manifest.schemaVersion === 1, "unsupported audit manifest schemaVersion");
  invariant(manifest.status === "candidate" || manifest.status === "sealed", "audit manifest status is invalid");
  if (requireSealed) {
    invariant(manifest.status === "sealed", "production materialization requires a sealed audit manifest");
  }

  const provenance = object(manifest.provenance, "provenance");
  exactKeys(provenance, [
    "upstreamManifestSha256",
    "upstreamTarballSha256",
    "upstreamTarballIntegrity",
    "upstreamSignatureKeyId",
    "upstreamArchiveFileCount",
    "upstreamArchiveUnpackedBytes",
    "upstreamArchiveInventorySha256",
    "dependencyGraphSha256",
    "packageJsonSha256",
    "lockfileSha256",
  ], "provenance");
  for (const key of [
    "upstreamManifestSha256",
    "dependencyGraphSha256",
    "packageJsonSha256",
    "lockfileSha256",
  ]) {
    invariant(SHA256.test(provenance[key]), `provenance.${key} is missing or invalid`);
  }
  invariant(
    provenance.upstreamTarballSha256 === "4cb58d4cb11c7d036bde169504f0ddbe9849159e40fe764950ad62853d1502bb",
    "upstream tarball digest is not the audited 1.0.32 archive",
  );
  invariant(
    provenance.upstreamTarballIntegrity === "sha512-k0csMxsrZZOmh1Cef4WF/KGwFBtusJGPhCq5d1xTlhTfxy6qd61sGzU9ImoagquJZnnIaGp5SOWBv3xASNT5Tw==",
    "upstream tarball SRI is not the audited 1.0.32 archive",
  );
  invariant(
    provenance.upstreamSignatureKeyId === "SHA256:DhQ8wR5APBvFHLF/+Tc+AYvPOdTpcIDqOhxsBHRwC7U",
    "upstream registry signature key is not pinned",
  );
  invariant(provenance.upstreamArchiveFileCount === 469, "upstream archive regular-file count mismatch");
  invariant(provenance.upstreamArchiveUnpackedBytes === 9_706_506, "upstream archive byte total mismatch");
  invariant(
    provenance.upstreamArchiveInventorySha256 === "de78c552b9e90a9a46e78bf10974eb0861cd270f4ca05c7bfdbeb73677de04fe",
    "upstream archive inventory digest mismatch",
  );

  const dependencies = object(manifest.dependencies, "dependencies");
  exactKeys(dependencies, ["publicEdge", "privateBackendClient", "schemaValidator", "v1V2BleedRejected"], "dependencies");
  const publicEdge = object(dependencies.publicEdge, "dependencies.publicEdge");
  const privateBackendClient = object(dependencies.privateBackendClient, "dependencies.privateBackendClient");
  const schemaValidator = object(dependencies.schemaValidator, "dependencies.schemaValidator");
  exactKeys(publicEdge, ["server", "core", "node"], "dependencies.publicEdge");
  exactKeys(privateBackendClient, ["sdk"], "dependencies.privateBackendClient");
  exactKeys(schemaValidator, ["package", "version", "integrity", "tarballSha256", "signatureKeyId"], "dependencies.schemaValidator");
  invariant(publicEdge.server === "2.0.0" && publicEdge.core === "2.0.0" && publicEdge.node === null, "public edge dependency versions are invalid");
  invariant(privateBackendClient.sdk === "1.29.0", "private backend SDK version is invalid");
  invariant(schemaValidator.package === "@cfworker/json-schema" && schemaValidator.version === "4.1.1", "schema validator dependency is invalid");
  invariant(schemaValidator.integrity === "sha512-gAmrUZSGtKc3AiBL71iNWxDsyUC5uMaKKGdvzYsBoTW/xi42JQHl7eKV2OYzCUqvc+D2RCcf7EXY2iCyFIk6og==", "schema validator SRI is invalid");
  invariant(schemaValidator.tarballSha256 === "f3a8076b450505f0671fa78a6efb5e7726883e2c6dfb13b29261872803610203", "schema validator tarball SHA256 is invalid");
  invariant(schemaValidator.signatureKeyId === "SHA256:DhQ8wR5APBvFHLF/+Tc+AYvPOdTpcIDqOhxsBHRwC7U", "schema validator signature key is invalid");
  invariant(dependencies.v1V2BleedRejected === true, "v1/v2 dependency isolation is not attested");

  const build = object(manifest.build, "build");
  exactKeys(build, ["commands", "nodeVersion", "packageManager", "outputInventoryComplete", "outputInventorySha256", "sealAttestationSha256"], "build");
  invariant(Array.isArray(build.commands) && build.commands.length > 0 && build.commands.every((command) => typeof command === "string" && command.length > 0), "build.commands must be non-empty strings");
  invariant(build.commands.some((command) => /\bpnpm install\b/.test(command) && command.includes("--frozen-lockfile") && command.includes("--offline") && command.includes("--ignore-workspace") && command.includes("--ignore-scripts")), "build.commands must include an offline frozen pnpm install with lifecycle scripts disabled");
  invariant(build.commands.every((command) => !/\bnpx\b|\bnpm\s+(?:i|install)\b|https?:\/\//.test(command)), "build.commands contains a forbidden resolver or network command");
  invariant(/^v[0-9]+\.[0-9]+\.[0-9]+$/.test(build.nodeVersion), "build.nodeVersion is invalid");
  invariant(build.packageManager === "pnpm@11.22.0", "build package manager is not frozen");
  invariant(typeof build.outputInventoryComplete === "boolean", "build.outputInventoryComplete must be boolean");
  invariant(build.outputInventorySha256 === null || SHA256.test(build.outputInventorySha256), "build.outputInventorySha256 is invalid");
  invariant(build.sealAttestationSha256 === null || SHA256.test(build.sealAttestationSha256), "build.sealAttestationSha256 is invalid");
  if (requireSealed) {
    invariant(build.outputInventoryComplete === true, "sealed materialization requires a complete output inventory");
    invariant(SHA256.test(build.outputInventorySha256), "sealed materialization requires a digest-bound output inventory");
    invariant(SHA256.test(build.sealAttestationSha256), "sealed materialization requires a digest-bound seal attestation");
  }

  const sourceClosure = object(manifest.sourceClosure, "sourceClosure");
  exactKeys(sourceClosure, ["exhaustive", "ownedSourcesManifestSha256", "patchManifestSha256", "derivationSha256", "productionLoaderTransformations"], "sourceClosure");
  invariant(typeof sourceClosure.exhaustive === "boolean", "sourceClosure.exhaustive must be boolean");
  invariant(Array.isArray(sourceClosure.productionLoaderTransformations), "sourceClosure.productionLoaderTransformations must be an array");
  invariant(sourceClosure.productionLoaderTransformations.length === 0, "production loader transformations are forbidden");
  if (requireSealed) {
    invariant(sourceClosure.exhaustive === true, "production materialization requires exhaustive source closure");
    invariant(SHA256.test(sourceClosure.ownedSourcesManifestSha256), "owned-sources manifest digest is missing or invalid");
    invariant(SHA256.test(sourceClosure.patchManifestSha256), "patch manifest digest is missing or invalid");
    invariant(SHA256.test(sourceClosure.derivationSha256), "source derivation digest is missing or invalid");
    invariant(sourceClosure.derivationSha256 === computeDerivationDigest(manifest), "source derivation digest does not bind the exact upstream, patch, source, and output inventories");
  }
  const constraints = object(manifest.constraints, "constraints");
  exactKeys(constraints, [
    "offlineBuild",
    "frozenLockfile",
    "sameProcessLaunch",
    "rejectUnlistedFiles",
    "ownerOnlyRuntime",
    "npx",
    "liveRegistryResolution",
    "versionRanges",
    "mutablePackageCache",
    "nodeOptions",
    "esmLoaderHooks",
    "networkAtMaterialization",
    "networkDependencyResolution",
    "entryBundleSelfContained",
    "barePackageImports",
    "dynamicImports",
    "ancestorNodeModulesResolution",
  ], "constraints");
  for (const key of [
    "offlineBuild",
    "frozenLockfile",
    "sameProcessLaunch",
    "rejectUnlistedFiles",
    "ownerOnlyRuntime",
    "entryBundleSelfContained",
  ]) {
    invariant(constraints[key] === true, `constraint ${key} must be true`);
  }
  for (const key of [
    "npx",
    "liveRegistryResolution",
    "versionRanges",
    "mutablePackageCache",
    "nodeOptions",
    "esmLoaderHooks",
    "networkAtMaterialization",
    "networkDependencyResolution",
    "barePackageImports",
    "dynamicImports",
    "ancestorNodeModulesResolution",
  ]) {
    invariant(constraints[key] === false, `constraint ${key} must be false`);
  }

  const distribution = object(manifest.distribution, "distribution");
  exactKeys(distribution, ["digest", "entryPoint", "entryExport", "files"], "distribution");
  invariant(DIGEST.test(distribution.digest), "distribution.digest must be a sha256-prefixed digest");
  invariant(distribution.digest === computeDistributionDigest(manifest), "distribution digest does not match canonical manifest content");
  const entryPoint = safeRelativePath(distribution.entryPoint, "distribution.entryPoint");
  invariant(distribution.entryExport === null || (typeof distribution.entryExport === "string" && /^[A-Za-z_$][A-Za-z0-9_$]*$/.test(distribution.entryExport)), "distribution.entryExport must be null or a JavaScript identifier");
  invariant(Array.isArray(distribution.files) && distribution.files.length > 0, "distribution.files must be non-empty");

  const paths = new Set();
  const sourcePaths = new Set();
  let previousPath = "";
  let entryCount = 0;
  for (const [index, rawRecord] of distribution.files.entries()) {
    const record = object(rawRecord, `distribution.files[${index}]`);
    exactKeys(record, ["sourcePath", "path", "sha256", "size", "mode", "role"], `distribution.files[${index}]`);
    const outputPath = safeRelativePath(record.path, `distribution.files[${index}].path`);
    const sourcePath = safeRelativePath(record.sourcePath, `distribution.files[${index}].sourcePath`);
    invariant(outputPath > previousPath, "distribution.files must be strictly sorted by output path");
    previousPath = outputPath;
    invariant(!paths.has(outputPath), `duplicate distribution path: ${outputPath}`);
    invariant(outputPath !== "audit-manifest.json", "audit-manifest.json is a reserved materializer control file");
    invariant(!sourcePaths.has(sourcePath), `duplicate distribution sourcePath: ${sourcePath}`);
    paths.add(outputPath);
    sourcePaths.add(sourcePath);
    invariant(SHA256.test(record.sha256), `invalid sha256 for ${outputPath}`);
    invariant(Number.isSafeInteger(record.size) && record.size >= 0, `invalid size for ${outputPath}`);
    invariant(record.mode === 0o600 || record.mode === 0o700, `mode for ${outputPath} must be 0600 or 0700`);
    invariant(ALLOWED_ROLES.has(record.role), `invalid role for ${outputPath}`);
    if (record.role === "entrypoint") {
      entryCount += 1;
      invariant(outputPath === entryPoint, "entrypoint role must match distribution.entryPoint");
    }
  }
  invariant(entryCount === 1, "distribution must contain exactly one entrypoint role");
  invariant(paths.has(entryPoint), "distribution entrypoint is absent from file inventory");
  return manifest;
}

export function validateOwnedSourcesManifest(value) {
  const manifest = object(value, "owned-sources manifest");
  exactKeys(manifest, [
    "schemaVersion",
    "status",
    "exhaustive",
    "entry",
    "modules",
    "moduleCount",
    "moduleInventorySha256",
    "lockedDependencyClosureSha256",
    "assets",
  ], "owned-sources manifest");
  invariant(manifest.schemaVersion === 1 && manifest.status === "sealed", "owned-sources manifest must be schemaVersion 1 and sealed");
  invariant(manifest.exhaustive === true, "owned-sources manifest must be exhaustive");
  invariant(manifest.entry === "src/runtime/main.ts", "owned-sources manifest entry is invalid");
  validateModuleRecords(manifest.modules, "owned-sources manifest modules");
  invariant(manifest.moduleCount === manifest.modules.length, "owned-sources manifest module count mismatch");
  invariant(
    manifest.moduleInventorySha256 === sha256Bytes(Buffer.from(canonicalJson(manifest.modules), "utf8")),
    "owned-sources manifest module inventory digest mismatch",
  );
  invariant(SHA256.test(manifest.lockedDependencyClosureSha256), "owned-sources manifest locked dependency closure digest is invalid");
  invariant(manifest.modules.some((record) => record.path === manifest.entry && record.kind === "owned-source"), "owned-sources manifest entry is absent from the exact module closure");
  validateAssetRecords(manifest.assets, "owned-sources manifest assets");
  return manifest;
}

export function validatePatchManifest(value) {
  const manifest = object(value, "patch manifest");
  exactKeys(manifest, [
    "schemaVersion",
    "status",
    "bundler",
    "productionLoaderTransformations",
    "validatorPolicySha256",
    "events",
    "eventCount",
    "eventsSha256",
    "buildAttestation",
    "buildAttestationSha256",
  ], "patch manifest");
  invariant(manifest.schemaVersion === 1 && manifest.status === "sealed", "patch manifest must be schemaVersion 1 and sealed");
  const bundler = object(manifest.bundler, "patch manifest bundler");
  exactKeys(bundler, ["name", "version"], "patch manifest bundler");
  invariant(bundler.name === "rolldown" && bundler.version === "1.2.6", "patch manifest bundler is not pinned rolldown 1.2.6");
  invariant(Array.isArray(manifest.productionLoaderTransformations) && manifest.productionLoaderTransformations.length === 0, "patch manifest production loader transformations are forbidden");
  invariant(SHA256.test(manifest.validatorPolicySha256), "patch manifest validator policy digest is invalid");
  validateTransformEvents(manifest.events, "patch manifest events");
  invariant(manifest.eventCount === manifest.events.length, "patch manifest event count mismatch");
  invariant(manifest.eventsSha256 === sha256Bytes(Buffer.from(canonicalJson(manifest.events), "utf8")), "patch manifest event digest mismatch");
  const attestation = validateBuildAttestation(manifest.buildAttestation, "patch manifest build attestation");
  invariant(attestation.validatorPolicySha256 === manifest.validatorPolicySha256, "patch manifest policy and attestation digests differ");
  invariant(attestation.transformEventsSha256 === manifest.eventsSha256, "patch manifest events and attestation digests differ");
  invariant(manifest.buildAttestationSha256 === sha256Bytes(Buffer.from(canonicalJson(attestation), "utf8")), "patch manifest build attestation digest mismatch");
  return manifest;
}

export function validateMaterializedOutputInventory(value, manifest) {
  const inventory = object(value, "materialized output inventory");
  exactKeys(inventory, [
    "schemaVersion",
    "status",
    "bundler",
    "modules",
    "transformations",
    "transformEvents",
    "transformEventsSha256",
    "validatorPolicySha256",
    "buildAttestation",
    "buildAttestationSha256",
    "lockedDependencyClosure",
    "sealAttestation",
    "sealAttestationSha256",
    "assets",
    "files",
  ], "materialized output inventory");
  invariant(inventory.schemaVersion === 1, "unsupported materialized output inventory schemaVersion");
  invariant(inventory.status === "sealed", "materialized output inventory must be sealed");

  const bundler = object(inventory.bundler, "materialized output inventory bundler");
  exactKeys(bundler, [
    "name",
    "version",
    "entry",
    "output",
    "format",
    "platform",
    "codeSplitting",
    "sourcemap",
    "minify",
    "comments",
    "polyfillRequire",
    "emittedChunks",
    "emittedAssets",
  ], "materialized output inventory bundler");
  invariant(bundler.name === "rolldown" && bundler.version === "1.2.6", "output inventory bundler is not pinned rolldown 1.2.6");
  invariant(bundler.entry === "src/runtime/main.ts", "output inventory entry is not src/runtime/main.ts");
  invariant(bundler.output === "dist/runtime/main.mjs", "output inventory bundle path is not dist/runtime/main.mjs");
  invariant(bundler.format === "esm" && bundler.platform === "node", "output inventory bundle target is invalid");
  invariant(bundler.codeSplitting === false && bundler.sourcemap === false, "output inventory permits split chunks or source maps");
  invariant(
    bundler.minify === "dce-only" && bundler.comments === false && bundler.polyfillRequire === false,
    "output inventory bundle normalization is not sealed",
  );
  invariant(bundler.emittedChunks === 1 && bundler.emittedAssets === 0, "output inventory is not a one-chunk bundle");

  validateModuleRecords(inventory.modules, "materialized output inventory modules");
  invariant(Array.isArray(inventory.transformations) && inventory.transformations.every((name) => typeof name === "string" && name.length > 0), "output inventory transformations are invalid");
  invariant(JSON.stringify([...inventory.transformations].sort()) === JSON.stringify(inventory.transformations), "output inventory transformations must be sorted");
  validateTransformEvents(inventory.transformEvents, "materialized output inventory transformEvents");
  invariant(inventory.transformEventsSha256 === sha256Bytes(Buffer.from(canonicalJson(inventory.transformEvents), "utf8")), "output inventory transform-event digest mismatch");
  invariant(SHA256.test(inventory.validatorPolicySha256), "output inventory validator policy digest is invalid");
  const attestation = validateBuildAttestation(inventory.buildAttestation, "materialized output inventory build attestation");
  invariant(attestation.entrySha256 === manifest.distribution.files.find((record) => record.role === "entrypoint")?.sha256, "output inventory attestation does not bind the entry bytes");
  invariant(attestation.validatorPolicySha256 === inventory.validatorPolicySha256, "output inventory attestation does not bind the validator policy");
  invariant(attestation.transformEventsSha256 === inventory.transformEventsSha256, "output inventory attestation does not bind the transform events");
  invariant(attestation.moduleInventorySha256 === sha256Bytes(Buffer.from(canonicalJson(inventory.modules), "utf8")), "output inventory attestation does not bind the module inventory");
  invariant(inventory.buildAttestationSha256 === sha256Bytes(Buffer.from(canonicalJson(attestation), "utf8")), "output inventory build attestation digest mismatch");
  const lockedDependencyClosure = validateLockedDependencyClosure(inventory.lockedDependencyClosure, "materialized output inventory locked dependency closure");
  const lockedModules = inventory.modules.filter((record) => record.kind === "locked-dependency");
  invariant(lockedDependencyClosure.modules.length === lockedModules.length, "output inventory locked dependency closure is incomplete");
  for (let index = 0; index < lockedModules.length; index += 1) {
    invariant(
      lockedDependencyClosure.modules[index].modulePath === lockedModules[index].path
      && lockedDependencyClosure.modules[index].sha256 === lockedModules[index].sha256
      && lockedDependencyClosure.modules[index].size === lockedModules[index].size,
      `output inventory locked dependency closure differs for ${lockedModules[index].path}`,
    );
  }
  validateAssetRecords(inventory.assets, "materialized output inventory assets");

  invariant(Array.isArray(inventory.files), "output inventory files must be an array");
  invariant(canonicalJson(inventory.files) === canonicalJson(manifest.distribution.files), "output inventory files differ from the sealed distribution");
  const sealAttestation = validateSealAttestation(inventory.sealAttestation, "materialized output inventory seal attestation");
  invariant(sealAttestation.buildAttestationSha256 === inventory.buildAttestationSha256, "seal attestation does not bind the build attestation");
  invariant(sealAttestation.lockedDependencyClosureSha256 === lockedDependencyClosure.inventorySha256, "seal attestation does not bind the locked dependency closure");
  invariant(sealAttestation.assetInventorySha256 === sha256Bytes(Buffer.from(canonicalJson(inventory.assets), "utf8")), "seal attestation does not bind the asset inventory");
  invariant(sealAttestation.distributionFileInventorySha256 === sha256Bytes(Buffer.from(canonicalJson(inventory.files), "utf8")), "seal attestation does not bind the distribution file inventory");
  invariant(inventory.sealAttestationSha256 === sha256Bytes(Buffer.from(canonicalJson(sealAttestation), "utf8")), "output inventory seal attestation digest mismatch");
  invariant(manifest.build.sealAttestationSha256 === inventory.sealAttestationSha256, "audit manifest does not bind the seal attestation");
  invariant(manifest.distribution.entryPoint === "runtime/main.mjs", "sealed entrypoint must be runtime/main.mjs");
  invariant(manifest.distribution.entryExport === "main", "sealed entry export must be main");
  const entryRecord = manifest.distribution.files.find((record) => record.role === "entrypoint");
  invariant(entryRecord?.sourcePath === "dist/runtime/main.mjs", "sealed entry source must be dist/runtime/main.mjs");
  return inventory;
}

export function validateDistributionDigestReceipt(value, manifest, auditManifestSha256) {
  const receipt = object(value, "distribution digest receipt");
  exactKeys(receipt, [
    "schemaVersion",
    "status",
    "auditManifestSha256",
    "outputInventorySha256",
    "distributionDigest",
    "entryPoint",
    "entryExport",
    "fileCount",
  ], "distribution digest receipt");
  invariant(receipt.schemaVersion === 1, "unsupported distribution digest receipt schemaVersion");
  invariant(receipt.status === "sealed", "distribution digest receipt must be sealed");
  invariant(receipt.auditManifestSha256 === auditManifestSha256, "distribution digest receipt does not bind the exact audit manifest bytes");
  invariant(receipt.outputInventorySha256 === manifest.build.outputInventorySha256, "distribution digest receipt does not bind the output inventory");
  invariant(receipt.distributionDigest === manifest.distribution.digest, "distribution digest receipt differs from the audit manifest");
  invariant(receipt.entryPoint === manifest.distribution.entryPoint, "distribution digest receipt entrypoint mismatch");
  invariant(receipt.entryExport === manifest.distribution.entryExport, "distribution digest receipt export mismatch");
  invariant(receipt.fileCount === manifest.distribution.files.length, "distribution digest receipt file count mismatch");
  return receipt;
}

function parseJsonBytes(bytes, label) {
  try {
    return JSON.parse(bytes.toString("utf8"));
  } catch (error) {
    throw new Error(`${label} is not valid JSON`, { cause: error });
  }
}

export function parseMaterializedOutputInventory(bytes, manifest) {
  return validateMaterializedOutputInventory(parseJsonBytes(bytes, "materialized output inventory"), manifest);
}

export function parseOwnedSourcesManifest(bytes) {
  return validateOwnedSourcesManifest(parseJsonBytes(bytes, "owned-sources manifest"));
}

export function parsePatchManifest(bytes) {
  return validatePatchManifest(parseJsonBytes(bytes, "patch manifest"));
}

export function parseDistributionDigestReceipt(bytes, manifest, auditManifestSha256) {
  return validateDistributionDigestReceipt(parseJsonBytes(bytes, "distribution digest receipt"), manifest, auditManifestSha256);
}

export async function readAuditManifestEvidence(manifestPath, options) {
  const { bytes } = await readSafeRegularFile(path.resolve(manifestPath), { label: "audit manifest" });
  const payload = parseJsonBytes(bytes, "audit manifest");
  return Object.freeze({
    bytes,
    sha256: sha256Bytes(bytes),
    manifest: validateAuditManifest(payload, options),
  });
}

export async function readAuditManifest(manifestPath, options) {
  return (await readAuditManifestEvidence(manifestPath, options)).manifest;
}
