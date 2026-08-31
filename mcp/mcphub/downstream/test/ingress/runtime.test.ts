import assert from "node:assert/strict";
import {
  chmod,
  mkdtemp,
  readFile,
  rm,
  writeFile,
} from "node:fs/promises";
import type { IncomingMessage, RequestListener, ServerResponse } from "node:http";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import { createOwnedLocalThingsInterceptor } from "../../src/runtime/local-control-plane.js";
import {
  evaluateRuntimeActivation,
  parseRemoteActivationReceipt,
  type RemoteActivationBindings,
} from "../../src/runtime/readiness.js";
import {
  assertInheritedSmartRoutingDisabled,
  assertSettingsSmartRoutingDisabled,
  loadAndValidateRuntimeSettings,
} from "../../src/runtime/settings-contract.js";
function exerciseLocalInterceptor(target: string): Readonly<{
  delegated: number;
  intercepted: number;
}> {
  let delegated = 0;
  let intercepted = 0;
  const listener: RequestListener = () => {
    intercepted += 1;
  };
  createOwnedLocalThingsInterceptor(() => listener)(
    { method: "POST", url: target } as IncomingMessage,
    {} as ServerResponse,
    () => {
      delegated += 1;
    },
  );
  return { delegated, intercepted };
}

const HASH = "1".repeat(64);
const ZERO_HASH = "0".repeat(64);

function activationBindings(mode: "capture" | "public"): RemoteActivationBindings {
  return Object.freeze({
    auditManifestSha256: HASH,
    capabilityManifestSha256: HASH,
    catalogSha256: HASH,
    cloudflaredConfigSha256: HASH,
    conformanceResultSha256: HASH,
    distributionDigest: `sha256-${HASH}`,
    manifestProjectionSha256: HASH,
    oauthLoginCredentialSha256: mode === "capture" ? ZERO_HASH : HASH,
    oauthPolicySha256: mode === "capture" ? ZERO_HASH : HASH,
    observedWireEvidenceSha256: mode === "capture" ? ZERO_HASH : HASH,
    routeManifestSha256: HASH,
    scopeMapSha256: HASH,
    settingsSha256: HASH,
  });
}

function activationReceipt(mode: "capture" | "public") {
  const bindings = activationBindings(mode);
  const now = 1_000_000;
  return parseRemoteActivationReceipt({
    bytes: Buffer.from(
      JSON.stringify({
        schemaVersion: 1,
        status: "pass",
        mode,
        noSecrets: true,
        createdAt: now - 1_000,
        expiresAt: now + 60_000,
        publicOrigin: "https://mcp.w4w.dev",
        publicResource: "https://mcp.w4w.dev/mcp/things",
        registrationMode: mode === "public" ? "cimd" : null,
        remotePublicReady: mode === "public",
        toolDispatchEnabled: mode === "public",
        tunnelAllowed: true,
        bindings,
      }),
    ),
    expectedBindings: bindings,
    expectedMode: mode,
    expectedRegistrationMode: mode === "public" ? "cimd" : null,
    now,
    receiptSha256: HASH,
  });
}

test("disabled mode binds no remote listener", () => {
  assert.deepEqual(
    evaluateRuntimeActivation({ mode: "disabled", receipt: null }),
    {
      bindRemoteListener: false,
      mode: "disabled",
      remotePublicReady: false,
      remoteToolDispatchEnabled: false,
      receiptSha256: null,
      tunnelAllowed: false,
    },
  );
});

test("capture mode requires an explicit receipt", () => {
  assert.throws(
    () => evaluateRuntimeActivation({ mode: "capture", receipt: null }),
    /capture_mode_not_ready/u,
  );
});

test("capture mode binds a dispatch-disabled loopback listener", () => {
  assert.deepEqual(
    evaluateRuntimeActivation({ mode: "capture", receipt: activationReceipt("capture") }),
    {
      bindRemoteListener: true,
      mode: "capture",
      remotePublicReady: false,
      remoteToolDispatchEnabled: false,
      receiptSha256: HASH,
      tunnelAllowed: true,
    },
  );
});

test("public mode remains fail closed without a digest-bound receipt", () => {
  assert.throws(
    () => evaluateRuntimeActivation({ mode: "public", receipt: null }),
    /remote_public_not_ready/u,
  );
});

