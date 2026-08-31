import { constants } from "node:fs";
import { builtinModules } from "node:module";
import { chmod, mkdir, open, writeFile } from "node:fs/promises";
import path from "node:path";

import { VERSION, rolldown } from "rolldown";
import { parseAst } from "rolldown/parseAst";

import { canonicalJson, sha256Bytes } from "./canonical.mjs";
import { assertSelfContainedModule, SEALED_MODULE_POLICY_SHA256 } from "./sealed-module.mjs";

const ROLLDOWN_VERSION = "1.2.6";
const ENTRY_PATH = "src/runtime/main.ts";
const OUTPUT_PATH = "dist/runtime/main.mjs";
const BARE_BUILTINS = new Set(builtinModules.map((name) => name.replace(/^node:/, "")));
const OPTIONAL_OTEL_API = "@opentelemetry/api";
const OPTIONAL_OTEL_IMPORTERS = Object.freeze([
  "/node_modules/@better-auth/core/dist/instrumentation/api.mjs",
  "/node_modules/@redis/client/dist/lib/opentelemetry/index.js",
]);
const OPTIONAL_OTEL_NOOP_RELATIVE_PATH = "src/materializer/optional-opentelemetry-noop.mjs";
const NODE_SQLITE_IMPORTER = "/node_modules/@better-auth/kysely-adapter/dist/index.mjs";
const NODE_SQLITE_TRANSFORMATION = "better-auth-kysely-node-sqlite-static-import-v1";
const BETTER_AUTH_GLOBAL_IMPORTER = "/node_modules/@better-auth/core/dist/context/global.mjs";
const BETTER_AUTH_GLOBAL_SYMBOL_TRANSFORMATION = "better-auth-global-symbol-static-v1";
const BETTER_AUTH_GLOBAL_SYMBOL_ACCESS = "globalThis[symbol]";
const BETTER_AUTH_GLOBAL_STATIC_SYMBOL_ACCESS = 'globalThis[Symbol.for("better-auth:global")]';
const BETTER_AUTH_GLOBAL_SYMBOL_ACCESS_COUNT = 5;
const MCPHUB_MODULE_DIR_IMPORTER = "/node_modules/@samanhappy/mcphub/dist/utils/moduleDir.js";
const MCPHUB_MODULE_DIR_TRANSFORMATION = "mcphub-module-dir-sealed-runtime-v1";
const MCPHUB_SSRF_IMPORTER = "/node_modules/@samanhappy/mcphub/dist/utils/ssrf.js";
const MCPHUB_SSRF_SHA256 = "d7fc7ac44dd23e74f599538c1bb92e698f5280311cfa6ed7582695abdd423e0e";
const MCPHUB_SSRF_RFC6598_TRANSFORMATION = "mcphub-ssrf-rfc6598-cgnat-range-v1";
const MCPHUB_SSRF_OVERBROAD_CGNAT_RANGE = "    [0x64000000, 0x657fffff], // 100.64.0.0/10 CGNAT";
const MCPHUB_SSRF_RFC6598_CGNAT_RANGE = "    [0x64400000, 0x647fffff], // 100.64.0.0/10 CGNAT";
const MCPHUB_MCP_SERVICE_IMPORTER = "/node_modules/@samanhappy/mcphub/dist/services/mcpService.js";
const MCPHUB_MCP_SERVICE_SHA256 = "e7a8f7d0b566ff4fb3988add3fa01bd7f6a058b0ad2e4fcdabc5ea5cd894f87e";
const MCPHUB_TRANSPORT_ISOLATION_TRANSFORMATION = "mcphub-transport-construction-isolation-v1";
const MCPHUB_UNISOLATED_TRANSPORT_CONSTRUCTION = [
  "            else {",
  "                transport = await createTransportFromConfig(name, expandedConf);",
  "            }",
].join("\n");
const MCPHUB_ISOLATED_TRANSPORT_CONSTRUCTION = [
  "            else {",
  "                try {",
  "                    transport = await createTransportFromConfig(name, expandedConf);",
  "                }",
  "                catch (error) {",
  "                    logger.error('Failed to construct transport for server', {",
  "                        serverName: name,",
  "                        error: summarizeErrorForLogging(error),",
  "                    });",
  "                    nextServerInfos.push({",
  "                        name,",
  "                        owner: expandedConf.owner,",
  "                        visibility: expandedConf.visibility,",
  "                        sharedWithUsers: expandedConf.sharedWithUsers,",
  "                        status: 'disconnected',",
  "                        error: `Failed to construct transport: ${formatErrorForLogging(error)}`,",
  "                        tools: [],",
  "                        prompts: [],",
  "                        resources: [],",
  "                        createTime: Date.now(),",
  "                        enabled: expandedConf.enabled === undefined ? true : expandedConf.enabled,",
  "                        config: expandedConf,",
  "                    });",
  "                    continue;",
  "                }",
  "            }",
].join("\n");
const MCPHUB_LOG_SERVICE_IMPORTER = "/node_modules/@samanhappy/mcphub/dist/services/logService.js";
const MCPHUB_LOG_SERVICE_SHA256 = "9b90bece03fbf452cee757e739da473e864b386c74969d956820539157a557cf";
const MCPHUB_LOG_SERVICE_PROCESS_TRANSFORMATION = "mcphub-log-service-global-process-v1";
const MCPHUB_LOG_SERVICE_PROCESS_IMPORT = "import * as process from 'process';";
const MCPHUB_LOG_SERVICE_GLOBAL_PROCESS = "const process = globalThis.process;";
const MCPHUB_JSON_SCHEMA_VALIDATOR_IMPORTER = "/node_modules/@samanhappy/mcphub/dist/utils/jsonSchemaValidator.js";
const MCPHUB_JSON_SCHEMA_VALIDATOR_TRANSFORMATION = "mcphub-cfworker-json-schema-validator-v1";
const MCP_SDK_VALIDATOR_IMPORTERS = Object.freeze([
  "/node_modules/@modelcontextprotocol/sdk/dist/esm/client/index.js",
  "/node_modules/@modelcontextprotocol/sdk/dist/esm/server/index.js",
]);
const MCP_SDK_VALIDATOR_TRANSFORMATION = "mcp-sdk-cfworker-json-schema-validator-v1";
const MCP_SERVER_NODE_SHIM_IMPORTER = "/node_modules/@modelcontextprotocol/server/dist/shimsNode.mjs";
const MCP_SERVER_VALIDATOR_TRANSFORMATION = "mcp-server-cfworker-json-schema-validator-v1";
const MCP_SERVER_NODE_SHIM_SHA256 = "efa8ef680135a81cd4b3dadaa765ad5cf506523e410c8a9702ab6d9095869d8f";
const MCP_SERVER_PROCESS_IMPORT = 'import process from "node:process";';
const MCP_SERVER_GLOBAL_PROCESS = "const process = globalThis.process;";
const RUNTIME_MODULE_DIR_TRANSFORMATION = "owned-runtime-module-dir-injection-v1";
const REDIS_DIGEST_IMPORTER = "/node_modules/@redis/client/dist/lib/utils/digest.js";
const REDIS_XXHASH_TRANSFORMATION = "redis-optional-xxhash-unavailable-v1";
const TYPEORM_IMPORT_UTILS_IMPORTER = "/node_modules/typeorm/util/ImportUtils.js";
const TYPEORM_IMPORT_UTILS_TRANSFORMATION = "typeorm-dynamic-module-loader-disabled-v1";
const TYPEORM_DIRECTORY_LOADER_IMPORTER = "/node_modules/typeorm/util/DirectoryExportedClassesLoader.js";
const TYPEORM_JSON_LOADER_TRANSFORMATION = "typeorm-dynamic-json-loader-disabled-v1";
const TYPEORM_ROOT_SPECIFIER = "typeorm";
const TYPEORM_SURFACE_TRANSFORMATION = "typeorm-mcphub-import-surface-v1";
const TYPEORM_DRIVER_FACTORY_TRANSFORMATION = "typeorm-postgres-driver-factory-v1";
const TYPEORM_MCPHUB_IMPORTERS = Object.freeze([
  "/node_modules/@samanhappy/mcphub/dist/db/connection.js",
  "/node_modules/@samanhappy/mcphub/dist/db/entities/Activity.js",
  "/node_modules/@samanhappy/mcphub/dist/db/entities/BearerKey.js",
  "/node_modules/@samanhappy/mcphub/dist/db/entities/BuiltinPrompt.js",
  "/node_modules/@samanhappy/mcphub/dist/db/entities/BuiltinResource.js",
  "/node_modules/@samanhappy/mcphub/dist/db/entities/Group.js",
  "/node_modules/@samanhappy/mcphub/dist/db/entities/OAuthClient.js",
  "/node_modules/@samanhappy/mcphub/dist/db/entities/OAuthToken.js",
  "/node_modules/@samanhappy/mcphub/dist/db/entities/Server.js",
  "/node_modules/@samanhappy/mcphub/dist/db/entities/SystemConfig.js",
  "/node_modules/@samanhappy/mcphub/dist/db/entities/User.js",
  "/node_modules/@samanhappy/mcphub/dist/db/entities/UserConfig.js",
  "/node_modules/@samanhappy/mcphub/dist/db/entities/VectorEmbedding.js",
  "/node_modules/@samanhappy/mcphub/dist/db/repositories/ActivityRepository.js",
  "/node_modules/@samanhappy/mcphub/dist/db/repositories/OAuthTokenRepository.js",
  "/node_modules/@samanhappy/mcphub/dist/db/subscribers/VectorEmbeddingSubscriber.js",
]);
const TYPEORM_SURFACE_RELATIVE_PATH = "src/materializer/typeorm-mcphub-surface.mjs";
const TYPEORM_DRIVER_FACTORY_RELATIVE_PATH = "src/materializer/typeorm-postgres-driver-factory.mjs";
const TYPEORM_DATA_SOURCE_IMPORTER = "/node_modules/typeorm/data-source/DataSource.js";
const TYPEORM_CONNECTION_OPTIONS_IMPORTER = "/node_modules/typeorm/connection/ConnectionOptionsReader.js";
const TYPEORM_CONNECTION_OPTIONS_TRANSFORMATION = "typeorm-dynamic-json-config-disabled-v1";
const TYPEORM_QUERY_BUILDER_IMPORTER = "/node_modules/typeorm/query-builder/QueryBuilder.js";
const TYPEORM_QUERY_BUILDER_SHA256 = "5943bc4d90807f249a3f9a12c65cbae9fc6173e0536a9800bc5d128739f696ad";
const TYPEORM_STATIC_QUERY_BUILDER_TRANSFORMATION = "typeorm-static-query-builder-factory-v1";
const TYPEORM_DYNAMIC_QUERY_BUILDER_CREATE = "        return new this.constructor(this.connection, queryRunner ?? this.queryRunner);";
const TYPEORM_STATIC_QUERY_BUILDER_CREATE = [
  "        const builder = this.clone();",
  "        builder.queryRunner = queryRunner ?? this.queryRunner;",
  "        builder.expressionMap = new QueryExpressionMap_1.QueryExpressionMap(this.connection);",
  "        return builder;",
].join("\n");
const TYPEORM_DYNAMIC_QUERY_BUILDER_CLONE = "        return new this.constructor(this);";
const TYPEORM_STATIC_QUERY_BUILDER_CLONE = [
  "        switch (this.expressionMap.queryType) {",
  "            case \"select\": return QueryBuilder.queryBuilderRegistry[\"SelectQueryBuilder\"](this);",
  "            case \"insert\": return QueryBuilder.queryBuilderRegistry[\"InsertQueryBuilder\"](this);",
  "            case \"update\": return QueryBuilder.queryBuilderRegistry[\"UpdateQueryBuilder\"](this);",
  "            case \"delete\": return QueryBuilder.queryBuilderRegistry[\"DeleteQueryBuilder\"](this);",
  "            case \"soft-delete\":",
  "            case \"restore\": return QueryBuilder.queryBuilderRegistry[\"SoftDeleteQueryBuilder\"](this);",
  "            case \"relation\": return QueryBuilder.queryBuilderRegistry[\"RelationQueryBuilder\"](this);",
  "            default: throw new error_1.TypeORMError(`Unsupported query builder clone type: ${this.expressionMap.queryType}`);",
  "        }",
].join("\n");
const APP_ROOT_PATH_IMPORTER = "/node_modules/app-root-path/lib/app-root-path.js";
const APP_ROOT_PATH_TRANSFORMATION = "app-root-path-dynamic-require-disabled-v1";
const APP_ROOT_PATH_INDEX_IMPORTER = "/node_modules/app-root-path/index.js";
const APP_ROOT_PATH_INDEX_SHA256 = "f1ce2f832c30d67d42e5a715827a117c2fc13babad4991af67017105e9add695";
const APP_ROOT_PATH_INDEX_TRANSFORMATION = "app-root-path-filesystem-root-disabled-v1";
const APP_ROOT_PATH_INDEX_DISABLED = [
  "'use strict';",
  "function unavailable() { throw new Error('sealed MCPHub runtime forbids app-root-path filesystem roots'); }",
  "module.exports = Object.freeze({",
  "  require: unavailable,",
  "  resolve: unavailable,",
  "  setPath: unavailable,",
  "  toString: unavailable,",
  "  get path() { return unavailable(); },",
  "});",
  "",
].join("\n");
const APP_ROOT_PATH_RESOLVE_IMPORTER = "/node_modules/app-root-path/lib/resolve.js";
const APP_ROOT_PATH_RESOLVE_SHA256 = "5cf55533205b382822aef9f06a6ecacf0c58ab5d85a6a9cbc12f07bffcf84012";
const APP_ROOT_PATH_RESOLVE_TRANSFORMATION = "app-root-path-static-resolver-v1";
const APP_ROOT_PATH_STATIC_RESOLVER = [
  "'use strict';",
  "var path = require('path');",
  "module.exports = function resolve(dirname) {",
  "  var marker = path.sep + 'node_modules';",
  "  var normalized = path.resolve(dirname);",
  "  var index = normalized.lastIndexOf(marker);",
  "  return index === -1 ? normalized : normalized.slice(0, index);",
  "};",
  "",
].join("\n");
const TYPEORM_PLATFORM_TOOLS_IMPORTER = "/node_modules/typeorm/platform/PlatformTools.js";
const TYPEORM_CWD_FALLBACK_TRANSFORMATION = "typeorm-cwd-node-modules-fallback-disabled-v1";
const TYPEORM_PLATFORM_UNAVAILABLE_TRANSFORMATION = "typeorm-unavailable-optional-packages-v1";
const TYPEORM_PLATFORM_POSTGRES_TRANSFORMATION = "typeorm-postgres-static-package-v1";
const TYPEORM_NON_POSTGRES_TRANSFORMATION = "typeorm-non-postgres-package-load-disabled-v1";
const TYPEORM_PACKAGE_VERSION_TRANSFORMATION = "typeorm-dynamic-package-version-disabled-v1";
const PG_NATIVE_CLIENT_IMPORTER = "/node_modules/pg/lib/native/client.js";
const PG_NATIVE_TRANSFORMATION = "pg-optional-native-unavailable-v1";
const TYPEORM_UNAVAILABLE_PLATFORM_PACKAGES = Object.freeze([
  "@google-cloud/spanner",
  "@sap/hana-client",
  "@sap/hana-client/extension/Stream",
  "ioredis",
  "mongodb",
  "mssql",
  "mysql",
  "mysql2",
  "oracledb",
  "pg-native",
  "pg-query-stream",
  "react-native-sqlite-storage",
  "sql.js",
  "sqlite3",
  "typeorm-aurora-data-api-driver",
]);
const TYPEORM_DISABLED_NON_POSTGRES_PACKAGES = Object.freeze(["better-sqlite3", "redis"]);
const NODE_BUILTIN_RESOLUTION_TRANSFORMATION = "emitted-node-builtins-static-import-v1";
const BARE_BUILTIN_RESOLUTION_TRANSFORMATION = "bare-node-builtin-external-v1";
const OPTIONAL_OTEL_TRANSFORMATION = "optional-opentelemetry-noop-v1";
const TYPEORM_DEEP_IMPORT_TRANSFORMATION = "typeorm-owned-shim-deep-import-v1";
const EXPRESS_VIEW_IMPORTER = "/node_modules/express/lib/view.js";
const EXPRESS_VIEW_TRANSFORMATION = "express-dynamic-view-engine-disabled-v1";
const WS_VALIDATION_IMPORTER = "/node_modules/ws/lib/validation.js";
const WS_BUFFER_UTIL_IMPORTER = "/node_modules/ws/lib/buffer-util.js";
const WS_VALIDATION_TRANSFORMATION = "ws-optional-utf8-validator-unavailable-v1";
const WS_BUFFER_UTIL_TRANSFORMATION = "ws-optional-buffer-accelerator-unavailable-v1";
const DEBUG_NODE_IMPORTER = "/node_modules/.pnpm/debug@4.4.3/node_modules/debug/src/node.js";
const DEBUG_SUPPORTS_COLOR_TRANSFORMATION = "debug-optional-supports-color-unavailable-v1";
const LODASH_IMPORTER = "/node_modules/lodash/lodash.js";
const LODASH_CODEGEN_TRANSFORMATION = "lodash-code-generation-disabled-v1";
const I18NEXT_FS_BACKEND_IMPORTER = "/node_modules/i18next-fs-backend/esm/readFile.js";
const I18NEXT_CODEGEN_TRANSFORMATION = "i18next-js-translation-codegen-disabled-v1";
const MCPHUB_SERVER_SPECIFIER = "@samanhappy/mcphub/dist/server.js";
const MCPHUB_MODULE_DIR_SPECIFIER = "@samanhappy/mcphub/dist/utils/moduleDir.js";
const MCPHUB_SERVER_IMPORT = `import McpHubAppServer from "${MCPHUB_SERVER_SPECIFIER}";`;
const MCPHUB_MODULE_DIR_SETTER_IMPORT = `import { setSealedRuntimeModuleDir as __setMcpHubSealedRuntimeModuleDir } from "${MCPHUB_MODULE_DIR_SPECIFIER}";`;
const MCPHUB_APP_SERVER_CONSTRUCTION = "  const upstream = new McpHubAppServer();";
const MCPHUB_CLI_MAIN_IMPORTER = "/node_modules/@samanhappy/mcphub/dist/cli/main.js";
const MCPHUB_CLI_MAIN_SHA256 = "0516012afb9dae320c9fc1383ae7c9bd58f1a4ae6a7ef5f07056acaf493c79d0";
const MCPHUB_CLI_SELF_RUN_TRANSFORMATION = "mcphub-cli-self-run-disabled-v1";
const MCPHUB_CLI_SELF_RUN = [
  "// Self-run when invoked directly (`tsx src/cli/main.ts ...` or",
  "// `node dist/cli/main.js ...`). bin/cli.js also imports runCli explicitly, so",
  "// the dispatcher works in both modes.",
  "import { fileURLToPath as toPath } from 'node:url';",
  "import process from 'node:process';",
  "const invokedDirectly = process.argv[1] !== undefined &&",
  "    (process.argv[1] === toPath(import.meta.url) ||",
  "        process.argv[1].endsWith('/cli/main.ts') ||",
  "        process.argv[1].endsWith('/cli/main.js'));",
  "if (invokedDirectly) {",
  "    void runCli(process.argv.slice(2));",
  "}",
].join("\n");
const MCPHUB_CLI_SELF_RUN_DISABLED = "// Sealed embedded runtime does not self-dispatch the MCPHub CLI.";
const MCPHUB_MODULE_DIR_FUNCTION = [
  "export function getCurrentModuleDir() {",
  "    const currentModuleFile = fileURLToPath(import.meta.url);",
  "    return path.dirname(currentModuleFile);",
  "}",
].join("\n");
const MCPHUB_SEALED_MODULE_DIR_FUNCTION = [
  "let sealedRuntimeModuleDir;",
  "export function setSealedRuntimeModuleDir(moduleDir) {",
  "    if (sealedRuntimeModuleDir !== undefined || typeof moduleDir !== 'string' || !path.isAbsolute(moduleDir)) {",
  "        throw new Error('sealed MCPHub module directory is invalid or already initialized');",
  "    }",
  "    sealedRuntimeModuleDir = moduleDir;",
  "}",
  "export function getCurrentModuleDir() {",
  "    if (sealedRuntimeModuleDir === undefined) {",
  "        throw new Error('sealed MCPHub module directory is unavailable before runtime initialization');",
  "    }",
  "    return sealedRuntimeModuleDir;",
  "}",
].join("\n");
const MCPHUB_AJV_VALIDATOR_IMPORT = "import { AjvJsonSchemaValidator } from '@modelcontextprotocol/sdk/validation/ajv-provider.js';";
const MCPHUB_CFWORKER_VALIDATOR_IMPORT = "import { CfWorkerJsonSchemaValidator } from '@modelcontextprotocol/sdk/validation/cfworker';";
const MCPHUB_AJV_VALIDATOR_CONSTRUCTION = "        this.delegate = new AjvJsonSchemaValidator();";
const MCPHUB_CFWORKER_VALIDATOR_CONSTRUCTION = "        this.delegate = new CfWorkerJsonSchemaValidator({ draft: '2020-12', shortcircuit: false });";
const MCP_SDK_AJV_VALIDATOR_IMPORT = "import { AjvJsonSchemaValidator } from '../validation/ajv-provider.js';";
const MCP_SDK_CFWORKER_VALIDATOR_IMPORT = "import { CfWorkerJsonSchemaValidator as AjvJsonSchemaValidator } from '@modelcontextprotocol/sdk/validation/cfworker';";
const MCP_SERVER_AJV_VALIDATOR_IMPORT = 'import { n as AjvJsonSchemaValidator } from "./ajvProvider-CEoC__sr.mjs";';
const MCP_SERVER_CFWORKER_VALIDATOR_IMPORT = 'import { CfWorkerJsonSchemaValidator as AjvJsonSchemaValidator } from "@modelcontextprotocol/server/validators/cf-worker";';
const SWAGGER_SCHEMA_VALIDATOR_IMPORTER = "/node_modules/@apidevtools/swagger-parser/lib/validators/schema.js";
const SWAGGER_SCHEMA_VALIDATOR_SHA256 = "42c173ec61dfb01dfeaea675704f1bf9fa65e14ca99ea83033adcc5333c37d87";
const SWAGGER_CFWORKER_VALIDATOR_TRANSFORMATION = "swagger-parser-cfworker-json-schema-validator-v1";
const SWAGGER_CFWORKER_VALIDATOR_SOURCE = [
  '"use strict";',
  'const { Validator } = require("@cfworker/json-schema");',
  'const { openapi } = require("@apidevtools/openapi-schemas");',
  "module.exports = validateSchema;",
  "function validateSchema(api) {",
  "  let schema;",
  '  let draft = "4";',
  "  if (api.swagger) {",
  "    schema = openapi.v2;",
  '  } else if (api.openapi.startsWith("3.1")) {',
  "    schema = openapi.v31;",
  '    draft = "2020-12";',
  "    const schemaDynamicRef = schema.$defs.schema;",
  "    delete schemaDynamicRef.$dynamicAnchor;",
  "    schema.$defs.components.properties.schemas.additionalProperties = schemaDynamicRef;",
  "    schema.$defs.header.dependentSchemas.schema.properties.schema = schemaDynamicRef;",
  '    schema.$defs["media-type"].properties.schema = schemaDynamicRef;',
  "    schema.$defs.parameter.properties.schema = schemaDynamicRef;",
  "  } else {",
  "    schema = openapi.v3;",
  "  }",
  "  const result = new Validator(schema, draft, false).validate(api);",
  "  if (result.valid) return;",
  "  const details = result.errors.map((entry) => ({",
  '    instancePath: typeof entry.instanceLocation === "string" && entry.instanceLocation.startsWith("#")',
  "      ? entry.instanceLocation.slice(1)",
  '      : entry.instanceLocation ?? "",',
  "    keyword: entry.keyword,",
  "    message: entry.error,",
  "  }));",
  '  const message = "Swagger schema validation failed.\\n" + details',
  '    .map((entry) => `  #${entry.instancePath.length ? entry.instancePath : "/"} ${entry.message}\\n`)',
  '    .join("");',
  "  const error = new SyntaxError(message);",
  "  error.details = details;",
  "  throw error;",
  "}",
  "",
].join("\n");
const REDIS_XXHASH_DYNAMIC_BLOCK = [
  "            const module = await import('@node-rs/xxhash');",
  "            xxh3Cache = module.xxh3;",
].join("\n");
const REDIS_XXHASH_UNAVAILABLE = `            throw new Error('The "digest" function requires the "@node-rs/xxhash" package, but it was not found.');`;
const TYPEORM_IMPORT_OR_REQUIRE_FUNCTION = [
  "async function importOrRequireFile(filePath) {",
  "    const tryToImport = async () => {",
  "        // `Function` is required to make sure the `import` statement wil stay `import` after",
  "        // transpilation and won't be converted to `require`",
  "        return [",
  "            // eslint-disable-next-line @typescript-eslint/no-implied-eval",
  '            await Function("return filePath => import(filePath)")()(filePath.startsWith("file://")',
  "                ? filePath",
  "                : (0, url_1.pathToFileURL)(filePath).toString()),",
  '            "esm",',
  "        ];",
  "    };",
  "    const tryToRequire = () => {",
  '        return [require(filePath), "commonjs"];',
  "    };",
  '    const extension = filePath.substring(filePath.lastIndexOf(".") + ".".length);',
  '    if (extension === "mjs" || extension === "mts")',
  "        return tryToImport();",
  '    else if (extension === "cjs" || extension === "cts")',
  "        return tryToRequire();",
  '    else if (extension === "js" || extension === "ts") {',
  "        const packageJson = await getNearestPackageJson(filePath);",
  "        if (packageJson != null) {",
  '            const isModule = packageJson?.type === "module";',
  "            if (isModule)",
  "                return tryToImport();",
  "            else",
  "                return tryToRequire();",
  "        }",
  "        else",
  "            return tryToRequire();",
  "    }",
  "    return tryToRequire();",
  "}",
].join("\n");
const TYPEORM_IMPORT_OR_REQUIRE_DISABLED = [
  "async function importOrRequireFile() {",
  "    throw new Error('sealed MCPHub runtime forbids dynamic TypeORM module loading');",
  "}",
].join("\n");
const TYPEORM_DYNAMIC_JSON_REQUIRE = "        .map((file) => require(PlatformTools_1.PlatformTools.pathResolve(file)));";
const TYPEORM_DYNAMIC_JSON_DISABLED = [
  "        .map(() => {",
  "        throw new Error(\"sealed MCPHub runtime forbids dynamic TypeORM JSON loading\");",
  "    });",
].join("\n");
const TYPEORM_DYNAMIC_CONFIG_REQUIRE = "            connectionOptions = require(configFile);";
const TYPEORM_DYNAMIC_CONFIG_DISABLED = "            throw new Error(\"sealed MCPHub runtime forbids dynamic TypeORM JSON configuration loading\");";
const APP_ROOT_PATH_DYNAMIC_REQUIRE = "\t\t\treturn require(publicInterface.resolve(pathToModule));";
const APP_ROOT_PATH_DYNAMIC_REQUIRE_DISABLED = "\t\t\tthrow new Error('sealed MCPHub runtime forbids app-root-path dynamic module loading');";
const TYPEORM_CWD_FALLBACK_REQUIRE = '            return require(path_1.default.resolve(process.cwd() + "/node_modules/" + name));';
const TYPEORM_CWD_FALLBACK_DISABLED = "            throw err;";
const TYPEORM_PACKAGE_VERSION_REQUIRE = "            return require(`${name}/package.json`).version;";
const TYPEORM_PACKAGE_VERSION_DISABLED = "            throw new Error(`sealed MCPHub runtime forbids dynamic package-version loading for ${name}`);";
const TYPEORM_PG_REQUIRE = 'return require("pg");';
const TYPEORM_PG_STATIC = "return __mcphubTypeormPg.default ?? __mcphubTypeormPg;";
const TYPEORM_PG_IMPORT = 'import * as __mcphubTypeormPg from "pg";';
const PG_NATIVE_REQUIRE = "  Native = require('pg-native')";
const PG_NATIVE_UNAVAILABLE = [
  "  throw Object.assign(new Error('optional pg-native is absent from the sealed dependency closure'), {",
  "    code: 'MODULE_NOT_FOUND'",
  "  })",
].join("\n");
const EXPRESS_DYNAMIC_VIEW_ENGINE_BLOCK = [
  "    // load engine",
  "    var mod = this.ext.slice(1)",
  "    debug('require \"%s\"', mod)",
  "",
  "    // default engine export",
  "    var fn = require(mod).__express",
  "",
  "    if (typeof fn !== 'function') {",
  "      throw new Error('Module \"' + mod + '\" does not provide a view engine.')",
  "    }",
  "",
  "    opts.engines[this.ext] = fn",
].join("\n");
const EXPRESS_DYNAMIC_VIEW_ENGINE_DISABLED = "    throw new Error('sealed MCPHub runtime requires a pre-registered Express view engine')";
const WS_UTF8_REQUIRE = "    const isValidUTF8 = require('utf-8-validate');";
const WS_UTF8_UNAVAILABLE = "    throw new Error('optional utf-8-validate is absent from the sealed dependency closure');";
const WS_BUFFER_UTIL_REQUIRE = "    const bufferUtil = require('bufferutil');";
const WS_BUFFER_UTIL_UNAVAILABLE = "    throw new Error('optional bufferutil is absent from the sealed dependency closure');";
const DEBUG_SUPPORTS_COLOR_REQUIRE = "\tconst supportsColor = require('supports-color');";
const DEBUG_SUPPORTS_COLOR_UNAVAILABLE = "\tthrow new Error('optional supports-color is absent from the sealed dependency closure');";
const LODASH_SHA256 = "f5465f55566bf544aad0a31c6135889ca1ed81eea8f53ec61c6cbe86926f07cf";
const LODASH_FUNCTION_GLOBAL = "  var root = freeGlobal || freeSelf || Function('return this')();";
const LODASH_STATIC_GLOBAL = "  var root = freeGlobal || freeSelf;";
const LODASH_CONTEXT_FUNCTION = "        Function = context.Function,\n";
const LODASH_FUNCTION_PROTOTYPE = "        funcProto = Function.prototype,";
const LODASH_STATIC_FUNCTION_PROTOTYPE = "        funcProto = Object.getPrototypeOf(function() {}),";
const LODASH_UTIL_REQUIRE = "      var types = freeModule && freeModule.require && freeModule.require('util').types;";
const LODASH_STATIC_UTIL = "      var types = __mcphubLodashNodeUtil.types;";
const LODASH_UTIL_IMPORT = 'import * as __mcphubLodashNodeUtil from "node:util";';
const LODASH_DYNAMIC_BUFFER_CONSTRUCTOR = "new buffer.constructor(length)";
const LODASH_STATIC_BUFFER_CONSTRUCTOR = "Buffer.alloc(length)";
const LODASH_DYNAMIC_ARRAY_BUFFER_CONSTRUCTOR = "new arrayBuffer.constructor(arrayBuffer.byteLength)";
const LODASH_STATIC_ARRAY_BUFFER_CONSTRUCTOR = "new ArrayBuffer(arrayBuffer.byteLength)";
const LODASH_DYNAMIC_DATA_VIEW_CONSTRUCTOR = "new dataView.constructor(buffer, dataView.byteOffset, dataView.byteLength)";
const LODASH_STATIC_DATA_VIEW_CONSTRUCTOR = "new DataView(buffer, dataView.byteOffset, dataView.byteLength)";
const LODASH_DYNAMIC_REGEXP_CONSTRUCTOR = "new regexp.constructor(regexp.source, reFlags.exec(regexp))";
const LODASH_STATIC_REGEXP_CONSTRUCTOR = "new RegExp(regexp.source, reFlags.exec(regexp))";
const LODASH_DYNAMIC_TYPED_ARRAY_CONSTRUCTOR = "      return new typedArray.constructor(buffer, typedArray.byteOffset, typedArray.length);";
const LODASH_STATIC_TYPED_ARRAY_CONSTRUCTOR = [
  "      var TypedArrayCtor =",
  "          typedArray instanceof Int8Array ? Int8Array :",
  "          typedArray instanceof Uint8Array ? Uint8Array :",
  "          typedArray instanceof Uint8ClampedArray ? Uint8ClampedArray :",
  "          typedArray instanceof Int16Array ? Int16Array :",
  "          typedArray instanceof Uint16Array ? Uint16Array :",
  "          typedArray instanceof Int32Array ? Int32Array :",
  "          typedArray instanceof Uint32Array ? Uint32Array :",
  "          typedArray instanceof Float32Array ? Float32Array :",
  "          typedArray instanceof Float64Array ? Float64Array :",
  "          typeof BigInt64Array != 'undefined' && typedArray instanceof BigInt64Array ? BigInt64Array :",
  "          typeof BigUint64Array != 'undefined' && typedArray instanceof BigUint64Array ? BigUint64Array : undefined;",
  "      if (!TypedArrayCtor) { throw new TypeError('Unsupported typed array clone'); }",
  "      return new TypedArrayCtor(buffer, typedArray.byteOffset, typedArray.length);",
].join("\n");
const LODASH_DYNAMIC_ARRAY_CONSTRUCTOR = "new array.constructor(length)";
const LODASH_STATIC_ARRAY_CONSTRUCTOR = "new Array(length)";
const I18NEXT_EVAL_ALIAS = "var evalAlias = eval;";
const I18NEXT_EVAL_DISABLED = "var evalAlias = function () { throw new Error('sealed MCPHub runtime forbids executable JavaScript or TypeScript translation files'); };";
const LODASH_TEMPLATE_FUNCTION = [
  "      var result = attempt(function() {",
  "        return Function(importsKeys, sourceURL + 'return ' + source)",
  "          .apply(undefined, importsValues);",
  "      });",
].join("\n");
const LODASH_TEMPLATE_DISABLED = [
  "      var result = attempt(function() {",
  "        throw new Error('sealed MCPHub runtime forbids lodash template compilation');",
  "      });",
].join("\n");
const NODE_SQLITE_DYNAMIC_BLOCK = [
  '\t\t\tconst nodeSqlite = "node:sqlite";',
  "\t\t\t({DatabaseSync} = await import(",
  "\t\t\t\t/* @vite-ignore */",
  "\t\t\t\t/* webpackIgnore: true */",
  "\t\t\t\tnodeSqlite",
  "));",
].join("\n");
const NODE_SQLITE_STATIC_IMPORT = 'import { DatabaseSync as __mcphubNodeDatabaseSync } from "node:sqlite";';
const HAS_OWN_FUNCTION_CALL = "Function.call.bind(Object.prototype.hasOwnProperty)";
const HAS_OWN_STATIC_CALL = "Object.prototype.hasOwnProperty.call.bind(Object.prototype.hasOwnProperty)";
const HAS_OWN_STATIC_TRANSFORMATION = "function-call-has-own-static-v1";
const HAS_INSTANCE_FUNCTION_CALL = "Function.call.bind(Function.prototype[Symbol.hasInstance])";
const HAS_INSTANCE_STATIC_CALL = "Object.getPrototypeOf(function() {}).call.bind(Object.getPrototypeOf(function() {})[Symbol.hasInstance])";
const HAS_INSTANCE_STATIC_TRANSFORMATION = "function-call-symbol-has-instance-static-v1";
const TYPEDARRAY_IMPORTER = "/node_modules/typedarray/index.js";
const TYPEDARRAY_SHA256 = "337fced9a3370de4414170aa0a4b2d61ca634ac2d82c358798afaf2a2a04e107";
const TYPEDARRAY_CONSTRUCTOR_TRANSFORMATION = "typedarray-static-subarray-constructor-v1";
const TYPEDARRAY_DYNAMIC_SUBARRAY = [
  "      return new this.constructor(",
  "        this.buffer, this.byteOffset + start * this.BYTES_PER_ELEMENT, len);",
].join("\n");
const TYPEDARRAY_STATIC_SUBARRAY = [
  "      return new ctor(",
  "        this.buffer, this.byteOffset + start * this.BYTES_PER_ELEMENT, len);",
].join("\n");
const UNDICI_GLOBAL_ORIGIN_IMPORTER = "/node_modules/undici/lib/web/fetch/global.js";
const UNDICI_GLOBAL_ORIGIN_SHA256 = "6b38813b82ec8d5002009640515d35f83ab96d4f8e0066d71fae89324079a289";
const UNDICI_GLOBAL_ORIGIN_TRANSFORMATION = "undici-global-origin-static-symbol-v1";
const UNDICI_GLOBAL_ORIGIN_ACCESS = "globalThis[globalOrigin]";
const UNDICI_GLOBAL_ORIGIN_STATIC_ACCESS = 'globalThis[Symbol.for("undici.globalOrigin.1")]';
const UNDICI_GLOBAL_DISPATCHER_IMPORTER = "/node_modules/undici/lib/global.js";
const UNDICI_GLOBAL_DISPATCHER_SHA256 = "d8e78f218c7bbefdec657f3ae81e31a7f811df511fe951e3a35e3dac1e368e21";
const UNDICI_GLOBAL_DISPATCHER_TRANSFORMATION = "undici-global-dispatcher-static-symbol-v1";
const UNDICI_GLOBAL_DISPATCHER_ACCESS = "globalThis[legacyGlobalDispatcher]";
const UNDICI_GLOBAL_DISPATCHER_STATIC_ACCESS = 'globalThis[Symbol.for("undici.globalDispatcher.1")]';
const ZOD_CORE_IMPORTER = "/node_modules/zod/v4/core/core.js";
const ZOD_CORE_SHA256 = "a5e713beaac4647151e03716a83f51ab714e5337cf66850f3b28eaf072a0bbfe";
const ZOD_JITLESS_TRANSFORMATION = "zod-jitless-runtime-v1";
const ZOD_GLOBAL_CONFIG_INITIALIZER = "(_a = globalThis).__zod_globalConfig ?? (_a.__zod_globalConfig = {});";
const ZOD_JITLESS_GLOBAL_CONFIG_INITIALIZER = [
  ZOD_GLOBAL_CONFIG_INITIALIZER,
  "globalThis.__zod_globalConfig.jitless = true;",
].join("\n");
const ZOD_UTIL_IMPORTER = "/node_modules/zod/v4/core/util.js";
const ZOD_UTIL_SHA256 = "968e3433e810cf7ba5efb609a1cb6d9a6cfb51215fd1f699938228f7ac25deb3";
const ZOD_ALLOWS_EVAL = [
  "export const allowsEval = /* @__PURE__*/ cached(() => {",
  "    // Skip the probe under `jitless`: strict CSPs report the caught `new Function`",
  "    // as a `securitypolicyviolation` even though the throw is swallowed.",
  "    if (globalConfig.jitless) {",
  "        return false;",
  "    }",
  "    // @ts-ignore",
  "    if (typeof navigator !== \"undefined\" && navigator?.userAgent?.includes(\"Cloudflare\")) {",
  "        return false;",
  "    }",
  "    try {",
  "        const F = Function;",
  "        new F(\"\");",
  "        return true;",
  "    }",
  "    catch (_) {",
  "        return false;",
  "    }",
  "});",
].join("\n");
const ZOD_ALLOWS_EVAL_DISABLED = "export const allowsEval = /* @__PURE__*/ cached(() => false);";
const ZOD_DOC_IMPORTER = "/node_modules/zod/v4/core/doc.js";
const ZOD_DOC_SHA256 = "e084bbcc536746a8942fd33b08afe4db345554b3a0383114f1dca95261c958d9";
const ZOD_DOC_COMPILE = [
  "    compile() {",
  "        const F = Function;",
  "        const args = this?.args;",
  "        const content = this?.content ?? [``];",
  "        const lines = [...content.map((x) => `  ${x}`)];",
  "        // console.log(lines.join(\"\\n\"));",
  "        return new F(...args, lines.join(\"\\n\"));",
  "    }",
].join("\n");
const ZOD_DOC_COMPILE_DISABLED = [
  "    compile() {",
  "        throw new Error(\"sealed MCPHub runtime requires Zod jitless parsing\");",
  "    }",
].join("\n");
const REFLECT_METADATA_IMPORTER = "/node_modules/reflect-metadata/Reflect.js";
const REFLECT_METADATA_SHA256 = "515c16dcde7492755691e3fca9eeca4656f1819b6e3307ecd4b0deaa93ad21e2";
const REFLECT_METADATA_STATIC_GLOBAL_TRANSFORMATION = "reflect-metadata-static-global-v1";
const REFLECT_METADATA_DYNAMIC_GLOBAL = [
  "        function functionThis() {",
  "            try {",
  "                return Function(\"return this;\")();",
  "            }",
  "            catch (_) { }",
  "        }",
  "        function indirectEvalThis() {",
  "            try {",
  "                return (void 0, eval)(\"(function() { return this; })()\");",
  "            }",
  "            catch (_) { }",
  "        }",
  "        function sloppyModeThis() {",
  "            return functionThis() || indirectEvalThis();",
  "        }",
].join("\n");
const REFLECT_METADATA_STATIC_GLOBAL = [
  "        function sloppyModeThis() {",
  "            return {};",
  "        }",
].join("\n");
const REFLECT_METADATA_FUNCTION_PROTOTYPE = "        var functionPrototype = Object.getPrototypeOf(Function);";
const REFLECT_METADATA_STATIC_FUNCTION_PROTOTYPE = "        var functionPrototype = Object.getPrototypeOf(function () {});";
const NODE_GYP_BUILD_IMPORTER = "/node_modules/node-gyp-build/index.js";
const NODE_GYP_BUILD_SHA256 = "a7ed0d5ae218a19bdbdf15a590d0893790ddf536313b66a787554693cfaae078";
const NODE_GYP_BUILD_TRANSFORMATION = "node-gyp-build-native-loader-disabled-v1";
const MCPHUB_USER_DAO_IMPORTER = "/node_modules/@samanhappy/mcphub/dist/dao/UserDaoDbImpl.js";
const MCPHUB_USER_DAO_SHA256 = "f672ec819bb0769d90dbfc33df7c090d995629474e934307e868b6eace533791";
const MCPHUB_USER_DAO_BCRYPTJS_TRANSFORMATION = "mcphub-user-dao-bcryptjs-v1";
const MCPHUB_USER_DAO_BCRYPT = "import bcrypt from 'bcrypt';";
const MCPHUB_USER_DAO_BCRYPTJS = "import bcrypt from 'bcryptjs';";
const MCPHUB_PATH_IMPORTER = "/node_modules/@samanhappy/mcphub/dist/utils/path.js";
const MCPHUB_PATH_SHA256 = "85ddabb827995e560bd09855630667e7ae7692bb5830a85dcf381b2e62587cba";
const MCPHUB_PATH_FILENAME_TRANSFORMATION = "mcphub-package-root-commonjs-fallback-disabled-v1";
const MCPHUB_PATH_FILENAME_FALLBACK = [
  "    if (typeof __filename !== 'undefined') {",
  "        const moduleDir = path.dirname(__filename);",
  "        possibleRoots.push(path.resolve(moduleDir, '..', '..'), path.resolve(moduleDir, '..'));",
  "    }",
].join("\n");
const UNDICI_INDEX_IMPORTER = "/node_modules/undici/index.js";
const UNDICI_INDEX_SHA256 = "dca95e2bbf4bae18325a4e5d9c887427a8a63a1345ed92a46f1067360dec0ffa";
const UNDICI_INDEX_FETCH_IMPORTER = "/node_modules/undici/index-fetch.js";
const UNDICI_INDEX_FETCH_SHA256 = "155df504376841f714239ffbb43c7fbbfe3532c44aafe19ca7fd1615a18d5f1d";
const UNDICI_FILENAME_TRANSFORMATION = "undici-commonjs-filename-disabled-v1";
const UNDICI_CURRENT_FILENAME = "const currentFilename = typeof __filename !== 'undefined' ? __filename : undefined";
const UNDICI_CURRENT_FILENAME_DISABLED = "const currentFilename = undefined";
const NODE_GYP_BUILD_DISABLED = [
  "module.exports = function unavailableNativeAddon() {",
  "  throw new Error('native addons are absent from the sealed MCPHub dependency closure');",
  "};",
  "",
].join("\n");
const QS_BROWSER_IMPORTER = "/node_modules/qs/dist/qs.js";
const QS_BROWSER_SHA256 = "0c03b0fabdac1e6514db5bdb2e9d21f17b31a9e11a1cfdeef3c433474f6de8b5";
const QS_INTRINSIC_CODEGEN_TRANSFORMATION = "qs-intrinsic-codegen-disabled-v1";
const QS_FUNCTION_INTRINSIC = "$Function=Function";
const QS_FUNCTION_INTRINSIC_DISABLED = "$Function=undefined";
const QS_EVAL_INTRINSIC = '"%eval%":eval';
const QS_EVAL_INTRINSIC_DISABLED = '"%eval%":undefined';
const GET_INTRINSIC_IMPORTER = "/node_modules/get-intrinsic/index.js";
const GET_INTRINSIC_SHA256 = "c3bc7278af37cede0da2db32724fa0b89a07c44205c44c4f5db0e4d8d497d49c";
const GET_INTRINSIC_CODEGEN_TRANSFORMATION = "get-intrinsic-codegen-disabled-v1";
const GET_INTRINSIC_FUNCTION = "var $Function = Function;";
const GET_INTRINSIC_FUNCTION_DISABLED = "var $Codegen = undefined;";
const GET_INTRINSIC_FUNCTION_CALL = "return $Function(";
const GET_INTRINSIC_FUNCTION_CALL_DISABLED = "return $Codegen(";
const GET_INTRINSIC_FUNCTION_VALUE = "'%Function%': $Function,";
const GET_INTRINSIC_FUNCTION_VALUE_DISABLED = "'%Function%': $Codegen,";
const GET_INTRINSIC_EVAL = "\t'%eval%': eval, // eslint-disable-line no-eval";
const GET_INTRINSIC_EVAL_DISABLED = "\t'%eval%': undefined,";
const FUNCTION_BIND_IMPORTER = "/node_modules/function-bind/implementation.js";
const FUNCTION_BIND_SHA256 = "5c52eb40601e0716dafff9759cf28d8d4af3e2fc2e2c96384f43dbfd0f7370b5";
const FUNCTION_BIND_TRANSFORMATION = "function-bind-native-only-v1";
const FUNCTION_BIND_NATIVE_ONLY = [
  "'use strict';",
  "module.exports = Object.getPrototypeOf(function () {}).bind;",
  "",
].join("\n");
const DEPD_IMPORTER = "/node_modules/depd/index.js";
const DEPD_SHA256 = "4d587a5662e20a7bb9bfe6555afe5987e1b80303a819b447394f37a93297ee91";
const DEPD_STATIC_WRAPPER_TRANSFORMATION = "depd-static-wrapper-v1";
const DEPD_DYNAMIC_WRAPPER = [
  "  // eslint-disable-next-line no-new-func",
  "  var deprecatedfn = new Function('fn', 'log', 'deprecate', 'message', 'site',",
  "    '\"use strict\"\\n' +",
  "    'return function (' + args + ') {' +",
  "    'log.call(deprecate, message, site)\\n' +",
  "    'return fn.apply(this, arguments)\\n' +",
  "    '}')(fn, log, this, message, site)",
].join("\n");
const DEPD_STATIC_WRAPPER = [
  "  var deprecate = this",
  "  var deprecatedfn = function () {",
  "    log.call(deprecate, message, site)",
  "    return fn.apply(this, arguments)",
  "  }",
].join("\n");
const MCP_SDK_STDIO_SERVER_IMPORTER = "/node_modules/@modelcontextprotocol/sdk/dist/esm/server/stdio.js";
const MCP_SDK_STDIO_SERVER_SHA256 = "f5acc5bf1651b872f62fc574682bae010b5ac56118ed617dffd3710dbfa36b90";
const MCP_SDK_STDIO_CLIENT_IMPORTER = "/node_modules/@modelcontextprotocol/sdk/dist/esm/client/stdio.js";
const MCP_SDK_STDIO_CLIENT_SHA256 = "a59fe1acb5cb7fd4c2973e9d86d8b3fdb3ce476dca62ecb752c59dcf876d4f57";
const MCP_SDK_GLOBAL_PROCESS_TRANSFORMATION = "mcp-sdk-stdio-global-process-v1";
const MCP_SDK_PROCESS_IMPORT = "import process from 'node:process';\n";
const FETCH_BLOB_STREAMS_IMPORTER = "/node_modules/fetch-blob/streams.cjs";
const FETCH_BLOB_STREAMS_SHA256 = "15fb4df5ad63eb35c7b00f7ffacc41848ae9c77e3d9fc7ff7ce229908d7752ae";
const FETCH_BLOB_GLOBAL_PROCESS_TRANSFORMATION = "fetch-blob-global-process-v1";
const FETCH_BLOB_PROCESS_REQUIRE = "    const process = require('node:process')";
const FETCH_BLOB_GLOBAL_PROCESS = "    const process = globalThis.process";
const GOOGLE_GENAI_NODE_IMPORTER = "/node_modules/@google/genai/dist/node/index.mjs";
const GOOGLE_GENAI_NODE_SHA256 = "748f86443c1c2c80e4ecf568d0c033ad9f1e9f34926c810e35c77e965a951c33";
const GOOGLE_GENAI_STATIC_CLIENT_TRANSFORMATION = "google-genai-static-client-constructor-v1";
const GOOGLE_GENAI_DYNAMIC_CLIENT = "new this.constructor(Object.assign(Object.assign(Object.assign({}, this._options)";
const GOOGLE_GENAI_STATIC_CLIENT = "new GeminiNextGenAPIClient(Object.assign(Object.assign(Object.assign({}, this._options)";
const OPENAI_CLIENT_IMPORTER = "/node_modules/openai/client.mjs";
const OPENAI_CLIENT_SHA256 = "9d4d9dea8292ecb184279344845826997474326dd4e0956cc2ec1a7d547b1877";
const OPENAI_STATIC_CLIENT_TRANSFORMATION = "openai-static-client-constructor-v1";
const OPENAI_DYNAMIC_CLIENT = "const client = new this.constructor({";
const OPENAI_STATIC_CLIENT = "const client = new OpenAI({";
const NOBLE_SHA2_IMPORTER = "/node_modules/@noble/hashes/sha2.js";
const NOBLE_SHA2_SHA256 = "471746bba6ec4c6238ca41358d1d3b40b6ff31cf3363f0b4d550c649c1a8e83b";
const NOBLE_SHA2_STATIC_CLONE_TRANSFORMATION = "noble-sha2-static-clone-v1";
const NOBLE_SHA2_32_DYNAMIC_CLONE = [
  "    _cloneInto(to) {",
  "        (to ||= new this.constructor()).set(...this.get());",
  "        return this._cloneIntoMeta(to);",
  "    }",
  "    process(view, offset) {",
  "        // Extend the first 16 words into the remaining 48 words w[16..63] of the message schedule array",
].join("\n");
const NOBLE_SHA2_32_STATIC_CLONE = [
  "    _cloneInto(to) {",
  "        to ||= this instanceof _SHA256 ? new _SHA256() : this instanceof _SHA224 ? new _SHA224() : undefined;",
  "        if (to === undefined) throw new Error('Unsupported SHA2_32B clone type');",
  "        to.set(...this.get());",
  "        return this._cloneIntoMeta(to);",
  "    }",
  "    process(view, offset) {",
  "        // Extend the first 16 words into the remaining 48 words w[16..63] of the message schedule array",
].join("\n");
const NOBLE_SHA2_64_DYNAMIC_CLONE = [
  "    _cloneInto(to) {",
  "        (to ||= new this.constructor()).set(...this.get());",
  "        return this._cloneIntoMeta(to);",
  "    }",
  "    process(view, offset) {",
  "        // Extend the first 16 words into the remaining 64 words w[16..79] of the message schedule array",
].join("\n");
const NOBLE_SHA2_64_STATIC_CLONE = [
  "    _cloneInto(to) {",
  "        to ||= this instanceof _SHA512 ? new _SHA512() : this instanceof _SHA384 ? new _SHA384() : this instanceof _SHA512_224 ? new _SHA512_224() : this instanceof _SHA512_256 ? new _SHA512_256() : undefined;",
  "        if (to === undefined) throw new Error('Unsupported SHA2_64B clone type');",
  "        to.set(...this.get());",
  "        return this._cloneIntoMeta(to);",
  "    }",
  "    process(view, offset) {",
  "        // Extend the first 16 words into the remaining 64 words w[16..79] of the message schedule array",
].join("\n");

