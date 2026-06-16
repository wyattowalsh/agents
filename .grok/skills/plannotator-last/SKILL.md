---
name: plannotator-last
description: Open Plannotator on the latest rendered assistant message and use the returned annotations to revise that message or continue.
allowed-tools: Bash(plannotator:*)
disable-model-invocation: true
---

# Plannotator Last

Run:

```bash
plannotator annotate-last $ARGUMENTS
```

The output will be one of:

1. The exact text `The user approved.`, or a JSON object with `"decision": "approved"`. Acknowledge with a single sentence and stop. Do not begin any work.
2. Empty, or a JSON object with `"decision": "dismissed"`. Acknowledge with a single sentence and stop. Do not begin any work.
3. Plaintext annotation feedback, or a JSON object with `"decision": "annotated"` and a `"feedback"` field. Revise the last message or continue based on the feedback.

Do not ask the user to copy shell commands into chat. Run the command yourself.