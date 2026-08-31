#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { chmod, lstat, mkdir, mkdtemp, readFile, readdir, realpath, rename, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { withBuildPublicationLock } from "./build-lock.mjs";
import { bundleRuntime } from "./bundle.mjs";
import { canonicalJson, sha256Bytes } from "./canonical.mjs";
import { verifyLockedDependencyClosure } from "./dependency-closure.mjs";
import { readSafeRegularFile } from "./safe-file.mjs";
import { publishSealCandidate, stageSealCandidate } from "./seal.mjs";

const DOWNSTREAM_ROOT = path.resolve(import.meta.dirname, "../..");
const REPO_ROOT = path.resolve(DOWNSTREAM_ROOT, "../../..");
const TSC = path.join(DOWNSTREAM_ROOT, "node_modules/.bin/tsc");
const VITEST = path.join(DOWNSTREAM_ROOT, "node_modules/.bin/vitest");

const EXPECTED = Object.freeze({
  distribution: { files: 4, suites: 0, tests: 51 },
  protocol: { files: 8, suites: 16, tests: 67 },
  oauth: { files: 3, suites: 0, tests: 20 },
});

function invariant(condition, message) {
  if (!condition) throw new Error(message);
}

function run(executable, args, { cwd = DOWNSTREAM_ROOT, env = { ...process.env, NODE_OPTIONS: "", NODE_PATH: "" } } = {}) {
  const result = spawnSync(executable, args, {
    cwd,
    encoding: "utf8",
    env,
    maxBuffer: 64 * 1024 * 1024,
  });
  if (result.error) throw result.error;
  if (result.status !== 0) {
    process.stderr.write(result.stdout);
    process.stderr.write(result.stderr);
    throw new Error(`gate command failed with status ${result.status}`);
  }
  return result.stdout;
}

function isolatedEnvironment(temporaryRoot) {
  const env = {
    CI: "1",
    COREPACK_ENABLE_DOWNLOAD_PROMPT: "0",
    FORCE_COLOR: "0",
    HOME: temporaryRoot,
    LOGNAME: process.env.LOGNAME,
    NO_COLOR: "1",
    NODE_OPTIONS: "",
    NODE_PATH: "",
    PATH: process.env.PATH,
    NPM_CONFIG_GLOBALCONFIG: path.join(temporaryRoot, "global.npmrc"),
    NPM_CONFIG_USERCONFIG: path.join(temporaryRoot, "user.npmrc"),
    TMPDIR: path.join(temporaryRoot, "tmp"),
    USER: process.env.USER,
    npm_config_update_notifier: "false",
    npm_config_verify_store_integrity: "true",
  };
  for (const [key, value] of Object.entries(env)) {
    if (value === undefined) delete env[key];
  }
  return env;
}

export async function validatePnpmCacheDirectory(value) {
  invariant(typeof value === "string" && value.length > 0, "MCPHUB_PNPM_CACHE_DIR is required for the offline seal");
  invariant(path.isAbsolute(value), "MCPHUB_PNPM_CACHE_DIR must be absolute");
  let stats;
  try {
    stats = await lstat(value, { bigint: true });
  } catch (error) {
    throw new Error("MCPHUB_PNPM_CACHE_DIR must be an existing directory", { cause: error });
  }
  invariant(stats.isDirectory() && !stats.isSymbolicLink(), "MCPHUB_PNPM_CACHE_DIR must be a non-symlink directory");
  invariant(typeof process.getuid === "function" && stats.uid === BigInt(process.getuid()), "MCPHUB_PNPM_CACHE_DIR must be owned by the current user");
  const permissions = stats.mode & 0o777n;
  invariant((permissions & 0o022n) === 0n, "MCPHUB_PNPM_CACHE_DIR must not be group- or other-writable");
  const resolved = await realpath(value);
  invariant(resolved === path.resolve(value), "MCPHUB_PNPM_CACHE_DIR must not resolve through a symlink");
  return resolved;
}

