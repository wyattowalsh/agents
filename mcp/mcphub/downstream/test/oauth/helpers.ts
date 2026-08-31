import { readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { mkdtempSync } from "node:fs";

import {
  OAuthSqliteStore,
  createTrustedOAuthRequestContext,
  resolveOAuthStatePaths,
  type OAuthStatePaths,
  type TrustedOAuthRequestContext,
} from "../../src/oauth/index.js";

export interface StoreFixture {
  readonly root: string;
  readonly paths: OAuthStatePaths;
  readonly store: OAuthSqliteStore;
  close(): void;
}

export function createStoreFixture(): StoreFixture {
  const root = mkdtempSync(path.join(tmpdir(), "mcphub-oauth-test-"));
  const stateDirectory = path.join(root, "state");
  const environment: NodeJS.ProcessEnv = { MCPHUB_OAUTH_STATE_DIR: stateDirectory };
  const paths = resolveOAuthStatePaths(environment);
  const store = OAuthSqliteStore.initialize(paths, 1_000);
  let closed = false;
  return {
    root,
    paths,
    store,
    close(): void {
      if (!closed) {
        store.close();
        rmSync(root, { recursive: true, force: true });
        closed = true;
      }
    },
  };
}

export function requestContext(
  sourceIp = "203.0.113.10",
  connectionKey = "synthetic_connection_key_000000000001",
): TrustedOAuthRequestContext {
  return createTrustedOAuthRequestContext({
    connectionKey,
    listenerId: "oauth-loopback-46684",
    sourceIp,
  });
}

export function loadFixture(name: string): unknown {
  const fixturePath = path.join(process.cwd(), "fixtures", "oauth", name);
  return JSON.parse(readFileSync(fixturePath, "utf8"));
}
