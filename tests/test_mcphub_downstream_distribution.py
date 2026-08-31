from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import cast

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
DOWNSTREAM = ROOT / "mcp" / "mcphub" / "downstream"
UPSTREAM = DOWNSTREAM / "provenance" / "upstream.json"
DEPENDENCY_GRAPH = DOWNSTREAM / "provenance" / "dependency-graph.json"
PACKAGE = DOWNSTREAM / "package.json"
LOCK = DOWNSTREAM / "pnpm-lock.yaml"
PATCH_CANDIDATE = DOWNSTREAM / "patches" / "candidate-inventory.json"
AUDIT_SCHEMA = ROOT / "config" / "schemas" / "mcphub-downstream-audit.schema.json"
MATERIALIZER = ROOT / "scripts" / "mcphub" / "downstream-materialize.mjs"
LAUNCHER = ROOT / "scripts" / "mcphub" / "downstream-launch.mjs"

TARBALL_SHA256 = "4cb58d4cb11c7d036bde169504f0ddbe9849159e40fe764950ad62853d1502bb"
NPM_INTEGRITY = "sha512-k0csMxsrZZOmh1Cef4WF/KGwFBtusJGPhCq5d1xTlhTfxy6qd61sGzU9ImoagquJZnnIaGp5SOWBv3xASNT5Tw=="
SIGNING_KEY_ID = "SHA256:DhQ8wR5APBvFHLF/+Tc+AYvPOdTpcIDqOhxsBHRwC7U"
ARCHIVE_INVENTORY_SHA256 = "de78c552b9e90a9a46e78bf10974eb0861cd270f4ca05c7bfdbeb73677de04fe"
CFWORKER_INTEGRITY = "sha512-gAmrUZSGtKc3AiBL71iNWxDsyUC5uMaKKGdvzYsBoTW/xi42JQHl7eKV2OYzCUqvc+D2RCcf7EXY2iCyFIk6og=="
CFWORKER_TARBALL_SHA256 = "f3a8076b450505f0671fa78a6efb5e7726883e2c6dfb13b29261872803610203"


