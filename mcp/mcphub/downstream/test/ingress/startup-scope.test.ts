import assert from "node:assert/strict";
import {
  chmod,
  mkdir,
  mkdtemp,
  readFile,
  realpath,
  rm,
  writeFile,
} from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { pathToFileURL } from "node:url";

const DOWNSTREAM_ROOT = path.resolve(process.cwd());
const REPO_ROOT = path.resolve(DOWNSTREAM_ROOT, "../../..");
const TRACKED_SETTINGS = path.join(REPO_ROOT, "mcp/mcphub/mcp_settings.json");
const LOCKED_MCPHUB_ROOT = path.join(
  DOWNSTREAM_ROOT,
  "node_modules/@samanhappy/mcphub",
);
const MCPHUB_MCP_SERVICE_RELATIVE_PATH =
  "node_modules/@samanhappy/mcphub/dist/services/mcpService.js";
const MCPHUB_SSRF_RELATIVE_PATH =
  "node_modules/@samanhappy/mcphub/dist/utils/ssrf.js";
const BLOCKED_CGNAT_URL = "http://100.64.0.1/mcp";
const FAILURE_SERVER = "deepwiki";
const THINGS_SERVERS = Object.freeze([
  "things-core",
  "things-shortcuts",
  "things-native",
] as const);

interface ServerConfig {
  enabled?: boolean;
  type?: string;
  url?: string;
  [key: string]: unknown;
}

interface GroupConfig {
  name?: string;
  servers?: unknown[];
  [key: string]: unknown;
}

interface McpHubSettings {
  mcpServers: Record<string, ServerConfig>;
  groups: GroupConfig[];
  [key: string]: unknown;
}

interface StartupServer {
  readonly name: string;
  readonly enabled: boolean;
  readonly type?: string;
  readonly url?: string;
}

interface StartupSimulation {
  readonly attempted: readonly string[];
  readonly connected: readonly string[];
  readonly disabledCount: number;
  readonly failed: Readonly<{
    name: string;
    status: string;
    error: string;
    hasTransport: boolean;
    toolCount: number;
  }>;
}

interface TransformResult {
  readonly code: string;
  readonly transformations: readonly string[];
}

interface MaterializerModule {
  bundleRuntime(input: Readonly<{
    entryPath: string;
    outputPath: string;
    inventoryRoot: string;
  }>): Promise<unknown>;
  transformLockedMcpHubSourceForUnitTest(input: Readonly<{
    code: string;
    relativePath: string;
  }>): TransformResult;
}

