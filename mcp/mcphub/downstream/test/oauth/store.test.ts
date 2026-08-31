import assert from "node:assert/strict";
import {
  chmodSync,
  copyFileSync,
  lstatSync,
  mkdirSync,
  readFileSync,
  renameSync,
  rmSync,
  symlinkSync,
  unlinkSync,
  writeFileSync,
} from "node:fs";
import path from "node:path";
import test from "node:test";
import { DatabaseSync } from "node:sqlite";

import {
  OAuthSqliteStore,
  THINGS_RESOURCE,
  hashOpaque,
  randomOpaque,
  resolveOAuthStatePaths,
} from "../../src/oauth/index.js";
import { createStoreFixture } from "./helpers.js";

function hasCode(code: string): Readonly<{ name: "OAuthSecurityError"; message: string }> {
  return { name: "OAuthSecurityError", message: code };
}

function insertGrant(store: OAuthSqliteStore, now: number) {
  const state = randomOpaque();
  const code = randomOpaque();
  const nonce = randomOpaque();
  const principal = randomOpaque();
  const codeChallenge = randomOpaque();
  store.putAuthorizationTransaction(
    {
      stateHash: hashOpaque(state),
      clientId: "client-1",
      registrationMode: "dcr",
      redirectUri: "https://chatgpt.com/connector_platform_oauth_redirect",
      codeChallenge,
      principalHash: hashOpaque(principal),
      resource: THINGS_RESOURCE,
      scopes: ["things.read", "things.write", "things.admin"],
      nonceHash: hashOpaque(nonce),
      expiresAt: now + 10_000,
    },
    now,
  );
  store.consumeStateAndIssueCode(
    hashOpaque(state),
    hashOpaque(code),
    now + 5_000,
    { principalHash: hashOpaque(principal), nonceHash: hashOpaque(nonce) },
    now,
  );
  return { code, codeChallenge, principal, state, nonce };
}

test("creates only owner-private non-symlink OAuth state", () => {
  const fixture = createStoreFixture();
  try {
    const directory = lstatSync(fixture.paths.stateDirectory);
    const database = lstatSync(fixture.paths.databasePath);
    assert.equal(directory.mode & 0o777, 0o700);
    assert.equal(database.mode & 0o777, 0o600);
    assert.equal(database.isFile(), true);
    assert.equal(database.nlink, 1);
    assert.equal(directory.uid, process.getuid?.());
    assert.equal(database.uid, process.getuid?.());
  } finally {
    fixture.close();
  }
});

test("rejects permissive state roots and symlinked databases", () => {
  const fixture = createStoreFixture();
  const permissive = path.join(fixture.root, "permissive");
  const linked = path.join(fixture.root, "linked");
  try {
    mkdirSync(permissive, { mode: 0o700 });
    chmodSync(permissive, 0o755);
    assert.throws(
      () => resolveOAuthStatePaths({ MCPHUB_OAUTH_STATE_DIR: permissive }),
      hasCode("oauth_database_unsafe"),
    );

    mkdirSync(linked, { mode: 0o700 });
    const target = path.join(fixture.root, "target.sqlite3");
    writeFileSync(target, "");
    chmodSync(target, 0o600);
    symlinkSync(target, path.join(linked, "oauth.sqlite3"));
    assert.throws(
      () => new OAuthSqliteStore(resolveOAuthStatePaths({ MCPHUB_OAUTH_STATE_DIR: linked })),
      hasCode("oauth_database_unsafe"),
    );
  } finally {
    fixture.close();
  }
});