function invariant(condition, message) {
  if (!condition) throw new Error(message);
}

function replaceExactlyOnce(code, anchor, replacement, label) {
  invariant(code.split(anchor).length === 2, `${label} anchor drift`);
  return code.replace(anchor, replacement);
}

function transformEvent(events, { name, kind, source = null, importer = null, target, preimage, postimage }) {
  const event = Object.freeze({
    name,
    kind,
    source,
    importer,
    target,
    preimageSha256: sha256Bytes(Buffer.from(preimage, "utf8")),
    postimageSha256: sha256Bytes(Buffer.from(postimage, "utf8")),
    count: 1,
  });
  const key = canonicalJson(event);
  if (events.has(key)) return;
  events.set(key, event);
}

function replaceWithEvent(code, anchor, replacement, { events, name, target, label, postimage = replacement }) {
  const transformed = replaceExactlyOnce(code, anchor, replacement, label);
  transformEvent(events, {
    name,
    kind: "replacement",
    target,
    preimage: anchor,
    postimage,
  });
  return transformed;
}

function prependWithEvent(code, prefix, { events, name, target, label }) {
  const anchor = code.slice(0, Math.min(code.length, 96));
  invariant(anchor.length > 0 && code.startsWith(anchor), `${label} prefix anchor drift`);
  transformEvent(events, {
    name,
    kind: "prefix-injection",
    target,
    preimage: anchor,
    postimage: `${prefix}\n${anchor}`,
  });
  return `${prefix}\n${code}`;
}

