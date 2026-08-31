import { createPublicKey, verify as verifySignature } from "node:crypto";
import { gunzipSync } from "node:zlib";

import { canonicalJson, sha1Bytes, sha256Bytes, sha512Sri } from "./canonical.mjs";
import { safeRelativePath } from "./manifest.mjs";
import { readSafeRegularFile } from "./safe-file.mjs";

export const AUDITED_UPSTREAM_POLICY = Object.freeze({
  packageName: "@samanhappy/mcphub",
  version: "1.0.32",
  tarballSha256: "4cb58d4cb11c7d036bde169504f0ddbe9849159e40fe764950ad62853d1502bb",
  npmSha1: "ba035b96295c6b782e9e46469e978fecccde7793",
  npmIntegrity: "sha512-k0csMxsrZZOmh1Cef4WF/KGwFBtusJGPhCq5d1xTlhTfxy6qd61sGzU9ImoagquJZnnIaGp5SOWBv3xASNT5Tw==",
  keyId: "SHA256:DhQ8wR5APBvFHLF/+Tc+AYvPOdTpcIDqOhxsBHRwC7U",
  signatureBase64: "MEUCIE4wBPBLywNsc45NXX6HDrkTrSeW+Rn43y6QY67qeauBAiEA5vLlZj/eKCHFyciZzAYlU6fUcmFkEZJyr8/WpUWsuZ8=",
  publicKeySpkiBase64: "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEY6Ya7W++7aUPzvMTrezH6Ycx3c+HOKYCcNGybJZSCJq/fd7Qa8uuAKtdIkUQtQiEKERhAmE5lMMJhP8OkDOa2g==",
  archiveFileCount: 469,
  archiveUnpackedBytes: 9_706_506,
  archiveInventorySha256: "de78c552b9e90a9a46e78bf10974eb0861cd270f4ca05c7bfdbeb73677de04fe",
});

