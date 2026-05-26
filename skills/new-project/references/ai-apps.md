# AI Apps

## Python

Use Pydantic AI for simple typed Python LLM apps and LangGraph for graph/stateful workflows. Consult framework-selection before complex LangChain/LangGraph/Deep Agents work.

## TypeScript

Use the Vercel AI SDK package `ai`. Do not use `@vercel/ai`.

## Observability

LangSmith and Langfuse require user-owned environment variables. Generate placeholders only.

## AWS Bedrock And AgentCore

Treat AgentCore as an advanced planning profile. Local dev may use `agentcore dev`; deployment, IAM, ECR, account, gateway, memory, and identity operations require explicit approval.