function transformLockedMcpHubSource({ code, normalizedId, target, transformations, events }) {
  if (normalizedId.endsWith(MCPHUB_SSRF_IMPORTER)) {
    invariant(
      sha256Bytes(Buffer.from(code, "utf8")) === MCPHUB_SSRF_SHA256,
      `MCPHub SSRF source drift (${normalizedId})`,
    );
    transformations.add(MCPHUB_SSRF_RFC6598_TRANSFORMATION);
    return replaceWithEvent(
      code,
      MCPHUB_SSRF_OVERBROAD_CGNAT_RANGE,
      MCPHUB_SSRF_RFC6598_CGNAT_RANGE,
      {
        events,
        name: MCPHUB_SSRF_RFC6598_TRANSFORMATION,
        target,
        label: `MCPHub SSRF RFC6598 CGNAT range (${normalizedId})`,
      },
    );
  }
  if (normalizedId.endsWith(MCPHUB_MCP_SERVICE_IMPORTER)) {
    invariant(
      sha256Bytes(Buffer.from(code, "utf8")) === MCPHUB_MCP_SERVICE_SHA256,
      `MCPHub MCP service source drift (${normalizedId})`,
    );
    transformations.add(MCPHUB_TRANSPORT_ISOLATION_TRANSFORMATION);
    return replaceWithEvent(
      code,
      MCPHUB_UNISOLATED_TRANSPORT_CONSTRUCTION,
      MCPHUB_ISOLATED_TRANSPORT_CONSTRUCTION,
      {
        events,
        name: MCPHUB_TRANSPORT_ISOLATION_TRANSFORMATION,
        target,
        label: `MCPHub backend transport construction (${normalizedId})`,
      },
    );
  }
  return null;
}

