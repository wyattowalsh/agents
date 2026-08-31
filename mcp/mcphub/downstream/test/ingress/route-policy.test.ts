import { readFile } from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import assert from "node:assert/strict";

import {
  decideIngressRoute,
  frozenRemoteRouteManifest,
} from "../../src/ingress/route-policy.js";

interface Matrix {
  readonly remoteAllowed: readonly (readonly [string, string])[];
  readonly methodDenied: readonly (readonly [string, string, string])[];
  readonly alwaysDenied: readonly (readonly [string, string])[];
}

const matrix = JSON.parse(
  await readFile(path.resolve(process.cwd(), "fixtures/ingress/route-matrix.json"), "utf8"),
) as Matrix;

test("dispatches every frozen remote allowlist row", () => {
  for (const [method, target] of matrix.remoteAllowed) {
    assert.equal(
      decideIngressRoute({ kind: "remote-oauth", method, target }).action,
      "dispatch",
      `${method} ${target}`,
    );
  }
});

test("returns the exact method contract for canonical MCP GET and DELETE", () => {
  for (const [method, target, allow] of matrix.methodDenied) {
    const decision = decideIngressRoute({ kind: "remote-oauth", method, target });
    assert.equal(decision.action, "method-not-allowed");
    if (decision.action === "method-not-allowed") {
      assert.deepEqual(decision.allow, allow === "" ? [] : [allow]);
    }
  }
});

test("production ingress rejects encoded and alternate route forms", () => {
  for (const [method, target] of matrix.alwaysDenied) {
    assert.equal(
      decideIngressRoute({ kind: "remote-oauth", method, target }).action,
      "not-found",
      `${method} ${target}`,
    );
  }
});

test("preserves unrelated local MCPHub control-plane routing", () => {
  for (const target of [
    "/health",
    "/api/servers?status=connected&name=with%20space",
    "/mcp/harness?client=local",
    "/MCP/harness?client=local",
    "/sse/harness",
    "/SSE/harness",
    "/alice/mcp/harness",
    "/alice/MCP/harness",
    "/API/servers?status=connected",
  ]) {
    assert.equal(
      decideIngressRoute({ kind: "local-bearer", method: "GET", target }).action,
      "delegate-local-control-plane",
    );
  }
});

test("denies local global and direct Things execution aliases", () => {
  for (const [method, target] of matrix.alwaysDenied) {
    if (target === "/" || target === "/health") continue;
    assert.equal(
      decideIngressRoute({ kind: "local-bearer", method, target }).action,
      "not-found",
      `${method} ${target}`,
    );
  }
});

test("denies duplicate and unknown authorization query parameters", () => {
  for (const target of [
    "/oauth/authorize?state=a&state=b",
    "/oauth/authorize?state=a&access_token=secret",
  ]) {
    assert.equal(
      decideIngressRoute({ kind: "remote-oauth", method: "GET", target }).action,
      "not-found",
    );
  }
});

test("accepts only known unique authorization query parameters", () => {
  const target = "/oauth/authorize?client_id=https%3A%2F%2Fchatgpt.com%2Foauth%2Fclient.json&response_type=code&state=s";
  assert.deepEqual(decideIngressRoute({ kind: "remote-oauth", method: "GET", target }), {
    action: "dispatch",
    route: "oauth-authorize",
  });
});

test("renders exactly the fourteen frozen remote route rows", () => {
  const rendered = frozenRemoteRouteManifest().map(({ method, path: target }) => [method, target]);
  assert.equal(rendered.length, 14);
  assert.deepEqual(rendered, matrix.remoteAllowed);
});
