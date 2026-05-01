# External Skills Install Set

Approved external Agent Skill sources for this repo. Treat these as
trust-bearing assets: inspect source-list output, hooks, scripts, commands,
network access, credential handling, and dedupe before repo promotion.

Target agents for installs in this environment:

- `antigravity`
- `claude-code`
- `codex`
- `cursor`
- `gemini-cli`
- `github-copilot`
- `opencode`

Use this exact target suffix unless a user asks for a different target set:

```bash
-a antigravity claude-code codex cursor gemini-cli github-copilot opencode
```

## Install Now After Trust Gate

```bash
npx skills add addyosmani/web-quality-skills --skill web-quality-audit --skill accessibility --skill seo --skill performance --skill core-web-vitals --skill best-practices -y -g -a antigravity claude-code codex cursor gemini-cli github-copilot opencode
```

```bash
npx skills add currents-dev/playwright-best-practices-skill --skill playwright-best-practices -y -g -a antigravity claude-code codex cursor gemini-cli github-copilot opencode
```

```bash
npx skills add vercel-labs/agent-skills --skill vercel-react-best-practices --skill vercel-composition-patterns --skill vercel-react-view-transitions --skill web-design-guidelines --skill vercel-react-native-skills -y -g -a antigravity claude-code codex cursor gemini-cli github-copilot opencode
```

```bash
npx skills add vercel-labs/next-skills --skill next-best-practices --skill next-cache-components --skill next-upgrade -y -g -a antigravity claude-code codex cursor gemini-cli github-copilot opencode
```

```bash
npx skills add cloudflare/skills --skill cloudflare --skill wrangler --skill workers-best-practices --skill durable-objects --skill agents-sdk -y -g -a antigravity claude-code codex cursor gemini-cli github-copilot opencode
```

```bash
npx skills add supabase/agent-skills --skill supabase-postgres-best-practices --skill supabase -y -g -a antigravity claude-code codex cursor gemini-cli github-copilot opencode
```

```bash
npx skills add stripe/ai --skill stripe-best-practices --skill upgrade-stripe -y -g -a antigravity claude-code codex cursor gemini-cli github-copilot opencode
```

## Inspect Then Install

Run these only after `external-skill-auditor` confirms the source-list output,
scripts, hooks, credential behavior, and dedupe fit.

```bash
npx skills add trailofbits/skills --skill codeql --skill semgrep --skill property-based-testing -y -g -a antigravity claude-code codex cursor gemini-cli github-copilot opencode
```

```bash
npx skills add github/awesome-copilot --skill agent-governance --skill agent-supply-chain --skill agent-owasp-compliance --skill agentic-eval -y -g -a antigravity claude-code codex cursor gemini-cli github-copilot opencode
```

```bash
npx skills add langchain-ai/langchain-skills --skill framework-selection --skill langchain-fundamentals --skill langgraph-fundamentals --skill langgraph-human-in-the-loop --skill langgraph-persistence --skill langchain-rag -y -g -a antigravity claude-code codex cursor gemini-cli github-copilot opencode
```

```bash
npx skills add expo/skills --skill building-native-ui --skill expo-dev-client --skill expo-deployment --skill expo-cicd-workflows --skill upgrading-expo -y -g -a antigravity claude-code codex cursor gemini-cli github-copilot opencode
```

```bash
npx skills add getsentry/sentry-for-ai --skill sentry-fix-issues --skill sentry-setup-ai-monitoring --skill sentry-sdk-setup -y -g -a antigravity claude-code codex cursor gemini-cli github-copilot opencode
```

```bash
npx skills add github/awesome-copilot --skill phoenix-tracing --skill phoenix-evals --skill arize-instrumentation --skill arize-evaluator --skill arize-prompt-optimization -y -g -a antigravity claude-code codex cursor gemini-cli github-copilot opencode
```

