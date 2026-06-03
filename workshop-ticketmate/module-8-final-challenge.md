# 8. Final Challenge

## Goal

Use a free multi-turn TicketMate conversation to create real token variation across the class, then prove who spent the most tokens.

## Challenge Task

Do not copy a provided prompt. Use TicketMate freely to achieve this task:

```text
Plan the best concert night for your group within your budget.
```

You may ask follow-up questions, compare events, change constraints, review policies, and ask for a final recommendation.

Do not enter real payment, identity, or private customer information.

## Student Work

Run a multi-turn conversation in the TicketMate UI.

Capture:

- your approximate token total from the UI
- one trace ID or trace timestamp
- the best event recommendation
- the key policy or budget caveat

## Class Investigation

In the `TicketMate Tokenomics` dashboard:

1. Rank token usage by `student.id`.
2. Rank token usage by `department.name`.
3. Rank token usage by `chargeback.account`.
4. Compare input/prompt and output/completion tokens.
5. Open a high-token trace.
6. Inspect tool calls and model spans.
7. Compare the same time window with NIM and GPU metrics.

## Finding Format

Use this format:

```text
Top student:
Top department:
Top chargeback account:
Highest-token window:
Prompt/input vs completion/output:
Trace evidence:
Tool-call evidence:
NIM/GPU evidence:
Likely cause:
Recommended guardrail:
```

Good guardrails include:

- token budget per request
- max agent turns
- clearer tool descriptions
- fail-fast handling for impossible constraints
- prompt length controls
- rate limits by student, department, or chargeback account

Checkpoint:

```text
You can defend the tokenomics answer with dashboard, trace, GenAI, NIM, and GPU evidence.
```
