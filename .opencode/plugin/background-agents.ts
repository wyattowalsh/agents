import * as fs from "node:fs/promises"
import * as os from "node:os"
import * as path from "node:path"
import { type Plugin, tool } from "@opencode-ai/plugin"
import { adjectives, animals, colors, uniqueNamesGenerator } from "unique-names-generator"

type DelegationStatus = "queued" | "running" | "complete" | "error"

type DelegationRecord = {
  id: string
  sessionID: string
  messageID: string
  agent: string
  prompt: string
  status: DelegationStatus
  createdAt: string
  updatedAt: string
  outputPath: string
  result?: string
  error?: string
}

type SessionStore = {
  delegations: DelegationRecord[]
}

function generateReadableId(): string {
  return uniqueNamesGenerator({
    dictionaries: [adjectives, colors, animals],
    separator: "-",
    length: 3,
    style: "lowerCase",
  })
}

function getBaseDir(): string {
  return path.join(os.homedir(), ".local", "share", "opencode", "delegations")
}

async function ensureDir(dir: string): Promise<void> {
  await fs.mkdir(dir, { recursive: true })
}

async function readJson<T>(filePath: string, fallback: T): Promise<T> {
  try {
    const content = await fs.readFile(filePath, "utf8")
    return JSON.parse(content) as T
  } catch {
    return fallback
  }
}

async function writeJson(filePath: string, value: unknown): Promise<void> {
  await ensureDir(path.dirname(filePath))
  await fs.writeFile(filePath, JSON.stringify(value, null, 2) + "\n", "utf8")
}

async function getStore(sessionID: string): Promise<{ filePath: string; store: SessionStore }> {
  const root = getBaseDir()
  const filePath = path.join(root, sessionID, "index.json")
  const store = await readJson<SessionStore>(filePath, { delegations: [] })
  return { filePath, store }
}

function formatDelegation(record: DelegationRecord): string {
  const lines = [
    `# Delegation ${record.id}`,
    "",
    `- Status: ${record.status}`,
    `- Agent: ${record.agent}`,
    `- Session: ${record.sessionID}`,
    `- Message: ${record.messageID}`,
    `- Created: ${record.createdAt}`,
    `- Updated: ${record.updatedAt}`,
    "",
    "## Prompt",
    "",
    record.prompt,
    "",
  ]

  if (record.result) {
    lines.push("## Result", "", record.result, "")
  }

  if (record.error) {
    lines.push("## Error", "", record.error, "")
  }

  return lines.join("\n")
}

async function persistRecord(record: DelegationRecord): Promise<void> {
  await ensureDir(path.dirname(record.outputPath))
  await fs.writeFile(record.outputPath, formatDelegation(record), "utf8")
}

function summarizeRecord(record: DelegationRecord): string {
  const summary = record.result ?? record.error ?? "No output captured yet."
  const compact = summary.replace(/\s+/g, " ").trim()
  return compact.length > 140 ? `${compact.slice(0, 137)}...` : compact
}

export const BackgroundAgentsPlugin: Plugin = async ({ client }) => {
  const logger = (level: "debug" | "info" | "warn" | "error", message: string) =>
    client.app.log({ body: { service: "background-agents", level, message } }).catch(() => {})

  return {
    tool: {
      delegate: tool({
        description:
          "Queue a background delegation request and persist the prompt. This local vendored fallback records the work request and returns an ID for later tracking.",
        args: {
          agent: tool.schema.string().min(1).describe("Agent name to delegate to"),
          prompt: tool.schema.string().min(1).describe("Prompt for the background agent"),
        },
        async execute(args, context) {
          if (!context.sessionID) {
            throw new Error("delegate requires a sessionID in tool context")
          }
          if (!context.messageID) {
            throw new Error("delegate requires a messageID in tool context")
          }

          const id = generateReadableId()
          const outputPath = path.join(getBaseDir(), context.sessionID, `${id}.md`)
          const now = new Date().toISOString()
          const record: DelegationRecord = {
            id,
            sessionID: context.sessionID,
            messageID: context.messageID,
            agent: args.agent,
            prompt: args.prompt,
            status: "queued",
            createdAt: now,
            updatedAt: now,
            outputPath,
            result:
              "Local vendored fallback installed. This repo tracks delegation requests and artifacts, but full async sub-agent execution still requires the upstream KDCO plugin or native hosted support.",
          }

          const { filePath, store } = await getStore(context.sessionID)
          store.delegations = [record, ...store.delegations.filter((item) => item.id !== id)]
          await writeJson(filePath, store)
          await persistRecord(record)
          await logger("info", `Queued background delegation ${id} for agent ${args.agent}`)

          return [
            `Delegation queued: ${id}`,
            `Agent: ${args.agent}`,
            `Artifact: ${outputPath}`,
            "Status: queued",
            "This vendored fallback records the request locally for later inspection.",
          ].join("\n")
        },
      }),
      delegation_read: tool({
        description: "Read a previously recorded background delegation artifact by ID.",
        args: {
          id: tool.schema.string().min(1).describe("Delegation ID returned by delegate"),
        },
        async execute(args, context) {
          if (!context.sessionID) {
            throw new Error("delegation_read requires a sessionID in tool context")
          }

          const artifactPath = path.join(getBaseDir(), context.sessionID, `${args.id}.md`)
          try {
            return await fs.readFile(artifactPath, "utf8")
          } catch {
            return `No delegation artifact found for ${args.id}.`
          }
        },
      }),
      delegation_list: tool({
        description: "List recorded background delegations for the current session.",
        args: {},
        async execute(_args, context) {
          if (!context.sessionID) {
            throw new Error("delegation_list requires a sessionID in tool context")
          }

          const { store } = await getStore(context.sessionID)
          if (store.delegations.length === 0) {
            return "No delegations recorded for this session."
          }

          return store.delegations
            .map((record) => {
              const unread = record.status === "queued" || record.status === "running" ? "pending" : "done"
              return `- ${record.id} [${record.status}/${unread}] ${record.agent}: ${summarizeRecord(record)}`
            })
            .join("\n")
        },
      }),
    },
  }
}
