import type { Plugin } from "@opencode-ai/plugin"
import path from "node:path"

const SAFE_ENV_BASENAMES = new Set([
  ".env.example",
  ".env.sample",
  ".env.template",
  ".env.test",
  ".env.testing",
])

const SENSITIVE_SUFFIXES = [".pem", ".p12", ".pfx", ".key"]

const SENSITIVE_PATH_MARKERS = [
  `${path.sep}.aws${path.sep}credentials`,
  `${path.sep}.docker${path.sep}config.json`,
  `${path.sep}.kube${path.sep}config`,
  `${path.sep}.npmrc`,
  `${path.sep}.pypirc`,
  `${path.sep}.netrc`,
  `${path.sep}.ssh${path.sep}id_ed25519`,
  `${path.sep}.ssh${path.sep}id_rsa`,
  `${path.sep}application_default_credentials.json`,
]

const BASH_SECRET_PATTERNS = [
  /\b(?:cat|less|head|tail|sed|awk|grep|rg)\b[^\n]*(?:\.env(?:\.[^/\s]+)?|\.npmrc|\.pypirc|\.netrc|id_(?:rsa|ed25519)|application_default_credentials\.json|\.pem|\.p12|\.pfx|\.key)\b/i,
  /\bsecurity\s+find-(?:generic|internet)-password\b/i,
  /\bgh\s+auth\s+token\b/i,
  /\bgcloud\s+auth\s+print-(?:access-token|identity-token)\b/i,
  /\baws\s+configure\s+get\b/i,
  /\bop\s+read\b/i,
  /\bpass\s+show\b/i,
  /\bkubectl\s+config\s+view\b[^\n]*--raw\b/i,
]

function looksPathLike(value: string) {
  return value.includes("/") || value.includes("\\") || value.startsWith(".")
}

function normalizeCandidate(value: string) {
  const expanded = value.replace(/^~(?=\/|\\)/, process.env.HOME ?? "~")
  return path.normalize(expanded)
}

function isSensitivePath(raw: string) {
  const normalized = normalizeCandidate(raw)
  const lower = normalized.toLowerCase()
  const basename = path.basename(lower)

  if (SAFE_ENV_BASENAMES.has(basename)) {
    return false
  }
  if (/^\.env(?:\.[^./\\]+)?$/.test(basename)) {
    return true
  }
  if (SENSITIVE_SUFFIXES.some((suffix) => basename.endsWith(suffix))) {
    return true
  }
  if (basename === "credentials.json" || basename === "auth.json" || basename === "secrets.toml") {
    return true
  }
  return SENSITIVE_PATH_MARKERS.some((marker) => lower.includes(marker.toLowerCase()))
}

function collectCandidatePaths(value: unknown, key = ""): string[] {
  if (typeof value === "string") {
    const keyLooksRelevant = /(path|file|target|source|old|new)/i.test(key)
    return keyLooksRelevant || looksPathLike(value) ? [value] : []
  }
  if (Array.isArray(value)) {
    return value.flatMap((item) => collectCandidatePaths(item, key))
  }
  if (value && typeof value === "object") {
    return Object.entries(value as Record<string, unknown>).flatMap(([nextKey, nextValue]) => collectCandidatePaths(nextValue, nextKey))
  }
  return []
}

function assertSafePaths(args: unknown) {
  const matches = [...new Set(collectCandidatePaths(args).filter(isSensitivePath))]
  if (matches.length === 0) {
    return
  }
  throw new Error(
    [
      "Blocked access to sensitive credential material.",
      "Ask the human to inspect or edit these files directly instead of using AI tools.",
      `Matched: ${matches.join(", ")}`,
      'Set OPENCODE_ALLOW_SECRET_FILES=1 only if you intentionally want to bypass this guard.',
    ].join(" "),
  )
}

function assertSafeCommand(command: string) {
  const matched = BASH_SECRET_PATTERNS.some((pattern) => pattern.test(command))
  if (!matched) {
    return
  }
  throw new Error(
    [
      "Blocked a shell command that appears to reveal or extract credentials.",
      "Use a human-run terminal command if you truly need to inspect secrets.",
      'Set OPENCODE_ALLOW_SECRET_FILES=1 only if you intentionally want to bypass this guard.',
    ].join(" "),
  )
}

function collectPatchPaths(patchText: string) {
  const matches = patchText.match(/^\*\*\* (?:Add|Update|Delete) File: (.+)$/gm) || []
  return matches.map((line) => line.replace(/^\*\*\* (?:Add|Update|Delete) File: /, "").trim())
}

export const CredentialGuardPlugin: Plugin = async () => {
  return {
    "tool.execute.before": async (input, output) => {
      if (process.env.OPENCODE_ALLOW_SECRET_FILES === "1") {
        return
      }

      if (input.tool === "read" || input.tool === "write" || input.tool === "edit") {
        assertSafePaths(output.args)
      }

      if (input.tool === "apply_patch" && typeof output.args?.patchText === "string") {
        assertSafePaths(collectPatchPaths(output.args.patchText))
      }

      if (input.tool === "bash" && typeof output.args?.command === "string") {
        assertSafeCommand(output.args.command)
      }
    },
  }
}
