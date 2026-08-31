import { createServer, type RequestListener, type Server } from "node:http";
import path from "node:path";

import McpHubAppServer from "@samanhappy/mcphub/dist/server.js";

import {
  CaptureOnlyOAuthHandler,
  CaptureEvidenceRecorder,
  LOCAL_LISTENER,
  ProductionOAuthHandler,
  REMOTE_LISTENER,
  createThingsIngressRequestListener,
  frozenCloudflareIngressManifest,
  validateCaptureEvidenceForPublic,
} from "../ingress/index.js";
import {
  OAuthSqliteStore,
  ThingsOAuthService,
  resolveOAuthStatePaths,
} from "../oauth/index.js";
import {
  canonicalSha256,
  createThingsProtocolHandler,
} from "../protocol/index.js";
import type { ThingsManifestProjection } from "../protocol/types.js";
import { installOwnedLocalThingsInterceptor } from "./local-control-plane.js";
import { McpHubThingsProvider } from "./provider.js";
import {
  auditManifestIdentity,
  evaluateRuntimeActivation,
  loadRemoteActivationReceipt,
  type RemoteActivationBindings,
  type RemoteRuntimeMode,
  type ValidatedRemoteActivationReceipt,
} from "./readiness.js";
import {
  assertInheritedSmartRoutingDisabled,
  loadAndValidateRuntimeSettingsContract,
  type ValidatedRuntimeSettingsContract,
} from "./settings-contract.js";
import {
  loadOAuthRuntimeConfig,
  registrationModeOf,
  type LoadedOAuthRuntimeConfig,
} from "./oauth-config.js";
import { readOwnerOnlyRuntimeFile } from "./secure-file.js";

export interface SealedMainInput {
  readonly argv: readonly string[];
  readonly distributionRoot: string;
  readonly auditManifest: unknown;
}

const CONTRACT_ASSET = "things-capability-manifest.json";

function modeFromEnvironment(): RemoteRuntimeMode {
  const value = process.env.MCPHUB_REMOTE_MODE ?? "disabled";
  if (value === "disabled" || value === "capture" || value === "public") return value;
  throw new Error("remote_mode_invalid");
}

function requiredEnvironmentPath(name: string): string {
  const value = process.env[name];
  if (value === undefined || value.length === 0 || value.includes("\0")) {
    throw new Error(`runtime_environment_path_missing:${name}`);
  }
  return value;
}

function readProjection(distributionRoot: string): ValidatedRuntimeSettingsContract {
  const asset = path.join(distributionRoot, CONTRACT_ASSET);
  const relative = path.relative(distributionRoot, asset);
  if (relative !== CONTRACT_ASSET) throw new Error("runtime_contract_asset_invalid");
  const settingsPath = process.env.MCPHUB_SETTING_PATH;
  if (settingsPath === undefined) throw new Error("runtime_settings_path_missing");
  return loadAndValidateRuntimeSettingsContract({
    capabilityManifestPath: asset,
    settingsPath,
  });
}

function loadOAuthConfig(mode: RemoteRuntimeMode): LoadedOAuthRuntimeConfig | null {
  if (mode !== "public") return null;
  return loadOAuthRuntimeConfig({
    credentialPath: requiredEnvironmentPath("MCPHUB_OAUTH_LOGIN_CREDENTIAL_PATH"),
    policyPath: requiredEnvironmentPath("MCPHUB_OAUTH_POLICY_PATH"),
  });
}

function activationBindings(input: {
  readonly auditManifest: unknown;
  readonly mode: Exclude<RemoteRuntimeMode, "disabled">;
  readonly oauthConfig: LoadedOAuthRuntimeConfig | null;
  readonly protocolHandler: Awaited<ReturnType<typeof createThingsProtocolHandler>>;
  readonly settings: ValidatedRuntimeSettingsContract;
}): RemoteActivationBindings {
  const audit = auditManifestIdentity(input.auditManifest);
  const cloudflared = readOwnerOnlyRuntimeFile(
    requiredEnvironmentPath("MCPHUB_TUNNEL_RUNTIME_CONFIG"),
    64 * 1024,
  );
  const conformance = readOwnerOnlyRuntimeFile(
    requiredEnvironmentPath("MCPHUB_REMOTE_CONFORMANCE_RESULT_PATH"),
    8 * 1024 * 1024,
  );
  let observed = "0".repeat(64);
  if (input.mode === "public") {
    if (input.oauthConfig === null) throw new Error("runtime_oauth_config_invalid");
    const observedFile = readOwnerOnlyRuntimeFile(
      requiredEnvironmentPath("MCPHUB_REMOTE_OBSERVED_WIRE_EVIDENCE_PATH"),
      8 * 1024 * 1024,
    );
    validateCaptureEvidenceForPublic({
      bytes: observedFile.bytes,
      expectedRegistrationMode: registrationModeOf(input.oauthConfig),
    });
    observed = observedFile.sha256;
  }
  return Object.freeze({
    auditManifestSha256: audit.auditManifestSha256,
    capabilityManifestSha256: input.settings.capabilityManifestSha256,
    catalogSha256: input.protocolHandler.catalog.catalogSha256,
    cloudflaredConfigSha256: cloudflared.sha256,
    conformanceResultSha256: conformance.sha256,
    distributionDigest: audit.distributionDigest,
    manifestProjectionSha256: input.protocolHandler.catalog.manifestProjectionSha256,
    oauthLoginCredentialSha256: input.oauthConfig?.credentialSha256 ?? "0".repeat(64),
    oauthPolicySha256: input.oauthConfig?.policySha256 ?? "0".repeat(64),
    observedWireEvidenceSha256: observed,
    routeManifestSha256: canonicalSha256(frozenCloudflareIngressManifest()),
    scopeMapSha256: input.protocolHandler.catalog.scopeMapSha256,
    settingsSha256: input.settings.settingsSha256,
  });
}

