#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${AGENTS_REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
MCP_ROOT="${AGENTS_MCP_ROOT:-$REPO_ROOT/mcp}"

node - "$REPO_ROOT" "$MCP_ROOT" <<'NODE'
const { spawn } = require("node:child_process");

const repoRoot = process.argv[2];
const mcpRoot = process.argv[3];
const request = JSON.stringify({
  jsonrpc: "2.0",
  id: 1,
  method: "initialize",
  params: {
    protocolVersion: "2024-11-05",
    capabilities: {},
    clientInfo: { name: "agents-mcp-check", version: "0.0.0" },
  },
});

const checks = [
  {
    name: "atom-of-thoughts",
    command: "node",
    args: [`${mcpRoot}/servers/MCP_Atom_of_Thoughts/build/index.js`],
    expect: "atom-of-thoughts",
  },
  {
    name: "lotus-wisdom-mcp",
    command: "node",
    args: [`${mcpRoot}/servers/lotus-wisdom-mcp/dist/bundle.js`],
    expect: "lotus-wisdom-server",
  },
  {
    name: "creative-thinking",
    command: `${repoRoot}/scripts/mcp_tools/run_mcp_thinking.sh`,
    args: [],
    expect: "enhanced-sequential-thinking-server",
  },
];

function probe(check) {
  return new Promise((resolve) => {
    const child = spawn(check.command, check.args, { stdio: ["pipe", "pipe", "pipe"] });
    let stdout = "";
    let stderr = "";
    let settled = false;
    const finish = (result) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      if (child.exitCode === null && child.signalCode === null) {
        child.kill("SIGTERM");
      }
      resolve(result);
    };
    const maybeResolveFromStdout = () => {
      const text = stdout.trim().split(/\n/).find((line) => line.includes('"jsonrpc"'));
      if (text) finish({ ...check, stdout, stderr });
    };
    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
      maybeResolveFromStdout();
    });
    child.stderr.on("data", (chunk) => (stderr += chunk.toString()));
    child.stdin.write(request + "\n");

    const timer = setTimeout(() => {
      finish({ ...check, ok: false, reason: "timeout", stdout, stderr });
    }, check.timeoutMs || 15000);

    child.on("exit", (code, signal) => {
      finish({ ...check, code, signal, stdout, stderr });
    });
  }).then((result) => {
    const text = result.stdout.trim().split(/\n/).find((line) => line.includes('"jsonrpc"'));
    if (!text) {
      return { ...result, ok: false, reason: result.reason || "no initialize response" };
    }
    try {
      const parsed = JSON.parse(text);
      const name = parsed?.result?.serverInfo?.name;
      return { ...result, ok: name === check.expect, actual: name };
    } catch (error) {
      return { ...result, ok: false, reason: `invalid JSON response: ${error.message}` };
    }
  });
}

(async () => {
  let failed = false;
  for (const check of checks) {
    const result = await probe(check);
    if (result.ok) {
      console.log(`ok ${check.name}: ${result.actual}`);
      continue;
    }
    failed = true;
    console.error(`fail ${check.name}: ${result.reason || `expected ${check.expect}, got ${result.actual || "none"}`}`);
    if (result.stderr) console.error(result.stderr.trim().slice(0, 2000));
  }
  process.exit(failed ? 1 : 0);
})();
NODE
