from __future__ import annotations

import json
import os
import sqlite3
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOWNSTREAM = ROOT / "mcp" / "mcphub" / "downstream"
SOURCE = DOWNSTREAM / "src"
OAUTH_SOURCE = SOURCE / "oauth"
POLICY_SOURCE = SOURCE / "policy" / "oauth-policy.ts"
COMMON_SECURITY = SOURCE / "security" / "common"
OAUTH_SECURITY = SOURCE / "security" / "oauth"
FIXTURES = DOWNSTREAM / "fixtures" / "oauth"
OAUTH_TESTS = DOWNSTREAM / "test" / "oauth"
TSC = DOWNSTREAM / "node_modules" / ".bin" / "tsc"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _all_owned_typescript() -> str:
    roots = (OAUTH_SOURCE, SOURCE / "policy", COMMON_SECURITY, OAUTH_SECURITY)
    return "\n".join(_text(path) for root in roots for path in sorted(root.rglob("*.ts")))


@pytest.fixture(scope="session")
def compiled_oauth(tmp_path_factory: pytest.TempPathFactory) -> Path:
    build_root = tmp_path_factory.mktemp("mcphub-oauth-compiled")
    output = build_root / "dist"
    config = build_root / "tsconfig.json"
    config.write_text(
        json.dumps(
            {
                "extends": str(DOWNSTREAM / "tsconfig.json"),
                "compilerOptions": {
                    "declaration": False,
                    "declarationMap": False,
                    "outDir": str(output),
                    "rootDir": str(DOWNSTREAM),
                    "sourceMap": False,
                    "typeRoots": [str(DOWNSTREAM / "node_modules" / "@types")],
                },
                "exclude": [],
                "include": [
                    str(OAUTH_SOURCE / "**" / "*.ts"),
                    str(SOURCE / "policy" / "**" / "*.ts"),
                    str(COMMON_SECURITY / "**" / "*.ts"),
                    str(OAUTH_SECURITY / "**" / "*.ts"),
                    str(SOURCE / "protocol" / "canonical-json.ts"),
                    str(SOURCE / "runtime" / "readiness.ts"),
                    str(SOURCE / "runtime" / "secure-file.ts"),
                    str(OAUTH_TESTS / "**" / "*.ts"),
                ],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    subprocess.run(
        [str(TSC), "-p", str(config)],
        cwd=DOWNSTREAM,
        check=True,
        capture_output=True,
        text=True,
    )
    (output / "package.json").write_text('{"type":"module"}\n', encoding="utf-8")
    return output


def test_exact_things_oauth_resource_issuer_and_independent_scopes() -> None:
    policy = _text(POLICY_SOURCE)
    assert 'THINGS_RESOURCE = "https://mcp.w4w.dev/mcp/things"' in policy
    assert "THINGS_ISSUER = THINGS_RESOURCE" in policy
    assert '["things.read", "things.write", "things.admin"]' in policy
    assert 'OFFLINE_ACCESS_SCOPE = "offline_access"' in policy
    assert "return THINGS_SCOPES.filter" in policy
    assert "requireCatalogScopes" in policy
    assert "requireAuthorizationScopes" in policy
    assert "requireToolScope" in policy
    assert "normalized.includes(minimumScope)" in policy
    assert "ACCESS_TOKEN_TTL_MS = 10 * 60 * 1_000" in policy
    assert "REFRESH_TOKEN_SLIDING_TTL_MS = 24 * 60 * 60 * 1_000" in policy
    assert "REFRESH_TOKEN_ABSOLUTE_TTL_MS = 30 * 24 * 60 * 60 * 1_000" in policy


def test_offline_access_is_refresh_capability_not_things_authorization(
    compiled_oauth: Path,
) -> None:
    policy_uri = (compiled_oauth / "src" / "policy" / "oauth-policy.js").as_uri()
    exercise = f"""
      import assert from "node:assert/strict";
      import {{
        requireAuthorizationScopes, requireCatalogScopes, requireToolScope
      }} from {json.dumps(policy_uri)};
      const requested = ["things.admin", "offline_access", "things.read", "things.write"];
      assert.deepEqual(
        requireAuthorizationScopes(requested),
        ["things.read", "things.write", "things.admin", "offline_access"],
      );
      assert.deepEqual(
        requireCatalogScopes(requested),
        ["things.read", "things.write", "things.admin"],
      );
      assert.throws(
        () => requireAuthorizationScopes(["things.read", "things.write", "things.admin"]),
        /oauth_catalog_scope_mismatch/u,
      );
      assert.throws(
        () => requireToolScope(["offline_access"], "things.read"),
        /oauth_scope_insufficient/u,
      );
      assert.doesNotThrow(
        () => requireToolScope(["offline_access", "things.read"], "things.read"),
      );
    """
    subprocess.run(
        ["node", "--input-type=module", "--eval", exercise],
        cwd=DOWNSTREAM,
        check=True,
        capture_output=True,
        text=True,
    )


def test_oauth_state_is_separate_owner_private_and_nofollow_guarded() -> None:
    files = _text(COMMON_SECURITY / "files.ts")
    store = _text(OAUTH_SOURCE / "store.ts")
    assert "environment.MCPHUB_OAUTH_STATE_DIR" in files
    assert 'path.join(stateDirectory, "oauth.sqlite3")' in files
    assert "0o700" in files
    assert "0o600" in files
    assert "constants.O_NOFOLLOW" in files
    assert "stat.uid !== currentUid()" in files
    assert "stat.nlink !== 1" in files
    assert "assertRetainedSecureDescriptor" in files
    assert "currentIdentity.dev !== descriptor.identity.device" in files
    assert "currentIdentity.ino !== descriptor.identity.inode" in files
    assert "createSecureFile(paths.databasePath)" in store
    assert "new OAuthSqliteStore(paths, INITIALIZE)" in store
    assert "PRAGMA secure_delete = ON" in store
    assert "PRAGMA synchronous = FULL" in store
    assert "things.sqlite" not in files.lower()
    assert "things.sqlite" not in store.lower()


def test_sqlite_schema_persists_hashes_not_raw_oauth_credentials() -> None:
    store = _text(OAUTH_SOURCE / "store.ts")
    for table in (
        "authorization_transactions",
        "authorization_codes",
        "token_families",
        "access_tokens",
        "refresh_tokens",
        "dcr_clients",
        "jwt_jti_replay",
        "browser_sessions",
        "rate_limits",
    ):
        assert f"CREATE TABLE IF NOT EXISTS {table}" in store
    for hash_column in (
        "state_hash",
        "code_hash",
        "token_hash",
        "family_hash",
        "secret_hash",
        "principal_hash",
        "nonce_hash",
        "csrf_hash",
        "session_hash",
        "jti_hash",
        "bucket_hash",
    ):
        assert hash_column in store
    forbidden_columns = (
        "access_token TEXT",
        "refresh_token TEXT",
        "client_secret TEXT",
        "authorization_code TEXT",
        "state TEXT",
        "csrf_token TEXT",
        "session_token TEXT",
        "jti TEXT",
    )
    for column in forbidden_columns:
        assert column not in store


def test_cimd_dcr_pkce_issuer_refresh_and_replay_contracts_are_present() -> None:
    source = _all_owned_typescript()
    required_contracts = (
        "CimdMetadataResolver",
        "validateCimdDocument",
        "validateDcrMetadata",
        'method !== "S256"',
        "verifyPrivateKeyJwt",
        "consumeJwtJti",
        "authorization_response_iss_parameter_supported: true",
        "consumeStateAndIssueCode",
        "rotateRefreshToken",
        "oauth_refresh_replayed",
        "#revokeFamily",
        "validateAccessToken",
        "revokeToken",
    )
    for contract in required_contracts:
        assert contract in source
    assert "fetch(" not in _text(OAUTH_SOURCE / "service.ts")
    assert "CimdLoader" in _text(OAUTH_SECURITY / "clients.ts")


def test_login_cookie_csrf_origin_and_persistent_rate_limit_contracts() -> None:
    service = _text(OAUTH_SOURCE / "service.ts")
    store = _text(OAUTH_SOURCE / "store.ts")
    assert "__Host-mcphub_things_session=" in service
    assert "; Path=/; Secure; HttpOnly; SameSite=Lax" in service
    assert "Domain=" not in service
    assert "origin !== THINGS_ORIGIN" in service
    assert "rotateBrowserSession" in service
    assert "consumeAndRevokeBrowserSession" in service
    assert "csrf_consumed" in store
    assert "CREATE TABLE IF NOT EXISTS rate_limits" in store
    assert "LOGIN_RATE_LIMIT" in service
    assert "REGISTRATION_RATE_LIMIT" in service
    assert "TOKEN_AUTHORIZATION_RATE_LIMIT" in service


def test_remote_and_tool_dispatch_require_a_content_bound_activation_receipt() -> None:
    readiness = _text(SOURCE / "runtime" / "readiness.ts")
    main = _text(SOURCE / "runtime" / "main.ts")
    service = _text(OAUTH_SOURCE / "service.ts")
    ingress_contract = _text(SOURCE / "policy" / "oauth-ingress-contract.ts")
    assert "readOwnerOnlyRuntimeFile" in readiness
    assert "parseRemoteActivationReceipt" in readiness
    assert "loadRemoteActivationReceipt" in readiness
    assert "bindingsEqual" in readiness
    for binding in (
        "auditManifestSha256",
        "capabilityManifestSha256",
        "catalogSha256",
        "cloudflaredConfigSha256",
        "conformanceResultSha256",
        "distributionDigest",
        "manifestProjectionSha256",
        "oauthPolicySha256",
        "observedWireEvidenceSha256",
        "routeManifestSha256",
        "scopeMapSha256",
        "settingsSha256",
    ):
        assert f'"{binding}"' in readiness
    assert 'source.status !== "pass"' in readiness
    assert "source.noSecrets !== true" in readiness
    assert "expiresAt <= now" in readiness
    assert "input.receipt === null" in readiness
    assert "MCPHUB_FINAL_STAMP_VALID" not in main
    assert "MCPHUB_CAPTURE_RECEIPT_VALID" not in main
    assert "MCPHUB_TOOL_DISPATCH_ENABLED" not in main
    assert "REMOTE_PUBLIC_READY = true" not in main
    assert "TOOL_DISPATCH_ENABLED = true" not in main
    assert "REMOTE_PUBLIC_READY" not in service
    assert "TOOL_DISPATCH_ENABLED" not in service
    assert 'remoteActivation: "digest-bound-receipt-required"' in ingress_contract
    assert 'toolDispatch: "receipt-and-independent-scope-gated"' in ingress_contract


def test_v17_public_and_capture_activation_receipts_are_behaviorally_gated(
    compiled_oauth: Path,
    tmp_path: Path,
) -> None:
    module_uri = (compiled_oauth / "src" / "runtime" / "readiness.js").as_uri()
    binding_keys = (
        "auditManifestSha256",
        "capabilityManifestSha256",
        "catalogSha256",
        "cloudflaredConfigSha256",
        "conformanceResultSha256",
        "manifestProjectionSha256",
        "oauthLoginCredentialSha256",
        "oauthPolicySha256",
        "observedWireEvidenceSha256",
        "routeManifestSha256",
        "scopeMapSha256",
        "settingsSha256",
    )
    bindings = {key: f"{index + 1:x}" * 64 for index, key in enumerate(binding_keys)}
    bindings["distributionDigest"] = f"sha256-{'d' * 64}"
    public_receipt = {
        "bindings": bindings,
        "createdAt": 1_000_000,
        "expiresAt": 1_600_000,
        "mode": "public",
        "noSecrets": True,
        "publicOrigin": "https://mcp.w4w.dev",
        "publicResource": "https://mcp.w4w.dev/mcp/things",
        "registrationMode": "cimd",
        "remotePublicReady": True,
        "schemaVersion": 1,
        "status": "pass",
        "toolDispatchEnabled": True,
        "tunnelAllowed": True,
    }
    public_path = tmp_path / "public-receipt.json"
    public_path.write_text(json.dumps(public_receipt), encoding="utf-8")
    public_path.chmod(0o600)
    drifted_receipt = json.loads(json.dumps(public_receipt))
    drifted_receipt["bindings"]["settingsSha256"] = "e" * 64
    drifted_path = tmp_path / "drifted-receipt.json"
    drifted_path.write_text(json.dumps(drifted_receipt), encoding="utf-8")
    drifted_path.chmod(0o600)
    capture_bindings = {
        **bindings,
        "oauthLoginCredentialSha256": "0" * 64,
        "oauthPolicySha256": "0" * 64,
        "observedWireEvidenceSha256": "0" * 64,
    }
    capture_receipt = {
        **public_receipt,
        "bindings": capture_bindings,
        "mode": "capture",
        "registrationMode": None,
        "remotePublicReady": False,
        "toolDispatchEnabled": False,
    }
    capture_path = tmp_path / "capture-receipt.json"
    capture_path.write_text(json.dumps(capture_receipt), encoding="utf-8")
    capture_path.chmod(0o600)
    exercise = f"""
      import assert from "node:assert/strict";
      import {{
        evaluateRuntimeActivation, loadRemoteActivationReceipt
      }} from {json.dumps(module_uri)};
      const publicBindings = {json.dumps(bindings)};
      assert.throws(
        () => evaluateRuntimeActivation({{ mode: "public", receipt: null }}),
        /remote_public_not_ready/u,
      );
      const publicReceipt = loadRemoteActivationReceipt({{
        expectedBindings: publicBindings,
        expectedMode: "public",
        expectedRegistrationMode: "cimd",
        now: 1_100_000,
        path: {json.dumps(str(public_path))},
      }});
      assert.deepEqual(
        {{
          bindRemoteListener: evaluateRuntimeActivation({{
            mode: "public", receipt: publicReceipt
          }}).bindRemoteListener,
          remotePublicReady: publicReceipt.remotePublicReady,
          remoteToolDispatchEnabled: publicReceipt.toolDispatchEnabled,
          tunnelAllowed: publicReceipt.tunnelAllowed,
        }},
        {{
          bindRemoteListener: true,
          remotePublicReady: true,
          remoteToolDispatchEnabled: true,
          tunnelAllowed: true,
        }},
      );
      assert.throws(
        () => loadRemoteActivationReceipt({{
          expectedBindings: publicBindings,
          expectedMode: "public",
          expectedRegistrationMode: "cimd",
          now: 1_100_000,
          path: {json.dumps(str(drifted_path))},
        }}),
        /remote_activation_receipt_invalid/u,
      );
      const captureReceipt = loadRemoteActivationReceipt({{
        expectedBindings: {json.dumps(capture_bindings)},
        expectedMode: "capture",
        expectedRegistrationMode: null,
        now: 1_100_000,
        path: {json.dumps(str(capture_path))},
      }});
      assert.deepEqual(evaluateRuntimeActivation({{
        mode: "capture", receipt: captureReceipt
      }}), {{
        bindRemoteListener: true,
        mode: "capture",
        receiptSha256: captureReceipt.receiptSha256,
        remotePublicReady: false,
        remoteToolDispatchEnabled: false,
        tunnelAllowed: true,
      }});
    """
    subprocess.run(
        ["node", "--input-type=module", "--eval", exercise],
        cwd=DOWNSTREAM,
        check=True,
        capture_output=True,
        text=True,
    )


def test_logs_and_public_errors_are_content_free() -> None:
    redaction = _text(COMMON_SECURITY / "redaction.ts")
    errors = _text(COMMON_SECURITY / "errors.ts")
    assert "ALLOWED_AUDIT_FIELDS" in redaction
    for forbidden in ("token", "secret", "path", "privateContent", "todo"):
        assert f'"{forbidden}"' not in redaction
    assert "super(code)" in errors
    assert "error_description: this.code" in errors
    assert "cause" not in errors
    assert "stack" not in redaction


def test_oauth_fixtures_are_synthetic_and_cover_callback_adversaries() -> None:
    cimd = json.loads(_text(FIXTURES / "cimd-none.json"))
    dcr = json.loads(_text(FIXTURES / "dcr-approved.json"))
    callbacks = json.loads(_text(FIXTURES / "adversarial-callbacks.json"))
    approved = "https://chatgpt.com/connector_platform_oauth_redirect"
    assert cimd == {
        "client_id": "https://chatgpt.com/oauth/client.json",
        "redirect_uris": [approved],
        "token_endpoint_auth_method": "none",
    }
    assert dcr["redirect_uris"] == [approved]
    assert dcr["grant_types"] == ["authorization_code", "refresh_token"]
    assert dcr["response_types"] == ["code"]
    assert dcr["token_endpoint_auth_method"] == "client_secret_basic"
    assert len(callbacks) >= 9
    assert any(value.startswith("http://") for value in callbacks)
    assert any("localhost" in value for value in callbacks)
    assert any(value.startswith("file:") for value in callbacks)
    assert any("#fragment" in value for value in callbacks)
    serialized = json.dumps({"cimd": cimd, "dcr": dcr, "callbacks": callbacks})
    assert "Bearer " not in serialized
    assert "client_secret" not in cimd
    assert "client_secret" not in dcr


def test_downstream_oauth_tests_are_hermetic_and_cover_positive_and_negative_paths() -> None:
    tests = "\n".join(_text(path) for path in sorted(OAUTH_TESTS.glob("*.test.ts")))
    assert "node:test" in tests
    assert "runs the constrained DCR code" in tests
    assert "validates CIMD none clients" in tests
    assert "private_key_jwt" in tests
    assert "oauth_refresh_replayed" in tests
    assert "oauth_token_revoked" in tests
    assert "oauth_client_assertion_replayed" in tests
    assert "oauth_database_unsafe" in tests
    assert "https://mcp.w4w.dev" not in tests.replace('const THINGS_RESOURCE = "https://mcp.w4w.dev/mcp/things"', "")
    assert "fetch(" not in tests


def test_oauth_uses_only_node_builtins_and_locked_workspace_dependencies() -> None:
    package = json.loads(_text(DOWNSTREAM / "package.json"))
    combined = _all_owned_typescript()
    for dependency in ("better-sqlite3", "jsonwebtoken", "jose", "express", "oauth2-server"):
        assert dependency not in package.get("dependencies", {})
        assert dependency not in package.get("devDependencies", {})
        assert f'from "{dependency}"' not in combined
    assert 'from "node:sqlite"' in combined
    assert 'from "node:crypto"' in combined


def test_v17_invokes_behavioral_node_oauth_adversarial_suite(compiled_oauth: Path) -> None:
    tests = sorted((compiled_oauth / "test" / "oauth").glob("*.test.js"))
    assert {path.name for path in tests} == {
        "private-key-jwt.test.js",
        "service.test.js",
        "store.test.js",
    }
    completed = subprocess.run(
        ["node", "--test", *(str(path) for path in tests)],
        cwd=DOWNSTREAM,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    output = completed.stdout + completed.stderr
    assert "fail 0" in output
    assert "pass 20" in output


def test_v17_inspects_real_sqlite_hash_only_restart_rollback_and_gate_contract(
    compiled_oauth: Path,
    tmp_path: Path,
) -> None:
    state_directory = tmp_path / "oauth-state"
    module_uri = (compiled_oauth / "src" / "oauth" / "index.js").as_uri()
    raw_values = {
        "client_secret": "raw-client-secret-v17",
        "state": "raw-client-state-v17",
        "nonce": "raw-server-nonce-v17",
        "principal": "raw-principal-v17",
    }
    initialize = f"""
      import {{
        OAuthSqliteStore, THINGS_RESOURCE, hashOpaque, resolveOAuthStatePaths
      }} from {json.dumps(module_uri)};
      const paths = resolveOAuthStatePaths(process.env);
      const store = OAuthSqliteStore.initialize(paths, 90000000);
      store.putDcrClient({{
        clientId: "dcr_v17",
        clientSecret: {json.dumps(raw_values["client_secret"])},
        metadataDigest: "a".repeat(64),
        redirectUri: "https://chatgpt.com/connector_platform_oauth_redirect",
        principalHash: hashOpaque({json.dumps(raw_values["principal"])}),
        resource: THINGS_RESOURCE,
        now: 90000000,
      }});
      store.putAuthorizationTransaction({{
        stateHash: hashOpaque({json.dumps(raw_values["state"])}),
        clientId: "dcr_v17",
        registrationMode: "dcr",
        redirectUri: "https://chatgpt.com/connector_platform_oauth_redirect",
        codeChallenge: "b".repeat(43),
        principalHash: hashOpaque({json.dumps(raw_values["principal"])}),
        resource: THINGS_RESOURCE,
        scopes: ["things.read", "things.write", "things.admin"],
        nonceHash: hashOpaque({json.dumps(raw_values["nonce"])}),
        expiresAt: 90100000,
      }}, 90000000);
      store.consumeRateLimit("restart-proof", {{ limit: 1, windowMs: 60000 }}, 90000000);
      store.close();
    """
    environment = {**os.environ, "MCPHUB_OAUTH_STATE_DIR": str(state_directory)}
    subprocess.run(
        ["node", "--input-type=module", "--eval", initialize],
        cwd=DOWNSTREAM,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )

    database_path = state_directory / "oauth.sqlite3"
    receipt_path = state_directory / "oauth.sqlite3.init-receipt.json"
    assert database_path.stat().st_mode & 0o777 == 0o600
    assert receipt_path.stat().st_mode & 0o777 == 0o600
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt == {
        "databaseId": receipt["databaseId"],
        "initializedAt": 90_000_000,
        "rollbackExcluded": True,
        "schemaEpoch": 2,
    }

    with sqlite3.connect(database_path) as connection:
        table_names = {
            row[0] for row in connection.execute("SELECT name FROM sqlite_schema WHERE type = 'table' ORDER BY name")
        }
        assert {
            "oauth_store_metadata",
            "authorization_transactions",
            "authorization_codes",
            "token_families",
            "access_tokens",
            "refresh_tokens",
            "dcr_clients",
            "jwt_jti_replay",
            "browser_sessions",
            "rate_limits",
        } <= table_names
        metadata = connection.execute(
            "SELECT schema_epoch, rollback_excluded FROM oauth_store_metadata WHERE singleton = 1"
        ).fetchone()
        assert metadata == (2, 1)

    database_bytes = database_path.read_bytes()
    for raw_value in raw_values.values():
        assert raw_value.encode() not in database_bytes

    reopen = f"""
      import {{ OAuthSecurityError, OAuthSqliteStore, resolveOAuthStatePaths }} from {json.dumps(module_uri)};
      const store = new OAuthSqliteStore(resolveOAuthStatePaths(process.env));
      try {{
        store.consumeRateLimit("restart-proof", {{ limit: 1, windowMs: 60000 }}, 90000001);
        process.exit(8);
      }} catch (error) {{
        if (!(error instanceof OAuthSecurityError) || error.code !== "oauth_rate_limited") process.exit(9);
      }} finally {{ store.close(); }}
    """
    subprocess.run(
        ["node", "--input-type=module", "--eval", reopen],
        cwd=DOWNSTREAM,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )

    with sqlite3.connect(database_path) as connection:
        connection.execute("UPDATE oauth_store_metadata SET schema_epoch = 1 WHERE singleton = 1")
        connection.commit()
    rollback_probe = f"""
      import {{ OAuthSecurityError, OAuthSqliteStore, resolveOAuthStatePaths }} from {json.dumps(module_uri)};
      try {{ new OAuthSqliteStore(resolveOAuthStatePaths(process.env)); process.exit(10); }}
      catch (error) {{
        if (!(error instanceof OAuthSecurityError) || error.code !== "oauth_database_unsafe") process.exit(11);
      }}
    """
    subprocess.run(
        ["node", "--input-type=module", "--eval", rollback_probe],
        cwd=DOWNSTREAM,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