def _json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _dict(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return cast("dict[str, object]", value)


def _list(value: object) -> list[object]:
    assert isinstance(value, list)
    return cast("list[object]", value)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest_digest(manifest: dict[str, object]) -> str:
    payload = copy.deepcopy(manifest)
    distribution = _dict(payload["distribution"])
    distribution.pop("digest")
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return f"sha256-{hashlib.sha256(encoded).hexdigest()}"


def _derivation_digest(manifest: dict[str, object]) -> str:
    provenance = _dict(manifest["provenance"])
    source_closure = _dict(manifest["sourceClosure"])
    distribution = _dict(manifest["distribution"])
    payload = {
        "upstream": {
            "tarballSha256": provenance["upstreamTarballSha256"],
            "tarballIntegrity": provenance["upstreamTarballIntegrity"],
            "signatureKeyId": provenance["upstreamSignatureKeyId"],
            "archiveFileCount": provenance["upstreamArchiveFileCount"],
            "archiveUnpackedBytes": provenance["upstreamArchiveUnpackedBytes"],
            "archiveInventorySha256": provenance["upstreamArchiveInventorySha256"],
        },
        "ownedSourcesManifestSha256": source_closure["ownedSourcesManifestSha256"],
        "patchManifestSha256": source_closure["patchManifestSha256"],
        "productionLoaderTransformations": source_closure["productionLoaderTransformations"],
        "outputInventorySha256": _dict(manifest["build"])["outputInventorySha256"],
        "outputs": distribution["files"],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _sealed_fixture() -> dict[str, object]:
    sha = "a" * 64
    manifest: dict[str, object] = {
        "schemaVersion": 1,
        "status": "sealed",
        "provenance": {
            "upstreamManifestSha256": sha,
            "upstreamTarballSha256": TARBALL_SHA256,
            "upstreamTarballIntegrity": NPM_INTEGRITY,
            "upstreamSignatureKeyId": SIGNING_KEY_ID,
            "upstreamArchiveFileCount": 469,
            "upstreamArchiveUnpackedBytes": 9_706_506,
            "upstreamArchiveInventorySha256": ARCHIVE_INVENTORY_SHA256,
            "dependencyGraphSha256": sha,
            "packageJsonSha256": sha,
            "lockfileSha256": sha,
        },
        "dependencies": {
            "publicEdge": {"server": "2.0.0", "core": "2.0.0", "node": None},
            "privateBackendClient": {"sdk": "1.29.0"},
            "schemaValidator": {
                "package": "@cfworker/json-schema",
                "version": "4.1.1",
                "integrity": CFWORKER_INTEGRITY,
                "tarballSha256": CFWORKER_TARBALL_SHA256,
                "signatureKeyId": SIGNING_KEY_ID,
            },
            "v1V2BleedRejected": True,
        },
        "sourceClosure": {
            "exhaustive": True,
            "ownedSourcesManifestSha256": sha,
            "patchManifestSha256": sha,
            "derivationSha256": "0" * 64,
            "productionLoaderTransformations": [],
        },
        "build": {
            "commands": [
                "pnpm install --frozen-lockfile --offline --ignore-workspace --ignore-scripts",
                "pnpm run build",
            ],
            "nodeVersion": "v26.5.0",
            "packageManager": "pnpm@11.22.0",
            "outputInventoryComplete": True,
            "outputInventorySha256": sha,
            "sealAttestationSha256": sha,
        },
        "constraints": {
            "offlineBuild": True,
            "frozenLockfile": True,
            "sameProcessLaunch": True,
            "rejectUnlistedFiles": True,
            "ownerOnlyRuntime": True,
            "npx": False,
            "liveRegistryResolution": False,
            "versionRanges": False,
            "mutablePackageCache": False,
            "nodeOptions": False,
            "esmLoaderHooks": False,
            "networkAtMaterialization": False,
            "networkDependencyResolution": False,
            "entryBundleSelfContained": True,
            "barePackageImports": False,
            "dynamicImports": False,
            "ancestorNodeModulesResolution": False,
        },
        "distribution": {
            "digest": f"sha256-{'0' * 64}",
            "entryPoint": "runtime/main.mjs",
            "entryExport": "main",
            "files": [
                {
                    "sourcePath": "dist/runtime/main.mjs",
                    "path": "runtime/main.mjs",
                    "sha256": sha,
                    "size": 1,
                    "mode": 384,
                    "role": "entrypoint",
                }
            ],
        },
    }
    distribution = _dict(manifest["distribution"])
    source_closure = _dict(manifest["sourceClosure"])
    source_closure["derivationSha256"] = _derivation_digest(manifest)
    distribution["digest"] = _manifest_digest(manifest)
    return manifest


def test_verified_upstream_identity_is_exact_and_secret_free() -> None:
    provenance = _json(UPSTREAM)
    package = _dict(provenance["package"])
    signature = _dict(provenance["signature"])
    inventory = _dict(provenance["archiveInventory"])
    limitations = _dict(provenance["sourceLimitations"])

    assert provenance["evidenceStatus"] == "verified-from-official-registry-bytes"
    assert package == {
        "name": "@samanhappy/mcphub",
        "version": "1.0.32",
        "registryVersionManifestSha256": "1b1daf6bf5b5d6c40a19cf02f970d60e93c132c8fa23e84a83c39f50fcc6203e",
        "tarballUrl": "https://registry.npmjs.org/@samanhappy/mcphub/-/mcphub-1.0.32.tgz",
        "npmIntegrity": NPM_INTEGRITY,
        "npmSha1": "ba035b96295c6b782e9e46469e978fecccde7793",
        "tarballSha256": TARBALL_SHA256,
        "fileCount": 469,
        "unpackedSize": 9_706_506,
        "license": "Apache-2.0",
        "nodeRange": "^18.0.0 || >=20.0.0",
        "moduleType": "module",
        "binaryEntryPoint": "bin/cli.js",
        "libraryEntryPoint": "dist/index.js",
    }
    assert signature["verified"] is True
    assert signature["algorithm"] == "ecdsa-sha2-nistp256"
    assert signature["keyId"] == SIGNING_KEY_ID
    assert inventory["regularFiles"] == 469
    assert inventory["regularFileBytes"] == 9_706_506
    assert inventory["canonicalInventorySha256"] == ARCHIVE_INVENTORY_SHA256
    assert limitations["typescriptSourcesIncluded"] is False
    assert limitations["fullDependencyLockIncluded"] is False
    serialized = json.dumps(provenance)
    assert "/Users/" not in serialized
    assert "token" not in serialized.lower()


def test_package_and_lock_freeze_exact_protocol_boundaries() -> None:
    package = _json(PACKAGE)
    graph = _json(DEPENDENCY_GRAPH)
    lock = LOCK.read_text(encoding="utf-8")

    assert package["engines"] == {"node": ">=24.0.0"}
    assert package["packageManager"] == "pnpm@11.22.0"
    assert package["dependencies"] == {
        "@cfworker/json-schema": "4.1.1",
        "@modelcontextprotocol/sdk": "1.29.0",
        "@modelcontextprotocol/server": "2.0.0",
        "@samanhappy/mcphub": "1.0.32",
    }
    assert package["devDependencies"] == {
        "@types/node": "26.3.0",
        "rolldown": "1.2.6",
        "typescript": "7.0.2",
        "vitest": "4.1.11",
    }
    for value in (package["dependencies"], package["devDependencies"]):
        section = _dict(value)
        assert all(isinstance(version, str) and not re.search(r"[~^*<>=| ]", version) for version in section.values())

    scripts = _dict(package["scripts"])
    assert {"build", "typecheck", "test", "test:distribution", "test:protocol", "test:oauth"} <= scripts.keys()
    assert not any(name.startswith(("pre", "post")) for name in scripts if isinstance(name, str))
    assert not any(
        "passWithNoTests" in command or "pending" in command or "if [" in command
        for command in scripts.values()
        if isinstance(command, str)
    )
    assert "@modelcontextprotocol/core@2.0.0" in lock
    assert "@modelcontextprotocol/server@2.0.0" in lock
    assert "@modelcontextprotocol/sdk@1.29.0" in lock
    assert "'@samanhappy/mcphub@1.0.32':" in lock
    assert NPM_INTEGRITY in lock
    assert "@modelcontextprotocol/node@" not in lock
    lockfile = _dict(graph["lockfile"])
    protocol_isolation = _dict(graph["protocolIsolation"])
    public_edge = _dict(protocol_isolation["publicEdge"])
    private_backend = _dict(protocol_isolation["privateBackendClient"])
    install_policy = _dict(graph["installPolicy"])
    direct_dependencies = _dict(graph["directDependencies"])
    production_dependencies = _dict(direct_dependencies["production"])
    assert lockfile["sha256"] == _sha256(LOCK)
    assert lockfile["packageRecordCount"] == 468
    assert production_dependencies["@cfworker/json-schema"] == "4.1.1"
    assert public_edge["version"] == "2.0.0"
    assert private_backend["version"] == "1.29.0"
    assert install_policy["lifecycleScriptsAllowed"] is False
    assert isinstance(install_policy["command"], str)
    assert "--ignore-scripts" in install_policy["command"]
    assert "--frozen-store" in install_policy["command"]
    assert "--package-import-method=copy" in install_policy["command"]
    assert "--verify-store-integrity" in install_policy["command"]


def test_legacy_patch_count_is_explicitly_non_authorizing_candidate_evidence() -> None:
    candidate = _json(PATCH_CANDIDATE)
    baseline = _dict(candidate["legacyBaseline"])
    final = _dict(candidate["finalSeal"])
    assert candidate["status"] == "candidate-unsealed"
    assert candidate["activationAllowed"] is False
    assert baseline == {
        "wholeReplacements": 6,
        "guardedPatches": 5,
        "baselineOnly": True,
        "entryDetailsFrozen": False,
    }
    assert len(_list(candidate["currentLiveLoaderEvidence"])) == 2
    assert final["requiresBothF2Joins"] is True
    assert set(_list(final["requiredArtifacts"])) == {
        "provenance/owned-sources.json",
        "provenance/patch-manifest.json",
        "provenance/materialized-output-inventory.json",
        "provenance/audit-manifest.json",
        "provenance/distribution-digest.json",
    }


def test_audit_schema_is_strict_and_sealed_fixture_validates() -> None:
    schema = _json(AUDIT_SCHEMA)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    manifest = _sealed_fixture()
    validator.validate(manifest)
    source_closure = _dict(manifest["sourceClosure"])
    assert "legacyBaseline" not in source_closure
    assert source_closure["productionLoaderTransformations"] == []

    source_closure["exhaustive"] = False
    errors = list(validator.iter_errors(manifest))
    assert errors

    source_closure["exhaustive"] = True
    source_closure["productionLoaderTransformations"] = ["legacy-esm-hook"]
    assert list(validator.iter_errors(manifest))


def test_materializer_and_launcher_are_same_process_and_loader_free() -> None:
    materializer = MATERIALIZER.read_text(encoding="utf-8")
    launcher = LAUNCHER.read_text(encoding="utf-8")
    launch_module = (DOWNSTREAM / "src" / "materializer" / "launch.mjs").read_text(encoding="utf-8")
    bundle_module = (DOWNSTREAM / "src" / "materializer" / "bundle.mjs").read_text(encoding="utf-8")
    materialize_module = (DOWNSTREAM / "src" / "materializer" / "materialize.mjs").read_text(encoding="utf-8")
    combined = materializer + launcher + launch_module
    assert "child_process" not in combined
    assert "spawn(" not in combined
    assert "exec(" not in combined
    assert "importSelfContainedModule(entryBytes)" in launch_module
    assert "pathToFileURL" not in launch_module
    assert "readSafeRegularFile" in (DOWNSTREAM / "src" / "materializer" / "safe-file.mjs").read_text(encoding="utf-8")
    assert "mcphub-esm-loader" not in combined
    assert "@samanhappy/mcphub@" not in combined
    assert "exec npx" not in combined
    assert 'const ROLLDOWN_VERSION = "1.2.6"' in bundle_module
    assert "codeSplitting: false" in bundle_module
    assert "sourcemap: false" in bundle_module
    assert "outputRelativePath = OUTPUT_PATH" in bundle_module
    assert "provenance/materialized-output-inventory.json" in materialize_module
    assert "provenance/distribution-digest.json" in materialize_module


def test_distribution_node_suite() -> None:
    result = subprocess.run(
        ["node", "src/materializer/gate.mjs", "distribution"],
        cwd=DOWNSTREAM,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
