/**
 * OpenCode Context Cache plugin.
 *
 * Vendored from JackDrogon/opencode-context-cache and hardened so debug logs never
 * write the raw cache key. The plugin aligns promptCacheKey and provider session
 * headers with one SHA-256 digest to improve provider prompt-cache reuse.
 */

import { createHash } from "crypto";
import { appendFileSync, existsSync, mkdirSync } from "fs";
import { hostname, userInfo } from "os";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const SESSION_ID_HEADER_NAMES = [
  "x-session-id",
  "conversation_id",
  "session_id",
];
const PROMPT_CACHE_KEY_ENV_VAR = "OPENCODE_PROMPT_CACHE_KEY";
const STICKY_SESSION_ID_ENV_VAR = "OPENCODE_STICKY_SESSION_ID";
const CACHE_DEBUG_ENV_VAR = "OPENCODE_CONTEXT_CACHE_DEBUG";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const LOG_FILE_PATH = join(__dirname, "context-cache.log");

class DebugLogger {
  constructor(logFilePath) {
    this.logFilePath = logFilePath;
    this.debugEnabled = null;
    this.loggedInputStructure = false;
    this.ensureLogDirectory();
  }

  ensureLogDirectory() {
    try {
      const logDir = dirname(this.logFilePath);
      if (!existsSync(logDir)) {
        mkdirSync(logDir, { recursive: true });
      }
    } catch {
      // Debug logging must never break chat execution.
    }
  }

  isEnabled() {
    if (this.debugEnabled === null) {
      this.debugEnabled =
        process?.env?.[CACHE_DEBUG_ENV_VAR] === "1" ||
        process?.env?.[CACHE_DEBUG_ENV_VAR] === "true";
    }
    return this.debugEnabled;
  }

  toLogString(value) {
    if (typeof value !== "object" || value === null) {
      return String(value);
    }
    try {
      return JSON.stringify(value);
    } catch {
      return String(value);
    }
  }

  log(...args) {
    if (!this.isEnabled()) return;

    const timestamp = new Date().toISOString();
    const pid = process.pid;
    const message = args.map((arg) => this.toLogString(arg)).join(" ");
    const safeMessage = message.replace(/\n/g, "\\n").replace(/\r/g, "\\r");
    const logLine = `[${timestamp}] [pid:${pid}] [context-cache] ${safeMessage}\n`;

    try {
      appendFileSync(this.logFilePath, logLine, "utf8");
    } catch {
      console.error(`[pid:${pid}] [context-cache]`, ...args);
    }
  }

  logInputStructureOnce(input) {
    if (this.loggedInputStructure) return;
    this.loggedInputStructure = true;

    this.log("Input structure:", {
      hasProvider: !!input?.provider,
      providerKeys: input?.provider ? Object.keys(input.provider) : [],
      hasModel: !!input?.model,
      modelKeys: input?.model ? Object.keys(input.model) : [],
      hasSessionID: !!input?.sessionID,
    });
  }
}

class CacheKeyResolver {
  constructor(logger) {
    this.logger = logger;
  }

  sha256(input) {
    return createHash("sha256").update(input, "utf8").digest("hex");
  }

  isSha256Hex(value) {
    if (typeof value !== "string") return false;
    const normalized = value.trim();
    return normalized.length === 64 && /^[a-fA-F0-9]{64}$/.test(normalized);
  }

  getTrimmedEnv(name) {
    const value = process?.env?.[name];
    return typeof value === "string" ? value.trim() : "";
  }

  getUsername() {
    try {
      const info = userInfo();
      if (info?.username) return info.username;
    } catch {
      // userInfo can fail in restricted sandboxes.
    }

    return (
      process?.env?.USER ||
      process?.env?.USERNAME ||
      process?.env?.LOGNAME ||
      "unknown"
    );
  }

  getUserHostDirectoryKey() {
    try {
      return `${this.getUsername()}@${hostname()}:${process.cwd()}`;
    } catch {
      return null;
    }
  }