function listen(server: Server, host: string, port: number): Promise<void> {
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(port, host, () => {
      server.off("error", reject);
      resolve();
    });
  });
}

function close(server: Server | undefined): Promise<void> {
  if (server === undefined || !server.listening) return Promise.resolve();
  return new Promise((resolve, reject) => {
    server.close((error) => (error === undefined ? resolve() : reject(error)));
    server.closeAllConnections();
  });
}

function waitForShutdown(expiresAt?: number): Promise<void> {
  return new Promise((resolve) => {
    let timer: NodeJS.Timeout | undefined;
    let settled = false;
    const finish = (): void => {
      if (settled) return;
      settled = true;
      process.off("SIGINT", finish);
      process.off("SIGTERM", finish);
      if (timer !== undefined) clearTimeout(timer);
      resolve();
    };
    process.once("SIGINT", finish);
    process.once("SIGTERM", finish);
    if (expiresAt !== undefined) {
      timer = setTimeout(finish, Math.max(0, expiresAt - Date.now()));
    }
  });
}

export async function main(input: SealedMainInput): Promise<void> {
  if (input.argv.length !== 0 || !path.isAbsolute(input.distributionRoot)) {
    throw new Error("runtime_arguments_invalid");
  }
  const settings = readProjection(input.distributionRoot);
  const projection: ThingsManifestProjection = settings.projection;
  assertInheritedSmartRoutingDisabled(process.env.SMART_ROUTING_ENABLED);
  const mode = modeFromEnvironment();
  const oauthConfig = loadOAuthConfig(mode);
  const provider = new McpHubThingsProvider();
  const upstream = new McpHubAppServer();
  const upstreamApplication = upstream.getApp();
  let localIngress: RequestListener | undefined;
  let local: Server | undefined;
  let remote: Server | undefined;
  let oauthStore: OAuthSqliteStore | undefined;
  let protocolHandler: Awaited<ReturnType<typeof createThingsProtocolHandler>> | undefined;
  installOwnedLocalThingsInterceptor(upstreamApplication, () => localIngress);
  try {
    await upstream.initialize();
    await provider.initialize();
    protocolHandler = await createThingsProtocolHandler(provider, projection);
    const receipt: ValidatedRemoteActivationReceipt | null =
      mode === "disabled"
        ? null
        : loadRemoteActivationReceipt({
            expectedBindings: activationBindings({
              auditManifest: input.auditManifest,
              mode,
              oauthConfig,
              protocolHandler,
              settings,
            }),
            expectedMode: mode,
            expectedRegistrationMode:
              oauthConfig === null ? null : registrationModeOf(oauthConfig),
            path: requiredEnvironmentPath("MCPHUB_REMOTE_ACTIVATION_RECEIPT_PATH"),
          });
    const activation = evaluateRuntimeActivation({ mode, receipt });
    if (receipt !== null && Date.now() >= receipt.expiresAt) {
      throw new Error("remote_activation_receipt_expired");
    }
    let oauthService: ThingsOAuthService | undefined;
    const captureRecorder =
      mode === "capture" && receipt !== null
        ? new CaptureEvidenceRecorder({
            captureReceiptSha256: receipt.receiptSha256,
            createdAt: receipt.createdAt,
            expiresAt: receipt.expiresAt,
            path: requiredEnvironmentPath("MCPHUB_REMOTE_CAPTURE_EVIDENCE_PATH"),
          })
        : undefined;
    if (mode === "public") {
      if (oauthConfig === null) throw new Error("runtime_oauth_config_invalid");
      oauthStore = OAuthSqliteStore.openOrInitialize(resolveOAuthStatePaths());
      oauthService = new ThingsOAuthService({
        store: oauthStore,
        clientPolicy: oauthConfig.clientPolicy,
        cimdResolver: oauthConfig.cimdResolver,
        registrationPrincipal: oauthConfig.registrationPrincipal,
        verifyLoginProof: oauthConfig.verifyLoginProof,
      });
    }
    localIngress = createThingsIngressRequestListener({
      kind: "local-bearer",
      protocolHandler,
      ...(process.env.MCPHUB_BEARER_TOKEN === undefined
        ? {}
        : { localBearerToken: process.env.MCPHUB_BEARER_TOKEN }),
    });
    local = createServer(upstreamApplication);
    remote = activation.bindRemoteListener
      ? createServer(
          createThingsIngressRequestListener({
            kind: "remote-oauth",
            protocolHandler,
            oauthHandler:
              mode === "public" && oauthService !== undefined
                ? new ProductionOAuthHandler(oauthService)
                : new CaptureOnlyOAuthHandler(captureRecorder),
            ...(captureRecorder === undefined ? {} : { captureRecorder }),
            ...(oauthService === undefined ? {} : { oauthService }),
            ...(receipt === null ? {} : { remoteExpiresAt: receipt.expiresAt }),
            remoteToolDispatchEnabled: activation.remoteToolDispatchEnabled,
          }),
        )
      : undefined;
    await listen(local, LOCAL_LISTENER.host, LOCAL_LISTENER.port);
    if (remote !== undefined) {
      await listen(remote, REMOTE_LISTENER.host, REMOTE_LISTENER.port);
    }
    await waitForShutdown(receipt?.expiresAt);
  } finally {
    try {
      await Promise.all([close(remote), close(local)]);
    } finally {
      try {
        await protocolHandler?.close();
      } finally {
        try {
          oauthStore?.close();
        } finally {
          provider.close();
          await upstream.shutdown();
        }
      }
    }
  }
}
