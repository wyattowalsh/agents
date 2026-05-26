/**
 * Tuned local copy of ilgizar-valiullin/opencode-incomplete-resume-plugin.
 *
 * The upstream plugin is source-only. Keep this file structurally close to
 * upstream `auto-continue.ts`; the local changes are the conservative constants
 * below: lower retry count, longer cooldown, and explicit status trigger only.
 */

const AUTO_PROMPT = `
Continue autonomously from the current state. Do not recap. Do not restart from scratch.
Inspect the workspace state if needed. Perform the next unfinished action.
Stop only on COMPLETE or BLOCKED.
`.trim();

const MAX_CONTINUES = 3;
const COOLDOWN_MS = 2000;

// Trigger phrases that indicate the agent should continue.
const TRIGGER_PHRASES = [/TASK_STATUS:\s*INCOMPLETE/i];

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function extractText(parts) {
  return parts
    .map((part) => {
      if (part.type === "text") return part.text ?? "";
      if (typeof part.text === "string") return part.text;
      return "";
    })
    .join("\n");
}

function shouldAutoContinue(text) {
  // Don't continue if already complete or blocked.
  if (/TASK_STATUS:\s*COMPLETE/i.test(text)) return false;
  if (/TASK_STATUS:\s*BLOCKED/i.test(text)) return false;

  // Continue if INCOMPLETE or trigger phrases found.
  if (/TASK_STATUS:\s*INCOMPLETE/i.test(text)) return true;

  // Check for manual trigger phrases.
  for (const pattern of TRIGGER_PHRASES) {
    if (pattern.test(text)) return true;
  }

  return false;
}

export const AutoContinuePlugin = async ({ client }) => {
  const continueCounts = new Map();
  const lastTexts = new Map();
  const running = new Set();

  return {
    event: async ({ event }) => {
      // Listen to both session.idle and message.updated events.
      if (event.type !== "session.idle" && event.type !== "message.updated") {
        return;
      }

      const sessionId = event.properties?.sessionID ?? event.properties?.sessionId ?? event.properties?.id;

      if (!sessionId) return;
      if (running.has(sessionId)) return;

      const count = continueCounts.get(sessionId) ?? 0;
      if (count >= MAX_CONTINUES) {
        console.log(`[AutoContinue] Max continues (${MAX_CONTINUES}) reached for session ${sessionId}`);
        return;
      }

      try {
        const messages = await client.session.messages({
          path: { id: sessionId },
        });

        const items = messages.data ?? [];

        // Find the last assistant message.
        const last = [...items].reverse().find((item) => item.info?.role === "assistant");

        if (!last) return;

        const text = extractText(last.parts ?? []);
        if (!text.trim()) return;

        // Check if we should auto-continue.
        if (!shouldAutoContinue(text)) {
          // Reset counter if task is complete or blocked.
          if (/TASK_STATUS:\s*(COMPLETE|BLOCKED)/i.test(text)) {
            continueCounts.delete(sessionId);
            lastTexts.delete(sessionId);
          }
          return;
        }

        // Avoid duplicate triggers on the same text.
        if (lastTexts.get(sessionId) === text) return;

        running.add(sessionId);

        continueCounts.set(sessionId, count + 1);
        lastTexts.set(sessionId, text);

        console.log(`[AutoContinue] Triggering auto-continue #${count + 1} for session ${sessionId}`);

        await sleep(COOLDOWN_MS);

        await client.session.prompt({
          path: { id: sessionId },
          body: {
            parts: [{ type: "text", text: AUTO_PROMPT }],
          },
        });
      } catch (error) {
        console.error("[AutoContinue] Error:", error);
      } finally {
        running.delete(sessionId);
      }
    },
  };
};

export default AutoContinuePlugin;