export function transformLockedMcpHubSourceForUnitTest({ code, relativePath }) {
  invariant(process.env.NODE_TEST_CONTEXT !== undefined, "test-only MCPHub source transformation is unavailable outside node:test");
  invariant(typeof code === "string" && typeof relativePath === "string", "test-only MCPHub source transformation input is invalid");
  const normalizedId = `/${relativePath}`;
  invariant(
    normalizedId.endsWith(MCPHUB_SSRF_IMPORTER) || normalizedId.endsWith(MCPHUB_MCP_SERVICE_IMPORTER),
    "test-only MCPHub source transformation target is invalid",
  );
  const transformations = new Set();
  const events = new Map();
  const transformed = transformLockedMcpHubSource({
    code,
    normalizedId,
    target: relativePath,
    transformations,
    events,
  });
  invariant(transformed !== null, "test-only MCPHub source transformation was not applied");
  return Object.freeze({
    code: transformed,
    transformations: Object.freeze([...transformations].sort()),
    transformEvents: Object.freeze([...events.values()].sort((left, right) => codeUnitCompare(canonicalJson(left), canonicalJson(right)))),
  });
}

function codeUnitCompare(left, right) {
  return left < right ? -1 : left > right ? 1 : 0;
}

function normalizedTarget(inventoryRoot, id) {
  return portableRelative(inventoryRoot, id, "transformation target");
}

function portableRelative(root, candidate, label) {
  invariant(path.isAbsolute(root) && path.isAbsolute(candidate), `${label} paths must be absolute`);
  const relative = path.relative(root, candidate).split(path.sep).join("/");
  invariant(relative.length > 0 && relative !== "." && !relative.startsWith("../") && !path.posix.isAbsolute(relative), `${label} escapes the inventory root`);
  return relative;
}

function ownedInventoryPath(inventoryRoot, relativePath) {
  const target = path.join(inventoryRoot, ...relativePath.split("/"));
  invariant(portableRelative(inventoryRoot, target, "owned transformation target") === relativePath, `owned transformation target is invalid: ${relativePath}`);
  return target;
}

function moduleKind(relativePath) {
  if (relativePath.startsWith("src/")) return "owned-source";
  if (relativePath.includes("node_modules/")) return "locked-dependency";
  return "build-input";
}

function failLog(level, log, defaultHandler) {
  if (level === "warn") {
    const location = typeof log.id === "string" ? ` in ${log.id}` : "";
    const detail = typeof log.message === "string" ? `: ${log.message}` : "";
    throw new Error(`rolldown warning is forbidden: ${log.code ?? "UNKNOWN"}${location}${detail}`);
  }
  if (level === "error") defaultHandler(level, log);
}

function assertLiteralDynamicImports(ast, id, sourceText) {
  const pending = [ast];
  const seen = new WeakSet();
  while (pending.length > 0) {
    const value = pending.pop();
    if (value === null || typeof value !== "object" || seen.has(value)) continue;
    seen.add(value);
    if (value.type === "ImportExpression") {
      const offset = Number.isInteger(value.start) ? value.start : null;
      const snippet = offset === null ? "" : `: ${JSON.stringify(sourceText.slice(offset, Math.min(sourceText.length, offset + 160)))}`;
      invariant(
        value.source?.type === "Literal" && typeof value.source.value === "string",
        `computed dynamic import is forbidden in ${id} at offset ${offset ?? "unknown"}${snippet}`,
      );
    }
    for (const child of Object.values(value)) {
      if (Array.isArray(child)) pending.push(...child);
      else if (child !== null && typeof child === "object") pending.push(child);
    }
  }
}

function astConstantString(node) {
  if (node?.type === "Literal" && typeof node.value === "string") return node.value;
  if (node?.type === "BinaryExpression" && node.operator === "+") {
    const left = astConstantString(node.left);
    const right = astConstantString(node.right);
    return left === null || right === null ? null : `${left}${right}`;
  }
  if (node?.type === "TemplateLiteral") {
    let value = "";
    for (let index = 0; index < node.quasis.length; index += 1) {
      value += node.quasis[index].value.cooked;
      if (index < node.expressions.length) {
        const expression = astConstantString(node.expressions[index]);
        if (expression === null) return null;
        value += expression;
      }
    }
    return value;
  }
  if (
    node?.type === "CallExpression"
    && node.callee?.type === "MemberExpression"
    && !node.callee.computed
    && node.callee.property?.name === "join"
    && node.callee.object?.type === "ArrayExpression"
    && node.arguments?.length <= 1
  ) {
    const separator = node.arguments.length === 0 ? "," : astConstantString(node.arguments[0]);
    if (separator === null) return null;
    const elements = node.callee.object.elements.map((element) => astConstantString(element));
    return elements.some((element) => element === null) ? null : elements.join(separator);
  }
  return null;
}

function astMemberProperty(node, constantStrings) {
  if (node?.type !== "MemberExpression") return null;
  return node.computed
    ? astConstantString(node.property) ?? (node.property?.type === "Identifier" ? constantStrings.get(node.property.name) ?? null : null)
    : node.property?.name ?? null;
}

function astStaticGlobalSymbolName(node) {
  return node?.type === "CallExpression"
    && node.callee?.type === "MemberExpression"
    && !node.callee.computed
    && node.callee.object?.type === "Identifier"
    && node.callee.object.name === "Symbol"
    && node.callee.property?.name === "for"
    && node.arguments?.length === 1
    ? astConstantString(node.arguments[0])
    : null;
}

function astStaticGlobalSymbol(node, staticGlobalSymbols) {
  return astStaticGlobalSymbolName(node) !== null
    || (node?.type === "Identifier" && staticGlobalSymbols.has(node.name));
}

function assertSealedOutputAst(ast, id, sourceText) {
  const pending = [ast];
  const seen = new WeakSet();
  const parents = new WeakMap();
  const processAliases = new Set(["process"]);
  const globalAliases = new Set(["global", "globalThis"]);
  const reflectAliases = new Set(["Reflect"]);
  const reflectGetAliases = new Set();
  const processFactoryAliases = new Set();
  const globalFactoryAliases = new Set();
  const staticGlobalSymbols = new Map();
  const constantStrings = new Map();
  const declarators = [];
  const namedFunctions = [];
  const nodes = [];
  while (pending.length > 0) {
    const value = pending.pop();
    if (value === null || typeof value !== "object" || seen.has(value)) continue;
    seen.add(value);
    nodes.push(value);
    if (value.type === "VariableDeclarator") declarators.push(value);
    if (value.type === "FunctionDeclaration" && value.id?.type === "Identifier") {
      namedFunctions.push(value);
    }
    for (const child of Object.values(value)) {
      if (Array.isArray(child)) {
        for (const item of child) {
          if (item !== null && typeof item === "object" && !parents.has(item)) parents.set(item, value);
          pending.push(item);
        }
      } else if (child !== null && typeof child === "object") {
        if (!parents.has(child)) parents.set(child, value);
        pending.push(child);
      }
    }
  }
  // Rolldown's one-chunk output reuses identifier spellings across lexical
  // scopes. A name-only fixed-point scan can therefore oscillate forever when
  // two bindings with the same spelling hold different constants, and reverse
  // alias chains make a full declarator rescan quadratic. Keep the deliberately
  // conservative name-based safety model, but propagate it through a monotonic
  // dependency worklist. Conflicting constants become unknown, which makes
  // computed global access fail closed instead of selecting an arbitrary scope.
  const ambiguousConstants = new Set();
  const dependents = new Map();
  const worklist = [];
  const queued = new Set();
  const enqueue = (index) => {
    if (queued.has(index)) return;
    queued.add(index);
    worklist.push(index);
  };
  const enqueueDependents = (name) => {
    for (const index of dependents.get(name) ?? []) enqueue(index);
  };
  const registerDependency = (name, index) => {
    if (typeof name !== "string") return;
    const indexes = dependents.get(name) ?? new Set();
    indexes.add(index);
    dependents.set(name, indexes);
  };
  const directReturnedExpressions = (functionNode) => {
    if (functionNode?.type === "ArrowFunctionExpression" && functionNode.body?.type !== "BlockStatement") {
      return [functionNode.body];
    }
    const expressions = [];
    const stack = [...(functionNode?.body?.body ?? [])];
    while (stack.length > 0) {
      const current = stack.pop();
      if (current === null || typeof current !== "object") continue;
      if (current !== functionNode && (
        current.type === "FunctionDeclaration"
        || current.type === "FunctionExpression"
        || current.type === "ArrowFunctionExpression"
      )) continue;
      if (current.type === "ReturnStatement" && current.argument) {
        expressions.push(current.argument);
        continue;
      }
      for (const child of Object.values(current)) {
        if (Array.isArray(child)) stack.push(...child);
        else if (child !== null && typeof child === "object") stack.push(child);
      }
    }
    return expressions;
  };
  const returnedAliasKind = (functionNode) => {
    let returnsProcess = false;
    let returnsGlobal = false;
    for (const expression of directReturnedExpressions(functionNode)) {
      if (expression.type === "Identifier") {
        returnsProcess ||= processAliases.has(expression.name);
        returnsGlobal ||= globalAliases.has(expression.name);
      }
      if (
        expression.type === "MemberExpression"
        && expression.object?.type === "Identifier"
        && globalAliases.has(expression.object.name)
        && astMemberProperty(expression, constantStrings) === "process"
      ) {
        returnsProcess = true;
      }
    }
    return { returnsProcess, returnsGlobal };
  };
  for (const [index, declaration] of declarators.entries()) {
    if (declaration.init?.type === "Identifier") registerDependency(declaration.init.name, index);
    if (declaration.init?.type === "MemberExpression") {
      if (declaration.init.object?.type === "Identifier") registerDependency(declaration.init.object.name, index);
      if (declaration.init.computed && declaration.init.property?.type === "Identifier") {
        registerDependency(declaration.init.property.name, index);
      }
    }
    if (declaration.init?.type === "CallExpression" && declaration.init.callee?.type === "Identifier") {
      registerDependency(declaration.init.callee.name, index);
    }
    enqueue(index);
  }
  const mergeConstant = (name, value) => {
    if (ambiguousConstants.has(name)) return;
    if (value === null) return;
    if (value === undefined) {
      constantStrings.delete(name);
      ambiguousConstants.add(name);
      enqueueDependents(name);
      return;
    }
    const existing = constantStrings.get(name);
    if (existing === undefined) {
      constantStrings.set(name, value);
      enqueueDependents(name);
    } else if (existing !== value) {
      constantStrings.delete(name);
      ambiguousConstants.add(name);
      enqueueDependents(name);
    }
  };
  const addAlias = (aliases, name) => {
    if (aliases.has(name)) return;
    aliases.add(name);
    enqueueDependents(name);
  };
  for (const declaration of namedFunctions) {
    const returned = returnedAliasKind(declaration);
    if (returned.returnsProcess) addAlias(processFactoryAliases, declaration.id.name);
    if (returned.returnsGlobal) addAlias(globalFactoryAliases, declaration.id.name);
  }
  for (let cursor = 0; cursor < worklist.length; cursor += 1) {
    const index = worklist[cursor];
    queued.delete(index);
    const declaration = declarators[index];
    if (declaration.id?.type === "Identifier") {
      const direct = astConstantString(declaration.init);
      if (direct !== null) mergeConstant(declaration.id.name, direct);
      else if (declaration.init?.type === "Identifier") {
        if (ambiguousConstants.has(declaration.init.name)) mergeConstant(declaration.id.name, undefined);
        else mergeConstant(declaration.id.name, constantStrings.get(declaration.init.name) ?? null);
      }
    }
    if (
      declaration.id?.type === "Identifier"
      && declaration.init?.type === "Identifier"
      && processAliases.has(declaration.init.name)
    ) {
      addAlias(processAliases, declaration.id.name);
    }
    if (
      declaration.id?.type === "Identifier"
      && declaration.init?.type === "MemberExpression"
      && declaration.init.object?.type === "Identifier"
      && globalAliases.has(declaration.init.object.name)
      && astMemberProperty(declaration.init, constantStrings) === "process"
    ) {
      addAlias(processAliases, declaration.id.name);
    }
    if (
      declaration.id?.type === "ObjectPattern"
      && declaration.init?.type === "Identifier"
      && globalAliases.has(declaration.init.name)
    ) {
      for (const property of declaration.id.properties ?? []) {
        if (
          property?.type === "Property"
          && !property.computed
          && (property.key?.name ?? property.key?.value) === "process"
          && property.value?.type === "Identifier"
        ) {
          addAlias(processAliases, property.value.name);
        }
      }
    }
    if (
      declaration.id?.type === "Identifier"
      && declaration.init?.type === "Identifier"
      && globalAliases.has(declaration.init.name)
    ) {
      addAlias(globalAliases, declaration.id.name);
    }
    if (
      declaration.id?.type === "Identifier"
      && declaration.init?.type === "CallExpression"
      && declaration.init.callee?.type === "Identifier"
      && processFactoryAliases.has(declaration.init.callee.name)
    ) {
      addAlias(processAliases, declaration.id.name);
    }
    if (
      declaration.id?.type === "Identifier"
      && declaration.init?.type === "CallExpression"
      && declaration.init.callee?.type === "Identifier"
      && globalFactoryAliases.has(declaration.init.callee.name)
    ) {
      addAlias(globalAliases, declaration.id.name);
    }
    if (
      declaration.id?.type === "Identifier"
      && declaration.init?.type === "Identifier"
      && reflectAliases.has(declaration.init.name)
    ) {
      addAlias(reflectAliases, declaration.id.name);
    }
    if (
      declaration.id?.type === "Identifier"
      && (declaration.init?.type === "ArrowFunctionExpression" || declaration.init?.type === "FunctionExpression")
    ) {
      const returned = returnedAliasKind(declaration.init);
      if (returned.returnsProcess) addAlias(processFactoryAliases, declaration.id.name);
      if (returned.returnsGlobal) addAlias(globalFactoryAliases, declaration.id.name);
    }
    if (declaration.id?.type === "Identifier" && declaration.init?.type === "Identifier") {
      if (processFactoryAliases.has(declaration.init.name)) addAlias(processFactoryAliases, declaration.id.name);
      if (globalFactoryAliases.has(declaration.init.name)) addAlias(globalFactoryAliases, declaration.id.name);
    }
    if (
      declaration.id?.type === "Identifier"
      && declaration.init?.type === "MemberExpression"
      && declaration.init.object?.type === "Identifier"
      && reflectAliases.has(declaration.init.object.name)
      && astMemberProperty(declaration.init, constantStrings) === "get"
    ) {
      addAlias(reflectGetAliases, declaration.id.name);
    }
    if (
      declaration.id?.type === "ObjectPattern"
      && declaration.init?.type === "Identifier"
      && reflectAliases.has(declaration.init.name)
    ) {
      for (const property of declaration.id.properties ?? []) {
        const propertyName = property?.computed ? astConstantString(property.key) : property?.key?.name ?? property?.key?.value;
        if (property?.type === "Property" && propertyName === "get" && property.value?.type === "Identifier") {
          addAlias(reflectGetAliases, property.value.name);
        }
      }
    }
  }
  const declarationsByName = new Map();
  for (const declaration of declarators) {
    if (declaration.id?.type === "Identifier") {
      const declarations = declarationsByName.get(declaration.id.name) ?? [];
      declarations.push(declaration);
      declarationsByName.set(declaration.id.name, declarations);
    }
  }
  for (const [name, declarations] of declarationsByName) {
    const symbols = declarations.map((declaration) => astStaticGlobalSymbolName(declaration.init));
    if (symbols.every((symbol) => symbol !== null) && new Set(symbols).size === 1) {
      staticGlobalSymbols.set(name, symbols[0]);
    }
  }
  const forbiddenComputedGlobalLoaders = new Set(["Function", "createRequire", "dlopen", "eval", "getBuiltinModule", "process", "require"]);
  const referencesAlias = (node, aliases) => {
    const stack = [node];
    const localSeen = new WeakSet();
    while (stack.length > 0) {
      const current = stack.pop();
      if (current === null || typeof current !== "object" || localSeen.has(current)) continue;
      localSeen.add(current);
      if (current.type === "Identifier" && aliases.has(current.name)) return true;
      for (const child of Object.values(current)) {
        if (Array.isArray(child)) stack.push(...child);
        else if (child !== null && typeof child === "object") stack.push(child);
      }
    }
    return false;
  };
  for (const value of nodes) {
    const offset = Number.isInteger(value.start) ? value.start : null;
    const snippet = offset === null ? "" : `: ${JSON.stringify(sourceText.slice(offset, Math.min(sourceText.length, offset + 160)))}`;
    invariant(value.type !== "ImportExpression", `sealed output AST retains dynamic import in ${id} at offset ${offset ?? "unknown"}${snippet}`);
    if (value.type === "MetaProperty") {
      invariant(
        value.meta?.name !== "import" || value.property?.name !== "meta",
        `sealed output AST retains import.meta in ${id} at offset ${offset ?? "unknown"}${snippet}`,
      );
    }
    if (value.type === "ImportDeclaration") {
      invariant(
        value.source?.value !== "node:module" && value.source?.value !== "node:process" && value.source?.value !== "node:vm",
        `sealed output AST imports forbidden mutable loader ${value.source?.value} in ${id} at offset ${offset ?? "unknown"}${snippet}`,
      );
    }
    if (value.type === "CallExpression" && value.callee?.type === "MemberExpression") {
      const calledProperty = astMemberProperty(value.callee, constantStrings);
      invariant(
        calledProperty !== "constructor",
        `sealed output AST retains callable constructor access in ${id} at offset ${offset ?? "unknown"}${snippet}`,
      );
    }
    if (value.type === "CallExpression") {
      const directReflectGet = value.callee?.type === "MemberExpression"
        && value.callee.object?.type === "Identifier"
        && reflectAliases.has(value.callee.object.name)
        && astMemberProperty(value.callee, constantStrings) === "get";
      const aliasedReflectGet = value.callee?.type === "Identifier" && reflectGetAliases.has(value.callee.name);
      if (directReflectGet || aliasedReflectGet) {
        const target = value.arguments?.[0];
        const reflectedProperty = astConstantString(value.arguments?.[1])
          ?? (value.arguments?.[1]?.type === "Identifier" ? constantStrings.get(value.arguments[1].name) ?? null : null);
        invariant(
          !referencesAlias(target, new Set([...processAliases, ...globalAliases])),
          `sealed output AST retains reflected process/global access in ${id} at offset ${offset ?? "unknown"}${snippet}`,
        );
        invariant(
          reflectedProperty !== "constructor",
          `sealed output AST retains reflected constructor access in ${id} at offset ${offset ?? "unknown"}${snippet}`,
        );
      }
    }
    if (
      value.type === "CallExpression"
      && value.callee?.type === "MemberExpression"
      && value.callee.object?.type === "Identifier"
      && value.callee.object.name === "Object"
      && (astMemberProperty(value.callee, constantStrings) === "getOwnPropertyDescriptor"
        || astMemberProperty(value.callee, constantStrings) === "getOwnPropertyDescriptors")
    ) {
      const descriptorProperty = astConstantString(value.arguments?.[1])
        ?? (value.arguments?.[1]?.type === "Identifier" ? constantStrings.get(value.arguments[1].name) ?? null : null);
      invariant(
        descriptorProperty !== "constructor"
          && descriptorProperty !== "process"
          && !referencesAlias(value.arguments?.[0], new Set([...processAliases, ...globalAliases])),
        `sealed output AST retains forbidden reflective descriptor access in ${id} at offset ${offset ?? "unknown"}${snippet}`,
      );
    }
    if (value.type === "Identifier") {
      const parent = parents.get(value);
      const safeRequirePropertyKey = value.name === "require"
        && parent?.type === "Property"
        && parent.key === value
        && !parent.computed;
      invariant(value.name !== "require" || safeRequirePropertyKey, `sealed output AST retains require in ${id} at offset ${offset ?? "unknown"}${snippet}`);
      const functionReference = offset === null ? "" : sourceText.slice(offset, Math.min(sourceText.length, offset + 128));
      const safeFunctionReference = value.name === "Function"
        && /^Function\s*\.\s*prototype(?!\s*\.\s*constructor\b)/.test(functionReference);
      invariant(value.name !== "eval" && (value.name !== "Function" || safeFunctionReference), `sealed output AST retains dynamic code generation in ${id} at offset ${offset ?? "unknown"}${snippet}`);
      invariant(value.name !== "dlopen", `sealed output AST retains native module loading in ${id} at offset ${offset ?? "unknown"}${snippet}`);
      invariant(
        value.name !== "__dirname" && value.name !== "__filename",
        `sealed output AST retains CommonJS pseudo-global ${value.name} in ${id} at offset ${offset ?? "unknown"}${snippet}`,
      );
    }
    if (value.type === "MemberExpression") {
      const property = astMemberProperty(value, constantStrings);
      invariant(
        property !== "createRequire" && property !== "getBuiltinModule",
        `sealed output AST retains mutable module resolution property ${property} in ${id} at offset ${offset ?? "unknown"}`,
      );
      const constructorTail = Number.isInteger(value.end)
        ? sourceText.slice(value.end, Math.min(sourceText.length, value.end + 32))
        : "";
      const safeConstructorName = property === "constructor" && /^\s*(?:\?\.\s*|\.\s*)name\b/.test(constructorTail);
      const safeConstructorComparison = property === "constructor" && /^\s*(?:===|!==|==|!=)/.test(constructorTail);
      const functionLikeConstructor = property === "constructor" && (
        value.object?.type === "ArrowFunctionExpression"
        || value.object?.type === "FunctionExpression"
        || value.object?.type === "ClassExpression"
        || value.object?.type === "CallExpression"
      );
      invariant(!functionLikeConstructor || safeConstructorName || safeConstructorComparison, `sealed output AST retains function constructor access in ${id} at offset ${offset ?? "unknown"}${snippet}`);
      invariant(property !== "constructor" || !value.computed, `sealed output AST retains computed constructor access in ${id} at offset ${offset ?? "unknown"}${snippet}`);
      if (value.object?.type === "Identifier" && processAliases.has(value.object.name)) {
        invariant(!value.computed, `sealed output AST retains computed process/global access in ${id} at offset ${offset ?? "unknown"}${snippet}`);
        invariant(property !== "dlopen", `sealed output AST retains process.dlopen in ${id} at offset ${offset ?? "unknown"}`);
      }
      if (value.object?.type === "Identifier" && globalAliases.has(value.object.name) && value.computed) {
        const staticSymbol = astStaticGlobalSymbol(value.property, staticGlobalSymbols);
        invariant(
          staticSymbol || property !== null,
          `sealed output AST retains unresolved computed global access in ${id} at offset ${offset ?? "unknown"}${snippet}`,
        );
        if (!staticSymbol) {
          invariant(
            !forbiddenComputedGlobalLoaders.has(property),
            `sealed output AST retains computed global loader ${property} in ${id} at offset ${offset ?? "unknown"}${snippet}`,
          );
        }
      }
      if (value.object?.type === "Identifier" && reflectAliases.has(value.object.name) && value.computed) {
        invariant(property !== null, `sealed output AST retains unresolved computed Reflect access in ${id} at offset ${offset ?? "unknown"}${snippet}`);
      }
    }
    if (
      value.type === "VariableDeclarator"
      && value.id?.type === "ObjectPattern"
      && value.init?.type === "Identifier"
      && globalAliases.has(value.init.name)
    ) {
      invariant(
        !(value.id.properties ?? []).some((property) => property?.type === "Property" && property.computed),
        `sealed output AST retains computed global destructuring in ${id} at offset ${offset ?? "unknown"}${snippet}`,
      );
    }
  }
}