test("binds state and code atomically and persists only opaque hashes", () => {
  const fixture = createStoreFixture();
  const now = 1_000_000;
  try {
    const state = randomOpaque();
    const nonce = randomOpaque();
    const principal = randomOpaque();
    fixture.store.putAuthorizationTransaction(
      {
        stateHash: hashOpaque(state),
        clientId: "client-opaque",
        registrationMode: "cimd",
        redirectUri: "https://chatgpt.com/connector_platform_oauth_redirect",
        codeChallenge: randomOpaque(),
        principalHash: hashOpaque(principal),
        resource: THINGS_RESOURCE,
        scopes: ["things.read", "things.write", "things.admin"],
        nonceHash: hashOpaque(nonce),
        expiresAt: now + 10_000,
      },
      now,
    );
    assert.throws(
      () =>
        fixture.store.consumeStateAndIssueCode(
          hashOpaque(state),
          hashOpaque(randomOpaque()),
          now + 1_000,
          { principalHash: hashOpaque("substituted"), nonceHash: hashOpaque(nonce) },
          now,
        ),
      hasCode("oauth_grant_binding_mismatch"),
    );
    const code = randomOpaque();
    fixture.store.consumeStateAndIssueCode(
      hashOpaque(state),
      hashOpaque(code),
      now + 1_000,
      { principalHash: hashOpaque(principal), nonceHash: hashOpaque(nonce) },
      now,
    );
    assert.throws(
      () =>
        fixture.store.consumeStateAndIssueCode(
          hashOpaque(state),
          hashOpaque(randomOpaque()),
          now + 1_000,
          { principalHash: hashOpaque(principal), nonceHash: hashOpaque(nonce) },
          now,
        ),
      hasCode("oauth_state_invalid"),
    );
    fixture.store.close();
    const databaseBytes = readFileSync(fixture.paths.databasePath);
    for (const secret of [state, nonce, principal, code]) {
      assert.equal(databaseBytes.includes(Buffer.from(secret, "utf8")), false);
    }
  } finally {
    fixture.close();
  }
});

test("rotates refresh tokens and commits family revocation on replay", () => {
  const fixture = createStoreFixture();
  const now = 2_000_000;
  try {
    const grant = insertGrant(fixture.store, now);
    const accessOne = randomOpaque();
    const refreshOne = randomOpaque();
    const family = randomOpaque();
    fixture.store.exchangeCode(
      hashOpaque(grant.code),
      {
        clientId: "client-1",
        registrationMode: "dcr",
        redirectUri: "https://chatgpt.com/connector_platform_oauth_redirect",
        codeChallenge: grant.codeChallenge,
        resource: THINGS_RESOURCE,
      },
      {
        accessTokenHash: hashOpaque(accessOne),
        accessExpiresAt: now + 20_000,
        refreshTokenHash: hashOpaque(refreshOne),
        refreshExpiresAt: now + 40_000,
        familyHash: hashOpaque(family),
      },
      now,
    );
    const accessTwo = randomOpaque();
    const refreshTwo = randomOpaque();
    fixture.store.rotateRefreshToken(
      hashOpaque(refreshOne),
      { clientId: "client-1", resource: THINGS_RESOURCE },
      {
        accessTokenHash: hashOpaque(accessTwo),
        accessExpiresAt: now + 25_000,
        refreshTokenHash: hashOpaque(refreshTwo),
        refreshExpiresAt: now + 45_000,
        familyHash: hashOpaque(randomOpaque()),
      },
      now + 1,
    );
    assert.throws(
      () =>
        fixture.store.rotateRefreshToken(
          hashOpaque(refreshOne),
          { clientId: "client-1", resource: THINGS_RESOURCE },
          {
            accessTokenHash: hashOpaque(randomOpaque()),
            accessExpiresAt: now + 30_000,
            refreshTokenHash: hashOpaque(randomOpaque()),
            refreshExpiresAt: now + 50_000,
            familyHash: hashOpaque(randomOpaque()),
          },
          now + 2,
        ),
      hasCode("oauth_refresh_replayed"),
    );
    assert.throws(
      () => fixture.store.validateAccessToken(hashOpaque(accessTwo), THINGS_RESOURCE, now + 3),
      hasCode("oauth_token_revoked"),
    );
    assert.throws(
      () =>
        fixture.store.rotateRefreshToken(
          hashOpaque(refreshTwo),
          { clientId: "client-1", resource: THINGS_RESOURCE },
          {
            accessTokenHash: hashOpaque(randomOpaque()),
            accessExpiresAt: now + 30_000,
            refreshTokenHash: hashOpaque(randomOpaque()),
            refreshExpiresAt: now + 50_000,
            familyHash: hashOpaque(randomOpaque()),
          },
          now + 3,
        ),
      hasCode("oauth_refresh_invalid"),
    );
  } finally {
    fixture.close();
  }
});

test("persists rate limits and one-time JWT identifiers across reopen", () => {
  const fixture = createStoreFixture();
  const now = 3_000_000;
  try {
    fixture.store.consumeRateLimit("login:account:ip", { limit: 1, windowMs: 60_000 }, now);
    fixture.store.consumeJwtJti("client", "jti-value", now + 60_000, now);
    fixture.store.close();
    const reopened = new OAuthSqliteStore(fixture.paths);
    try {
      assert.throws(
        () => reopened.consumeRateLimit("login:account:ip", { limit: 1, windowMs: 60_000 }, now + 1),
        hasCode("oauth_rate_limited"),
      );
      assert.throws(
        () => reopened.consumeJwtJti("client", "jti-value", now + 60_000, now + 1),
        hasCode("oauth_client_assertion_replayed"),
      );
    } finally {
      reopened.close();
    }
  } finally {
    fixture.close();
  }
});

