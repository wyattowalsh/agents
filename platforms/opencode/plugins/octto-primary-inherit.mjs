/**
 * Keep Octto's primary agent on the active OpenCode model.
 *
 * Upstream octto@0.3.1 hardcodes a Codex model on the primary `octto` agent.
 * This post-load config hook removes only that model pin while preserving Octto's
 * bootstrapper/probe defaults and any user-provided non-model settings.
 */

export const OcttoPrimaryInheritPlugin = async () => ({
  config: async (config) => {
    const octtoAgent = config?.agent?.octto;

    if (!octtoAgent || typeof octtoAgent !== "object") return;

    delete octtoAgent.model;
  },
});

export default OcttoPrimaryInheritPlugin;