  getSessionIdFromHeaders(input) {
    const headers =
      input?.model?.headers && typeof input.model.headers === "object"
        ? input.model.headers
        : {};

    const value = SESSION_ID_HEADER_NAMES.map((key) => headers[key]).find(
      (candidate) => typeof candidate === "string" && candidate.trim(),
    );

    return value?.trim?.() || null;
  }

  resolveCacheKey(input) {
    let rawKey = null;
    let source = null;
    let alreadyHashed = false;

    const promptCacheKey = this.getTrimmedEnv(PROMPT_CACHE_KEY_ENV_VAR);
    if (promptCacheKey) {
      rawKey = promptCacheKey;
      source = PROMPT_CACHE_KEY_ENV_VAR;
    }

    if (!rawKey) {
      const stickySessionKey = this.getTrimmedEnv(STICKY_SESSION_ID_ENV_VAR);
      if (stickySessionKey) {
        rawKey = stickySessionKey;
        source = STICKY_SESSION_ID_ENV_VAR;
      }
    }

    if (!rawKey) {
      const userHostDirKey = this.getUserHostDirectoryKey();
      if (userHostDirKey) {
        rawKey = userHostDirKey;
        source = "user@host:directory";
      }
    }

    if (!rawKey) {
      const headerValue = this.getSessionIdFromHeaders(input);
      if (headerValue) {
        rawKey = headerValue;
        source = "model headers";
        alreadyHashed = this.isSha256Hex(rawKey);
      }
    }

    if (!rawKey) {
      const sessionID =
        typeof input?.sessionID === "string" ? input.sessionID : "";
      if (sessionID) {
        rawKey = sessionID;
        source = "opencode sessionID";
      }
    }

    if (!rawKey) {
      this.logger.log("No stable cache key found");
      return null;
    }

    const hashedKey = alreadyHashed ? rawKey : this.sha256(rawKey);
    this.logger.log(`Using cache key from ${source}`);
    this.logger.log(`Set cache key hash: ${hashedKey}`);
    return { hashed: hashedKey };
  }
}

class CacheKeyApplier {
  constructor(logger) {
    this.logger = logger;
  }

  applyPromptCacheKey(output, cacheKey) {
    const existingOutputOptions =
      output?.options && typeof output.options === "object"
        ? output.options
        : {};

    output.options = {
      ...existingOutputOptions,
      promptCacheKey: cacheKey,
    };
  }

  applySessionHeaders(input, cacheKey) {
    if (!input?.model || typeof input.model !== "object") {
      this.logger.log(
        "Input model is missing or not an object, cannot set session headers",
      );
      return;
    }

    const headers =
      input.model.headers && typeof input.model.headers === "object"
        ? input.model.headers
        : (input.model.headers = {});

    for (const headerKey of SESSION_ID_HEADER_NAMES) {
      headers[headerKey] = cacheKey;
    }

    if (this.logger.isEnabled()) {
      headers["x-cache-debug"] = "1";
    }
  }

  apply(input, output, cacheKey) {
    this.applyPromptCacheKey(output, cacheKey);
    this.applySessionHeaders(input, cacheKey);
  }
}

const logger = new DebugLogger(LOG_FILE_PATH);
const keyResolver = new CacheKeyResolver(logger);
const keyApplier = new CacheKeyApplier(logger);

export const OpenCodeContextCachePlugin = async () => {
  logger.log("Plugin initialized");
  logger.log("Log file location:", LOG_FILE_PATH);

  return {
    "chat.params": async (input, output) => {
      logger.logInputStructureOnce(input);
      const cacheKeyInfo = keyResolver.resolveCacheKey(input);
      if (!cacheKeyInfo) return;
      keyApplier.apply(input, output, cacheKeyInfo.hashed);
    },
  };
};

export const EnhancedCachePlugin = OpenCodeContextCachePlugin;

export default OpenCodeContextCachePlugin;