function normalizeNodeBuiltinResolution(code, transformations, events, id) {
  const ast = parseAst(code, { lang: "js", sourceType: "module", astType: "js" }, id);
  const pending = [ast];
  const seen = new WeakSet();
  const replacements = [];
  const specifiers = new Set();
  while (pending.length > 0) {
    const value = pending.pop();
    if (value === null || typeof value !== "object" || seen.has(value)) continue;
    seen.add(value);
    if (value.type === "CallExpression" && value.callee?.type === "Identifier" && value.callee.name === "require") {
      const [argument] = value.arguments ?? [];
      invariant(
        value.arguments?.length === 1 && argument?.type === "Literal" && typeof argument.value === "string" && argument.value.startsWith("node:"),
        `emitted non-node or computed require is forbidden in ${id} at offset ${value.start ?? "unknown"}: ${JSON.stringify(
          Number.isInteger(value.start) ? code.slice(value.start, Math.min(code.length, value.start + 200)) : "",
        )}`,
      );
      if (argument.value !== "node:process") specifiers.add(argument.value);
      replacements.push({ start: value.start, end: value.end, specifier: argument.value, kind: "require" });
    }
    if (value.type === "ImportExpression") {
      invariant(
        value.source?.type === "Literal"
          && typeof value.source.value === "string"
          && value.source.value.startsWith("node:")
          && value.source.value !== "node:process",
        `emitted unresolved dynamic import is forbidden in ${id} at offset ${value.start ?? "unknown"}`,
      );
      specifiers.add(value.source.value);
      replacements.push({ start: value.start, end: value.end, specifier: value.source.value, kind: "import" });
    }
    for (const child of Object.values(value)) {
      if (Array.isArray(child)) pending.push(...child);
      else if (child !== null && typeof child === "object") pending.push(child);
    }
  }
  if (replacements.length === 0) return Object.freeze({ code, specifiers: Object.freeze([]) });

  const sortedSpecifiers = [...specifiers].sort();
  const bindings = new Map(sortedSpecifiers.map((specifier, index) => [specifier, `__mcphubSealedNodeBuiltin${index}`]));
  for (const binding of bindings.values()) invariant(!code.includes(binding), `node builtin binding collision: ${binding}`);
  let normalized = code;
  for (const replacement of replacements.sort((left, right) => right.start - left.start)) {
    const binding = bindings.get(replacement.specifier);
    const expression = replacement.specifier === "node:process"
      ? "globalThis.process"
      : replacement.kind === "require" ? `${binding}.default` : `Promise.resolve(${binding})`;
    transformEvent(events, {
      name: `${NODE_BUILTIN_RESOLUTION_TRANSFORMATION}:${replacement.kind}:${replacement.specifier}:${replacement.start}`,
      kind: "emitted-resolution",
      source: replacement.specifier,
      target: `${id}#${replacement.start}`,
      preimage: code.slice(replacement.start, replacement.end),
      postimage: expression,
    });
    normalized = `${normalized.slice(0, replacement.start)}${expression}${normalized.slice(replacement.end)}`;
  }
  const imports = sortedSpecifiers.map((specifier) => `import * as ${bindings.get(specifier)} from ${JSON.stringify(specifier)};`);
  transformations.add(NODE_BUILTIN_RESOLUTION_TRANSFORMATION);
  return Object.freeze({ code: `${imports.join("\n")}\n${normalized}`, specifiers: Object.freeze(sortedSpecifiers) });
}

function normalizeSafeFunctionReferences(code, transformations, events, id) {
  let normalized = code;
  if (normalized.includes(HAS_OWN_FUNCTION_CALL)) {
    invariant(normalized.split(HAS_OWN_FUNCTION_CALL).length === 2, "emitted hasOwn Function.call anchor drift");
    const anchorOffset = normalized.indexOf(HAS_OWN_FUNCTION_CALL);
    const anchorTail = normalized.slice(anchorOffset + HAS_OWN_FUNCTION_CALL.length, anchorOffset + HAS_OWN_FUNCTION_CALL.length + 32);
    invariant(!/^\s*(?:\?\.\s*|\.\s*)constructor\b/.test(anchorTail), "emitted hasOwn Function.call constructor extraction is forbidden");
    transformEvent(events, {
      name: HAS_OWN_STATIC_TRANSFORMATION,
      kind: "emitted-code",
      target: id,
      preimage: HAS_OWN_FUNCTION_CALL,
      postimage: HAS_OWN_STATIC_CALL,
    });
    transformations.add(HAS_OWN_STATIC_TRANSFORMATION);
    normalized = normalized.replace(HAS_OWN_FUNCTION_CALL, HAS_OWN_STATIC_CALL);
  }
  if (normalized.includes(HAS_INSTANCE_FUNCTION_CALL)) {
    invariant(normalized.split(HAS_INSTANCE_FUNCTION_CALL).length === 2, "emitted Symbol.hasInstance Function.call anchor drift");
    transformEvent(events, {
      name: HAS_INSTANCE_STATIC_TRANSFORMATION,
      kind: "emitted-code",
      target: id,
      preimage: HAS_INSTANCE_FUNCTION_CALL,
      postimage: HAS_INSTANCE_STATIC_CALL,
    });
    transformations.add(HAS_INSTANCE_STATIC_TRANSFORMATION);
    normalized = normalized.replace(HAS_INSTANCE_FUNCTION_CALL, HAS_INSTANCE_STATIC_CALL);
  }
  return normalized;
}