async function resolvePinnedPnpm(environment) {
  const candidates = [];
  for (const directory of (process.env.PATH ?? "").split(path.delimiter)) {
    if (directory.length === 0) continue;
    const candidate = path.resolve(directory, "pnpm");
    if (!candidates.includes(candidate)) candidates.push(candidate);
  }
  for (const candidate of candidates) {
    try {
      const resolved = await realpath(candidate);
      const opened = await readSafeRegularFile(resolved, { label: `pnpm executable ${resolved}`, requireSingleLink: false });
      if ((opened.mode & 0o100) === 0) continue;
      const version = run(resolved, ["--version"], { cwd: DOWNSTREAM_ROOT, env: environment }).trim();
      if (version !== "11.22.0") continue;
      return Object.freeze({
        executable: resolved,
        attestation: Object.freeze({
          version,
          executableSha256: sha256Bytes(opened.bytes),
          executableSize: opened.bytes.byteLength,
        }),
      });
    } catch {
      // Continue until an exact, owner-validated pnpm 11.22.0 executable is found.
    }
  }
  throw new Error("no exact owner-validated pnpm 11.22.0 executable is available on PATH");
}

async function filesUnder(root, suffix) {
  const results = [];
  async function visit(current) {
    for (const entry of await readdir(current, { withFileTypes: true })) {
      const candidate = path.join(current, entry.name);
      if (entry.isDirectory()) await visit(candidate);
      else if (entry.isFile() && entry.name.endsWith(suffix)) results.push(candidate);
    }
  }
  await visit(root);
  return results.sort();
}

async function copyRegularTree(sourceRoot, destinationRoot) {
  const stats = await lstat(sourceRoot);
  invariant(stats.isDirectory() && !stats.isSymbolicLink(), `isolated source tree must be a non-symlink directory: ${sourceRoot}`);
  await mkdir(destinationRoot, { recursive: true, mode: 0o700 });
  await chmod(destinationRoot, 0o700);
  const entries = await readdir(sourceRoot, { withFileTypes: true });
  entries.sort((left, right) => left.name < right.name ? -1 : left.name > right.name ? 1 : 0);
  for (const entry of entries) {
    const source = path.join(sourceRoot, entry.name);
    const destination = path.join(destinationRoot, entry.name);
    const entryStats = await lstat(source);
    invariant(!entryStats.isSymbolicLink(), `isolated build source contains a symlink: ${source}`);
    if (entryStats.isDirectory()) await copyRegularTree(source, destination);
    else {
      invariant(entryStats.isFile(), `isolated build source contains a non-regular entry: ${source}`);
      const opened = await readSafeRegularFile(source, { label: `isolated build source ${source}` });
      await writeFile(destination, opened.bytes, { flag: "wx", mode: 0o600 });
      await chmod(destination, 0o600);
    }
  }
}

async function copyRegularFile(source, destination, label) {
  const opened = await readSafeRegularFile(source, { label });
  await writeFile(destination, opened.bytes, { flag: "wx", mode: 0o600 });
  await chmod(destination, 0o600);
  return opened.bytes;
}

