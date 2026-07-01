import type { Plugin } from "@opencode-ai/plugin"
import { execFileSync } from "node:child_process"
import fs from "node:fs"
import path from "node:path"

/**
 * Bridge OpenCode tool execution to the repo-managed wagents hook dispatcher.
 *
 * OpenCode has no native registry-driven hook surface, so this plugin projects
 * the fleet's enforce-tier PreToolUse guards onto OpenCode's
 * `tool.execute.before` event. For each guarded tool it invokes
 * `hooks/run-wagents-hook <policy> --harness opencode` with a normalized JSON
 * payload on stdin and blocks (throws) when the dispatcher returns a deny.
 *
 * Enforce-tier only and fail-closed only for an explicit deny: if the repo
 * runner cannot be located or the dispatcher errors, the bridge stays inert
 * (fails open) so it never breaks an OpenCode session it does not understand.
 */

const HOOK_RUNNER_REL = path.join("hooks", "run-wagents-hook")

// tool name -> ordered list of enforce-tier policy ids to consult (first deny wins).
const POLICY_MAP: Record<string, string[]> = {
  bash: ["cursor-destructive-shell-guard", "git-commit-push-guard"],
  read: ["cursor-before-read-file-guard"],
  write: ["cursor-protected-file-guard"],
  edit: ["cursor-protected-file-guard"],
  apply_patch: ["cursor-protected-file-guard"],
}

function findRepoRoot(start: string): string | null {
  const fromEnv = process.env.WAGENTS_REPO_ROOT
  if (fromEnv && fs.existsSync(path.join(fromEnv, HOOK_RUNNER_REL))) {
    return fromEnv
  }
  let current = path.resolve(start)
  for (let depth = 0; depth < 40; depth += 1) {
    if (fs.existsSync(path.join(current, HOOK_RUNNER_REL))) {
      return current
    }
    const parent = path.dirname(current)
    if (parent === current) {
      break
    }
    current = parent
  }
  return null
}

function isDeny(decision: unknown): boolean {
  if (!decision || typeof decision !== "object") {
    return false
  }
  const record = decision as Record<string, unknown>
  if (record.decision === "deny" || record.decision === "block") {
    return true
  }
  if (record.permission === "deny" || record.permissionDecision === "deny") {
    return true
  }
  const specific = record.hookSpecificOutput
  if (specific && typeof specific === "object") {
    const inner = specific as Record<string, unknown>
    if (inner.permission === "deny" || inner.permissionDecision === "deny") {
      return true
    }
  }
  return false
}

function denyReason(decision: Record<string, unknown>): string {
  return (
    (typeof decision.reason === "string" && decision.reason) ||
    (typeof decision.permissionDecisionReason === "string" && decision.permissionDecisionReason) ||
    (typeof decision.user_message === "string" && decision.user_message) ||
    "Blocked by repo-managed wagents policy."
  )
}

function runPolicy(repoRoot: string, policyId: string, payload: unknown): void {
  let stdout = ""
  try {
    stdout = execFileSync(path.join(repoRoot, HOOK_RUNNER_REL), [policyId, "--harness", "opencode"], {
      input: JSON.stringify(payload),
      encoding: "utf8",
      timeout: 5000,
      cwd: repoRoot,
    })
  } catch {
    // Dispatcher missing the policy id, crash, or timeout: fail open.
    return
  }
  const trimmed = stdout.trim()
  if (!trimmed) {
    return
  }
  let decision: unknown
  try {
    decision = JSON.parse(trimmed)
  } catch {
    return
  }
  if (isDeny(decision)) {
    throw new Error(`[wagents-hook-bridge:${policyId}] ${denyReason(decision as Record<string, unknown>)}`)
  }
}

export const WagentsHookBridgePlugin: Plugin = async ({ directory }) => {
  const repoRoot = findRepoRoot(directory ?? process.cwd())
  if (!repoRoot) {
    return {}
  }
  return {
    "tool.execute.before": async (input, output) => {
      const policies = POLICY_MAP[input.tool]
      if (!policies || policies.length === 0) {
        return
      }
      const payload = {
        hook_event_name: "PreToolUse",
        tool_name: input.tool,
        tool_input: output.args ?? {},
        cwd: repoRoot,
      }
      for (const policyId of policies) {
        runPolicy(repoRoot, policyId, payload)
      }
    },
  }
}
