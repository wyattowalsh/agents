import { DatabaseSync } from "node:sqlite";
import { lstatSync } from "node:fs";

import {
  REFRESH_TOKEN_ABSOLUTE_TTL_MS,
  THINGS_RESOURCE,
  type OAuthScope,
  type RegistrationMode,
} from "../policy/oauth-policy.js";
import { constantTimeTextEqual, hashOpaque, randomOpaque } from "../security/common/crypto.js";
import { OAuthSecurityError } from "../security/common/errors.js";
import {
  assertRetainedSecureDescriptor,
  closeSecureDescriptor,
  createSecureFile,
  readRetainedSecureFile,
  retainSecureDirectory,
  retainSecureFile,
  resolveOAuthStatePaths,
  type OAuthStatePaths,
  type RetainedSecureDescriptor,
} from "../security/common/files.js";
import type {
  AccessTokenClaims,
  AuthorizationCodeGrant,
  AuthorizationTransaction,
  RateLimitRule,
} from "./types.js";

interface TokenMaterial {
  readonly accessTokenHash: string;
  readonly accessExpiresAt: number;
  readonly refreshTokenHash: string;
  readonly refreshExpiresAt: number;
  readonly familyHash: string;
}

interface CodeExchangeBinding {
  readonly clientId: string;
  readonly registrationMode: RegistrationMode;
  readonly redirectUri: string;
  readonly codeChallenge: string;
  readonly resource: string;
}

interface RefreshRotationBinding {
  readonly clientId: string;
  readonly resource: string;
}

interface BrowserSessionRow {
  readonly principalHash: string;
  readonly nonceHash: string;
  readonly expiresAt: number;
  readonly authenticated: boolean;
  readonly csrfConsumed: boolean;
  readonly revoked: boolean;
}

type RefreshRotationOutcome =
  | {
      readonly kind: "ok";
      readonly claims: AccessTokenClaims & {
        readonly generation: number;
        readonly absoluteExpiresAt: number;
        readonly refreshExpiresAt: number;
      };
    }
  | {
      readonly kind: "rejected";
      readonly code:
        | "oauth_grant_binding_mismatch"
        | "oauth_refresh_expired"
        | "oauth_refresh_replayed";
    };

type SqlRow = Record<string, unknown>;

const OAUTH_DATABASE_SCHEMA_EPOCH = 2;
const INITIALIZE = Symbol("oauth-sqlite-initialize");

interface InitializationReceipt {
  readonly databaseId: string;
  readonly initializedAt: number;
  readonly rollbackExcluded: true;
  readonly schemaEpoch: typeof OAUTH_DATABASE_SCHEMA_EPOCH;
}

function parseInitializationReceipt(value: string): InitializationReceipt {
  let parsed: unknown;
  try {
    parsed = JSON.parse(value);
  } catch {
    throw new OAuthSecurityError("oauth_database_unsafe", { httpStatus: 503 });
  }
  if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new OAuthSecurityError("oauth_database_unsafe", { httpStatus: 503 });
  }
  const record = parsed as Record<string, unknown>;
  if (
    Object.keys(record).sort().join(",") !== "databaseId,initializedAt,rollbackExcluded,schemaEpoch" ||
    typeof record.databaseId !== "string" ||
    !/^[A-Za-z0-9_-]{43}$/.test(record.databaseId) ||
    typeof record.initializedAt !== "number" ||
    !Number.isSafeInteger(record.initializedAt) ||
    record.rollbackExcluded !== true ||
    record.schemaEpoch !== OAUTH_DATABASE_SCHEMA_EPOCH
  ) {
    throw new OAuthSecurityError("oauth_database_unsafe", { httpStatus: 503 });
  }
  return Object.freeze({
    databaseId: record.databaseId,
    initializedAt: record.initializedAt,
    rollbackExcluded: true,
    schemaEpoch: OAUTH_DATABASE_SCHEMA_EPOCH,
  });
}

function asRow(value: unknown): SqlRow {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw new OAuthSecurityError("oauth_database_unsafe", { httpStatus: 503 });
  }
  return value as SqlRow;
}

function stringField(row: SqlRow, name: string): string {
  const value = row[name];
  if (typeof value !== "string") {
    throw new OAuthSecurityError("oauth_database_unsafe", { httpStatus: 503 });
  }
  return value;
}

function numberField(row: SqlRow, name: string): number {
  const value = row[name];
  if (typeof value !== "number" || !Number.isSafeInteger(value)) {
    throw new OAuthSecurityError("oauth_database_unsafe", { httpStatus: 503 });
  }
  return value;
}

function nullableNumberField(row: SqlRow, name: string): number | null {
  const value = row[name];
  if (value === null) {
    return null;
  }
  return numberField(row, name);
}

function registrationModeField(row: SqlRow): RegistrationMode {
  const mode = stringField(row, "registration_mode");
  if (mode !== "cimd" && mode !== "dcr") {
    throw new OAuthSecurityError("oauth_database_unsafe", { httpStatus: 503 });
  }
  return mode;
}

function scopesField(row: SqlRow): readonly OAuthScope[] {
  let parsed: unknown;
  try {
    parsed = JSON.parse(stringField(row, "scopes_json"));
  } catch {
    throw new OAuthSecurityError("oauth_database_unsafe", { httpStatus: 503 });
  }
  if (
    !Array.isArray(parsed) ||
    parsed.some(
      (scope) =>
        scope !== "things.read" &&
        scope !== "things.write" &&
        scope !== "things.admin" &&
        scope !== "offline_access",
    )
  ) {
    throw new OAuthSecurityError("oauth_database_unsafe", { httpStatus: 503 });
  }
  return parsed;
}

function scopesJson(scopes: readonly OAuthScope[]): string {
  return JSON.stringify(scopes);
}

function boolField(row: SqlRow, name: string): boolean {
  const value = numberField(row, name);
  if (value !== 0 && value !== 1) {
    throw new OAuthSecurityError("oauth_database_unsafe", { httpStatus: 503 });
  }
  return value === 1;
}

