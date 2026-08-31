import { randomBytes } from "node:crypto";
import { chmod, lstat, mkdir, rename, rm, writeFile } from "node:fs/promises";
import path from "node:path";

import { canonicalJson } from "./canonical.mjs";
import { fileExists, validateEvidenceFile, validateOwnerDirectory, validateSourceFile, verifyMaterializedFiles } from "./filesystem.mjs";
import {
  parseDistributionDigestReceipt,
  parseMaterializedOutputInventory,
  parseOwnedSourcesManifest,
  parsePatchManifest,
  readAuditManifest,
  readAuditManifestEvidence,
} from "./manifest.mjs";
import { assertSelfContainedModule } from "./sealed-module.mjs";
import { verifyAuditedUpstreamTarball } from "./tarball.mjs";

function invariant(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

async function ensureOwnerParents(root, relativePath) {
  const parts = relativePath.split("/").slice(0, -1);
  let current = root;
  for (const part of parts) {
    current = path.join(current, part);
    await mkdir(current, { mode: 0o700, recursive: true });
    await chmod(current, 0o700);
  }
}

async function verifySourceInventory(sourceRoot, manifest, outputInventory) {
  const stats = await lstat(sourceRoot);
  invariant(stats.isDirectory() && !stats.isSymbolicLink(), "source root must be a non-symlink directory");
  const resolved = new Map();
  for (const record of manifest.distribution.files) {
    const opened = await validateSourceFile(sourceRoot, record);
    if (record.role === "entrypoint") {
      const sealed = assertSelfContainedModule(opened.bytes);
      invariant(sealed.sha256 === outputInventory.buildAttestation.entrySha256, "entry bytes differ from the authoritative build AST attestation");
      invariant(sealed.policySha256 === outputInventory.validatorPolicySha256, "launch policy differs from the authoritative build AST attestation");
    }
    resolved.set(record.path, opened.bytes);
  }
  return resolved;
}

async function verifyEvidenceInventory(evidenceRoot, manifest, auditManifestSha256) {
  const records = [
    ["provenance/upstream.json", manifest.provenance.upstreamManifestSha256],
    ["provenance/dependency-graph.json", manifest.provenance.dependencyGraphSha256],
    ["package.json", manifest.provenance.packageJsonSha256],
    ["pnpm-lock.yaml", manifest.provenance.lockfileSha256],
    ["provenance/owned-sources.json", manifest.sourceClosure.ownedSourcesManifestSha256],
    ["provenance/patch-manifest.json", manifest.sourceClosure.patchManifestSha256],
    ["provenance/materialized-output-inventory.json", manifest.build.outputInventorySha256],
    ["provenance/distribution-digest.json", null],
  ];
  const artifacts = new Map();
  for (const [relativePath, digest] of records) {
    const opened = await validateEvidenceFile(evidenceRoot, relativePath, digest);
    artifacts.set(relativePath, opened.bytes);
  }
  const ownedSources = parseOwnedSourcesManifest(artifacts.get("provenance/owned-sources.json"));
  const patchManifest = parsePatchManifest(artifacts.get("provenance/patch-manifest.json"));
  const outputInventory = parseMaterializedOutputInventory(artifacts.get("provenance/materialized-output-inventory.json"), manifest);
  invariant(canonicalJson(ownedSources.modules) === canonicalJson(outputInventory.modules), "owned-sources and output module inventories differ");
  invariant(canonicalJson(ownedSources.assets) === canonicalJson(outputInventory.assets), "owned-sources and output asset inventories differ");
  invariant(canonicalJson(patchManifest.events) === canonicalJson(outputInventory.transformEvents), "patch and output transform-event inventories differ");
  invariant(patchManifest.validatorPolicySha256 === outputInventory.validatorPolicySha256, "patch and output validator policy digests differ");
  invariant(patchManifest.buildAttestationSha256 === outputInventory.buildAttestationSha256, "patch and output build attestations differ");
  parseDistributionDigestReceipt(
    artifacts.get("provenance/distribution-digest.json"),
    manifest,
    auditManifestSha256,
  );
  return { count: records.length, artifacts, ownedSources, patchManifest, outputInventory };
}

function parseUpstreamProvenance(bytes) {
  try {
    return JSON.parse(bytes.toString("utf8"));
  } catch (error) {
    throw new Error("upstream provenance evidence is not valid JSON", { cause: error });
  }
}

function assertUpstreamBinding(manifest, verification) {
  invariant(verification.tarballSha256 === manifest.provenance.upstreamTarballSha256, "tarball verification does not match manifest SHA256");
  invariant(verification.tarballIntegrity === manifest.provenance.upstreamTarballIntegrity, "tarball verification does not match manifest SRI");
  invariant(verification.signatureKeyId === manifest.provenance.upstreamSignatureKeyId, "tarball verification does not match manifest signing key");
  invariant(verification.archiveFileCount === manifest.provenance.upstreamArchiveFileCount, "tarball verification does not match manifest file count");
  invariant(verification.archiveUnpackedBytes === manifest.provenance.upstreamArchiveUnpackedBytes, "tarball verification does not match manifest byte total");
  invariant(verification.archiveInventorySha256 === manifest.provenance.upstreamArchiveInventorySha256, "tarball verification does not match manifest archive inventory");
}

async function verifyUpstream({ upstreamTarballPath }, manifest, evidence, testOnlyUpstreamVerification) {
  if (testOnlyUpstreamVerification !== undefined) {
    invariant(process.env.NODE_TEST_CONTEXT !== undefined, "test-only upstream verification is forbidden outside node:test");
    assertUpstreamBinding(manifest, testOnlyUpstreamVerification);
    return testOnlyUpstreamVerification;
  }
  invariant(typeof upstreamTarballPath === "string" && path.isAbsolute(upstreamTarballPath), "an absolute audited upstream tarball path is required");
  const provenance = parseUpstreamProvenance(evidence.artifacts.get("provenance/upstream.json"));
  const verification = await verifyAuditedUpstreamTarball(upstreamTarballPath, provenance);
  assertUpstreamBinding(manifest, verification);
  return verification;
}

async function verifyInputs(options, testOnlyUpstreamVerification) {
  const audit = await readAuditManifestEvidence(options.manifestPath, { requireSealed: true });
  const manifest = audit.manifest;
  await validateOwnerDirectory(options.runtimeRoot, "runtime root");
  const evidence = await verifyEvidenceInventory(options.evidenceRoot, manifest, audit.sha256);
  const upstream = await verifyUpstream(options, manifest, evidence, testOnlyUpstreamVerification);
  const sources = await verifySourceInventory(options.sourceRoot, manifest, evidence.outputInventory);
  return { manifest, evidenceCount: evidence.count, upstream, sources };
}

async function checkMaterializationWithVerification(options, testOnlyUpstreamVerification) {
  const { manifest, evidenceCount, upstream } = await verifyInputs(options, testOnlyUpstreamVerification);
  const distributionRoot = path.join(options.runtimeRoot, manifest.distribution.digest);
  const exists = await fileExists(distributionRoot);
  if (exists) {
    const storedManifest = await readAuditManifest(path.join(distributionRoot, "audit-manifest.json"), { requireSealed: true });
    invariant(storedManifest.distribution.digest === manifest.distribution.digest, "stored manifest digest differs from requested manifest");
    await verifyMaterializedFiles(distributionRoot, storedManifest);
  }
  return {
    mode: "check",
    digest: manifest.distribution.digest,
    evidenceCount,
    fileCount: manifest.distribution.files.length,
    upstreamArchiveInventorySha256: upstream.archiveInventorySha256,
    publishRequired: !exists,
  };
}

async function materializeDistributionWithVerification(options, testOnlyUpstreamVerification) {
  const { manifest, evidenceCount, upstream, sources } = await verifyInputs(options, testOnlyUpstreamVerification);
  const distributionRoot = path.join(options.runtimeRoot, manifest.distribution.digest);
  if (await fileExists(distributionRoot)) {
    const storedManifest = await readAuditManifest(path.join(distributionRoot, "audit-manifest.json"), { requireSealed: true });
    invariant(storedManifest.distribution.digest === manifest.distribution.digest, "existing distribution manifest digest mismatch");
    await verifyMaterializedFiles(distributionRoot, storedManifest);
    return {
      digest: manifest.distribution.digest,
      evidenceCount,
      fileCount: manifest.distribution.files.length,
      upstreamArchiveInventorySha256: upstream.archiveInventorySha256,
      published: false,
    };
  }

  const stagingName = `.${manifest.distribution.digest}.staging-${process.pid}-${randomBytes(6).toString("hex")}`;
  const stagingRoot = path.join(options.runtimeRoot, stagingName);
  await mkdir(stagingRoot, { mode: 0o700 });
  await chmod(stagingRoot, 0o700);
  try {
    for (const record of manifest.distribution.files) {
      await ensureOwnerParents(stagingRoot, record.path);
      const destination = path.join(stagingRoot, ...record.path.split("/"));
      await writeFile(destination, sources.get(record.path), { flag: "wx", mode: record.mode });
      await chmod(destination, record.mode);
    }
    await writeFile(path.join(stagingRoot, "audit-manifest.json"), `${canonicalJson(manifest)}\n`, { mode: 0o600, flag: "wx" });
    await chmod(path.join(stagingRoot, "audit-manifest.json"), 0o600);
    await verifyMaterializedFiles(stagingRoot, manifest);
    await rename(stagingRoot, distributionRoot);
  } catch (error) {
    await rm(stagingRoot, { recursive: true, force: true });
    throw error;
  }
  await verifyMaterializedFiles(distributionRoot, manifest);
  return {
    digest: manifest.distribution.digest,
    evidenceCount,
    fileCount: manifest.distribution.files.length,
    upstreamArchiveInventorySha256: upstream.archiveInventorySha256,
    published: true,
  };
}

export async function checkMaterialization(options) {
  return checkMaterializationWithVerification(options, undefined);
}

export async function materializeDistribution(options) {
  return materializeDistributionWithVerification(options, undefined);
}

// Hermetic unit tests exercise publication independently from the immutable
// official npm artifact, which is never committed. Production exports above
// have no override and always require descriptor-read audited tarball bytes.
export async function checkMaterializationForUnitTest(options, verifiedUpstream) {
  invariant(process.env.NODE_TEST_CONTEXT !== undefined, "unit-test materializer is unavailable outside node:test");
  return checkMaterializationWithVerification(options, verifiedUpstream);
}

export async function materializeDistributionForUnitTest(options, verifiedUpstream) {
  invariant(process.env.NODE_TEST_CONTEXT !== undefined, "unit-test materializer is unavailable outside node:test");
  return materializeDistributionWithVerification(options, verifiedUpstream);
}