function closurePlugin({ moduleIds, moduleInputs, transformations, events, entryPath, inventoryRoot, afterInputCaptured }) {
  let typeormRoot = null;
  const optionalOtelNoopPath = ownedInventoryPath(inventoryRoot, OPTIONAL_OTEL_NOOP_RELATIVE_PATH);
  const typeormSurfacePath = ownedInventoryPath(inventoryRoot, TYPEORM_SURFACE_RELATIVE_PATH);
  const typeormDriverFactoryPath = ownedInventoryPath(inventoryRoot, TYPEORM_DRIVER_FACTORY_RELATIVE_PATH);
  return {
    name: "mcphub-exhaustive-closure",
    async resolveId(source, importer) {
      const normalizedImporter = typeof importer === "string" ? importer.split(path.sep).join("/") : null;
      if (source === TYPEORM_ROOT_SPECIFIER) {
        invariant(
          normalizedImporter !== null && TYPEORM_MCPHUB_IMPORTERS.some((suffix) => normalizedImporter.endsWith(suffix)),
          `typeorm root import is forbidden outside the frozen MCPHub import surface: ${importer ?? "<entry>"}`,
        );
        const lockedResolution = await this.resolve(source, importer, { skipSelf: true });
        invariant(
          lockedResolution !== null && lockedResolution.id.split(path.sep).join("/").endsWith("/node_modules/typeorm/index.mjs"),
          `locked TypeORM root resolution is invalid: ${lockedResolution?.id ?? "<unresolved>"}`,
        );
        const resolvedRoot = path.dirname(lockedResolution.id);
        invariant(typeormRoot === null || typeormRoot === resolvedRoot, "multiple TypeORM package roots are forbidden");
        typeormRoot = resolvedRoot;
        transformations.add(TYPEORM_SURFACE_TRANSFORMATION);
        transformEvent(events, {
          name: TYPEORM_SURFACE_TRANSFORMATION,
          kind: "resolution",
          source,
          importer: normalizedTarget(inventoryRoot, importer),
          target: normalizedTarget(inventoryRoot, typeormSurfacePath),
          preimage: source,
          postimage: normalizedTarget(inventoryRoot, typeormSurfacePath),
        });
        return typeormSurfacePath;
      }
      if (
        source.startsWith("typeorm/")
        && (importer === typeormSurfacePath || importer === typeormDriverFactoryPath)
      ) {
        invariant(typeormRoot !== null, "TypeORM deep import was resolved before the locked package root");
        const relative = source.slice("typeorm/".length);
        invariant(/^[A-Za-z0-9_./-]+\.js$/.test(relative) && !relative.includes(".."), `invalid TypeORM deep import: ${source}`);
        const target = path.join(typeormRoot, ...relative.split("/"));
        transformations.add(TYPEORM_DEEP_IMPORT_TRANSFORMATION);
        transformEvent(events, {
          name: `${TYPEORM_DEEP_IMPORT_TRANSFORMATION}:${source}`,
          kind: "resolution",
          source,
          importer: normalizedTarget(inventoryRoot, importer),
          target: normalizedTarget(inventoryRoot, target),
          preimage: source,
          postimage: normalizedTarget(inventoryRoot, target),
        });
        return target;
      }
      if (
        normalizedImporter?.endsWith(TYPEORM_DATA_SOURCE_IMPORTER)
        && (source === "../driver/DriverFactory" || source === "../driver/DriverFactory.js")
      ) {
        transformations.add(TYPEORM_DRIVER_FACTORY_TRANSFORMATION);
        transformEvent(events, {
          name: TYPEORM_DRIVER_FACTORY_TRANSFORMATION,
          kind: "resolution",
          source,
          importer: normalizedTarget(inventoryRoot, importer),
          target: normalizedTarget(inventoryRoot, typeormDriverFactoryPath),
          preimage: source,
          postimage: normalizedTarget(inventoryRoot, typeormDriverFactoryPath),
        });
        return typeormDriverFactoryPath;
      }
      if (BARE_BUILTINS.has(source)) {
        const target = `node:${source}`;
        transformEvent(events, {
          name: `${BARE_BUILTIN_RESOLUTION_TRANSFORMATION}:${source}`,
          kind: "resolution",
          source,
          importer: importer === undefined ? null : normalizedTarget(inventoryRoot, importer),
          target,
          preimage: source,
          postimage: target,
        });
        return { id: target, external: true };
      }
      if (source === OPTIONAL_OTEL_API) {
        invariant(
          typeof importer === "string"
            && OPTIONAL_OTEL_IMPORTERS.some((suffix) => importer.split(path.sep).join("/").endsWith(suffix)),
          `optional OpenTelemetry import is forbidden outside the frozen optional-instrumentation set: ${importer ?? "<entry>"}`,
        );
        transformations.add(OPTIONAL_OTEL_TRANSFORMATION);
        transformEvent(events, {
          name: `${OPTIONAL_OTEL_TRANSFORMATION}:${normalizedTarget(inventoryRoot, importer)}`,
          kind: "resolution",
          source,
          importer: normalizedTarget(inventoryRoot, importer),
          target: normalizedTarget(inventoryRoot, optionalOtelNoopPath),
          preimage: source,
          postimage: normalizedTarget(inventoryRoot, optionalOtelNoopPath),
        });
        return optionalOtelNoopPath;
      }
      invariant(!source.endsWith(".node"), `native module import is forbidden: ${source}`);
      return null;
    },
    load(id) {
      invariant(!id.endsWith(".node"), `native module input is forbidden: ${id}`);
      return null;
    },
    async transform(code, id) {
      if (id.startsWith("\0")) return null;
      const capturedBytes = Buffer.from(code, "utf8");
      const prior = moduleInputs.get(id);
      invariant(prior === undefined || prior.bytes.equals(capturedBytes), `bundle input bytes changed between transform passes: ${id}`);
      if (prior === undefined) {
        moduleInputs.set(id, Object.freeze({ bytes: capturedBytes, sha256: sha256Bytes(capturedBytes) }));
        if (afterInputCaptured !== undefined) await afterInputCaptured(Object.freeze({ id, sha256: sha256Bytes(capturedBytes) }));
      }
      const normalizedId = id.split(path.sep).join("/");
      const target = normalizedTarget(inventoryRoot, id);
      const lockedMcpHubSource = transformLockedMcpHubSource({
        code,
        normalizedId,
        target,
        transformations,
        events,
      });
      if (lockedMcpHubSource !== null) return { code: lockedMcpHubSource, map: null };
      if (normalizedId.endsWith(SWAGGER_SCHEMA_VALIDATOR_IMPORTER)) {
        invariant(
          sha256Bytes(Buffer.from(code, "utf8")) === SWAGGER_SCHEMA_VALIDATOR_SHA256,
          `Swagger Parser schema validator source drift (${id})`,
        );
        transformations.add(SWAGGER_CFWORKER_VALIDATOR_TRANSFORMATION);
        transformEvent(events, {
          name: SWAGGER_CFWORKER_VALIDATOR_TRANSFORMATION,
          kind: "replacement",
          target,
          preimage: code,
          postimage: SWAGGER_CFWORKER_VALIDATOR_SOURCE,
        });
        return { code: SWAGGER_CFWORKER_VALIDATOR_SOURCE, map: null };
      }
      if (normalizedId.endsWith(TYPEDARRAY_IMPORTER)) {
        invariant(
          sha256Bytes(Buffer.from(code, "utf8")) === TYPEDARRAY_SHA256,
          `typedarray source drift (${id})`,
        );
        transformations.add(TYPEDARRAY_CONSTRUCTOR_TRANSFORMATION);
        return {
          code: replaceWithEvent(
            code,
            TYPEDARRAY_DYNAMIC_SUBARRAY,
            TYPEDARRAY_STATIC_SUBARRAY,
            {
              events,
              name: TYPEDARRAY_CONSTRUCTOR_TRANSFORMATION,
              target,
              label: `typedarray subarray constructor (${id})`,
            },
          ),
          map: null,
        };
      }
      if (normalizedId.endsWith(UNDICI_GLOBAL_ORIGIN_IMPORTER)) {
        invariant(
          sha256Bytes(Buffer.from(code, "utf8")) === UNDICI_GLOBAL_ORIGIN_SHA256,
          `Undici global-origin source drift (${id})`,
        );
        transformations.add(UNDICI_GLOBAL_ORIGIN_TRANSFORMATION);
        return {
          code: replaceWithEvent(
            code,
            UNDICI_GLOBAL_ORIGIN_ACCESS,
            UNDICI_GLOBAL_ORIGIN_STATIC_ACCESS,
            {
              events,
              name: UNDICI_GLOBAL_ORIGIN_TRANSFORMATION,
              target,
              label: `Undici global-origin access (${id})`,
            },
          ),
          map: null,
        };
      }
      if (normalizedId.endsWith(UNDICI_GLOBAL_DISPATCHER_IMPORTER)) {
        invariant(
          sha256Bytes(Buffer.from(code, "utf8")) === UNDICI_GLOBAL_DISPATCHER_SHA256,
          `Undici global-dispatcher source drift (${id})`,
        );
        transformations.add(UNDICI_GLOBAL_DISPATCHER_TRANSFORMATION);
        return {
          code: replaceWithEvent(
            code,
            UNDICI_GLOBAL_DISPATCHER_ACCESS,
            UNDICI_GLOBAL_DISPATCHER_STATIC_ACCESS,
            {
              events,
              name: UNDICI_GLOBAL_DISPATCHER_TRANSFORMATION,
              target,
              label: `Undici global-dispatcher access (${id})`,
            },
          ),
          map: null,
        };
      }
      if (normalizedId.endsWith(ZOD_CORE_IMPORTER)) {
        invariant(
          sha256Bytes(Buffer.from(code, "utf8")) === ZOD_CORE_SHA256,
          `Zod core source drift (${id})`,
        );
        transformations.add(ZOD_JITLESS_TRANSFORMATION);
        return {
          code: replaceWithEvent(
            code,
            ZOD_GLOBAL_CONFIG_INITIALIZER,
            ZOD_JITLESS_GLOBAL_CONFIG_INITIALIZER,
            {
              events,
              name: `${ZOD_JITLESS_TRANSFORMATION}:global-config`,
              target,
              label: `Zod jitless global configuration (${id})`,
            },
          ),
          map: null,
        };
      }
      if (normalizedId.endsWith(ZOD_UTIL_IMPORTER)) {
        invariant(
          sha256Bytes(Buffer.from(code, "utf8")) === ZOD_UTIL_SHA256,
          `Zod util source drift (${id})`,
        );
        transformations.add(ZOD_JITLESS_TRANSFORMATION);
        return {
          code: replaceWithEvent(
            code,
            ZOD_ALLOWS_EVAL,
            ZOD_ALLOWS_EVAL_DISABLED,
            {
              events,
              name: `${ZOD_JITLESS_TRANSFORMATION}:eval-probe`,
              target,
              label: `Zod eval probe (${id})`,
            },
          ),
          map: null,
        };
      }
      if (normalizedId.endsWith(ZOD_DOC_IMPORTER)) {
        invariant(
          sha256Bytes(Buffer.from(code, "utf8")) === ZOD_DOC_SHA256,
          `Zod document compiler source drift (${id})`,
        );
        transformations.add(ZOD_JITLESS_TRANSFORMATION);
        return {
          code: replaceWithEvent(
            code,
            ZOD_DOC_COMPILE,
            ZOD_DOC_COMPILE_DISABLED,
            {
              events,
              name: `${ZOD_JITLESS_TRANSFORMATION}:document-compiler`,
              target,
              label: `Zod document compiler (${id})`,
            },
          ),
          map: null,
        };
      }
      if (normalizedId.endsWith(REFLECT_METADATA_IMPORTER)) {
        invariant(
          sha256Bytes(Buffer.from(code, "utf8")) === REFLECT_METADATA_SHA256,
          `reflect-metadata source drift (${id})`,
        );
        transformations.add(REFLECT_METADATA_STATIC_GLOBAL_TRANSFORMATION);
        let transformed = replaceWithEvent(
          code,
          REFLECT_METADATA_DYNAMIC_GLOBAL,
          REFLECT_METADATA_STATIC_GLOBAL,
          {
            events,
            name: `${REFLECT_METADATA_STATIC_GLOBAL_TRANSFORMATION}:global-fallback`,
            target,
            label: `reflect-metadata dynamic global fallback (${id})`,
          },
        );
        transformed = replaceWithEvent(
          transformed,
          REFLECT_METADATA_FUNCTION_PROTOTYPE,
          REFLECT_METADATA_STATIC_FUNCTION_PROTOTYPE,
          {
            events,
            name: `${REFLECT_METADATA_STATIC_GLOBAL_TRANSFORMATION}:function-prototype`,
            target,
            label: `reflect-metadata Function prototype (${id})`,
          },
        );
        return { code: transformed, map: null };
      }
      if (normalizedId.endsWith(NODE_GYP_BUILD_IMPORTER)) {
        invariant(
          sha256Bytes(Buffer.from(code, "utf8")) === NODE_GYP_BUILD_SHA256,
          `node-gyp-build source drift (${id})`,
        );
        transformations.add(NODE_GYP_BUILD_TRANSFORMATION);
        transformEvent(events, {
          name: NODE_GYP_BUILD_TRANSFORMATION,
          kind: "replacement",
          target,
          preimage: code,
          postimage: NODE_GYP_BUILD_DISABLED,
        });
        return { code: NODE_GYP_BUILD_DISABLED, map: null };
      }
      if (normalizedId.endsWith(MCPHUB_USER_DAO_IMPORTER)) {
        invariant(
          sha256Bytes(Buffer.from(code, "utf8")) === MCPHUB_USER_DAO_SHA256,
          `MCPHub UserDaoDbImpl source drift (${id})`,
        );
        transformations.add(MCPHUB_USER_DAO_BCRYPTJS_TRANSFORMATION);
        return {
          code: replaceWithEvent(
            code,
            MCPHUB_USER_DAO_BCRYPT,
            MCPHUB_USER_DAO_BCRYPTJS,
            {
              events,
              name: MCPHUB_USER_DAO_BCRYPTJS_TRANSFORMATION,
              target,
              label: `MCPHub UserDaoDbImpl bcrypt import (${id})`,
            },
          ),
          map: null,
        };
      }
      if (normalizedId.endsWith(MCPHUB_PATH_IMPORTER)) {
        invariant(
          sha256Bytes(Buffer.from(code, "utf8")) === MCPHUB_PATH_SHA256,
          `MCPHub path utility source drift (${id})`,
        );
        transformations.add(MCPHUB_PATH_FILENAME_TRANSFORMATION);
        return {
          code: replaceWithEvent(
            code,
            MCPHUB_PATH_FILENAME_FALLBACK,
            "",
            {
              events,
              name: MCPHUB_PATH_FILENAME_TRANSFORMATION,
              target,
              label: `MCPHub CommonJS filename fallback (${id})`,
            },
          ),
          map: null,
        };
      }
      if (normalizedId.endsWith(UNDICI_INDEX_IMPORTER) || normalizedId.endsWith(UNDICI_INDEX_FETCH_IMPORTER)) {
        const expectedHash = normalizedId.endsWith(UNDICI_INDEX_FETCH_IMPORTER)
          ? UNDICI_INDEX_FETCH_SHA256
          : UNDICI_INDEX_SHA256;
        invariant(
          sha256Bytes(Buffer.from(code, "utf8")) === expectedHash,
          `undici entry source drift (${id})`,
        );
        transformations.add(UNDICI_FILENAME_TRANSFORMATION);
        return {
          code: replaceWithEvent(
            code,
            UNDICI_CURRENT_FILENAME,
            UNDICI_CURRENT_FILENAME_DISABLED,
            {
              events,
              name: `${UNDICI_FILENAME_TRANSFORMATION}:${normalizedId.endsWith(UNDICI_INDEX_FETCH_IMPORTER) ? "fetch" : "index"}`,
              target,
              label: `undici CommonJS filename fallback (${id})`,
            },
          ),
          map: null,
        };
      }
      if (normalizedId.endsWith(APP_ROOT_PATH_INDEX_IMPORTER)) {
        invariant(
          sha256Bytes(Buffer.from(code, "utf8")) === APP_ROOT_PATH_INDEX_SHA256,
          `app-root-path index source drift (${id})`,
        );
        transformations.add(APP_ROOT_PATH_INDEX_TRANSFORMATION);
        transformEvent(events, {
          name: APP_ROOT_PATH_INDEX_TRANSFORMATION,
          kind: "replacement",
          target,
          preimage: code,
          postimage: APP_ROOT_PATH_INDEX_DISABLED,
        });
        return { code: APP_ROOT_PATH_INDEX_DISABLED, map: null };
      }
      if (normalizedId.endsWith(QS_BROWSER_IMPORTER)) {
        invariant(
          sha256Bytes(Buffer.from(code, "utf8")) === QS_BROWSER_SHA256,
          `qs browser bundle source drift (${id})`,
        );
        transformations.add(QS_INTRINSIC_CODEGEN_TRANSFORMATION);
        let transformed = replaceWithEvent(
          code,
          QS_FUNCTION_INTRINSIC,
          QS_FUNCTION_INTRINSIC_DISABLED,
          {
            events,
            name: `${QS_INTRINSIC_CODEGEN_TRANSFORMATION}:function`,
            target,
            label: `qs Function intrinsic (${id})`,
          },
        );
        transformed = replaceWithEvent(
          transformed,
          QS_EVAL_INTRINSIC,
          QS_EVAL_INTRINSIC_DISABLED,
          {
            events,
            name: `${QS_INTRINSIC_CODEGEN_TRANSFORMATION}:eval`,
            target,
            label: `qs eval intrinsic (${id})`,
          },
        );
        return { code: transformed, map: null };
      }
      if (normalizedId.endsWith(GET_INTRINSIC_IMPORTER)) {
        invariant(
          sha256Bytes(Buffer.from(code, "utf8")) === GET_INTRINSIC_SHA256,
          `get-intrinsic source drift (${id})`,
        );
        transformations.add(GET_INTRINSIC_CODEGEN_TRANSFORMATION);
        let transformed = replaceWithEvent(
          code,
          GET_INTRINSIC_FUNCTION,
          GET_INTRINSIC_FUNCTION_DISABLED,
          {
            events,
            name: `${GET_INTRINSIC_CODEGEN_TRANSFORMATION}:function`,
            target,
            label: `get-intrinsic Function capability (${id})`,
          },
        );
        transformed = replaceWithEvent(
          transformed,
          GET_INTRINSIC_FUNCTION_CALL,
          GET_INTRINSIC_FUNCTION_CALL_DISABLED,
          {
            events,
            name: `${GET_INTRINSIC_CODEGEN_TRANSFORMATION}:function-call`,
            target,
            label: `get-intrinsic Function call alias (${id})`,
          },
        );
        transformed = replaceWithEvent(
          transformed,
          GET_INTRINSIC_FUNCTION_VALUE,
          GET_INTRINSIC_FUNCTION_VALUE_DISABLED,
          {
            events,
            name: `${GET_INTRINSIC_CODEGEN_TRANSFORMATION}:function-value`,
            target,
            label: `get-intrinsic Function value alias (${id})`,
          },
        );
        transformed = replaceWithEvent(
          transformed,
          GET_INTRINSIC_EVAL,
          GET_INTRINSIC_EVAL_DISABLED,
          {
            events,
            name: `${GET_INTRINSIC_CODEGEN_TRANSFORMATION}:eval`,
            target,
            label: `get-intrinsic eval capability (${id})`,
          },
        );
        return { code: transformed, map: null };
      }
      if (normalizedId.endsWith(FUNCTION_BIND_IMPORTER)) {
        invariant(
          sha256Bytes(Buffer.from(code, "utf8")) === FUNCTION_BIND_SHA256,
          `function-bind source drift (${id})`,
        );
        transformations.add(FUNCTION_BIND_TRANSFORMATION);
        transformEvent(events, {
          name: FUNCTION_BIND_TRANSFORMATION,
          kind: "replacement",
          target,
          preimage: code,
          postimage: FUNCTION_BIND_NATIVE_ONLY,
        });
        return { code: FUNCTION_BIND_NATIVE_ONLY, map: null };
      }
      if (normalizedId.endsWith(DEPD_IMPORTER)) {
        invariant(
          sha256Bytes(Buffer.from(code, "utf8")) === DEPD_SHA256,
          `depd source drift (${id})`,
        );
        transformations.add(DEPD_STATIC_WRAPPER_TRANSFORMATION);
        return {
          code: replaceWithEvent(
            code,
            DEPD_DYNAMIC_WRAPPER,
            DEPD_STATIC_WRAPPER,
            {
              events,
              name: DEPD_STATIC_WRAPPER_TRANSFORMATION,
              target,
              label: `depd dynamic arity wrapper (${id})`,
            },
          ),
          map: null,
        };
      }
      if (
        normalizedId.endsWith(MCP_SDK_STDIO_SERVER_IMPORTER)
        || normalizedId.endsWith(MCP_SDK_STDIO_CLIENT_IMPORTER)
      ) {
        const expectedSha256 = normalizedId.endsWith(MCP_SDK_STDIO_SERVER_IMPORTER)
          ? MCP_SDK_STDIO_SERVER_SHA256
          : MCP_SDK_STDIO_CLIENT_SHA256;
        invariant(
          sha256Bytes(Buffer.from(code, "utf8")) === expectedSha256,
          `MCP SDK stdio source drift (${id})`,
        );
        const role = normalizedId.endsWith(MCP_SDK_STDIO_SERVER_IMPORTER) ? "server" : "client";
        transformations.add(MCP_SDK_GLOBAL_PROCESS_TRANSFORMATION);
        return {
          code: replaceWithEvent(
            code,
            MCP_SDK_PROCESS_IMPORT,
            "",
            {
              events,
              name: `${MCP_SDK_GLOBAL_PROCESS_TRANSFORMATION}:${role}`,
              target,
              label: `MCP SDK ${role} stdio process import (${id})`,
            },
          ),
          map: null,
        };
      }
      if (normalizedId.endsWith(FETCH_BLOB_STREAMS_IMPORTER)) {
        invariant(
          sha256Bytes(Buffer.from(code, "utf8")) === FETCH_BLOB_STREAMS_SHA256,
          `fetch-blob streams source drift (${id})`,
        );
        transformations.add(FETCH_BLOB_GLOBAL_PROCESS_TRANSFORMATION);
        return {
          code: replaceWithEvent(
            code,
            FETCH_BLOB_PROCESS_REQUIRE,
            FETCH_BLOB_GLOBAL_PROCESS,
            {
              events,
              name: FETCH_BLOB_GLOBAL_PROCESS_TRANSFORMATION,
              target,
              label: `fetch-blob process shim (${id})`,
            },
          ),
          map: null,
        };
      }
      if (normalizedId.endsWith(GOOGLE_GENAI_NODE_IMPORTER)) {
        invariant(
          sha256Bytes(Buffer.from(code, "utf8")) === GOOGLE_GENAI_NODE_SHA256,
          `Google GenAI node source drift (${id})`,
        );
        transformations.add(GOOGLE_GENAI_STATIC_CLIENT_TRANSFORMATION);
        return {
          code: replaceWithEvent(
            code,
            GOOGLE_GENAI_DYNAMIC_CLIENT,
            GOOGLE_GENAI_STATIC_CLIENT,
            {
              events,
              name: GOOGLE_GENAI_STATIC_CLIENT_TRANSFORMATION,
              target,
              label: `Google GenAI client constructor (${id})`,
            },
          ),
          map: null,
        };
      }
      if (normalizedId.endsWith(OPENAI_CLIENT_IMPORTER)) {
        invariant(
          sha256Bytes(Buffer.from(code, "utf8")) === OPENAI_CLIENT_SHA256,
          `OpenAI client source drift (${id})`,
        );
        transformations.add(OPENAI_STATIC_CLIENT_TRANSFORMATION);
        return {
          code: replaceWithEvent(
            code,
            OPENAI_DYNAMIC_CLIENT,
            OPENAI_STATIC_CLIENT,
            {
              events,
              name: OPENAI_STATIC_CLIENT_TRANSFORMATION,
              target,
              label: `OpenAI client constructor (${id})`,
            },
          ),
          map: null,
        };
      }
      if (normalizedId.endsWith(NOBLE_SHA2_IMPORTER)) {
        invariant(
          sha256Bytes(Buffer.from(code, "utf8")) === NOBLE_SHA2_SHA256,
          `Noble SHA2 source drift (${id})`,
        );
        transformations.add(NOBLE_SHA2_STATIC_CLONE_TRANSFORMATION);
        let transformed = replaceWithEvent(
          code,
          NOBLE_SHA2_32_DYNAMIC_CLONE,
          NOBLE_SHA2_32_STATIC_CLONE,
          {
            events,
            name: `${NOBLE_SHA2_STATIC_CLONE_TRANSFORMATION}:sha32`,
            target,
            label: `Noble SHA2 32-bit clone (${id})`,
          },
        );
        transformed = replaceWithEvent(
          transformed,
          NOBLE_SHA2_64_DYNAMIC_CLONE,
          NOBLE_SHA2_64_STATIC_CLONE,
          {
            events,
            name: `${NOBLE_SHA2_STATIC_CLONE_TRANSFORMATION}:sha64`,
            target,
            label: `Noble SHA2 64-bit clone (${id})`,
          },
        );
        return { code: transformed, map: null };
      }
      if (normalizedId.endsWith(BETTER_AUTH_GLOBAL_IMPORTER)) {
        const accessCount = code.split(BETTER_AUTH_GLOBAL_SYMBOL_ACCESS).length - 1;
        invariant(
          accessCount === BETTER_AUTH_GLOBAL_SYMBOL_ACCESS_COUNT,
          `Better Auth global symbol access anchor drift (${id})`,
        );
        transformations.add(BETTER_AUTH_GLOBAL_SYMBOL_TRANSFORMATION);
        for (let index = 0; index < accessCount; index += 1) {
          transformEvent(events, {
            name: `${BETTER_AUTH_GLOBAL_SYMBOL_TRANSFORMATION}:${index}`,
            kind: "replacement",
            target,
            preimage: BETTER_AUTH_GLOBAL_SYMBOL_ACCESS,
            postimage: BETTER_AUTH_GLOBAL_STATIC_SYMBOL_ACCESS,
          });
        }
        return {
          code: code.split(BETTER_AUTH_GLOBAL_SYMBOL_ACCESS).join(BETTER_AUTH_GLOBAL_STATIC_SYMBOL_ACCESS),
          map: null,
        };
      }
      if (normalizedId.endsWith(NODE_SQLITE_IMPORTER)) {
        transformations.add(NODE_SQLITE_TRANSFORMATION);
        const replaced = replaceWithEvent(
          code,
          NODE_SQLITE_DYNAMIC_BLOCK,
          "\t\t\tDatabaseSync = __mcphubNodeDatabaseSync;",
          {
            events,
            name: `${NODE_SQLITE_TRANSFORMATION}:dynamic-import-replacement`,
            target,
            label: `Better Auth node:sqlite import (${id})`,
          },
        );
        return {
          code: prependWithEvent(replaced, NODE_SQLITE_STATIC_IMPORT, {
            events,
            name: `${NODE_SQLITE_TRANSFORMATION}:static-import-prefix`,
            target,
            label: `Better Auth node:sqlite import (${id})`,
          }),
          map: null,
        };
      }
      if (normalizedId.endsWith(TYPEORM_QUERY_BUILDER_IMPORTER)) {
        invariant(
          sha256Bytes(Buffer.from(code, "utf8")) === TYPEORM_QUERY_BUILDER_SHA256,
          `TypeORM QueryBuilder source drift (${id})`,
        );
        transformations.add(TYPEORM_STATIC_QUERY_BUILDER_TRANSFORMATION);
        let transformed = replaceWithEvent(
          code,
          TYPEORM_DYNAMIC_QUERY_BUILDER_CREATE,
          TYPEORM_STATIC_QUERY_BUILDER_CREATE,
          {
            events,
            name: `${TYPEORM_STATIC_QUERY_BUILDER_TRANSFORMATION}:create`,
            target,
            label: `TypeORM QueryBuilder create factory (${id})`,
          },
        );
        transformed = replaceWithEvent(
          transformed,
          TYPEORM_DYNAMIC_QUERY_BUILDER_CLONE,
          TYPEORM_STATIC_QUERY_BUILDER_CLONE,
          {
            events,
            name: `${TYPEORM_STATIC_QUERY_BUILDER_TRANSFORMATION}:clone`,
            target,
            label: `TypeORM QueryBuilder clone factory (${id})`,
          },
        );
        return { code: transformed, map: null };
      }
      if (normalizedId.endsWith(MCPHUB_MODULE_DIR_IMPORTER)) {
        transformations.add(MCPHUB_MODULE_DIR_TRANSFORMATION);
        return {
          code: replaceWithEvent(
            code,
            MCPHUB_MODULE_DIR_FUNCTION,
            MCPHUB_SEALED_MODULE_DIR_FUNCTION,
            { events, name: MCPHUB_MODULE_DIR_TRANSFORMATION, target, label: `MCPHub module-directory source (${id})` },
          ),
          map: null,
        };
      }
      if (normalizedId.endsWith(MCPHUB_LOG_SERVICE_IMPORTER)) {
        invariant(
          sha256Bytes(Buffer.from(code, "utf8")) === MCPHUB_LOG_SERVICE_SHA256,
          `MCPHub log service source drift (${id})`,
        );
        transformations.add(MCPHUB_LOG_SERVICE_PROCESS_TRANSFORMATION);
        return {
          code: replaceWithEvent(
            code,
            MCPHUB_LOG_SERVICE_PROCESS_IMPORT,
            MCPHUB_LOG_SERVICE_GLOBAL_PROCESS,
            {
              events,
              name: MCPHUB_LOG_SERVICE_PROCESS_TRANSFORMATION,
              target,
              label: `MCPHub log service process import (${id})`,
            },
          ),
          map: null,
        };
      }
      if (normalizedId.endsWith(MCPHUB_CLI_MAIN_IMPORTER)) {
        invariant(
          sha256Bytes(Buffer.from(code, "utf8")) === MCPHUB_CLI_MAIN_SHA256,
          `MCPHub CLI main source drift (${id})`,
        );
        transformations.add(MCPHUB_CLI_SELF_RUN_TRANSFORMATION);
        return {
          code: replaceWithEvent(
            code,
            MCPHUB_CLI_SELF_RUN,
            MCPHUB_CLI_SELF_RUN_DISABLED,
            {
              events,
              name: MCPHUB_CLI_SELF_RUN_TRANSFORMATION,
              target,
              label: `MCPHub embedded CLI self-run (${id})`,
            },
          ),
          map: null,
        };
      }
      if (normalizedId.endsWith(MCPHUB_JSON_SCHEMA_VALIDATOR_IMPORTER)) {
        transformations.add(MCPHUB_JSON_SCHEMA_VALIDATOR_TRANSFORMATION);
        const withProvider = replaceWithEvent(
          code,
          MCPHUB_AJV_VALIDATOR_IMPORT,
          MCPHUB_CFWORKER_VALIDATOR_IMPORT,
          {
            events,
            name: `${MCPHUB_JSON_SCHEMA_VALIDATOR_TRANSFORMATION}:provider-import`,
            target,
            label: `MCPHub JSON Schema validator provider (${id})`,
          },
        );
        return {
          code: replaceWithEvent(
            withProvider,
            MCPHUB_AJV_VALIDATOR_CONSTRUCTION,
            MCPHUB_CFWORKER_VALIDATOR_CONSTRUCTION,
            {
              events,
              name: `${MCPHUB_JSON_SCHEMA_VALIDATOR_TRANSFORMATION}:provider-construction`,
              target,
              label: `MCPHub JSON Schema validator construction (${id})`,
            },
          ),
          map: null,
        };
      }
      if (MCP_SDK_VALIDATOR_IMPORTERS.some((suffix) => normalizedId.endsWith(suffix))) {
        transformations.add(MCP_SDK_VALIDATOR_TRANSFORMATION);
        return {
          code: replaceWithEvent(
            code,
            MCP_SDK_AJV_VALIDATOR_IMPORT,
            MCP_SDK_CFWORKER_VALIDATOR_IMPORT,
            {
              events,
              name: `${MCP_SDK_VALIDATOR_TRANSFORMATION}:${target}`,
              target,
              label: `MCP SDK JSON Schema validator provider (${id})`,
            },
          ),
          map: null,
        };
      }
      if (normalizedId.endsWith(MCP_SERVER_NODE_SHIM_IMPORTER)) {
        invariant(
          sha256Bytes(Buffer.from(code, "utf8")) === MCP_SERVER_NODE_SHIM_SHA256,
          `MCP Server Node shim source drift (${id})`,
        );
        transformations.add(MCP_SERVER_VALIDATOR_TRANSFORMATION);
        let transformed = replaceWithEvent(
          code,
          MCP_SERVER_AJV_VALIDATOR_IMPORT,
          MCP_SERVER_CFWORKER_VALIDATOR_IMPORT,
          {
            events,
            name: MCP_SERVER_VALIDATOR_TRANSFORMATION,
            target,
            label: `MCP Server default JSON Schema validator (${id})`,
          },
        );
        transformed = replaceWithEvent(
          transformed,
          MCP_SERVER_PROCESS_IMPORT,
          MCP_SERVER_GLOBAL_PROCESS,
          {
            events,
            name: `${MCP_SERVER_VALIDATOR_TRANSFORMATION}:global-process`,
            target,
            label: `MCP Server Node process shim (${id})`,
          },
        );
        return {
          code: transformed,
          map: null,
        };
      }
      if (normalizedId.endsWith(REDIS_DIGEST_IMPORTER)) {
        transformations.add(REDIS_XXHASH_TRANSFORMATION);
        return {
          code: replaceWithEvent(
            code,
            REDIS_XXHASH_DYNAMIC_BLOCK,
            REDIS_XXHASH_UNAVAILABLE,
            { events, name: REDIS_XXHASH_TRANSFORMATION, target, label: `Redis optional xxhash source (${id})` },
          ),
          map: null,
        };
      }
      if (normalizedId.endsWith(TYPEORM_IMPORT_UTILS_IMPORTER)) {
        transformations.add(TYPEORM_IMPORT_UTILS_TRANSFORMATION);
        return {
          code: replaceWithEvent(
            code,
            TYPEORM_IMPORT_OR_REQUIRE_FUNCTION,
            TYPEORM_IMPORT_OR_REQUIRE_DISABLED,
            { events, name: TYPEORM_IMPORT_UTILS_TRANSFORMATION, target, label: `TypeORM dynamic module-loader source (${id})` },
          ),
          map: null,
        };
      }
      if (normalizedId.endsWith(TYPEORM_DIRECTORY_LOADER_IMPORTER)) {
        transformations.add(TYPEORM_JSON_LOADER_TRANSFORMATION);
        return {
          code: replaceWithEvent(
            code,
            TYPEORM_DYNAMIC_JSON_REQUIRE,
            TYPEORM_DYNAMIC_JSON_DISABLED,
            { events, name: TYPEORM_JSON_LOADER_TRANSFORMATION, target, label: `TypeORM dynamic JSON loader (${id})` },
          ),
          map: null,
        };
      }
      if (normalizedId.endsWith(TYPEORM_CONNECTION_OPTIONS_IMPORTER)) {
        transformations.add(TYPEORM_CONNECTION_OPTIONS_TRANSFORMATION);
        return {
          code: replaceWithEvent(
            code,
            TYPEORM_DYNAMIC_CONFIG_REQUIRE,
            TYPEORM_DYNAMIC_CONFIG_DISABLED,
            { events, name: TYPEORM_CONNECTION_OPTIONS_TRANSFORMATION, target, label: `TypeORM dynamic JSON configuration (${id})` },
          ),
          map: null,
        };
      }
      if (normalizedId.endsWith(APP_ROOT_PATH_IMPORTER)) {
        transformations.add(APP_ROOT_PATH_TRANSFORMATION);
        return {
          code: replaceWithEvent(
            code,
            APP_ROOT_PATH_DYNAMIC_REQUIRE,
            APP_ROOT_PATH_DYNAMIC_REQUIRE_DISABLED,
            { events, name: APP_ROOT_PATH_TRANSFORMATION, target, label: `app-root-path dynamic require (${id})` },
          ),
          map: null,
        };
      }
      if (normalizedId.endsWith(APP_ROOT_PATH_RESOLVE_IMPORTER)) {
        invariant(
          sha256Bytes(Buffer.from(code, "utf8")) === APP_ROOT_PATH_RESOLVE_SHA256,
          `app-root-path resolver source drift (${id})`,
        );
        transformations.add(APP_ROOT_PATH_RESOLVE_TRANSFORMATION);
        transformEvent(events, {
          name: APP_ROOT_PATH_RESOLVE_TRANSFORMATION,
          kind: "replacement",
          target,
          preimage: code,
          postimage: APP_ROOT_PATH_STATIC_RESOLVER,
        });
        return { code: APP_ROOT_PATH_STATIC_RESOLVER, map: null };
      }
      if (normalizedId.endsWith(TYPEORM_PLATFORM_TOOLS_IMPORTER)) {
        transformations.add(TYPEORM_CWD_FALLBACK_TRANSFORMATION);
        transformations.add(TYPEORM_PLATFORM_UNAVAILABLE_TRANSFORMATION);
        transformations.add(TYPEORM_PLATFORM_POSTGRES_TRANSFORMATION);
        transformations.add(TYPEORM_NON_POSTGRES_TRANSFORMATION);
        transformations.add(TYPEORM_PACKAGE_VERSION_TRANSFORMATION);
        let transformed = replaceWithEvent(
          code,
          TYPEORM_CWD_FALLBACK_REQUIRE,
          TYPEORM_CWD_FALLBACK_DISABLED,
          { events, name: TYPEORM_CWD_FALLBACK_TRANSFORMATION, target, label: `TypeORM cwd node_modules fallback (${id})` },
        );
        transformed = replaceWithEvent(
          transformed,
          TYPEORM_PACKAGE_VERSION_REQUIRE,
          TYPEORM_PACKAGE_VERSION_DISABLED,
          { events, name: TYPEORM_PACKAGE_VERSION_TRANSFORMATION, target, label: `TypeORM dynamic package version (${id})` },
        );
        transformed = replaceWithEvent(
          transformed,
          TYPEORM_PG_REQUIRE,
          TYPEORM_PG_STATIC,
          {
            events,
            name: `${TYPEORM_PLATFORM_POSTGRES_TRANSFORMATION}:package-load-replacement`,
            target,
            label: `TypeORM pg package load (${id})`,
          },
        );
        for (const specifier of TYPEORM_UNAVAILABLE_PLATFORM_PACKAGES) {
          transformed = replaceWithEvent(
            transformed,
            `return require(${JSON.stringify(specifier)});`,
            `throw new Error(${JSON.stringify(`optional TypeORM package ${specifier} is absent from the sealed dependency closure`)});`,
            {
              events,
              name: `${TYPEORM_PLATFORM_UNAVAILABLE_TRANSFORMATION}:${specifier}`,
              target,
              label: `TypeORM unavailable optional package ${specifier} (${id})`,
            },
          );
        }
        for (const specifier of TYPEORM_DISABLED_NON_POSTGRES_PACKAGES) {
          transformed = replaceWithEvent(
            transformed,
            `return require(${JSON.stringify(specifier)});`,
            `throw new Error(${JSON.stringify(`sealed MCPHub TypeORM surface is PostgreSQL-only; ${specifier} is not a TypeORM driver`)});`,
            {
              events,
              name: `${TYPEORM_NON_POSTGRES_TRANSFORMATION}:${specifier}`,
              target,
              label: `TypeORM disabled non-Postgres package ${specifier} (${id})`,
            },
          );
        }
        return {
          code: prependWithEvent(transformed, TYPEORM_PG_IMPORT, {
            events,
            name: `${TYPEORM_PLATFORM_POSTGRES_TRANSFORMATION}:static-import-prefix`,
            target,
            label: `TypeORM pg package import (${id})`,
          }),
          map: null,
        };
      }
      if (normalizedId.endsWith(EXPRESS_VIEW_IMPORTER)) {
        transformations.add(EXPRESS_VIEW_TRANSFORMATION);
        return {
          code: replaceWithEvent(
            code,
            EXPRESS_DYNAMIC_VIEW_ENGINE_BLOCK,
            EXPRESS_DYNAMIC_VIEW_ENGINE_DISABLED,
            { events, name: EXPRESS_VIEW_TRANSFORMATION, target, label: `Express dynamic view-engine source (${id})` },
          ),
          map: null,
        };
      }
      if (normalizedId.endsWith(WS_VALIDATION_IMPORTER)) {
        transformations.add(WS_VALIDATION_TRANSFORMATION);
        return {
          code: replaceWithEvent(code, WS_UTF8_REQUIRE, WS_UTF8_UNAVAILABLE, {
            events,
            name: WS_VALIDATION_TRANSFORMATION,
            target,
            label: `ws optional UTF-8 validator (${id})`,
          }),
          map: null,
        };
      }
      if (normalizedId.endsWith(WS_BUFFER_UTIL_IMPORTER)) {
        transformations.add(WS_BUFFER_UTIL_TRANSFORMATION);
        return {
          code: replaceWithEvent(code, WS_BUFFER_UTIL_REQUIRE, WS_BUFFER_UTIL_UNAVAILABLE, {
            events,
            name: WS_BUFFER_UTIL_TRANSFORMATION,
            target,
            label: `ws optional buffer accelerator (${id})`,
          }),
          map: null,
        };
      }
      if (normalizedId.endsWith(DEBUG_NODE_IMPORTER)) {
        transformations.add(DEBUG_SUPPORTS_COLOR_TRANSFORMATION);
        return {
          code: replaceWithEvent(
            code,
            DEBUG_SUPPORTS_COLOR_REQUIRE,
            DEBUG_SUPPORTS_COLOR_UNAVAILABLE,
            { events, name: DEBUG_SUPPORTS_COLOR_TRANSFORMATION, target, label: `debug optional color source (${id})` },
          ),
          map: null,
        };
      }
      if (normalizedId.endsWith(LODASH_IMPORTER)) {
        invariant(
          sha256Bytes(Buffer.from(code, "utf8")) === LODASH_SHA256,
          `lodash source drift (${id})`,
        );
        transformations.add(LODASH_CODEGEN_TRANSFORMATION);
        const staticGlobal = replaceWithEvent(code, LODASH_FUNCTION_GLOBAL, LODASH_STATIC_GLOBAL, {
          events,
          name: `${LODASH_CODEGEN_TRANSFORMATION}:global-detection`,
          target,
          label: `lodash global detection (${id})`,
        });
        const withoutFunctionAlias = replaceWithEvent(staticGlobal, LODASH_CONTEXT_FUNCTION, "", {
          events,
          name: `${LODASH_CODEGEN_TRANSFORMATION}:function-alias-removal`,
          target,
          label: `lodash Function alias (${id})`,
        });
        const staticFunctionPrototype = replaceWithEvent(
          withoutFunctionAlias,
          LODASH_FUNCTION_PROTOTYPE,
          LODASH_STATIC_FUNCTION_PROTOTYPE,
          {
            events,
            name: `${LODASH_CODEGEN_TRANSFORMATION}:function-prototype`,
            target,
            label: `lodash Function prototype (${id})`,
          },
        );
        const withoutTemplateCompiler = replaceWithEvent(staticFunctionPrototype, LODASH_TEMPLATE_FUNCTION, LODASH_TEMPLATE_DISABLED, {
            events,
            name: `${LODASH_CODEGEN_TRANSFORMATION}:template-compiler`,
            target,
            label: `lodash template compiler (${id})`,
          });
        const staticUtil = replaceWithEvent(withoutTemplateCompiler, LODASH_UTIL_REQUIRE, LODASH_STATIC_UTIL, {
          events,
          name: `${LODASH_CODEGEN_TRANSFORMATION}:node-util-resolution`,
          target,
          label: `lodash node:util resolution (${id})`,
        });
        let staticConstructors = replaceWithEvent(
          staticUtil,
          LODASH_DYNAMIC_BUFFER_CONSTRUCTOR,
          LODASH_STATIC_BUFFER_CONSTRUCTOR,
          {
            events,
            name: `${LODASH_CODEGEN_TRANSFORMATION}:buffer-constructor`,
            target,
            label: `lodash Buffer clone constructor (${id})`,
          },
        );
        staticConstructors = replaceWithEvent(
          staticConstructors,
          LODASH_DYNAMIC_ARRAY_BUFFER_CONSTRUCTOR,
          LODASH_STATIC_ARRAY_BUFFER_CONSTRUCTOR,
          {
            events,
            name: `${LODASH_CODEGEN_TRANSFORMATION}:array-buffer-constructor`,
            target,
            label: `lodash ArrayBuffer clone constructor (${id})`,
          },
        );
        staticConstructors = replaceWithEvent(
          staticConstructors,
          LODASH_DYNAMIC_DATA_VIEW_CONSTRUCTOR,
          LODASH_STATIC_DATA_VIEW_CONSTRUCTOR,
          {
            events,
            name: `${LODASH_CODEGEN_TRANSFORMATION}:data-view-constructor`,
            target,
            label: `lodash DataView clone constructor (${id})`,
          },
        );
        staticConstructors = replaceWithEvent(
          staticConstructors,
          LODASH_DYNAMIC_REGEXP_CONSTRUCTOR,
          LODASH_STATIC_REGEXP_CONSTRUCTOR,
          {
            events,
            name: `${LODASH_CODEGEN_TRANSFORMATION}:regexp-constructor`,
            target,
            label: `lodash RegExp clone constructor (${id})`,
          },
        );
        staticConstructors = replaceWithEvent(
          staticConstructors,
          LODASH_DYNAMIC_TYPED_ARRAY_CONSTRUCTOR,
          LODASH_STATIC_TYPED_ARRAY_CONSTRUCTOR,
          {
            events,
            name: `${LODASH_CODEGEN_TRANSFORMATION}:typed-array-constructor`,
            target,
            label: `lodash typed array clone constructor (${id})`,
          },
        );
        staticConstructors = replaceWithEvent(
          staticConstructors,
          LODASH_DYNAMIC_ARRAY_CONSTRUCTOR,
          LODASH_STATIC_ARRAY_CONSTRUCTOR,
          {
            events,
            name: `${LODASH_CODEGEN_TRANSFORMATION}:array-constructor`,
            target,
            label: `lodash Array clone constructor (${id})`,
          },
        );
        return {
          code: prependWithEvent(staticConstructors, LODASH_UTIL_IMPORT, {
            events,
            name: `${LODASH_CODEGEN_TRANSFORMATION}:node-util-import`,
            target,
            label: `lodash node:util import (${id})`,
          }),
          map: null,
        };
      }
      if (normalizedId.endsWith(I18NEXT_FS_BACKEND_IMPORTER)) {
        transformations.add(I18NEXT_CODEGEN_TRANSFORMATION);
        return {
          code: replaceWithEvent(code, I18NEXT_EVAL_ALIAS, I18NEXT_EVAL_DISABLED, {
            events,
            name: I18NEXT_CODEGEN_TRANSFORMATION,
            target,
            label: `i18next executable translation loader (${id})`,
          }),
          map: null,
        };
      }
      if (normalizedId.endsWith(PG_NATIVE_CLIENT_IMPORTER)) {
        transformations.add(PG_NATIVE_TRANSFORMATION);
        return {
          code: replaceWithEvent(code, PG_NATIVE_REQUIRE, PG_NATIVE_UNAVAILABLE, {
            events,
            name: PG_NATIVE_TRANSFORMATION,
            target,
            label: `pg optional native client (${id})`,
          }),
          map: null,
        };
      }
      if (id === entryPath && code.includes(MCPHUB_SERVER_SPECIFIER)) {
        const withSetterImport = replaceWithEvent(
          code,
          MCPHUB_SERVER_IMPORT,
          `${MCPHUB_SERVER_IMPORT}\n${MCPHUB_MODULE_DIR_SETTER_IMPORT}`,
          {
            events,
            name: `${RUNTIME_MODULE_DIR_TRANSFORMATION}:setter-import`,
            target,
            label: "owned runtime MCPHub server import",
          },
        );
        transformations.add(RUNTIME_MODULE_DIR_TRANSFORMATION);
        return {
          code: replaceWithEvent(
            withSetterImport,
            MCPHUB_APP_SERVER_CONSTRUCTION,
            `  __setMcpHubSealedRuntimeModuleDir(path.join(input.distributionRoot, "package", "dist", "utils"));\n${MCPHUB_APP_SERVER_CONSTRUCTION}`,
            {
              events,
              name: `${RUNTIME_MODULE_DIR_TRANSFORMATION}:appserver-construction`,
              target,
              label: "owned runtime MCPHub AppServer construction",
            },
          ),
          map: null,
        };
      }
      return null;
    },
    moduleParsed(info) {
      invariant(!info.id.startsWith("\0"), `virtual module input is not exhaustively hashable: ${info.id}`);
      invariant(typeof info.code === "string", `bundle module source is unavailable: ${info.id}`);
      invariant(moduleInputs.has(info.id), `bundle module exact input bytes were not captured: ${info.id}`);
      moduleIds.add(info.id);
    },
  };
}