async function prepareIsolatedBuildRoot(root) {
  await chmod(root, 0o700);
  await mkdir(path.join(root, "tmp"), { mode: 0o700 });
  await copyRegularTree(path.join(DOWNSTREAM_ROOT, "src"), path.join(root, "src"));
  const packageBytes = await copyRegularFile(path.join(DOWNSTREAM_ROOT, "package.json"), path.join(root, "package.json"), "downstream package.json");
  const lockBytes = await copyRegularFile(path.join(DOWNSTREAM_ROOT, "pnpm-lock.yaml"), path.join(root, "pnpm-lock.yaml"), "downstream frozen lockfile");
  await writeFile(path.join(root, "user.npmrc"), "", { flag: "wx", mode: 0o600 });
  await writeFile(path.join(root, "global.npmrc"), "", { flag: "wx", mode: 0o600 });
  const discoveryEnvironment = { ...process.env, NODE_OPTIONS: "", NODE_PATH: "", npm_config_update_notifier: "false" };
  const pnpm = await resolvePinnedPnpm(discoveryEnvironment);
  const storeRoot = (run(pnpm.executable, ["store", "path"], { cwd: DOWNSTREAM_ROOT, env: discoveryEnvironment })).trim();
  invariant(path.isAbsolute(storeRoot) && path.basename(storeRoot) === "v11", "pnpm store path is not the expected absolute v11 store");
  const cacheRoot = await validatePnpmCacheDirectory(process.env.MCPHUB_PNPM_CACHE_DIR);
  const environment = isolatedEnvironment(root);
  run(pnpm.executable, [
    "install",
    "--frozen-lockfile",
    "--frozen-store",
    "--offline",
    "--ignore-workspace",
    "--ignore-scripts",
    "--package-import-method=copy",
    "--verify-store-integrity",
    `--config.cache-dir=${cacheRoot}`,
    "--store-dir",
    storeRoot,
  ], { cwd: root, env: environment });
  run(pnpm.executable, ["store", "status", "--store-dir", storeRoot], { cwd: root, env: environment });
  const packageLink = path.join(root, "node_modules/@samanhappy/mcphub");
  const linkStats = await lstat(packageLink);
  invariant(linkStats.isSymbolicLink() && linkStats.nlink === 1, "isolated MCPHub package link identity is invalid");
  const upstreamPackageRoot = await realpath(packageLink);
  invariant(upstreamPackageRoot.startsWith(`${path.join(root, "node_modules/.pnpm")}${path.sep}`), "isolated MCPHub package resolves outside the frozen workroot");
  const packageRootStats = await lstat(upstreamPackageRoot);
  invariant(packageRootStats.isDirectory() && !packageRootStats.isSymbolicLink(), "resolved isolated MCPHub package root is invalid");
  const installedPackage = JSON.parse((await readSafeRegularFile(path.join(upstreamPackageRoot, "package.json"), { label: "isolated MCPHub package metadata" })).bytes.toString("utf8"));
  invariant(installedPackage.name === "@samanhappy/mcphub" && installedPackage.version === "1.0.32", "isolated MCPHub package identity is invalid");
  invariant(JSON.parse(packageBytes.toString("utf8")).dependencies["@samanhappy/mcphub"] === "1.0.32", "isolated package source does not pin MCPHub 1.0.32");
  return Object.freeze({ environment, lockBytes, storeRoot, upstreamPackageRoot, pnpm });
}

async function compileTo(outputRoot) {
  const sourceFiles = [
    ...await filesUnder(path.join(DOWNSTREAM_ROOT, "src"), ".ts"),
    ...await filesUnder(path.join(DOWNSTREAM_ROOT, "test"), ".ts"),
  ];
  invariant(sourceFiles.length > 0, "TypeScript source inventory is empty");
  run(TSC, ["-p", "tsconfig.json", "--outDir", outputRoot]);
  for (const source of sourceFiles) {
    const relative = path.relative(DOWNSTREAM_ROOT, source).replace(/\.ts$/, ".js");
    const stats = await lstat(path.join(outputRoot, relative));
    invariant(stats.isFile() && !stats.isSymbolicLink(), `fresh build output missing for ${relative}`);
  }
  const javascript = await filesUnder(outputRoot, ".js");
  invariant(javascript.length === sourceFiles.length, "fresh build contains missing or unexpected JavaScript outputs");
  return { sourceCount: sourceFiles.length, outputCount: javascript.length };
}

function assertTap(output, expected) {
  const value = (label) => {
    const matches = [...output.matchAll(new RegExp(`^# ${label} ([0-9]+)$`, "gm"))];
    invariant(matches.length === 1, `TAP summary is missing exact ${label}`);
    return Number.parseInt(matches[0][1], 10);
  };
  invariant(value("tests") === expected.tests, "TAP test count changed");
  invariant(value("suites") === expected.suites, "TAP suite count changed");
  invariant(value("pass") === expected.tests, "TAP pass count is incomplete");
  invariant(value("fail") === 0, "TAP failures are forbidden");
  invariant(value("cancelled") === 0, "TAP cancellations are forbidden");
  invariant(value("skipped") === 0, "TAP skips are forbidden");
  invariant(value("todo") === 0, "TAP todo cases are forbidden");
}

