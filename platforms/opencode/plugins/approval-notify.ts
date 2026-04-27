import type { Plugin } from "@opencode-ai/plugin"
import { execFile } from "node:child_process"
import path from "node:path"
import { promisify } from "node:util"

const execFileAsync = promisify(execFile)

function findTerminalNotifier(): string | null {
  const candidates = [
    "/opt/homebrew/bin/terminal-notifier",
    "/usr/local/bin/terminal-notifier",
    "/usr/bin/terminal-notifier",
  ]
  for (const candidate of candidates) {
    try {
      // eslint-disable-next-line no-sync
      require("node:fs").accessSync(candidate)
      return candidate
    } catch {
      // continue
    }
  }
  return null
}

async function notify(title: string, message: string) {
  if (process.platform !== "darwin") {
    return
  }

  const notifier = findTerminalNotifier()
  if (!notifier) {
    // terminal-notifier not installed; silently skip so the session is never interrupted
    return
  }

  const args = [
    "-title", title,
    "-message", message,
    "-group", "opencode",
    "-activate", "com.mitchellh.ghostty",
    "-sender", "com.mitchellh.ghostty",
  ]

  try {
    await execFileAsync(notifier, args, { encoding: "utf8" })
  } catch {
    // Notifications should never interrupt the session.
  }
}

function firstString(...values: unknown[]) {
  for (const value of values) {
    if (typeof value === "string" && value.trim()) {
      return value.trim()
    }
  }
  return null
}

function describeEvent(event: any) {
  if (event.type === "permission.asked" || event.type === "permission.updated") {
    const toolName = firstString(
      event.properties?.title,
      event.properties?.metadata?.tool,
      event.tool,
      event.body?.tool,
      event.properties?.tool,
      event.permission?.tool,
      event.body?.permission?.tool,
    )
    return toolName ? `Approval requested for ${toolName}` : "Approval requested"
  }
  if (event.type === "session.error") {
    return "Session error"
  }
  if (event.type === "session.idle") {
    return "Session finished"
  }
  return event.type
}

export const ApprovalNotifyPlugin: Plugin = async ({ directory }) => {
  const workspace = path.basename(directory)

  return {
    event: async ({ event }) => {
      if (process.env.OPENCODE_NOTIFY_APPROVALS === "0") {
        return
      }
      if (event.type !== "permission.asked" && event.type !== "permission.updated" && event.type !== "session.error" && event.type !== "session.idle") {
        return
      }
      await notify("OpenCode", `${describeEvent(event)} in ${workspace}`)
    },
  }
}