async function stableInputBytes(id) {
  let handle;
  try {
    handle = await open(id, constants.O_RDONLY | constants.O_NOFOLLOW);
  } catch (error) {
    throw new Error(`bundle input could not be reopened without following links: ${id}`, { cause: error });
  }
  try {
    const before = await handle.stat({ bigint: true });
    invariant(before.isFile(), `bundle input is not a regular file: ${id}`);
    const bytes = await handle.readFile();
    const after = await handle.stat({ bigint: true });
    for (const field of ["dev", "ino", "size", "mode", "uid", "gid", "nlink", "mtimeNs", "ctimeNs"]) {
      invariant(before[field] === after[field], `bundle input identity changed during revalidation (${field}): ${id}`);
    }
    invariant(BigInt(bytes.byteLength) === before.size, `bundle input short read during revalidation: ${id}`);
    return bytes;
  } finally {
    await handle.close();
  }
}

async function moduleInventory(inventoryRoot, moduleIds, moduleInputs) {
  const records = [];
  for (const id of [...moduleIds].sort()) {
    invariant(path.isAbsolute(id), `bundle module is not an absolute file: ${id}`);
    const relativePath = portableRelative(inventoryRoot, id, "bundle module");
    const captured = moduleInputs.get(id);
    invariant(captured !== undefined, `bundle module exact input bytes are absent: ${relativePath}`);
    const currentBytes = await stableInputBytes(id);
    invariant(currentBytes.equals(captured.bytes), `bundle input changed after Rolldown captured exact bytes: ${relativePath}`);
    invariant(captured.bytes.byteLength > 0, `bundle module is empty: ${relativePath}`);
    records.push(Object.freeze({
      path: relativePath,
      sha256: captured.sha256,
      size: captured.bytes.byteLength,
      kind: moduleKind(relativePath),
    }));
  }
  records.sort((left, right) => codeUnitCompare(left.path, right.path));
  invariant(records.length > 0, "bundle module inventory is empty");
  invariant(new Set(records.map((record) => record.path)).size === records.length, "bundle module inventory contains duplicate paths");
  return Object.freeze(records);
}