async function runDistribution() {
  const files = await filesUnder(path.join(DOWNSTREAM_ROOT, "test/distribution"), ".test.mjs");
  invariant(files.length === EXPECTED.distribution.files, "distribution source suite count changed");
  const output = run(process.execPath, ["--disallow-code-generation-from-strings", "--test", "--test-reporter=tap", ...files]);
  assertTap(output, EXPECTED.distribution);
  process.stdout.write(output);
}

async function runProtocol() {
  const files = await filesUnder(path.join(DOWNSTREAM_ROOT, "test/protocol"), ".test.ts");
  invariant(files.length === EXPECTED.protocol.files, "protocol source file count changed");
  const output = run(VITEST, ["run", ...files, "--reporter=json"]);
  const report = JSON.parse(output);
  invariant(report.testResults.length === EXPECTED.protocol.files, "protocol executed file count changed");
  invariant(report.numTotalTestSuites === EXPECTED.protocol.suites, "protocol suite count changed");
  invariant(report.numTotalTests === EXPECTED.protocol.tests, "protocol case count changed");
  invariant(report.numPassedTests === EXPECTED.protocol.tests, "protocol pass count is incomplete");
  invariant(report.numFailedTests === 0 && report.numPendingTests === 0 && report.numTodoTests === 0, "protocol failures, pending, or todo cases are forbidden");
  process.stdout.write(`${JSON.stringify({ lane: "protocol", files: report.testResults.length, suites: report.numTotalTestSuites, tests: report.numTotalTests, passed: report.numPassedTests })}\n`);
}

async function runOauth() {
  const files = await filesUnder(path.join(DOWNSTREAM_ROOT, "test/oauth"), ".test.ts");
  invariant(files.length === EXPECTED.oauth.files, "OAuth source file count changed");
  const outputRoot = await mkdtemp(path.join(os.tmpdir(), "mcphub-oauth-gate-"));
  await chmod(outputRoot, 0o700);
  try {
    await compileTo(outputRoot);
    const compiled = files.map((file) => path.join(outputRoot, path.relative(DOWNSTREAM_ROOT, file).replace(/\.ts$/, ".js")));
    const output = run(process.execPath, ["--test", "--test-reporter=tap", ...compiled]);
    assertTap(output, EXPECTED.oauth);
    process.stdout.write(output);
  } finally {
    await rm(outputRoot, { recursive: true, force: true });
  }
}

async function build() {
  return withBuildPublicationLock(DOWNSTREAM_ROOT, async () => {
    const staging = await mkdtemp(path.join(DOWNSTREAM_ROOT, ".dist-staging-"));
    await chmod(staging, 0o700);
    const destination = path.join(DOWNSTREAM_ROOT, "dist");
    const backup = `${staging}.previous`;
    let previous = false;
    let published = false;
    try {
      const report = await bundleRuntime({
        entryPath: path.join(DOWNSTREAM_ROOT, "src/runtime/main.ts"),
        outputPath: path.join(staging, "runtime/main.mjs"),
        outputRelativePath: "dist/runtime/main.mjs",
        inventoryRoot: DOWNSTREAM_ROOT,
      });
      try {
        await rename(destination, backup);
        previous = true;
      } catch (error) {
        if (error.code !== "ENOENT") throw error;
      }
      await rename(staging, destination);
      published = true;
      if (previous) await rm(backup, { recursive: true, force: true });
      process.stdout.write(`${JSON.stringify({
        lane: "build",
        fresh: true,
        bundler: report.bundler,
        moduleCount: report.modules.length,
        transformations: report.transformations,
        entrySha256: report.entrySha256,
        entrySize: report.entrySize,
      })}\n`);
    } catch (error) {
      if (published) await rm(destination, { recursive: true, force: true });
      if (previous) await rename(backup, destination);
      await rm(staging, { recursive: true, force: true });
      throw error;
    }
  });
}

