---
name: plannotator-annotate
description: Open Plannotator's annotation UI for a markdown file, converted HTML file, URL, or folder and then respond to the returned annotations.
allowed-tools: Bash(plannotator:*)
disable-model-invocation: true
---

# Plannotator Annotate

Run:

```bash
plannotator annotate $ARGUMENTS
```

The output will be one of:

1. The exact text `The user approved.`, or a JSON object with `"decision": "approved"`. Acknowledge with a single sentence and stop. Do not begin any work.
2. Empty, or a JSON object with `"decision": "dismissed"`. Acknowledge with a single sentence and stop. Do not begin any work.
3. Plaintext annotation feedback, or a JSON object with `"decision": "annotated"` and a `"feedback"` field. Address the feedback in the same conversation.

Do not ask the user to copy shell commands into chat. Run the command yourself.