const DIGEST = /^sha256-[0-9a-f]{64}$/;

export const REVOKED_DISTRIBUTION_DIGESTS = Object.freeze([
  "sha256-7369fbfd45eebe415500d41cbb9de5c55b2d95338932344ed09820d7e72a7262",
  "sha256-bda99d286dd44377d37a7c9500fea8d3f9005c426c59ce92b4a0018bebce0182",
]);

if (
  REVOKED_DISTRIBUTION_DIGESTS.some((digest) => !DIGEST.test(digest))
  || new Set(REVOKED_DISTRIBUTION_DIGESTS).size !== REVOKED_DISTRIBUTION_DIGESTS.length
) {
  throw new Error("revoked distribution digest registry is invalid");
}

const REVOKED_DIGESTS = new Set(REVOKED_DISTRIBUTION_DIGESTS);

export function assertDistributionDigestNotRevoked(digest) {
  if (typeof digest !== "string" || !DIGEST.test(digest)) {
    throw new Error("distribution digest is invalid");
  }
  if (REVOKED_DIGESTS.has(digest)) {
    throw new Error("distribution digest is revoked");
  }
  return digest;
}