```bash
npx skills add pydantic/skills --skill building-pydantic-ai-agents --skill instrumentation -y -g -a antigravity claude-code codex cursor gemini-cli github-copilot opencode
```

```bash
npx skills add mcp-use/skills --skill mcp-builder --skill chatgpt-app-builder -y -g -a antigravity claude-code codex cursor gemini-cli github-copilot opencode
```

```bash
npx skills add openai/skills --skill chatgpt-apps --skill cli-creator --skill security-threat-model --skill security-best-practices --skill security-ownership-map -y -g -a antigravity claude-code codex cursor gemini-cli github-copilot opencode
```

```bash
npx skills add ljagiello/ctf-skills --skill ctf-ai-ml --skill ctf-crypto --skill ctf-forensics --skill ctf-malware --skill ctf-misc --skill ctf-osint --skill ctf-pwn --skill ctf-reverse --skill ctf-web --skill ctf-writeup --skill solve-challenge -y -g -a antigravity claude-code codex cursor gemini-cli github-copilot opencode
```

Use `ljagiello/ctf-skills` only for authorized CTF, lab, and security-research work. Its audit found MIT licensing and responsible-use framing, but also offensive-security workflows, write-capable permissions, and a broad local installer that can invoke `pip`, `apt`, `brew`, `gem`, `go`, and possibly `sudo`; run the installer dry-run before executing it.

```bash
npx skills add nextlevelbuilder/ui-ux-pro-max-skill --skill ui-ux-pro-max -y -g -a antigravity claude-code codex cursor gemini-cli github-copilot opencode
```

Install only `ui-ux-pro-max` from `nextlevelbuilder/ui-ux-pro-max-skill`. Keep bundled `ckm:*` skills out of the curated install set unless explicitly requested because they overlap existing local skills and introduce broader API/script surfaces.

```bash
npx skills add Leonxlnx/taste-skill --skill design-taste-frontend -y -g -a antigravity claude-code codex cursor gemini-cli github-copilot opencode
```

Install only `design-taste-frontend` from `Leonxlnx/taste-skill` by default. The source-list exposes 12 skills and the repository has strong public adoption, MIT licensing, and no observed hooks in the inspected skill frontmatter, but the bundle substantially overlaps local design/image-generation workflows; keep style variants, image-generation variants, `full-output-enforcement`, and `stitch-design-taste` global-only unless a user explicitly requests them.

## Keep Global Only Or Avoid

- `vercel-labs/skills@find-skills`: duplicate of `discover-skills`.
- `vercel-labs/agent-browser`: useful, but broad operational scope and overlaps browser automation.
- `anthropics/skills`: inspect case-by-case; many skills duplicate local/system skills.
- `huggingface/skills`: keep global unless ML workflows become frequent.
- Community Better Auth, Clerk, Neon, and generic OpenAI Agent SDK skills: lower source confidence or duplicate local architecture coverage.
- `docs.stripe.com@stripe-best-practices`: registry syntax and provenance still need verification before automated sync/install.
- `nextlevelbuilder/ui-ux-pro-max-skill@ckm:*`: avoid by default; overlaps existing local skills and has broader API/script surfaces than the approved `ui-ux-pro-max` skill.
- `Leonxlnx/taste-skill` bundle variants besides `design-taste-frontend`: keep global-only unless explicitly requested; many are visual-style, image-generation, Google Stitch, or output-behavior skills that overlap current design workflows.

## Validation After Install Or Promotion

```bash
uv run wagents validate
uv run wagents eval validate
uv run python skills/skill-creator/scripts/audit.py skills/external-skill-auditor
uv run python skills/skill-creator/scripts/audit.py skills/i18n-localization
uv run python skills/skill-creator/scripts/audit.py skills/agent-runtime-governance
uv run wagents package external-skill-auditor --dry-run
uv run wagents package i18n-localization --dry-run
uv run wagents package agent-runtime-governance --dry-run
```