test("requires explicit initialization and fails closed on deletion and older epochs", () => {
  const root = path.join(process.env.TMPDIR ?? "/tmp", `oauth-explicit-${randomOpaque()}`);
  mkdirSync(root, { mode: 0o700 });
  const stateDirectory = path.join(root, "state");
  const paths = resolveOAuthStatePaths({ MCPHUB_OAUTH_STATE_DIR: stateDirectory });
  assert.throws(() => new OAuthSqliteStore(paths), hasCode("oauth_database_unsafe"));
  assert.equal(lstatSync(stateDirectory).isDirectory(), true);
  assert.throws(() => lstatSync(paths.databasePath));

  const initialized = OAuthSqliteStore.initialize(paths, 123_456);
  initialized.close();
  const receipt = JSON.parse(readFileSync(paths.initializationReceiptPath, "utf8")) as Record<
    string,
    unknown
  >;
  assert.deepEqual(Object.keys(receipt).sort(), [
    "databaseId",
    "initializedAt",
    "rollbackExcluded",
    "schemaEpoch",
  ]);
  assert.equal(receipt.rollbackExcluded, true);
  assert.equal(receipt.schemaEpoch, 2);

  const db = new DatabaseSync(paths.databasePath);
  db.prepare("UPDATE oauth_store_metadata SET schema_epoch = 1 WHERE singleton = 1").run();
  db.close();
  assert.throws(() => new OAuthSqliteStore(paths), hasCode("oauth_database_unsafe"));

  unlinkSync(paths.databasePath);
  assert.throws(() => new OAuthSqliteStore(paths), hasCode("oauth_database_unsafe"));
  assert.throws(() => lstatSync(paths.databasePath));
  rmSync(root, { recursive: true, force: true });
});

test("detects chmod, symlink, and open/path replacement before transactions", () => {
  const databaseFixture = createStoreFixture();
  try {
    const replacement = path.join(databaseFixture.paths.stateDirectory, "replacement.sqlite3");
    const displaced = path.join(databaseFixture.paths.stateDirectory, "displaced.sqlite3");
    copyFileSync(databaseFixture.paths.databasePath, replacement);
    chmodSync(replacement, 0o600);
    renameSync(databaseFixture.paths.databasePath, displaced);
    renameSync(replacement, databaseFixture.paths.databasePath);
    assert.throws(
      () => databaseFixture.store.consumeRateLimit("swap", { limit: 2, windowMs: 1_000 }, 1),
      hasCode("oauth_database_unsafe"),
    );
  } finally {
    databaseFixture.close();
  }

  const receiptFixture = createStoreFixture();
  try {
    const replacement = path.join(receiptFixture.paths.stateDirectory, "replacement-receipt.json");
    const displaced = path.join(receiptFixture.paths.stateDirectory, "displaced-receipt.json");
    copyFileSync(receiptFixture.paths.initializationReceiptPath, replacement);
    chmodSync(replacement, 0o600);
    renameSync(receiptFixture.paths.initializationReceiptPath, displaced);
    renameSync(replacement, receiptFixture.paths.initializationReceiptPath);
    assert.throws(
      () => receiptFixture.store.consumeRateLimit("receipt-swap", { limit: 2, windowMs: 1_000 }, 1),
      hasCode("oauth_database_unsafe"),
    );
  } finally {
    receiptFixture.close();
  }

  const permissionFixture = createStoreFixture();
  try {
    chmodSync(permissionFixture.paths.databasePath, 0o644);
    assert.throws(
      () => permissionFixture.store.consumeRateLimit("chmod", { limit: 2, windowMs: 1_000 }, 1),
      hasCode("oauth_database_unsafe"),
    );
  } finally {
    permissionFixture.close();
  }

  const directoryModeFixture = createStoreFixture();
  try {
    chmodSync(directoryModeFixture.paths.stateDirectory, 0o755);
    assert.throws(
      () => directoryModeFixture.store.consumeRateLimit("dir-chmod", { limit: 2, windowMs: 1_000 }, 1),
      hasCode("oauth_database_unsafe"),
    );
  } finally {
    directoryModeFixture.close();
  }

  const receiptSymlinkFixture = createStoreFixture();
  try {
    receiptSymlinkFixture.store.close();
    const displacedReceipt = path.join(
      receiptSymlinkFixture.paths.stateDirectory,
      "displaced-init-receipt.json",
    );
    renameSync(receiptSymlinkFixture.paths.initializationReceiptPath, displacedReceipt);
    symlinkSync(displacedReceipt, receiptSymlinkFixture.paths.initializationReceiptPath);
    assert.throws(
      () => new OAuthSqliteStore(receiptSymlinkFixture.paths),
      hasCode("oauth_database_unsafe"),
    );
  } finally {
    receiptSymlinkFixture.close();
  }

  const directoryFixture = createStoreFixture();
  try {
    const displacedState = `${directoryFixture.paths.stateDirectory}-displaced`;
    renameSync(directoryFixture.paths.stateDirectory, displacedState);
    mkdirSync(directoryFixture.paths.stateDirectory, { mode: 0o700 });
    assert.throws(
      () => directoryFixture.store.consumeRateLimit("directory", { limit: 2, windowMs: 1_000 }, 1),
      hasCode("oauth_database_unsafe"),
    );
  } finally {
    directoryFixture.close();
  }
});