function invariant(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function stringField(buffer, start, length) {
  const field = buffer.subarray(start, start + length);
  const nul = field.indexOf(0);
  return field.subarray(0, nul === -1 ? field.length : nul).toString("utf8");
}

function octalField(buffer, start, length, label) {
  const raw = stringField(buffer, start, length).trim();
  invariant(raw === "" || /^[0-7]+$/.test(raw), `${label} is not a portable octal field`);
  const value = raw === "" ? 0 : Number.parseInt(raw, 8);
  invariant(Number.isSafeInteger(value) && value >= 0, `${label} is outside the safe integer range`);
  return value;
}

function headerIsZero(header) {
  return header.every((byte) => byte === 0);
}

function verifyHeaderChecksum(header) {
  const expected = octalField(header, 148, 8, "tar checksum");
  let actual = 0;
  for (let index = 0; index < header.length; index += 1) {
    actual += index >= 148 && index < 156 ? 0x20 : header[index];
  }
  invariant(actual === expected, "tar header checksum mismatch");
}

export function extractTarInventory(tarBytes, policy) {
  const entries = [];
  const extracted = new Map();
  let offset = 0;
  let sawTerminator = false;
  while (offset + 512 <= tarBytes.byteLength) {
    const header = tarBytes.subarray(offset, offset + 512);
    offset += 512;
    if (headerIsZero(header)) {
      sawTerminator = true;
      invariant(tarBytes.subarray(offset).every((byte) => byte === 0), "tar archive has data after its terminator");
      break;
    }
    verifyHeaderChecksum(header);
    const name = stringField(header, 0, 100);
    const prefix = stringField(header, 345, 155);
    const archivePath = prefix ? `${prefix}/${name}` : name;
    const type = header[156];
    const size = octalField(header, 124, 12, `tar size for ${archivePath}`);
    const mode = octalField(header, 100, 8, `tar mode for ${archivePath}`) & 0o777;
    const paddedSize = Math.ceil(size / 512) * 512;
    invariant(offset + paddedSize <= tarBytes.byteLength, "tar member exceeds archive bounds");
    const payload = tarBytes.subarray(offset, offset + size);
    offset += paddedSize;

    if (type === 0 || type === 0x30) {
      invariant(archivePath.startsWith("package/"), "tar regular file is outside package root");
      const relativePath = safeRelativePath(archivePath.slice("package/".length), "tar member path");
      invariant(!extracted.has(relativePath), "tar archive contains a duplicate regular file");
      const bytes = Buffer.from(payload);
      extracted.set(relativePath, bytes);
      entries.push(Object.freeze({ path: relativePath, size, mode, sha256: sha256Bytes(bytes) }));
    } else if (type === 0x35) {
      invariant(size === 0, "tar directory member must be empty");
      const directoryPath = archivePath.endsWith("/") ? archivePath.slice(0, -1) : archivePath;
      invariant(directoryPath === "package" || directoryPath.startsWith("package/"), "tar directory is outside package root");
      if (directoryPath !== "package") {
        safeRelativePath(directoryPath.slice("package/".length), "tar directory path");
      }
    } else {
      throw new Error("tar archive contains a forbidden non-regular member");
    }
  }
  invariant(sawTerminator, "tar archive is missing its zero terminator");
  entries.sort((left, right) => left.path.localeCompare(right.path));
  const totalBytes = entries.reduce((total, entry) => total + entry.size, 0);
  invariant(entries.length === policy.archiveFileCount, "tar regular-file count mismatch");
  invariant(totalBytes === policy.archiveUnpackedBytes, "tar regular-file byte total mismatch");
  const inventorySha256 = sha256Bytes(Buffer.from(canonicalJson(entries), "utf8"));
  if (policy.archiveInventorySha256 !== null && policy.archiveInventorySha256 !== undefined) {
    invariant(inventorySha256 === policy.archiveInventorySha256, "tar inventory digest mismatch");
  }
  return Object.freeze({ entries: Object.freeze(entries), extracted, fileCount: entries.length, unpackedBytes: totalBytes, inventorySha256 });
}

function verifyProvenance(provenance, policy, bytes) {
  invariant(provenance !== null && typeof provenance === "object" && !Array.isArray(provenance), "upstream provenance must be an object");
  const packageEvidence = provenance.package;
  const signature = provenance.signature;
  invariant(packageEvidence !== null && typeof packageEvidence === "object", "upstream package evidence is missing");
  invariant(signature !== null && typeof signature === "object", "upstream signature evidence is missing");
  invariant(packageEvidence.name === policy.packageName && packageEvidence.version === policy.version, "upstream package identity mismatch");
  invariant(packageEvidence.tarballSha256 === policy.tarballSha256, "upstream provenance SHA256 mismatch");
  invariant(packageEvidence.npmSha1 === policy.npmSha1, "upstream provenance SHA1 mismatch");
  invariant(packageEvidence.npmIntegrity === policy.npmIntegrity, "upstream provenance SRI mismatch");
  invariant(packageEvidence.fileCount === policy.archiveFileCount, "upstream provenance file count mismatch");
  invariant(packageEvidence.unpackedSize === policy.archiveUnpackedBytes, "upstream provenance unpacked size mismatch");
  invariant(sha256Bytes(bytes) === policy.tarballSha256, "upstream tarball SHA256 mismatch");
  invariant(sha1Bytes(bytes) === policy.npmSha1, "upstream tarball SHA1 mismatch");
  invariant(sha512Sri(bytes) === policy.npmIntegrity, "upstream tarball SRI mismatch");

  const signedMessage = `${policy.packageName}@${policy.version}:${policy.npmIntegrity}`;
  invariant(signature.verified === true, "registry signature is not attested as verified");
  invariant(signature.algorithm === "ecdsa-sha2-nistp256", "registry signature algorithm mismatch");
  invariant(signature.signedMessage === signedMessage, "registry signed message mismatch");
  invariant(signature.keyId === policy.keyId, "registry signature key ID mismatch");
  invariant(signature.signatureBase64 === policy.signatureBase64, "registry signature bytes mismatch");
  invariant(signature.publicKeySpkiBase64 === policy.publicKeySpkiBase64, "registry public key mismatch");
  const publicKey = createPublicKey({ key: Buffer.from(policy.publicKeySpkiBase64, "base64"), format: "der", type: "spki" });
  invariant(
    verifySignature("sha256", Buffer.from(signedMessage, "utf8"), publicKey, Buffer.from(policy.signatureBase64, "base64")),
    "registry ECDSA signature verification failed",
  );
}

export function verifyUpstreamTarballBytes(bytes, provenance, policy = AUDITED_UPSTREAM_POLICY) {
  invariant(Buffer.isBuffer(bytes), "upstream tarball input must be bytes");
  verifyProvenance(provenance, policy, bytes);
  let tarBytes;
  try {
    tarBytes = gunzipSync(bytes, { maxOutputLength: Math.max(policy.archiveUnpackedBytes * 2, 16 * 1024 * 1024) });
  } catch (error) {
    throw new Error("upstream tarball gzip extraction failed", { cause: error });
  }
  const archive = extractTarInventory(tarBytes, policy);
  const packageJsonBytes = archive.extracted.get("package.json");
  invariant(packageJsonBytes !== undefined, "upstream archive package.json is missing");
  let packageJson;
  try {
    packageJson = JSON.parse(packageJsonBytes.toString("utf8"));
  } catch (error) {
    throw new Error("upstream archive package.json is invalid", { cause: error });
  }
  invariant(packageJson.name === policy.packageName && packageJson.version === policy.version, "archive package.json identity mismatch");
  return Object.freeze({
    tarballSha256: policy.tarballSha256,
    tarballIntegrity: policy.npmIntegrity,
    signatureKeyId: policy.keyId,
    archiveFileCount: archive.fileCount,
    archiveUnpackedBytes: archive.unpackedBytes,
    archiveInventorySha256: archive.inventorySha256,
  });
}

export async function verifyAuditedUpstreamTarball(tarballPath, provenance) {
  const { bytes } = await readSafeRegularFile(tarballPath, {
    label: "audited upstream tarball",
    expectedSha256: AUDITED_UPSTREAM_POLICY.tarballSha256,
  });
  return verifyUpstreamTarballBytes(bytes, provenance, AUDITED_UPSTREAM_POLICY);
}
