#!/usr/bin/env node

import path from "node:path";

import { checkMaterialization, materializeDistribution } from "../../mcp/mcphub/downstream/src/materializer/materialize.mjs";

function parseArgs(argv) {
  const result = { check: false };
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--check") {
      result.check = true;
      continue;
    }
    if (["--manifest", "--evidence-root", "--source-root", "--runtime-root", "--upstream-tarball"].includes(argument)) {
      const value = argv[index + 1];
      if (!value) throw new Error("argument value missing");
      result[argument.slice(2).replaceAll("-", "_")] = path.resolve(value);
      index += 1;
      continue;
    }
    throw new Error("unknown argument");
  }
  if (!result.manifest || !result.evidence_root || !result.source_root || !result.runtime_root || !result.upstream_tarball) {
    throw new Error("required argument missing");
  }
  return result;
}

let args;
try {
  args = parseArgs(process.argv.slice(2));
} catch {
  process.stderr.write('{"status":"error","reasonCode":"MCPHUB_DOWNSTREAM_ARGUMENT_INVALID"}\n');
  process.exitCode = 2;
}

if (args !== undefined) {
  try {
  const operation = args.check ? checkMaterialization : materializeDistribution;
  const report = await operation({
    manifestPath: args.manifest,
    evidenceRoot: args.evidence_root,
    sourceRoot: args.source_root,
    runtimeRoot: args.runtime_root,
    upstreamTarballPath: args.upstream_tarball,
  });
  process.stdout.write(`${JSON.stringify(report)}\n`);
  } catch {
    process.stderr.write('{"status":"error","reasonCode":"MCPHUB_DOWNSTREAM_MATERIALIZATION_FAILED"}\n');
    process.exitCode = 1;
  }
}