export class OAuthSqliteStore {
  readonly paths: OAuthStatePaths;
  readonly #database: DatabaseSync;
  readonly #databaseDescriptor: RetainedSecureDescriptor;
  readonly #directoryDescriptor: RetainedSecureDescriptor;
  readonly #receiptDescriptor: RetainedSecureDescriptor;
  readonly #receiptHash: string;
  #closed = false;

  static initialize(paths: OAuthStatePaths = resolveOAuthStatePaths(), now = Date.now()): OAuthSqliteStore {
    const receipt: InitializationReceipt = Object.freeze({
      databaseId: randomOpaque(),
      initializedAt: now,
      rollbackExcluded: true,
      schemaEpoch: OAUTH_DATABASE_SCHEMA_EPOCH,
    });
    createSecureFile(paths.databasePath);
    createSecureFile(paths.initializationReceiptPath, JSON.stringify(receipt));
    return new OAuthSqliteStore(paths, INITIALIZE);
  }

  static openOrInitialize(paths: OAuthStatePaths = resolveOAuthStatePaths()): OAuthSqliteStore {
    const exists = (pathname: string): boolean => {
      try {
        lstatSync(pathname);
        return true;
      } catch (error) {
        const code = error instanceof Error && "code" in error ? error.code : undefined;
        if (code === "ENOENT") return false;
        throw new OAuthSecurityError("oauth_database_unsafe", { httpStatus: 503 });
      }
    };
    const databaseExists = exists(paths.databasePath);
    const receiptExists = exists(paths.initializationReceiptPath);
    if (!databaseExists && !receiptExists) return OAuthSqliteStore.initialize(paths);
    if (databaseExists && receiptExists) return new OAuthSqliteStore(paths);
    throw new OAuthSecurityError("oauth_database_unsafe", { httpStatus: 503 });
  }

