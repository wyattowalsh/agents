export interface DistributionFileRecord {
  readonly sourcePath: string;
  readonly path: string;
  readonly sha256: string;
  readonly size: number;
  readonly mode: number;
  readonly role: "entrypoint" | "runtime" | "asset" | "dependency";
}

export interface OutputInventoryModuleRecord {
  readonly path: string;
  readonly sha256: string;
  readonly size: number;
  readonly kind: "owned-source" | "locked-dependency" | "build-input";
}

export interface LockedDependencyModuleRecord {
  readonly modulePath: string;
  readonly package: string;
  readonly version: string;
  readonly packageRelativePath: string;
  readonly lockKey: string;
  readonly lockIntegrity: string;
  readonly sha256: string;
  readonly size: number;
  readonly installedMode: number;
  readonly cafsSha512: string;
  readonly cafsPath: string;
  readonly packageIndexKey: string;
  readonly packageIndexRowSha256: string;
  readonly packageIndexRowSize: number;
}

export interface LockedDependencyClosure {
  readonly schemaVersion: 1;
  readonly status: "verified";
  readonly method: "fresh-offline-copy-install+pnpm-v11-cafs-sha512";
  readonly lockfileSha256: string;
  readonly lifecycleScriptsExecuted: false;
  readonly networkResolution: false;
  readonly packageImportMethod: "copy";
  readonly storeFormat: "v11";
  readonly pnpm: {
    readonly version: "11.22.0";
    readonly executableSha256: string;
    readonly executableSize: number;
  };
  readonly storeIndexSha256: string;
  readonly packageCount: number;
  readonly moduleCount: number;
  readonly packages: readonly {
    readonly package: string;
    readonly version: string;
    readonly lockIntegrity: string;
    readonly packageIndexKey: string;
    readonly packageIndexRowSha256: string;
    readonly packageIndexRowSize: number;
    readonly moduleCount: number;
  }[];
  readonly modules: readonly LockedDependencyModuleRecord[];
  readonly inventorySha256: string;
}

export interface MaterializedOutputInventory {
  readonly schemaVersion: 1;
  readonly status: "sealed";
  readonly bundler: {
    readonly name: "rolldown";
    readonly version: "1.2.6";
    readonly entry: "src/runtime/main.ts";
    readonly output: "dist/runtime/main.mjs";
    readonly format: "esm";
    readonly platform: "node";
    readonly codeSplitting: false;
    readonly sourcemap: false;
    readonly minify: "dce-only";
    readonly comments: false;
    readonly polyfillRequire: false;
    readonly emittedChunks: 1;
    readonly emittedAssets: 0;
  };
  readonly modules: readonly OutputInventoryModuleRecord[];
  readonly transformations: readonly string[];
  readonly transformEvents: readonly Record<string, unknown>[];
  readonly transformEventsSha256: string;
  readonly validatorPolicySha256: string;
  readonly buildAttestation: Readonly<Record<string, unknown>>;
  readonly buildAttestationSha256: string;
  readonly lockedDependencyClosure: LockedDependencyClosure;
  readonly sealAttestation: Readonly<Record<string, unknown>>;
  readonly sealAttestationSha256: string;
  readonly assets: readonly Readonly<Record<string, unknown>>[];
  readonly files: readonly DistributionFileRecord[];
}

export interface DistributionDigestReceipt {
  readonly schemaVersion: 1;
  readonly status: "sealed";
  readonly auditManifestSha256: string;
  readonly outputInventorySha256: string;
  readonly distributionDigest: string;
  readonly entryPoint: string;
  readonly entryExport: string | null;
  readonly fileCount: number;
}

export interface DownstreamAuditManifest {
  readonly schemaVersion: 1;
  readonly status: "candidate" | "sealed";
  readonly provenance: {
    readonly upstreamManifestSha256: string;
    readonly upstreamTarballSha256: string;
    readonly upstreamTarballIntegrity: string;
    readonly upstreamSignatureKeyId: string;
    readonly upstreamArchiveFileCount: 469;
    readonly upstreamArchiveUnpackedBytes: 9706506;
    readonly upstreamArchiveInventorySha256: string;
    readonly dependencyGraphSha256: string;
    readonly packageJsonSha256: string;
    readonly lockfileSha256: string;
  };
  readonly sourceClosure: {
    readonly exhaustive: boolean;
    readonly ownedSourcesManifestSha256: string | null;
    readonly patchManifestSha256: string | null;
    readonly derivationSha256: string | null;
    readonly productionLoaderTransformations: readonly [];
  };
  readonly build: {
    readonly commands: readonly string[];
    readonly nodeVersion: string;
    readonly packageManager: "pnpm@11.22.0";
    readonly outputInventoryComplete: boolean;
    readonly outputInventorySha256: string | null;
    readonly sealAttestationSha256: string | null;
  };
  readonly distribution: {
    readonly digest: string;
    readonly entryPoint: string;
    readonly entryExport: string | null;
    readonly files: readonly DistributionFileRecord[];
  };
}
