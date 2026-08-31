#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { chmod, mkdtemp, readdir, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";

const DOWNSTREAM_ROOT = path.resolve(import.meta.dirname, "../..");
const TSC = path.join(DOWNSTREAM_ROOT, "node_modules/.bin/tsc");
const EXPECTED = Object.freeze({ files: 5, suites: 0, tests: 46 });

function invariant(condition, message) {
  if (!condition) throw new Error(message);
}

function run(executable, args) {
  const result = spawnSync(executable, args, {
    cwd: DOWNSTREAM_ROOT,
    encoding: "utf8",
    env: { ...process.env, NODE_OPTIONS: "", NODE_PATH: "" },
    maxBuffer: 64 * 1024 * 1024,
  });
  if (result.error) throw result.error;
  if (result.status !== 0) {
    process.stderr.write(result.stdout);
    process.stderr.write(result.stderr);
    throw new Error(`ingress gate command failed with status ${result.status}`);
  }
  return result.stdout;
}

function assertTap(output) {
  const value = (label) => {
    const matches = [...output.matchAll(new RegExp(`^# ${label} ([0-9]+)$`, "gm"))];
    invariant(matches.length === 1, `TAP summary is missing exact ${label}`);
    return Number.parseInt(matches[0][1], 10);
  };
  invariant(value("tests") === EXPECTED.tests, "ingress TAP test count changed");
  invariant(value("suites") === EXPECTED.suites, "ingress TAP suite count changed");
  invariant(value("pass") === EXPECTED.tests, "ingress TAP pass count is incomplete");
  invariant(value("fail") === 0, "ingress TAP failures are forbidden");
  invariant(value("cancelled") === 0, "ingress TAP cancellations are forbidden");
  invariant(value("skipped") === 0, "ingress TAP skips are forbidden");
  invariant(value("todo") === 0, "ingress TAP todo cases are forbidden");
}

const names = (await readdir(path.join(DOWNSTREAM_ROOT, "test/ingress")))
  .filter((name) => name.endsWith(".test.ts"))
  .sort();
invariant(names.length === EXPECTED.files, "ingress source file count changed");

const outputRoot = await mkdtemp(path.join(os.tmpdir(), "mcphub-ingress-gate-"));
await chmod(outputRoot, 0o700);
try {
  run(TSC, ["-p", "tsconfig.json", "--outDir", outputRoot]);
  const compiled = names.map((name) => path.join(outputRoot, "test/ingress", name.replace(/\.ts$/, ".js")));
  const output = run(process.execPath, ["--test", "--test-reporter=tap", ...compiled]);
  assertTap(output);
  process.stdout.write(output);
} finally {
  await rm(outputRoot, { recursive: true, force: true });
}