async function seal() {
  return withBuildPublicationLock(DOWNSTREAM_ROOT, async () => {
    const isolatedRoot = await realpath(await mkdtemp(path.join(os.tmpdir(), "mcphub-seal-workroot-")));
    const candidateRoot = await realpath(await mkdtemp(path.join(DOWNSTREAM_ROOT, ".seal-candidate-")));
    await chmod(isolatedRoot, 0o700);
    await chmod(candidateRoot, 0o700);
    try {
      const isolated = await prepareIsolatedBuildRoot(isolatedRoot);
      const firstOutput = path.join(isolatedRoot, "first/dist/runtime/main.mjs");
      const secondOutput = path.join(isolatedRoot, "second/dist/runtime/main.mjs");
      const buildOptions = {
        entryPath: path.join(isolatedRoot, "src/runtime/main.ts"),
        outputRelativePath: "dist/runtime/main.mjs",
        inventoryRoot: isolatedRoot,
      };
      const first = await bundleRuntime({ ...buildOptions, outputPath: firstOutput });
      const second = await bundleRuntime({ ...buildOptions, outputPath: secondOutput });
      const firstBytes = await readFile(firstOutput);
      const secondBytes = await readFile(secondOutput);
      invariant(firstBytes.equals(secondBytes), "repeated isolated builds are not byte-identical");
      invariant(canonicalJson(first) === canonicalJson(second), "repeated isolated build reports are not byte-identical");
      const dependencyClosure = await verifyLockedDependencyClosure({
        inventoryRoot: isolatedRoot,
        modules: first.modules,
        lockBytes: isolated.lockBytes,
        storeRoot: isolated.storeRoot,
        pnpm: isolated.pnpm.attestation,
      });
      const staged = await stageSealCandidate({
        repoRoot: REPO_ROOT,
        downstreamRoot: DOWNSTREAM_ROOT,
        candidateRoot,
        bundleReport: first,
        bundlePath: firstOutput,
        upstreamPackageRoot: isolated.upstreamPackageRoot,
        dependencyClosure,
        buildCommands: [
          "pnpm install --frozen-lockfile --frozen-store --offline --ignore-workspace --ignore-scripts --package-import-method=copy --verify-store-integrity --config.cache-dir=<verified-pnpm-cache> --store-dir <verified-pnpm-store-v11>",
          "pnpm store status --store-dir <verified-pnpm-store-v11>",
          "node src/materializer/gate.mjs seal",
        ],
      });
      const published = await publishSealCandidate({
        candidateRoot,
        downstreamRoot: DOWNSTREAM_ROOT,
        withPublicationLock: async (operation) => operation(),
      });
      process.stdout.write(`${JSON.stringify({
        lane: "seal",
        fresh: true,
        reproducibleBuilds: 2,
        receiptCount: published.receiptCount,
        moduleCount: first.modules.length,
        lockedDependencyModuleCount: dependencyClosure.moduleCount,
        assetCount: staged.outputInventory.assets.length,
        fileCount: staged.auditManifest.distribution.files.length,
        entrySha256: first.entrySha256,
        sealAttestationSha256: staged.outputInventory.sealAttestationSha256,
        distributionDigest: staged.auditManifest.distribution.digest,
      })}\n`);
    } catch (error) {
      await rm(candidateRoot, { recursive: true, force: true });
      throw error;
    } finally {
      await rm(isolatedRoot, { recursive: true, force: true });
    }
  });
}

if (process.argv[1] !== undefined && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const operation = process.argv[2];
  if (operation === "build") await build();
  else if (operation === "seal") await seal();
  else if (operation === "distribution") await runDistribution();
  else if (operation === "protocol") await runProtocol();
  else if (operation === "oauth") await runOauth();
  else throw new Error("unknown package gate");
}
