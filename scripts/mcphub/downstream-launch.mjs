#!/usr/bin/env node

import path from "node:path";

import { checkLaunch, launchDistribution } from "../../mcp/mcphub/downstream/src/materializer/launch.mjs";

function parseArgs(argv) {
  const result = { check: false, forwarded: [] };
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--") {
      result.forwarded = argv.slice(index + 1);
      break;
    }
    if (argument === "--check") {
      result.check = true;
      continue;
    }
    if (argument === "--runtime-root") {
      const value = argv[index + 1];
      if (!value) throw new Error("argument value missing");
      result.runtime_root = path.resolve(value);
      index += 1;
      continue;
    }
    throw new Error("unknown argument");
  }
  if (!result.runtime_root) throw new Error("required argument missing");
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
  const report = args.check
    ? await checkLaunch({ runtimeRoot: args.runtime_root })
    : await launchDistribution({ runtimeRoot: args.runtime_root, argv: args.forwarded });
  process.stdout.write(`${JSON.stringify(report)}\n`);
  } catch (error) {
    const message = error instanceof Error ? error.message : "unknown_error";
    process.stderr.write(
      `${JSON.stringify({ status: "error", reasonCode: "MCPHUB_DOWNSTREAM_LAUNCH_FAILED", error: message })}\n`,
    );
    process.exitCode = 1;
  }
}