  constructor(paths: OAuthStatePaths = resolveOAuthStatePaths(), initializationKey?: symbol) {
    this.paths = paths;
    this.#directoryDescriptor = retainSecureDirectory(paths.stateDirectory);
    try {
      this.#databaseDescriptor = retainSecureFile(paths.databasePath);
      this.#receiptDescriptor = retainSecureFile(paths.initializationReceiptPath);
    } catch (error) {
      closeSecureDescriptor(this.#directoryDescriptor);
      throw error;
    }
    const receiptText = readRetainedSecureFile(this.#receiptDescriptor);
    const receipt = parseInitializationReceipt(receiptText);
    this.#receiptHash = hashOpaque(receiptText);
    try {
      this.#database = new DatabaseSync(paths.databasePath, {
        allowExtension: false,
        enableForeignKeyConstraints: true,
        timeout: 5_000,
      });
    } catch {
      closeSecureDescriptor(this.#receiptDescriptor);
      closeSecureDescriptor(this.#databaseDescriptor);
      closeSecureDescriptor(this.#directoryDescriptor);
      throw new OAuthSecurityError("oauth_database_unsafe", { httpStatus: 503 });
    }
    try {
      this.#assertDescriptors();
      this.#database.exec(`
      PRAGMA trusted_schema = OFF;
      PRAGMA foreign_keys = ON;
      PRAGMA journal_mode = DELETE;
      PRAGMA synchronous = FULL;
      PRAGMA secure_delete = ON;
      PRAGMA temp_store = MEMORY;
      PRAGMA busy_timeout = 5000;
    `);
      if (initializationKey === INITIALIZE) {
        this.#database.exec(`
      CREATE TABLE IF NOT EXISTS oauth_store_metadata (
        singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
        schema_epoch INTEGER NOT NULL,
        initialization_receipt_hash TEXT NOT NULL CHECK(length(initialization_receipt_hash) = 64),
        database_id_hash TEXT NOT NULL CHECK(length(database_id_hash) = 64),
        rollback_excluded INTEGER NOT NULL CHECK(rollback_excluded = 1),
        initialized_at INTEGER NOT NULL
      ) STRICT;

      CREATE TABLE IF NOT EXISTS authorization_transactions (
        nonce_hash TEXT PRIMARY KEY CHECK(length(nonce_hash) = 64),
        state_hash TEXT NOT NULL CHECK(length(state_hash) = 64),
        client_id TEXT NOT NULL,
        registration_mode TEXT NOT NULL CHECK(registration_mode IN ('cimd', 'dcr')),
        redirect_uri TEXT NOT NULL,
        code_challenge TEXT NOT NULL,
        principal_hash TEXT NOT NULL CHECK(length(principal_hash) = 64),
        resource TEXT NOT NULL CHECK(resource = '${THINGS_RESOURCE}'),
        scopes_json TEXT NOT NULL,
        created_at INTEGER NOT NULL,
        expires_at INTEGER NOT NULL,
        consumed_at INTEGER
      ) STRICT;

      CREATE TABLE IF NOT EXISTS authorization_codes (
        code_hash TEXT PRIMARY KEY CHECK(length(code_hash) = 64),
        nonce_hash TEXT NOT NULL REFERENCES authorization_transactions(nonce_hash),
        state_hash TEXT NOT NULL CHECK(length(state_hash) = 64),
        client_id TEXT NOT NULL,
        registration_mode TEXT NOT NULL CHECK(registration_mode IN ('cimd', 'dcr')),
        redirect_uri TEXT NOT NULL,
        code_challenge TEXT NOT NULL,
        principal_hash TEXT NOT NULL CHECK(length(principal_hash) = 64),
        resource TEXT NOT NULL CHECK(resource = '${THINGS_RESOURCE}'),
        scopes_json TEXT NOT NULL,
        created_at INTEGER NOT NULL,
        expires_at INTEGER NOT NULL,
        consumed_at INTEGER
      ) STRICT;

      CREATE TABLE IF NOT EXISTS token_families (
        family_hash TEXT PRIMARY KEY CHECK(length(family_hash) = 64),
        client_id TEXT NOT NULL,
        principal_hash TEXT NOT NULL CHECK(length(principal_hash) = 64),
        resource TEXT NOT NULL CHECK(resource = '${THINGS_RESOURCE}'),
        scopes_json TEXT NOT NULL,
        created_at INTEGER NOT NULL,
        absolute_expires_at INTEGER NOT NULL,
        revoked_at INTEGER
      ) STRICT;

      CREATE TABLE IF NOT EXISTS access_tokens (
        token_hash TEXT PRIMARY KEY CHECK(length(token_hash) = 64),
        family_hash TEXT NOT NULL REFERENCES token_families(family_hash),
        client_id TEXT NOT NULL,
        principal_hash TEXT NOT NULL CHECK(length(principal_hash) = 64),
        resource TEXT NOT NULL CHECK(resource = '${THINGS_RESOURCE}'),
        scopes_json TEXT NOT NULL,
        created_at INTEGER NOT NULL,
        expires_at INTEGER NOT NULL,
        revoked_at INTEGER
      ) STRICT;

      CREATE TABLE IF NOT EXISTS refresh_tokens (
        token_hash TEXT PRIMARY KEY CHECK(length(token_hash) = 64),
        family_hash TEXT NOT NULL REFERENCES token_families(family_hash),
        generation INTEGER NOT NULL CHECK(generation >= 0),
        created_at INTEGER NOT NULL,
        expires_at INTEGER NOT NULL,
        consumed_at INTEGER,
        revoked_at INTEGER
      ) STRICT;

      CREATE TABLE IF NOT EXISTS dcr_clients (
        client_id TEXT PRIMARY KEY,
        secret_hash TEXT NOT NULL CHECK(length(secret_hash) = 64),
        metadata_digest TEXT NOT NULL CHECK(length(metadata_digest) = 64),
        redirect_uri TEXT NOT NULL,
        principal_hash TEXT NOT NULL CHECK(length(principal_hash) = 64),
        resource TEXT NOT NULL CHECK(resource = '${THINGS_RESOURCE}'),
        created_at INTEGER NOT NULL,
        revoked_at INTEGER
      ) STRICT;

      CREATE TABLE IF NOT EXISTS jwt_jti_replay (
        jti_hash TEXT PRIMARY KEY CHECK(length(jti_hash) = 64),
        client_id TEXT NOT NULL,
        expires_at INTEGER NOT NULL
      ) STRICT;

      CREATE TABLE IF NOT EXISTS browser_sessions (
        session_hash TEXT PRIMARY KEY CHECK(length(session_hash) = 64),
        principal_hash TEXT NOT NULL CHECK(length(principal_hash) = 64),
        csrf_hash TEXT NOT NULL CHECK(length(csrf_hash) = 64),
        nonce_hash TEXT NOT NULL CHECK(length(nonce_hash) = 64),
        authenticated INTEGER NOT NULL CHECK(authenticated IN (0, 1)),
        csrf_consumed INTEGER NOT NULL CHECK(csrf_consumed IN (0, 1)),
        created_at INTEGER NOT NULL,
        expires_at INTEGER NOT NULL,
        revoked_at INTEGER
      ) STRICT;

      CREATE TABLE IF NOT EXISTS rate_limits (
        bucket_hash TEXT PRIMARY KEY CHECK(length(bucket_hash) = 64),
        window_started_at INTEGER NOT NULL,
        window_ms INTEGER NOT NULL CHECK(window_ms > 0),
        attempt_count INTEGER NOT NULL CHECK(attempt_count > 0),
        expires_at INTEGER NOT NULL
      ) STRICT;

      CREATE INDEX IF NOT EXISTS access_tokens_family_idx ON access_tokens(family_hash);
      CREATE INDEX IF NOT EXISTS refresh_tokens_family_idx ON refresh_tokens(family_hash);
      CREATE INDEX IF NOT EXISTS rate_limits_expiry_idx ON rate_limits(expires_at);
      CREATE INDEX IF NOT EXISTS jwt_jti_expiry_idx ON jwt_jti_replay(expires_at);
    `);
        this.#database
          .prepare(`
          INSERT INTO oauth_store_metadata (
            singleton, schema_epoch, initialization_receipt_hash, database_id_hash,
            rollback_excluded, initialized_at
          ) VALUES (1, ?, ?, ?, 1, ?)
        `)
          .run(
            OAUTH_DATABASE_SCHEMA_EPOCH,
            this.#receiptHash,
            hashOpaque(receipt.databaseId),
            receipt.initializedAt,
          );
      } else if (initializationKey !== undefined) {
        throw new OAuthSecurityError("oauth_database_unsafe", { httpStatus: 503 });
      }
      this.#assertDescriptors();
      const metadata = this.#database
        .prepare("SELECT * FROM oauth_store_metadata WHERE singleton = 1")
        .get();
      if (metadata === undefined) {
        throw new OAuthSecurityError("oauth_database_unsafe", { httpStatus: 503 });
      }
      const metadataRow = asRow(metadata);
      if (
        numberField(metadataRow, "schema_epoch") !== OAUTH_DATABASE_SCHEMA_EPOCH ||
        !constantTimeTextEqual(
          stringField(metadataRow, "initialization_receipt_hash"),
          this.#receiptHash,
        ) ||
        !constantTimeTextEqual(
          stringField(metadataRow, "database_id_hash"),
          hashOpaque(receipt.databaseId),
        ) ||
        numberField(metadataRow, "rollback_excluded") !== 1 ||
        numberField(metadataRow, "initialized_at") !== receipt.initializedAt
      ) {
        throw new OAuthSecurityError("oauth_database_unsafe", { httpStatus: 503 });
      }
    } catch (error) {
      this.close();
      if (error instanceof OAuthSecurityError) {
        throw error;
      }
      throw new OAuthSecurityError("oauth_database_unsafe", { httpStatus: 503 });
    }
  }

  close(): void {
    if (!this.#closed) {
      this.#database.close();
      closeSecureDescriptor(this.#receiptDescriptor);
      closeSecureDescriptor(this.#databaseDescriptor);
      closeSecureDescriptor(this.#directoryDescriptor);
      this.#closed = true;
    }
  }

  #assertDescriptors(): void {
    if (this.#closed) {
      throw new OAuthSecurityError("oauth_database_unsafe", { httpStatus: 503 });
    }
    assertRetainedSecureDescriptor(this.#directoryDescriptor);
    assertRetainedSecureDescriptor(this.#databaseDescriptor);
    assertRetainedSecureDescriptor(this.#receiptDescriptor);
  }

  #assertSafe(): void {
    this.#assertDescriptors();
    const receiptText = readRetainedSecureFile(this.#receiptDescriptor);
    if (!constantTimeTextEqual(hashOpaque(receiptText), this.#receiptHash)) {
      throw new OAuthSecurityError("oauth_database_unsafe", { httpStatus: 503 });
    }
  }

  #transaction<T>(operation: () => T): T {
    this.#assertSafe();
    this.#database.exec("BEGIN IMMEDIATE");
    try {
      const result = operation();
      this.#assertSafe();
      this.#database.exec("COMMIT");
      this.#assertSafe();
      return result;
    } catch (error) {
      try {
        this.#database.exec("ROLLBACK");
      } catch {
        // Preserve the original content-free failure.
      }
      if (error instanceof OAuthSecurityError) {
        throw error;
      }
      throw new OAuthSecurityError("oauth_database_unsafe", { httpStatus: 503 });
    }
  }

  #read<T>(operation: () => T): T {
    this.#assertSafe();
    try {
      const result = operation();
      this.#assertSafe();
      return result;
    } catch (error) {
      if (error instanceof OAuthSecurityError) {
        throw error;
      }
      throw new OAuthSecurityError("oauth_database_unsafe", { httpStatus: 503 });
    }
  }

  putAuthorizationTransaction(transaction: AuthorizationTransaction, now: number): void {
    this.#transaction(() => {
      this.#database
        .prepare(`
          INSERT INTO authorization_transactions (
            state_hash, client_id, registration_mode, redirect_uri, code_challenge,
            principal_hash, resource, scopes_json, nonce_hash, created_at, expires_at
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `)
        .run(
          transaction.stateHash,
          transaction.clientId,
          transaction.registrationMode,
          transaction.redirectUri,
          transaction.codeChallenge,
          transaction.principalHash,
          transaction.resource,
          scopesJson(transaction.scopes),
          transaction.nonceHash,
          now,
          transaction.expiresAt,
        );
    });
  }

  consumeStateAndIssueCode(
    stateHash: string,
    codeHash: string,
    codeExpiresAt: number,
    binding: { readonly principalHash: string; readonly nonceHash: string },
    now: number,
  ): AuthorizationCodeGrant {
    return this.#transaction(() => {
      const raw = this.#database
        .prepare("SELECT * FROM authorization_transactions WHERE nonce_hash = ?")
        .get(binding.nonceHash);
      if (raw === undefined) {
        throw new OAuthSecurityError("oauth_state_invalid", { oauthError: "invalid_grant" });
      }
      const row = asRow(raw);
      if (nullableNumberField(row, "consumed_at") !== null) {
        throw new OAuthSecurityError("oauth_state_invalid", { oauthError: "invalid_grant" });
      }
      if (numberField(row, "expires_at") <= now) {
        throw new OAuthSecurityError("oauth_state_expired", { oauthError: "invalid_grant" });
      }
      if (
        !constantTimeTextEqual(stringField(row, "state_hash"), stateHash) ||
        !constantTimeTextEqual(stringField(row, "principal_hash"), binding.principalHash) ||
        !constantTimeTextEqual(stringField(row, "nonce_hash"), binding.nonceHash)
      ) {
        throw new OAuthSecurityError("oauth_grant_binding_mismatch", { oauthError: "invalid_grant" });
      }
      this.#database
        .prepare("UPDATE authorization_transactions SET consumed_at = ? WHERE nonce_hash = ? AND consumed_at IS NULL")
        .run(now, binding.nonceHash);
      this.#database
        .prepare(`
          INSERT INTO authorization_codes (
            code_hash, nonce_hash, state_hash, client_id, registration_mode, redirect_uri,
            code_challenge, principal_hash, resource, scopes_json, created_at, expires_at
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `)
        .run(
          codeHash,
          binding.nonceHash,
          stateHash,
          stringField(row, "client_id"),
          registrationModeField(row),
          stringField(row, "redirect_uri"),
          stringField(row, "code_challenge"),
          stringField(row, "principal_hash"),
          stringField(row, "resource"),
          stringField(row, "scopes_json"),
          now,
          codeExpiresAt,
        );
      return {
        codeHash,
        clientId: stringField(row, "client_id"),
        registrationMode: registrationModeField(row),
        redirectUri: stringField(row, "redirect_uri"),
        codeChallenge: stringField(row, "code_challenge"),
        principalHash: stringField(row, "principal_hash"),
        resource: stringField(row, "resource"),
        scopes: scopesField(row),
        expiresAt: codeExpiresAt,
      };
    });
  }

  consumeStateForDenial(
    stateHash: string,
    binding: { readonly principalHash: string; readonly nonceHash: string },
    now: number,
  ): Readonly<{ redirectUri: string }> {
    return this.#transaction(() => {
      const raw = this.#database
        .prepare("SELECT * FROM authorization_transactions WHERE nonce_hash = ?")
        .get(binding.nonceHash);
      if (raw === undefined) {
        throw new OAuthSecurityError("oauth_state_invalid", { oauthError: "invalid_grant" });
      }
      const row = asRow(raw);
      if (nullableNumberField(row, "consumed_at") !== null) {
        throw new OAuthSecurityError("oauth_state_invalid", { oauthError: "invalid_grant" });
      }
      if (numberField(row, "expires_at") <= now) {
        throw new OAuthSecurityError("oauth_state_expired", { oauthError: "invalid_grant" });
      }
      if (
        !constantTimeTextEqual(stringField(row, "state_hash"), stateHash) ||
        !constantTimeTextEqual(stringField(row, "principal_hash"), binding.principalHash) ||
        !constantTimeTextEqual(stringField(row, "nonce_hash"), binding.nonceHash)
      ) {
        throw new OAuthSecurityError("oauth_grant_binding_mismatch", { oauthError: "invalid_grant" });
      }
      const updated = this.#database
        .prepare(
          "UPDATE authorization_transactions SET consumed_at = ? WHERE nonce_hash = ? AND consumed_at IS NULL",
        )
        .run(now, binding.nonceHash);
      if (updated.changes !== 1) {
        throw new OAuthSecurityError("oauth_state_invalid", { oauthError: "invalid_grant" });
      }
      return Object.freeze({ redirectUri: stringField(row, "redirect_uri") });
    });
  }

  exchangeCode(
    codeHash: string,
    binding: CodeExchangeBinding,
    tokens: TokenMaterial,
    now: number,
  ): AuthorizationCodeGrant {
    return this.#transaction(() => {
      const raw = this.#database.prepare("SELECT * FROM authorization_codes WHERE code_hash = ?").get(codeHash);
      if (raw === undefined) {
        throw new OAuthSecurityError("oauth_code_invalid", { oauthError: "invalid_grant" });
      }
      const row = asRow(raw);
      if (nullableNumberField(row, "consumed_at") !== null) {
        throw new OAuthSecurityError("oauth_code_invalid", { oauthError: "invalid_grant" });
      }
      if (numberField(row, "expires_at") <= now) {
        throw new OAuthSecurityError("oauth_code_expired", { oauthError: "invalid_grant" });
      }
      if (
        stringField(row, "client_id") !== binding.clientId ||
        registrationModeField(row) !== binding.registrationMode ||
        stringField(row, "redirect_uri") !== binding.redirectUri ||
        stringField(row, "code_challenge") !== binding.codeChallenge ||
        stringField(row, "resource") !== binding.resource
      ) {
        throw new OAuthSecurityError("oauth_grant_binding_mismatch", { oauthError: "invalid_grant" });
      }
      const scopes = scopesField(row);
      const principalHash = stringField(row, "principal_hash");
      this.#database
        .prepare("UPDATE authorization_codes SET consumed_at = ? WHERE code_hash = ? AND consumed_at IS NULL")
        .run(now, codeHash);
      this.#database
        .prepare(`
          INSERT INTO token_families (
            family_hash, client_id, principal_hash, resource, scopes_json,
            created_at, absolute_expires_at
          ) VALUES (?, ?, ?, ?, ?, ?, ?)
        `)
        .run(
          tokens.familyHash,
          binding.clientId,
          principalHash,
          binding.resource,
          scopesJson(scopes),
          now,
          now + REFRESH_TOKEN_ABSOLUTE_TTL_MS,
        );
      this.#insertAccessToken(tokens, binding.clientId, principalHash, binding.resource, scopes, now);
      this.#database
        .prepare(`
          INSERT INTO refresh_tokens (
            token_hash, family_hash, generation, created_at, expires_at
          ) VALUES (?, ?, 0, ?, ?)
        `)
        .run(tokens.refreshTokenHash, tokens.familyHash, now, tokens.refreshExpiresAt);
      return {
        codeHash,
        clientId: binding.clientId,
        registrationMode: binding.registrationMode,
        redirectUri: binding.redirectUri,
        codeChallenge: binding.codeChallenge,
        principalHash,
        resource: binding.resource,
        scopes,
        expiresAt: numberField(row, "expires_at"),
      };
    });
  }

  #insertAccessToken(
    tokens: TokenMaterial,
    clientId: string,
    principalHash: string,
    resource: string,
    scopes: readonly OAuthScope[],
    now: number,
  ): void {
    this.#database
      .prepare(`
        INSERT INTO access_tokens (
          token_hash, family_hash, client_id, principal_hash, resource,
          scopes_json, created_at, expires_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      `)
      .run(
        tokens.accessTokenHash,
        tokens.familyHash,
        clientId,
        principalHash,
        resource,
        scopesJson(scopes),
        now,
        tokens.accessExpiresAt,
      );
  }

  rotateRefreshToken(
    presentedHash: string,
    binding: RefreshRotationBinding,
    tokens: TokenMaterial,
    now: number,
  ): AccessTokenClaims & {
    readonly generation: number;
    readonly absoluteExpiresAt: number;
    readonly refreshExpiresAt: number;
  } {
    const outcome = this.#transaction<RefreshRotationOutcome>(() => {
      const raw = this.#database
        .prepare(`
          SELECT r.*, f.client_id, f.principal_hash, f.resource, f.scopes_json,
                 f.absolute_expires_at, f.revoked_at AS family_revoked_at
          FROM refresh_tokens r
          JOIN token_families f ON f.family_hash = r.family_hash
          WHERE r.token_hash = ?
        `)
        .get(presentedHash);
      if (raw === undefined) {
        throw new OAuthSecurityError("oauth_refresh_invalid", { oauthError: "invalid_grant" });
      }
      const row = asRow(raw);
      const familyHash = stringField(row, "family_hash");
      if (nullableNumberField(row, "consumed_at") !== null) {
        this.#revokeFamily(familyHash, now);
        return { kind: "rejected", code: "oauth_refresh_replayed" };
      }
      if (nullableNumberField(row, "revoked_at") !== null) {
        throw new OAuthSecurityError("oauth_refresh_invalid", { oauthError: "invalid_grant" });
      }
      if (nullableNumberField(row, "family_revoked_at") !== null) {
        throw new OAuthSecurityError("oauth_refresh_invalid", { oauthError: "invalid_grant" });
      }
      if (numberField(row, "expires_at") <= now || numberField(row, "absolute_expires_at") <= now) {
        this.#revokeFamily(familyHash, now);
        return { kind: "rejected", code: "oauth_refresh_expired" };
      }
      if (stringField(row, "client_id") !== binding.clientId || stringField(row, "resource") !== binding.resource) {
        this.#revokeFamily(familyHash, now);
        return { kind: "rejected", code: "oauth_grant_binding_mismatch" };
      }
      const generation = numberField(row, "generation") + 1;
      const absoluteExpiresAt = numberField(row, "absolute_expires_at");
      const refreshExpiresAt = Math.min(tokens.refreshExpiresAt, absoluteExpiresAt);
      const scopes = scopesField(row);
      const principalHash = stringField(row, "principal_hash");
      this.#database
        .prepare("UPDATE refresh_tokens SET consumed_at = ? WHERE token_hash = ? AND consumed_at IS NULL")
        .run(now, presentedHash);
      const nextMaterial = { ...tokens, familyHash };
      this.#insertAccessToken(nextMaterial, binding.clientId, principalHash, binding.resource, scopes, now);
      this.#database
        .prepare(`
          INSERT INTO refresh_tokens (
            token_hash, family_hash, generation, created_at, expires_at
          ) VALUES (?, ?, ?, ?, ?)
        `)
        .run(tokens.refreshTokenHash, familyHash, generation, now, refreshExpiresAt);
      return {
        kind: "ok",
        claims: {
          clientId: binding.clientId,
          principalHash,
          resource: binding.resource,
          scopes,
          expiresAt: tokens.accessExpiresAt,
          generation,
          absoluteExpiresAt,
          refreshExpiresAt,
        },
      };
    });
    if (outcome.kind === "rejected") {
      throw new OAuthSecurityError(outcome.code, { oauthError: "invalid_grant" });
    }
    return outcome.claims;
  }

  validateAccessToken(tokenHash: string, resource: string, now: number): AccessTokenClaims {
    return this.#read(() => {
      const raw = this.#database
        .prepare(`
        SELECT a.*, f.revoked_at AS family_revoked_at
        FROM access_tokens a
        JOIN token_families f ON f.family_hash = a.family_hash
        WHERE a.token_hash = ?
        `)
        .get(tokenHash);
      if (raw === undefined) {
        throw new OAuthSecurityError("oauth_token_invalid", {
          httpStatus: 401,
          oauthError: "invalid_grant",
        });
      }
      const row = asRow(raw);
      if (
        nullableNumberField(row, "revoked_at") !== null ||
        nullableNumberField(row, "family_revoked_at") !== null
      ) {
        throw new OAuthSecurityError("oauth_token_revoked", {
          httpStatus: 401,
          oauthError: "invalid_grant",
        });
      }
      if (numberField(row, "expires_at") <= now) {
        throw new OAuthSecurityError("oauth_token_invalid", {
          httpStatus: 401,
          oauthError: "invalid_grant",
        });
      }
      if (stringField(row, "resource") !== resource) {
        throw new OAuthSecurityError("oauth_resource_mismatch", {
          httpStatus: 403,
          oauthError: "access_denied",
        });
      }
      return {
        clientId: stringField(row, "client_id"),
        principalHash: stringField(row, "principal_hash"),
        resource,
        scopes: scopesField(row),
        expiresAt: numberField(row, "expires_at"),
      };
    });
  }

  revokeToken(
    tokenHash: string,
    binding: { readonly clientId: string; readonly resource: string },
    now: number,
  ): void {
    this.#transaction(() => {
      const access = this.#database
        .prepare(`
          SELECT family_hash FROM access_tokens
          WHERE token_hash = ? AND client_id = ? AND resource = ?
        `)
        .get(tokenHash, binding.clientId, binding.resource);
      if (access !== undefined) {
        this.#database.prepare("UPDATE access_tokens SET revoked_at = ? WHERE token_hash = ?").run(now, tokenHash);
        return;
      }
      const refresh = this.#database
        .prepare(`
          SELECT r.family_hash
          FROM refresh_tokens r
          JOIN token_families f ON f.family_hash = r.family_hash
          WHERE r.token_hash = ? AND f.client_id = ? AND f.resource = ?
        `)
        .get(tokenHash, binding.clientId, binding.resource);
      if (refresh !== undefined) {
        this.#revokeFamily(stringField(asRow(refresh), "family_hash"), now);
      }
    });
  }

  #revokeFamily(familyHash: string, now: number): void {
    this.#database.prepare("UPDATE token_families SET revoked_at = ? WHERE family_hash = ?").run(now, familyHash);
    this.#database.prepare("UPDATE access_tokens SET revoked_at = ? WHERE family_hash = ?").run(now, familyHash);
    this.#database.prepare("UPDATE refresh_tokens SET revoked_at = ? WHERE family_hash = ?").run(now, familyHash);
  }

  putDcrClient(input: {
    readonly clientId: string;
    readonly clientSecret: string;
    readonly metadataDigest: string;
    readonly redirectUri: string;
    readonly principalHash: string;
    readonly resource: string;
    readonly now: number;
  }): void {
    this.#transaction(() => {
      this.#database
        .prepare(`
          INSERT INTO dcr_clients (
            client_id, secret_hash, metadata_digest, redirect_uri,
            principal_hash, resource, created_at
          ) VALUES (?, ?, ?, ?, ?, ?, ?)
        `)
        .run(
          input.clientId,
          hashOpaque(input.clientSecret),
          input.metadataDigest,
          input.redirectUri,
          input.principalHash,
          input.resource,
          input.now,
        );
    });
  }

  verifyDcrClient(clientId: string, clientSecret: string, resource: string): void {
    this.#read(() => {
      const raw = this.#database.prepare("SELECT * FROM dcr_clients WHERE client_id = ?").get(clientId);
      if (raw === undefined) {
        throw new OAuthSecurityError("oauth_client_metadata_invalid", {
          httpStatus: 401,
          oauthError: "invalid_client",
        });
      }
      const row = asRow(raw);
      if (
        nullableNumberField(row, "revoked_at") !== null ||
        stringField(row, "resource") !== resource ||
        !constantTimeTextEqual(stringField(row, "secret_hash"), hashOpaque(clientSecret))
      ) {
        throw new OAuthSecurityError("oauth_client_metadata_invalid", {
          httpStatus: 401,
          oauthError: "invalid_client",
        });
      }
    });
  }

  validateDcrAuthorizationClient(input: {
    readonly clientId: string;
    readonly metadataDigest: string;
    readonly redirectUri: string;
    readonly principalHash: string;
    readonly resource: string;
  }): void {
    this.#read(() => {
      const raw = this.#database.prepare("SELECT * FROM dcr_clients WHERE client_id = ?").get(input.clientId);
      if (raw === undefined) {
        throw new OAuthSecurityError("oauth_client_metadata_invalid", { oauthError: "invalid_client" });
      }
      const row = asRow(raw);
      if (
        nullableNumberField(row, "revoked_at") !== null ||
        !constantTimeTextEqual(stringField(row, "metadata_digest"), input.metadataDigest) ||
        !constantTimeTextEqual(stringField(row, "redirect_uri"), input.redirectUri) ||
        !constantTimeTextEqual(stringField(row, "principal_hash"), input.principalHash) ||
        stringField(row, "resource") !== input.resource
      ) {
        throw new OAuthSecurityError("oauth_client_metadata_invalid", { oauthError: "invalid_client" });
      }
    });
  }

  consumeJwtJti(clientId: string, jti: string, expiresAt: number, now: number): void {
    this.#transaction(() => {
      this.#database.prepare("DELETE FROM jwt_jti_replay WHERE expires_at <= ?").run(now);
      const jtiHash = hashOpaque(jti);
      const existing = this.#database.prepare("SELECT 1 FROM jwt_jti_replay WHERE jti_hash = ?").get(jtiHash);
      if (existing !== undefined) {
        throw new OAuthSecurityError("oauth_client_assertion_replayed", {
          httpStatus: 401,
          oauthError: "invalid_client",
        });
      }
      this.#database
        .prepare("INSERT INTO jwt_jti_replay (jti_hash, client_id, expires_at) VALUES (?, ?, ?)")
        .run(jtiHash, clientId, expiresAt);
    });
  }

  putBrowserSession(input: {
    readonly sessionHash: string;
    readonly principalHash: string;
    readonly csrfHash: string;
    readonly nonceHash: string;
    readonly authenticated: boolean;
    readonly now: number;
    readonly expiresAt: number;
  }): void {
    this.#transaction(() => {
      this.#database
        .prepare(`
          INSERT INTO browser_sessions (
            session_hash, principal_hash, csrf_hash, nonce_hash, authenticated,
            csrf_consumed, created_at, expires_at
          ) VALUES (?, ?, ?, ?, ?, 0, ?, ?)
        `)
        .run(
          input.sessionHash,
          input.principalHash,
          input.csrfHash,
          input.nonceHash,
          input.authenticated ? 1 : 0,
          input.now,
          input.expiresAt,
        );
    });
  }

  rotateBrowserSession(input: {
    readonly oldSessionHash: string;
    readonly oldCsrfHash: string;
    readonly newSessionHash: string;
    readonly newPrincipalHash: string;
    readonly newCsrfHash: string;
    readonly newNonceHash: string;
    readonly now: number;
    readonly expiresAt: number;
  }): BrowserSessionRow {
    return this.#transaction(() => {
      const raw = this.#database
        .prepare("SELECT * FROM browser_sessions WHERE session_hash = ?")
        .get(input.oldSessionHash);
      if (raw === undefined) {
        throw new OAuthSecurityError("oauth_session_invalid", { httpStatus: 401 });
      }
      const row = asRow(raw);
      const previous: BrowserSessionRow = {
        principalHash: stringField(row, "principal_hash"),
        nonceHash: stringField(row, "nonce_hash"),
        expiresAt: numberField(row, "expires_at"),
        authenticated: boolField(row, "authenticated"),
        csrfConsumed: boolField(row, "csrf_consumed"),
        revoked: nullableNumberField(row, "revoked_at") !== null,
      };
      if (
        previous.expiresAt <= input.now ||
        previous.authenticated ||
        previous.revoked ||
        previous.csrfConsumed ||
        !constantTimeTextEqual(stringField(row, "csrf_hash"), input.oldCsrfHash)
      ) {
        throw new OAuthSecurityError("oauth_csrf_invalid", { httpStatus: 403, oauthError: "access_denied" });
      }
      this.#database
        .prepare(`
          UPDATE browser_sessions
          SET csrf_consumed = 1, revoked_at = ?
          WHERE session_hash = ? AND csrf_consumed = 0 AND revoked_at IS NULL
        `)
        .run(input.now, input.oldSessionHash);
      this.#database
        .prepare(`
          INSERT INTO browser_sessions (
            session_hash, principal_hash, csrf_hash, nonce_hash, authenticated,
            csrf_consumed, created_at, expires_at
          ) VALUES (?, ?, ?, ?, 1, 0, ?, ?)
        `)
        .run(
          input.newSessionHash,
          input.newPrincipalHash,
          input.newCsrfHash,
          input.newNonceHash,
          input.now,
          input.expiresAt,
        );
      return previous;
    });
  }

  consumeAndRevokeBrowserSession(sessionHash: string, csrfHash: string, now: number): void {
    this.#transaction(() => {
      const raw = this.#database.prepare("SELECT * FROM browser_sessions WHERE session_hash = ?").get(sessionHash);
      if (raw === undefined) {
        throw new OAuthSecurityError("oauth_session_invalid", { httpStatus: 401 });
      }
      const row = asRow(raw);
      if (
        numberField(row, "expires_at") <= now ||
        nullableNumberField(row, "revoked_at") !== null ||
        boolField(row, "csrf_consumed") ||
        !constantTimeTextEqual(stringField(row, "csrf_hash"), csrfHash)
      ) {
        throw new OAuthSecurityError("oauth_csrf_invalid", { httpStatus: 403, oauthError: "access_denied" });
      }
      this.#database
        .prepare(`
          UPDATE browser_sessions
          SET csrf_consumed = 1, revoked_at = ?
          WHERE session_hash = ? AND csrf_consumed = 0 AND revoked_at IS NULL
        `)
        .run(now, sessionHash);
    });
  }

  validateBrowserSession(sessionHash: string, now: number, requireAuthenticated: boolean): BrowserSessionRow {
    return this.#read(() => {
      const raw = this.#database.prepare("SELECT * FROM browser_sessions WHERE session_hash = ?").get(sessionHash);
      if (raw === undefined) {
        throw new OAuthSecurityError("oauth_session_invalid", { httpStatus: 401 });
      }
      const row = asRow(raw);
      const result: BrowserSessionRow = {
        principalHash: stringField(row, "principal_hash"),
        nonceHash: stringField(row, "nonce_hash"),
        expiresAt: numberField(row, "expires_at"),
        authenticated: boolField(row, "authenticated"),
        csrfConsumed: boolField(row, "csrf_consumed"),
        revoked: nullableNumberField(row, "revoked_at") !== null,
      };
      if (result.expiresAt <= now || result.revoked || (requireAuthenticated && !result.authenticated)) {
        throw new OAuthSecurityError("oauth_session_invalid", { httpStatus: 401 });
      }
      return result;
    });
  }

  consumeBrowserCsrf(sessionHash: string, csrfHash: string, now: number): BrowserSessionRow {
    return this.#transaction(() => {
      const raw = this.#database.prepare("SELECT * FROM browser_sessions WHERE session_hash = ?").get(sessionHash);
      if (raw === undefined) {
        throw new OAuthSecurityError("oauth_session_invalid", { httpStatus: 401 });
      }
      const row = asRow(raw);
      const result: BrowserSessionRow = {
        principalHash: stringField(row, "principal_hash"),
        nonceHash: stringField(row, "nonce_hash"),
        expiresAt: numberField(row, "expires_at"),
        authenticated: boolField(row, "authenticated"),
        csrfConsumed: boolField(row, "csrf_consumed"),
        revoked: nullableNumberField(row, "revoked_at") !== null,
      };
      if (
        result.expiresAt <= now ||
        result.revoked ||
        result.csrfConsumed ||
        !constantTimeTextEqual(stringField(row, "csrf_hash"), csrfHash)
      ) {
        throw new OAuthSecurityError("oauth_csrf_invalid", { httpStatus: 403, oauthError: "access_denied" });
      }
      this.#database
        .prepare("UPDATE browser_sessions SET csrf_consumed = 1 WHERE session_hash = ? AND csrf_consumed = 0")
        .run(sessionHash);
      return result;
    });
  }

  rotateBrowserSessionAfterConsent(input: {
    readonly oldSessionHash: string;
    readonly newSessionHash: string;
    readonly newPrincipalHash: string;
    readonly newCsrfHash: string;
    readonly newNonceHash: string;
    readonly now: number;
    readonly expiresAt: number;
  }): void {
    this.#transaction(() => {
      const raw = this.#database
        .prepare("SELECT * FROM browser_sessions WHERE session_hash = ?")
        .get(input.oldSessionHash);
      if (raw === undefined) {
        throw new OAuthSecurityError("oauth_session_invalid", { httpStatus: 401 });
      }
      const row = asRow(raw);
      if (
        numberField(row, "expires_at") <= input.now ||
        nullableNumberField(row, "revoked_at") !== null ||
        !boolField(row, "authenticated") ||
        !boolField(row, "csrf_consumed") ||
        !constantTimeTextEqual(stringField(row, "principal_hash"), input.newPrincipalHash)
      ) {
        throw new OAuthSecurityError("oauth_csrf_invalid", {
          httpStatus: 403,
          oauthError: "access_denied",
        });
      }
      this.#database
        .prepare("UPDATE browser_sessions SET revoked_at = ? WHERE session_hash = ? AND revoked_at IS NULL")
        .run(input.now, input.oldSessionHash);
      this.#database
        .prepare(`
          INSERT INTO browser_sessions (
            session_hash, principal_hash, csrf_hash, nonce_hash, authenticated,
            csrf_consumed, created_at, expires_at
          ) VALUES (?, ?, ?, ?, 1, 0, ?, ?)
        `)
        .run(
          input.newSessionHash,
          input.newPrincipalHash,
          input.newCsrfHash,
          input.newNonceHash,
          input.now,
          input.expiresAt,
        );
    });
  }

  revokeBrowserSession(sessionHash: string, now: number): void {
    this.#transaction(() => {
      this.#database.prepare("UPDATE browser_sessions SET revoked_at = ? WHERE session_hash = ?").run(now, sessionHash);
    });
  }

  consumeRateLimit(bucketKey: string, rule: RateLimitRule, now: number): number {
    return this.#transaction(() => {
      this.#database.prepare("DELETE FROM rate_limits WHERE expires_at <= ?").run(now);
      const bucketHash = hashOpaque(bucketKey);
      const raw = this.#database.prepare("SELECT * FROM rate_limits WHERE bucket_hash = ?").get(bucketHash);
      if (raw === undefined) {
        this.#database
          .prepare(`
            INSERT INTO rate_limits (
              bucket_hash, window_started_at, window_ms, attempt_count, expires_at
            ) VALUES (?, ?, ?, 1, ?)
          `)
          .run(bucketHash, now, rule.windowMs, now + rule.windowMs);
        return rule.limit - 1;
      }
      const row = asRow(raw);
      const startedAt = numberField(row, "window_started_at");
      const storedWindow = numberField(row, "window_ms");
      if (storedWindow !== rule.windowMs || startedAt + rule.windowMs <= now) {
        this.#database
          .prepare(`
            UPDATE rate_limits
            SET window_started_at = ?, window_ms = ?, attempt_count = 1, expires_at = ?
            WHERE bucket_hash = ?
          `)
          .run(now, rule.windowMs, now + rule.windowMs, bucketHash);
        return rule.limit - 1;
      }
      const attempts = numberField(row, "attempt_count");
      if (attempts >= rule.limit) {
        throw new OAuthSecurityError("oauth_rate_limited", {
          httpStatus: 429,
          oauthError: "temporarily_unavailable",
        });
      }
      this.#database.prepare("UPDATE rate_limits SET attempt_count = attempt_count + 1 WHERE bucket_hash = ?").run(bucketHash);
      return rule.limit - attempts - 1;
    });
  }
}
