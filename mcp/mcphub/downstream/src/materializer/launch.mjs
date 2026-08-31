import { lstat, readlink, realpath } from "node:fs/promises";
import path from "node:path";

import { validateOwnerDirectory, verifyMaterializedFiles } from "./filesystem.mjs";
import { readAuditManifest } from "./manifest.mjs";
import { assertDistributionDigestNotRevoked } from "./revocations.mjs";
import {
  assertRuntimeCapabilityEnvironment,
  assertSelfContainedModule,
  importSelfContainedModule,
  installRuntimeCapabilityBoundary,
} from "./sealed-module.mjs";

const DIGEST = /^sha256-[0-9a-f]{64}$/;

function invariant(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

export function assertSafeProcessEnvironment({ env = process.env, execArgv = process.execArgv, argv = process.argv } = {}) {
  invariant(!env.NODE_OPTIONS, "NODE_OPTIONS is forbidden for the downstream launcher");
  invariant(!env.NODE_PATH, "NODE_PATH is forbidden for the downstream launcher");
  for (const argument of execArgv) {
    invariant(argument !== "-r" && !/^(--experimental-loader|--loader|--import|--require)(=|$)/.test(argument), `forbidden Node preload argument: ${argument}`);
  }
  const executable = argv[1] ?? "";
  invariant(!executable.includes("/_npx/") && !/(^|\/)npx$/.test(executable), "npx execution is forbidden for the downstream launcher");
}

export async function resolveCurrentDistribution(runtimeRoot) {
  await validateOwnerDirectory(runtimeRoot, "runtime root");
  const pointerPath = path.join(runtimeRoot, "current");
  const pointerStats = await lstat(pointerPath);
  invariant(pointerStats.isSymbolicLink(), "current must be an atomic symbolic-link pointer");
  if (typeof process.getuid === "function") {
    invariant(pointerStats.uid === process.getuid(), "current pointer must be owned by the current user");
  }
  const target = await readlink(pointerPath);
  invariant(DIGEST.test(target), "current pointer must target one digest basename");
  assertDistributionDigestNotRevoked(target);
  const distributionRoot = path.join(runtimeRoot, target);
  invariant(await realpath(distributionRoot) === distributionRoot, "current pointer target must be a direct runtime-root child");
  const manifest = await readAuditManifest(path.join(distributionRoot, "audit-manifest.json"), { requireSealed: true });
  invariant(manifest.distribution.digest === target, "current pointer and audit manifest digest disagree");
  const verification = await verifyMaterializedFiles(distributionRoot, manifest);
  const entryBytes = verification.fileBytes.get(manifest.distribution.entryPoint);
  invariant(entryBytes !== undefined, "verified entrypoint bytes are missing");
  assertSelfContainedModule(entryBytes);
  return { distributionRoot, manifest, entryBytes };
}

export async function checkLaunch({ runtimeRoot }) {
  assertSafeProcessEnvironment();
  const { manifest } = await resolveCurrentDistribution(runtimeRoot);
  return {
    mode: "check",
    digest: manifest.distribution.digest,
    entryPoint: manifest.distribution.entryPoint,
    fileCount: manifest.distribution.files.length,
  };
}

export async function launchDistribution({ runtimeRoot, argv = [] }) {
  assertSafeProcessEnvironment();
  assertRuntimeCapabilityEnvironment();
  const { distributionRoot, manifest, entryBytes } = await resolveCurrentDistribution(runtimeRoot);
  installRuntimeCapabilityBoundary();
  const loaded = await importSelfContainedModule(entryBytes);
  if (manifest.distribution.entryExport !== null) {
    const entry = loaded[manifest.distribution.entryExport];
    invariant(typeof entry === "function", `entry export is not callable: ${manifest.distribution.entryExport}`);
    await entry({ argv: [...argv], distributionRoot, auditManifest: manifest });
  }
  return { digest: manifest.distribution.digest, entryPoint: manifest.distribution.entryPoint };
}