interface SealedModuleHelpers {
  importSelfContainedModule(bytes: Buffer): Promise<Readonly<{
    main(servers: readonly StartupServer[]): Promise<StartupSimulation>;
  }>>;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function parseSettings(value: unknown): McpHubSettings {
  assert.ok(isRecord(value));
  assert.ok(isRecord(value.mcpServers));
  assert.ok(Array.isArray(value.groups));
  return value as McpHubSettings;
}

function memberName(value: unknown): string {
  if (typeof value === "string") return value;
  assert.ok(isRecord(value));
  const name = value.name;
  if (typeof name !== "string") throw new TypeError("group member name must be a string");
  return name;
}

async function readTrackedSettings(): Promise<McpHubSettings> {
  return parseSettings(JSON.parse(await readFile(TRACKED_SETTINGS, "utf8")) as unknown);
}

function assertTrackedTopology(settings: McpHubSettings): void {
  const serverNames = Object.keys(settings.mcpServers);
  assert.equal(serverNames.length, 71);
  assert.equal(settings.groups.length, 32);

  const thingsGroups = settings.groups.filter((group) => group.name === "things");
  assert.equal(thingsGroups.length, 1);
  const thingsGroup = thingsGroups[0];
  assert.ok(thingsGroup);
  assert.ok(Array.isArray(thingsGroup.servers));
  assert.deepEqual(thingsGroup.servers.map(memberName), THINGS_SERVERS);

  const failureIndex = serverNames.indexOf(FAILURE_SERVER);
  assert.notEqual(failureIndex, -1);
  for (const server of THINGS_SERVERS) {
    assert.ok(failureIndex < serverNames.indexOf(server));
  }
  assert.equal(settings.mcpServers[FAILURE_SERVER]?.type, "streamable-http");
}

function deriveNoActivityFixture(settings: McpHubSettings): McpHubSettings {
  const fixture = structuredClone(settings);
  const things = new Set<string>(THINGS_SERVERS);
  for (const [name, config] of Object.entries(fixture.mcpServers)) {
    if (!things.has(name)) config.enabled = false;
  }
  const failure = fixture.mcpServers[FAILURE_SERVER];
  assert.ok(failure);
  failure.enabled = true;
  failure.type = "streamable-http";
  failure.url = BLOCKED_CGNAT_URL;
  return fixture;
}

function startupServers(settings: McpHubSettings): readonly StartupServer[] {
  return Object.entries(settings.mcpServers).map(([name, config]) => ({
    name,
    enabled: config.enabled !== false,
    ...(typeof config.type === "string" ? { type: config.type } : {}),
    ...(typeof config.url === "string" ? { url: config.url } : {}),
  }));
}

async function materializerHelpers(): Promise<Readonly<{
  materializer: MaterializerModule;
  sealed: SealedModuleHelpers;
}>> {
  const materializerUrl = pathToFileURL(
    path.join(DOWNSTREAM_ROOT, "src/materializer/bundle.mjs"),
  ).href;
  const sealedUrl = pathToFileURL(
    path.join(DOWNSTREAM_ROOT, "src/materializer/sealed-module.mjs"),
  ).href;
  return {
    materializer: await import(materializerUrl) as MaterializerModule,
    sealed: await import(sealedUrl) as SealedModuleHelpers,
  };
}

function isolatedTransportBranch(transformedMcpService: string): string {
  const start = transformedMcpService.indexOf([
    "            else {",
    "                try {",
    "                    transport = await createTransportFromConfig(name, expandedConf);",
  ].join("\n"));
  const end = transformedMcpService.indexOf(
    "            const serverInfoRef = {};",
    start,
  );
  assert.notEqual(start, -1);
  assert.notEqual(end, -1);
  const branch = transformedMcpService.slice(start, end).trimEnd();
  assert.equal(branch.split("continue;").length - 1, 1);
  return branch;
}

async function buildStartupSimulation(input: Readonly<{
  materializer: MaterializerModule;
  sealed: SealedModuleHelpers;
  isolatedBranch: string;
  transformedSsrf: string;
}>): Promise<Readonly<{
  run(servers: readonly StartupServer[]): Promise<StartupSimulation>;
  close(): Promise<void>;
}>> {
  const temporary = await realpath(
    await mkdtemp(path.join(os.tmpdir(), "mcphub-startup-scope-")),
  );
  await chmod(temporary, 0o700);
  const entryPath = path.join(temporary, "src/runtime/main.ts");
  const ssrfPath = path.join(temporary, "src/runtime/ssrf.ts");
  const outputPath = path.join(temporary, "dist/runtime/main.mjs");
  await mkdir(path.dirname(entryPath), { recursive: true, mode: 0o700 });
  await mkdir(path.dirname(outputPath), { recursive: true, mode: 0o700 });

  const source = [
    'import { assertSafeUrl } from "./ssrf.ts";',
    "const attempted = [];",
    "const logger = { error() {} };",
    "const summarizeErrorForLogging = (error) => ({ message: error instanceof Error ? error.message : String(error) });",
    "const formatErrorForLogging = (error) => error instanceof Error ? error.message : String(error);",
    "const createTransportFromConfig = async (name, config) => {",
    "  attempted.push(name);",
    "  if (config.url !== undefined) await assertSafeUrl(config.url);",
    "  return { name };",
    "};",
    "export async function main(allServers) {",
    "  attempted.length = 0;",
    "  const nextServerInfos = [];",
    "  for (const expandedConf of allServers) {",
    "    const { name } = expandedConf;",
    "    if (expandedConf.enabled === false) {",
    "      nextServerInfos.push({ name, status: 'disabled', error: null, tools: [], config: expandedConf });",
    "      continue;",
    "    }",
    "    let transport;",
    "    if (expandedConf.type === 'openapi') throw new Error('unexpected OpenAPI activation');",
    input.isolatedBranch,
    "    nextServerInfos.push({ name, status: 'connected', error: null, transport, config: expandedConf });",
    "  }",
    `  const failed = nextServerInfos.find((server) => server.name === ${JSON.stringify(FAILURE_SERVER)});`,
    "  if (failed === undefined) throw new Error('failure server missing');",
    "  return {",
    "    attempted: [...attempted],",
    "    connected: nextServerInfos.filter((server) => server.status === 'connected').map((server) => server.name),",
    "    disabledCount: nextServerInfos.filter((server) => server.status === 'disabled').length,",
    "    failed: {",
    "      name: failed.name,",
    "      status: failed.status,",
    "      error: failed.error,",
    "      hasTransport: Object.hasOwn(failed, 'transport'),",
    "      toolCount: failed.tools?.length ?? -1,",
    "    },",
    "  };",
    "}",
    "",
  ].join("\n");
  await writeFile(entryPath, source, { mode: 0o600 });
  await writeFile(ssrfPath, input.transformedSsrf, { mode: 0o600 });
  await input.materializer.bundleRuntime({ entryPath, outputPath, inventoryRoot: temporary });
  const loaded = await input.sealed.importSelfContainedModule(await readFile(outputPath));
  return {
    run: (servers) => loaded.main(servers),
    close: async () => rm(temporary, { recursive: true, force: true }),
  };
}

test("derives a no-activity fixture without contracting the tracked MCPHub topology", async () => {
  const tracked = await readTrackedSettings();
  assertTrackedTopology(tracked);
  const fixture = deriveNoActivityFixture(tracked);

  assert.deepEqual(Object.keys(fixture.mcpServers), Object.keys(tracked.mcpServers));
  assert.deepEqual(fixture.groups, tracked.groups);
  assert.equal(fixture.groups.length, 32);
  assert.equal(Object.keys(fixture.mcpServers).length, 71);

  for (const server of THINGS_SERVERS) {
    assert.deepEqual(fixture.mcpServers[server], tracked.mcpServers[server]);
  }
  for (const [name, config] of Object.entries(fixture.mcpServers)) {
    if (name === FAILURE_SERVER || THINGS_SERVERS.includes(name as (typeof THINGS_SERVERS)[number])) {
      continue;
    }
    assert.equal(config.enabled, false, name);
  }
  assert.deepEqual(
    {
      enabled: fixture.mcpServers[FAILURE_SERVER]?.enabled,
      type: fixture.mcpServers[FAILURE_SERVER]?.type,
      url: fixture.mcpServers[FAILURE_SERVER]?.url,
    },
    { enabled: true, type: "streamable-http", url: BLOCKED_CGNAT_URL },
  );
});

test("isolates one pre-Things CGNAT rejection and continues through exactly three Things backends", async () => {
  const tracked = await readTrackedSettings();
  assertTrackedTopology(tracked);
  const fixture = deriveNoActivityFixture(tracked);
  const helpers = await materializerHelpers();
  const rawMcpService = await readFile(
    path.join(LOCKED_MCPHUB_ROOT, "dist/services/mcpService.js"),
    "utf8",
  );
  const rawSsrf = await readFile(
    path.join(LOCKED_MCPHUB_ROOT, "dist/utils/ssrf.js"),
    "utf8",
  );
  const transformedMcpService = helpers.materializer.transformLockedMcpHubSourceForUnitTest({
    code: rawMcpService,
    relativePath: MCPHUB_MCP_SERVICE_RELATIVE_PATH,
  });
  const transformedSsrf = helpers.materializer.transformLockedMcpHubSourceForUnitTest({
    code: rawSsrf,
    relativePath: MCPHUB_SSRF_RELATIVE_PATH,
  });
  assert.deepEqual(
    transformedMcpService.transformations,
    ["mcphub-transport-construction-isolation-v1"],
  );
  assert.deepEqual(
    transformedSsrf.transformations,
    ["mcphub-ssrf-rfc6598-cgnat-range-v1"],
  );

  const simulation = await buildStartupSimulation({
    materializer: helpers.materializer,
    sealed: helpers.sealed,
    isolatedBranch: isolatedTransportBranch(transformedMcpService.code),
    transformedSsrf: transformedSsrf.code,
  });
  try {
    const result = await simulation.run(startupServers(fixture));
    const expectedAttempts = Object.keys(fixture.mcpServers).filter(
      (name) => name === FAILURE_SERVER || THINGS_SERVERS.includes(name as (typeof THINGS_SERVERS)[number]),
    );
    assert.deepEqual(result.attempted, expectedAttempts);
    assert.deepEqual(result.connected, expectedAttempts.filter((name) => name !== FAILURE_SERVER));
    assert.equal(result.disabledCount, 67);
    assert.deepEqual(result.failed, {
      name: FAILURE_SERVER,
      status: "disconnected",
      error: "Failed to construct transport: Blocked target IP: 100.64.0.1",
      hasTransport: false,
      toolCount: 0,
    });
    assert.deepEqual(new Set(result.connected), new Set(THINGS_SERVERS));
  } finally {
    await simulation.close();
  }
});
