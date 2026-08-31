import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { readFile } from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
  assertRuntimeCapabilityEnvironment,
  assertSelfContainedModule,
  importSelfContainedModule,
} from "../../src/materializer/sealed-module.mjs";

const DOWNSTREAM_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const CONSTRUCTOR_REJECTION = /known function constructor (?:extraction|destructuring)/;

test("rejects code-generation flag negation and proves the active runtime canary", () => {
  const required = "--disallow-code-generation-from-strings";
  assert.doesNotThrow(() => assertRuntimeCapabilityEnvironment({ execArgv: [required] }));
  assert.throws(
    () => assertRuntimeCapabilityEnvironment({ execArgv: [required, "--no-disallow-code-generation-from-strings"] }),
    /forbids --no-disallow-code-generation-from-strings/,
  );
  assert.throws(
    () => assertRuntimeCapabilityEnvironment({ execArgv: [required, "--no_disallow_code_generation_from_strings"] }),
    /forbids --no-disallow-code-generation-from-strings/,
  );
  assert.throws(() => assertRuntimeCapabilityEnvironment({ execArgv: [] }), /requires --disallow-code-generation-from-strings/);

  const moduleUrl = new URL("../../src/materializer/sealed-module.mjs", import.meta.url).href;
  const child = spawnSync(process.execPath, [
    "--input-type=module",
    "--eval",
    `import { assertRuntimeCapabilityEnvironment } from ${JSON.stringify(moduleUrl)}; assertRuntimeCapabilityEnvironment({ execArgv: [${JSON.stringify(required)}] });`,
  ], {
    cwd: DOWNSTREAM_ROOT,
    encoding: "utf8",
    env: { ...process.env, NODE_OPTIONS: "" },
  });
  assert.notEqual(child.status, 0);
  assert.match(child.stderr, /string code generation canary is enabled/);
});

test("rejects constructor extraction from a named function binding", async () => {
  const source = Buffer.from(
    'function f(){} const C=f.constructor; export function main(){ return C("return 42")(); }\n',
  );
  assert.throws(() => assertSelfContainedModule(source), CONSTRUCTOR_REJECTION);
  await assert.rejects(importSelfContainedModule(source), CONSTRUCTOR_REJECTION);
});

test("rejects optional constructor extraction through a function alias chain", () => {
  const source = Buffer.from(
    'const f=()=>{}; const g=f; const C=g?.constructor; export function main(){ return C("return 43")(); }\n',
  );
  assert.throws(() => assertSelfContainedModule(source), CONSTRUCTOR_REJECTION);
});

test("rejects computed constant constructor extraction through property aliases", () => {
  for (const source of [
    'function f(){} const key="constructor"; const C=f[key]; export function main(){ return C("return 44")(); }\n',
    'function f(){} const key0="con"+"structor"; const key1=key0; const C=f?.[key1]; export function main(){ return C("return 45")(); }\n',
    'const {constructor:C}=function f(){}; export function main(){ return C("return 46")(); }\n',
  ]) {
    assert.throws(() => assertSelfContainedModule(Buffer.from(source)), CONSTRUCTOR_REJECTION);
  }
});

test("permits safe constructor inspection and the complete sealed MCPHub bundle", async () => {
  const safe = Buffer.from(
    'const f=()=>{}; export function main(){ return [f.constructor.name, f.constructor === Object]; }\n',
  );
  const loaded = await importSelfContainedModule(safe);
  assert.deepEqual(loaded.main(), ["Function", false]);

  const productionEntry = await readFile(path.join(DOWNSTREAM_ROOT, "dist/runtime/main.mjs"));
  const auditManifest = JSON.parse(
    await readFile(path.join(DOWNSTREAM_ROOT, "provenance/audit-manifest.json"), "utf8"),
  );
  const entryRecord = auditManifest.distribution.files.find(
    (record) => record.path === auditManifest.distribution.entryPoint,
  );
  assert.ok(entryRecord);
  const sealed = assertSelfContainedModule(productionEntry);
  assert.equal(sealed.sha256, entryRecord.sha256);
});
