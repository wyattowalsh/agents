# Communications Templates

Use plain language. State facts, response, impact, and next update time. Do not speculate about root cause.

## Internal Responder Update

```text
Status: [investigating | mitigated | monitoring | resolved]
Severity: [SEV-x]
Impact: [who or what is affected]
Current understanding: [verified facts only]
Actions in progress: [top 1-3 actions]
Owner / commander: [name or role]
Next update: [time]
```

## Executive Update

```text
We are responding to a [SEV-x] incident affecting [customer journey / business area].
Known impact: [plain-language business impact].
Current mitigation: [what the team is doing now].
Risk to watch: [what could worsen or broaden impact].
Next decision point / update: [time].
```

## Support Update

```text
We are investigating an incident affecting [feature / workflow].
Customers may see: [observable symptoms].
Current guidance: [workaround or "no workaround at this time"].
Do not promise: [recovery time / root cause] until confirmed.
Next update: [time].
```

## Customer Update

```text
We are investigating an issue affecting [feature or workflow].
Users may experience [symptom].
Our team is actively working to restore normal service.
We will share the next update by [time].
```

## Cadence Guidance

- `SEV-1`: fixed cadence, usually every 15-30 minutes
- `SEV-2`: every 30-60 minutes or when major state changes occur
- `SEV-3` and `SEV-4`: event-driven updates unless customer impact broadens

## Communications Rules

- Mention the next update time even if there is no new root-cause detail.
- Separate responder, executive, support, and customer audiences.
- Prefer “what users may observe” over technical internals in customer updates.
- If the state changes materially, send an early update instead of waiting for the full cadence.
