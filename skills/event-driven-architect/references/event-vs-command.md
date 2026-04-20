# Event vs Command Decisions

Use this reference when a workflow description blurs together facts, requests,
and synchronous requirements.

## Choose an Event when

- The message records something that already happened
- Multiple independent consumers may react differently
- Replay is acceptable or valuable
- The producer should not wait for downstream side effects to complete
- The name reads naturally in past tense, such as `invoice.paid`

## Choose a Command when

- One owner is being asked to do something
- Success or failure belongs to a single responsible handler
- The sender expects a bounded action, not broad fan-out
- The name reads naturally as an imperative, such as `send-invoice`

## Keep a Synchronous Call when

- The caller needs immediate confirmation or strongly consistent state
- The workflow is user-facing and latency-sensitive
- Failure must be returned directly to the caller
- The interaction is really a query or RPC, not an asynchronous fact stream

## Smells

- A proposed event is named as an imperative verb phrase
- An event stream is used to fake request-response semantics
- Consumers rely on side effects that must happen before the producer returns
- One event type has so many conditional branches that it is really several commands or facts mixed together

## Decision Shortcuts

- Ask: "Did this already happen?" If yes, prefer an event.
- Ask: "Who owns the action?" If exactly one handler owns it, prefer a command.
- Ask: "Can this be replayed safely?" If no, redesign the handler or keep the interaction synchronous.