test("public mode binds and dispatches only with a validated receipt", () => {
  assert.deepEqual(
    evaluateRuntimeActivation({ mode: "public", receipt: activationReceipt("public") }),
    {
      bindRemoteListener: true,
      mode: "public",
      remotePublicReady: true,
      remoteToolDispatchEnabled: true,
      receiptSha256: HASH,
      tunnelAllowed: true,
    },
  );
});

test("modern and legacy catalogs remain the exact same seventy tools", async () => {
  const [reportBytes, contractBytes, manifestBytes] = await Promise.all([
    readFile(path.resolve(process.cwd(), "fixtures/protocol/conformance-report.json"), "utf8"),
    readFile(path.resolve(process.cwd(), "fixtures/protocol/normalized-catalog.contract.json"), "utf8"),
    readFile(
      path.resolve(
        process.cwd(),
        "../../../openspec/changes/replace-supathings-with-things-plus-plus/capability-manifest.json",
      ),
      "utf8",
    ),
  ]);
  const report = JSON.parse(reportBytes) as {
    readonly protocol: { readonly legacy: string; readonly modern: string };
    readonly catalog: {
      readonly serverCounts: Readonly<Record<string, number>>;
      readonly toolCount: number;
    };
    readonly execution: {
      readonly cases: readonly Readonly<{ id: string; status: string }>[];
      readonly status: string;
    };
  };
  const contract = JSON.parse(contractBytes) as {
    readonly equalFields: readonly string[];
    readonly orderedServerCounts: Readonly<Record<string, number>>;
    readonly toolCount: number;
  };
  const manifest = JSON.parse(manifestBytes) as {
    readonly counts: { readonly tools: number };
    readonly tools: readonly unknown[];
  };
  const cases = new Map(report.execution.cases.map((entry) => [entry.id, entry.status]));

  assert.equal(report.protocol.modern, "2026-07-28");
  assert.equal(report.protocol.legacy, "2025-11-25");
  assert.equal(report.execution.status, "passed");
  assert.equal(cases.get("modern-list"), "passed");
  assert.equal(cases.get("legacy-list"), "passed");
  assert.equal(report.catalog.toolCount, 70);
  assert.equal(contract.toolCount, 70);
  assert.equal(manifest.counts.tools, 70);
  assert.equal(manifest.tools.length, 70);
  assert.deepEqual(contract.orderedServerCounts, report.catalog.serverCounts);
  assert.deepEqual(contract.equalFields, [
    "name",
    "description",
    "inputSchema",
    "outputSchema",
    "annotations",
    "_meta",
  ]);
});