test("uses the server nonce as the unique authorization handle, independent of client state", () => {
  const fixture = createStoreFixture();
  const now = 4_000_000;
  const stateHash = hashOpaque("predictable-client-state");
  const principalHash = hashOpaque("principal");
  try {
    for (const nonce of ["server-nonce-one", "server-nonce-two"]) {
      fixture.store.putAuthorizationTransaction(
        {
          stateHash,
          clientId: "client",
          registrationMode: "dcr",
          redirectUri: "https://chatgpt.com/connector_platform_oauth_redirect",
          codeChallenge: randomOpaque(),
          principalHash,
          resource: THINGS_RESOURCE,
          scopes: ["things.read", "things.write", "things.admin"],
          nonceHash: hashOpaque(nonce),
          expiresAt: now + 10_000,
        },
        now,
      );
      fixture.store.consumeStateAndIssueCode(
        stateHash,
        hashOpaque(`code-${nonce}`),
        now + 5_000,
        { principalHash, nonceHash: hashOpaque(nonce) },
        now,
      );
    }
  } finally {
    fixture.close();
  }
});

test("binds idempotent access and refresh revocation to client and resource", () => {
  const fixture = createStoreFixture();
  const now = 5_000_000;
  try {
    const grant = insertGrant(fixture.store, now);
    const access = randomOpaque();
    const refresh = randomOpaque();
    fixture.store.exchangeCode(
      hashOpaque(grant.code),
      {
        clientId: "client-1",
        registrationMode: "dcr",
        redirectUri: "https://chatgpt.com/connector_platform_oauth_redirect",
        codeChallenge: grant.codeChallenge,
        resource: THINGS_RESOURCE,
      },
      {
        accessTokenHash: hashOpaque(access),
        accessExpiresAt: now + 20_000,
        refreshTokenHash: hashOpaque(refresh),
        refreshExpiresAt: now + 40_000,
        familyHash: hashOpaque(randomOpaque()),
      },
      now,
    );
    fixture.store.revokeToken(
      hashOpaque(access),
      { clientId: "substituted-client", resource: THINGS_RESOURCE },
      now + 1,
    );
    assert.equal(
      fixture.store.validateAccessToken(hashOpaque(access), THINGS_RESOURCE, now + 2).clientId,
      "client-1",
    );
    fixture.store.revokeToken(
      hashOpaque(refresh),
      { clientId: "substituted-client", resource: THINGS_RESOURCE },
      now + 3,
    );
    assert.equal(
      fixture.store.validateAccessToken(hashOpaque(access), THINGS_RESOURCE, now + 4).clientId,
      "client-1",
    );
    fixture.store.revokeToken(
      hashOpaque(refresh),
      { clientId: "client-1", resource: THINGS_RESOURCE },
      now + 5,
    );
    assert.throws(
      () => fixture.store.validateAccessToken(hashOpaque(access), THINGS_RESOURCE, now + 6),
      hasCode("oauth_token_revoked"),
    );
    fixture.store.revokeToken(
      hashOpaque(refresh),
      { clientId: "client-1", resource: THINGS_RESOURCE },
      now + 7,
    );
  } finally {
    fixture.close();
  }
});