export async function bundleRuntime({
  entryPath,
  outputPath,
  inventoryRoot,
  outputRelativePath = OUTPUT_PATH,
  afterInputCaptured = undefined,
}) {
  invariant(VERSION === ROLLDOWN_VERSION, `rolldown version drift: ${VERSION}`);
  invariant(portableRelative(inventoryRoot, entryPath, "bundle entry") === ENTRY_PATH, `bundle entry must be ${ENTRY_PATH}`);
  invariant(path.isAbsolute(outputPath), "bundle output path must be absolute");
  invariant(outputRelativePath === OUTPUT_PATH, `bundle output must be ${OUTPUT_PATH}`);

  const moduleIds = new Set();
  const moduleInputs = new Map();
  const transformations = new Set();
  const events = new Map();
  const build = await rolldown({
    cwd: inventoryRoot,
    input: entryPath,
    platform: "node",
    treeshake: true,
    external(id) {
      return id.startsWith("node:");
    },
    onLog: failLog,
    plugins: [closurePlugin({
      moduleIds,
      moduleInputs,
      transformations,
      events,
      entryPath,
      inventoryRoot,
      afterInputCaptured,
    })],
  });

  let generated;
  try {
    generated = await build.generate({
      file: outputPath,
      format: "esm",
      codeSplitting: false,
      sourcemap: false,
      minify: "dce-only",
      comments: false,
      exports: "named",
      polyfillRequire: false,
    });
  } finally {
    await build.close();
  }

  invariant(generated.output.length === 1, "rolldown must emit exactly one output");
  const [chunk] = generated.output;
  invariant(chunk.type === "chunk" && chunk.isEntry, "rolldown output must be one entry chunk");
  invariant(chunk.imports.every((specifier) => specifier.startsWith("node:")), "rolldown output retains a non-node external import");
  invariant(chunk.exports.includes("main"), "rolldown entry does not export main");
  invariant(chunk.map === null, "rolldown emitted a source map");
  invariant(!chunk.code.includes("sourceMappingURL"), "rolldown entry contains a source-map reference");
  invariant(
    transformations.has(MCPHUB_MODULE_DIR_TRANSFORMATION) === transformations.has(RUNTIME_MODULE_DIR_TRANSFORMATION),
    "sealed MCPHub module-directory transformation pair is incomplete",
  );
  const normalizedResolution = normalizeNodeBuiltinResolution(chunk.code, transformations, events, outputRelativePath);
  const outputCode = normalizeSafeFunctionReferences(normalizedResolution.code, transformations, events, outputRelativePath);
  const outputAst = parseAst(outputCode, { lang: "js", sourceType: "module", astType: "js" }, outputRelativePath);
  assertLiteralDynamicImports(outputAst, outputRelativePath, outputCode);
  assertSealedOutputAst(outputAst, outputRelativePath, outputCode);
  const outputImports = Object.freeze(outputAst.body
    .filter((statement) => statement.type === "ImportDeclaration")
    .map((statement) => statement.source.value)
    .sort(codeUnitCompare));
  invariant(outputImports.every((specifier) => specifier.startsWith("node:")), "normalized output retains a non-node external import");
  invariant(!outputImports.includes("node:module") && !outputImports.includes("node:process") && !outputImports.includes("node:vm"), "normalized output retains a mutable code-loader built-in");
  const bytes = Buffer.from(outputCode, "utf8");
  const sealed = assertSelfContainedModule(bytes);
  invariant(sealed.policySha256 === SEALED_MODULE_POLICY_SHA256, "sealed-module policy digest mismatch");
  await mkdir(path.dirname(outputPath), { mode: 0o700, recursive: true });
  await chmod(path.dirname(outputPath), 0o700);
  await writeFile(outputPath, bytes, { flag: "wx", mode: 0o600 });
  await chmod(outputPath, 0o600);

  const modules = await moduleInventory(inventoryRoot, moduleIds, moduleInputs);
  const transformEvents = Object.freeze([...events.values()].sort((left, right) => codeUnitCompare(canonicalJson(left), canonicalJson(right))));
  invariant(transformEvents.every((event) => event.count === 1), "bundle transform event counts must be exactly one");
  const transformEventsSha256 = sha256Bytes(Buffer.from(canonicalJson(transformEvents), "utf8"));
  const moduleInventorySha256 = sha256Bytes(Buffer.from(canonicalJson(modules), "utf8"));
  const entrySha256 = sha256Bytes(bytes);
  const buildAttestation = Object.freeze({
    schemaVersion: 1,
    astValidated: true,
    entrySha256,
    validatorPolicySha256: SEALED_MODULE_POLICY_SHA256,
    transformEventsSha256,
    moduleInventorySha256,
  });
  const buildAttestationSha256 = sha256Bytes(Buffer.from(canonicalJson(buildAttestation), "utf8"));
  return Object.freeze({
    schemaVersion: 1,
    bundler: Object.freeze({
      name: "rolldown",
      version: ROLLDOWN_VERSION,
      entry: ENTRY_PATH,
      output: OUTPUT_PATH,
      format: "esm",
      platform: "node",
      codeSplitting: false,
      sourcemap: false,
      minify: "dce-only",
      comments: false,
      polyfillRequire: false,
      emittedChunks: 1,
      emittedAssets: 0,
    }),
    modules,
    transformations: Object.freeze([...transformations].sort()),
    transformEvents,
    transformEventsSha256,
    validatorPolicySha256: SEALED_MODULE_POLICY_SHA256,
    buildAttestation,
    buildAttestationSha256,
    entrySha256,
    entrySize: bytes.byteLength,
    imports: Object.freeze(outputImports),
    exports: Object.freeze([...chunk.exports].sort()),
  });
}
