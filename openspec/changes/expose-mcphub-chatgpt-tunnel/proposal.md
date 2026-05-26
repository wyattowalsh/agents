# Proposal

## Problem

MCPHub is managed as a localhost-only control plane, but ChatGPT custom MCP
apps/connectors require a remote HTTPS MCP URL. A separate ChatGPT dev-harness
tunnel scaffold exists, but it is incomplete and would duplicate MCP server
ownership outside MCPHub.

## Intent

Let MCPHub optionally launch a stable Cloudflare Tunnel sidecar for ChatGPT
remote MCP access while keeping MCPHub itself bound to localhost. Publish the
same public MCP URL through launchd environment state and, when configured,
notify Zapier Central through a local-only webhook secret.

## Scope

- Add opt-in MCPHub tunnel lifecycle handling to the existing MCPHub shell
  scripts.
- Support stable Cloudflare named tunnels by token or local tunnel config.
- Keep tunnel credentials, bearer tokens, and Zapier webhook URLs in
  `.env.mcphub` only.
- Document the public ChatGPT MCP URL and Zapier handoff payload.

## Out Of Scope

- Creating or committing Cloudflare Tunnel credentials.
- Enabling public exposure by default.
- Replacing MCPHub bearer auth or adding OAuth.
- Reviving the incomplete standalone ChatGPT gateway process.