test("provider uses one closed static MCPHub 1.0.32 service graph", async () => {
  const source = await readFile(path.resolve(process.cwd(), "src/runtime/provider.ts"), "utf8");
  assert.match(source, /@samanhappy\/mcphub\/dist\/services\/mcpService\.js/u);
  assert.match(source, /@samanhappy\/mcphub\/dist\/services\/sseService\.js/u);
  assert.doesNotMatch(source, /dist\/index\.js|AppServer|import\s*\(/u);
  assert.doesNotMatch(source, /initUpstreamServers|cleanupAllServers/u);
  assert.match(source, /const GROUP = "things"/u);
  assert.match(source, /result\.tools\.length !== 70/u);
});

test("sealed runtime exposes main and requires the verified contract asset", async () => {
  const source = await readFile(path.resolve(process.cwd(), "src/runtime/main.ts"), "utf8");
  assert.match(source, /export async function main\(input: SealedMainInput\)/u);
  assert.match(source, /things-capability-manifest\.json/u);
  assert.doesNotMatch(source, /npx|NODE_OPTIONS|--loader|--import/u);
  assert.match(source, /@samanhappy\/mcphub\/dist\/server\.js/u);
  assert.match(source, /new McpHubAppServer\(\)/u);
  assert.match(source, /upstream\.getApp\(\)/u);
  assert.match(source, /await upstream\.initialize\(\)/u);
  assert.match(source, /await upstream\.shutdown\(\)/u);
  assert.match(source, /new CaptureEvidenceRecorder/u);
  assert.match(source, /MCPHUB_REMOTE_CAPTURE_EVIDENCE_PATH/u);
  assert.match(source, /captureReceiptSha256: receipt\.receiptSha256/u);
  assert.match(source, /validateCaptureEvidenceForPublic/u);
  assert.match(source, /remoteExpiresAt: receipt\.expiresAt/u);
  assert.match(source, /setTimeout\(finish, Math\.max\(0, expiresAt - Date\.now\(\)\)\)/u);
  assert.match(source, /await waitForShutdown\(receipt\?\.expiresAt\)/u);
  assert.match(source, /server\.closeAllConnections\(\)/u);
  assert.match(source, /createServer\(upstreamApplication\)/u);
  assert.doesNotMatch(source, /\.start\s*\(/u);
  assert.ok(
    source.indexOf("installOwnedLocalThingsInterceptor") <
      source.indexOf("await upstream.initialize()"),
  );
  assert.ok(
    source.indexOf(
      "assertInheritedSmartRoutingDisabled(process.env.SMART_ROUTING_ENABLED)",
    ) < source.indexOf("await upstream.initialize()"),
  );
});

test("runtime binds startup to generated group-only settings contract", async () => {
  const source = await readFile(path.resolve(process.cwd(), "src/runtime/settings-contract.ts"), "utf8");
  assert.match(source, /settings\.thingsContract/u);
  assert.match(source, /entry\.groupOnly !== true/u);
  assert.match(source, /entry\.toolApprovals/u);
  assert.match(source, /systemConfig\.nameSeparator !== "-"/u);
  assert.match(source, /"alias" in member/u);
  assert.match(source, /group\.name === "things"/u);
  assert.match(source, /SERVERS\.includes/u);
  assert.ok(
    source.indexOf("const settingsBytes = safeRead(input.settingsPath)") <
      source.indexOf("assertSettingsSmartRoutingDisabled(settings)"),
  );

  assert.doesNotThrow(() =>
    assertSettingsSmartRoutingDisabled({
      systemConfig: { nameSeparator: "-", smartRouting: { enabled: false } },
    }),
  );
  for (const invalid of [
    {},
    { systemConfig: {} },
    { systemConfig: { nameSeparator: "__", smartRouting: { enabled: false } } },
    { systemConfig: { nameSeparator: "-", smartRouting: {} } },
    { systemConfig: { nameSeparator: "-", smartRouting: { enabled: true } } },
    { systemConfig: { nameSeparator: "-", smartRouting: { enabled: "false" } } },
    { systemConfig: { nameSeparator: "-", smartRouting: { enabled: "private-value" } } },
  ]) {
    assert.throws(
      () => assertSettingsSmartRoutingDisabled(invalid),
      (error: unknown) => {
        assert.ok(error instanceof Error);
        assert.equal(error.message, "runtime_settings_contract_invalid");
        return true;
      },
    );
  }

  assert.doesNotThrow(() => assertInheritedSmartRoutingDisabled(undefined));
  assert.doesNotThrow(() => assertInheritedSmartRoutingDisabled("false"));
  for (const invalid of ["", "true", "TRUE", "0", "private-value"]) {
    assert.throws(
      () => assertInheritedSmartRoutingDisabled(invalid),
      (error: unknown) => {
        assert.ok(error instanceof Error);
        assert.equal(error.message, "runtime_smart_routing_environment_invalid");
        return true;
      },
    );
  }

  const temporary = await mkdtemp(
    path.join(os.tmpdir(), "mcphub-runtime-settings-contract-"),
  );
  await chmod(temporary, 0o700);
  try {
    const manifestSource = path.resolve(
      process.cwd(),
      "../../../openspec/changes/replace-supathings-with-things-plus-plus/capability-manifest.json",
    );
    const settingsSource = path.resolve(process.cwd(), "../mcp_settings.json");
    const [manifestBytes, settingsBytes] = await Promise.all([
      readFile(manifestSource),
      readFile(settingsSource),
    ]);
    const manifestPath = path.join(temporary, "things-capability-manifest.json");
    const settingsPath = path.join(temporary, "mcp_settings.json");
    await writeFile(manifestPath, manifestBytes, { flag: "wx", mode: 0o600 });
    await writeFile(settingsPath, settingsBytes, { flag: "wx", mode: 0o600 });
    await chmod(manifestPath, 0o600);
    await chmod(settingsPath, 0o600);

    const projection = loadAndValidateRuntimeSettings({
      capabilityManifestPath: manifestPath,
      settingsPath,
    });
    assert.deepEqual(projection.counts, {
      tools: 70,
      coreTools: 41,
      shortcutTools: 21,
      nativeTools: 8,
      supaOutcomes: 37,
      workflows: 17,
      legacyEvalIds: 25,
      newEvalIds: 16,
    });

    const settings = JSON.parse(settingsBytes.toString("utf8")) as {
      groups: Array<{ name: string; servers: unknown[] }>;
      systemConfig: { nameSeparator: string };
    };
    assert.equal(settings.systemConfig.nameSeparator, "-");
    assert.ok(
      settings.groups.some(
        (group) =>
          group.name !== "things" &&
          group.servers.some((member) => typeof member === "string") &&
          group.servers.some(
            (member) =>
              member !== null &&
              typeof member === "object" &&
              !Array.isArray(member),
          ),
      ),
    );

    const forbiddenMembership = structuredClone(settings);
    const forbiddenGroup = forbiddenMembership.groups.find(
      (group) => group.name !== "things",
    );
    assert.ok(forbiddenGroup);
    forbiddenGroup.servers.push("things-core");
    const forbiddenPath = path.join(temporary, "mcp_settings-forbidden.json");
    await writeFile(
      forbiddenPath,
      `${JSON.stringify(forbiddenMembership)}\n`,
      { flag: "wx", mode: 0o600 },
    );
    await chmod(forbiddenPath, 0o600);
    assert.throws(
      () =>
        loadAndValidateRuntimeSettings({
          capabilityManifestPath: manifestPath,
          settingsPath: forbiddenPath,
        }),
      /runtime_settings_contract_invalid/u,
    );

    const invalidMembership = structuredClone(settings);
    const invalidGroup = invalidMembership.groups.find(
      (group) => group.name !== "things",
    );
    assert.ok(invalidGroup);
    invalidGroup.servers.push(42);
    const invalidPath = path.join(temporary, "mcp_settings-invalid-member.json");
    await writeFile(invalidPath, `${JSON.stringify(invalidMembership)}\n`, {
      flag: "wx",
      mode: 0o600,
    });
    await chmod(invalidPath, 0o600);
    assert.throws(
      () =>
        loadAndValidateRuntimeSettings({
          capabilityManifestPath: manifestPath,
          settingsPath: invalidPath,
        }),
      /runtime_settings_contract_invalid/u,
    );

    const separatorDrift = structuredClone(settings);
    separatorDrift.systemConfig.nameSeparator = "__";
    const separatorPath = path.join(temporary, "mcp_settings-separator.json");
    await writeFile(separatorPath, `${JSON.stringify(separatorDrift)}\n`, {
      flag: "wx",
      mode: 0o600,
    });
    await chmod(separatorPath, 0o600);
    assert.throws(
      () =>
        loadAndValidateRuntimeSettings({
          capabilityManifestPath: manifestPath,
          settingsPath: separatorPath,
        }),
      /runtime_settings_contract_invalid/u,
    );

    const aliasDrift = structuredClone(settings);
    const thingsGroup = aliasDrift.groups.find((group) => group.name === "things");
    const firstThingsMember = thingsGroup?.servers[0];
    assert.ok(
      firstThingsMember !== null &&
        typeof firstThingsMember === "object" &&
        !Array.isArray(firstThingsMember),
    );
    (firstThingsMember as Record<string, unknown>).alias = "things_core";
    const aliasPath = path.join(temporary, "mcp_settings-alias.json");
    await writeFile(aliasPath, `${JSON.stringify(aliasDrift)}\n`, {
      flag: "wx",
      mode: 0o600,
    });
    await chmod(aliasPath, 0o600);
    assert.throws(
      () =>
        loadAndValidateRuntimeSettings({
          capabilityManifestPath: manifestPath,
          settingsPath: aliasPath,
        }),
      /runtime_settings_contract_invalid/u,
    );
  } finally {
    await rm(temporary, { force: true, recursive: true });
  }
});

test("owned local interceptor captures exact and forbidden Things bypasses", () => {
  for (const target of [
    "/mcp/things",
    "/mcp",
    "/mcp/$smart",
    "/mcp/things-core",
    "/mcp/things-shortcuts",
    "/mcp/things-native",
    "/mcp/things/alternate",
    "/sse",
    "/messages",
    "/api/tools/call/things-core",
    "/api/things/tools/things-native/run",
    "/alice/mcp/things-shortcuts",
  ]) {
    assert.deepEqual(exerciseLocalInterceptor(target), {
      delegated: 0,
      intercepted: 1,
    });
  }
});

test("owned local interceptor delegates unrelated control-plane routes", () => {
  for (const target of [
    "/health",
    "/api/servers?name=with%20space",
    "/mcp/harness?client=local",
  ]) {
    assert.deepEqual(exerciseLocalInterceptor(target), {
      delegated: 1,
      intercepted: 0,
    });
  }
});
