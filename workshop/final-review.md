# Final Review

## Goal

Turn your investigation into an operator-ready conclusion.

You are done when you can explain what happened, which signals prove it, and what you would change in production.

## Final Evidence Checklist

Confirm you have evidence for each item:

| Evidence | Found? |
| --- | --- |
| Your `student.id` filter works |  |
| ShopMate Sports trace is visible |  |
| Agent spans are visible |  |
| NIM LLM spans are visible |  |
| Token metrics are visible |  |
| GPU metrics are visible |  |
| NIM metrics are visible |  |
| Kubernetes namespace filter works |  |
| Agent-loop scenario is visible |  |
| Chargeback fields are present |  |

## Final Answer Template

Use this structure for your final answer:

```text
The highest token user was:

The highest token department was:

The highest-token conversation was:

The scenario was:

The spend was properly chargeback-tagged:

The trace evidence was:

The metric evidence was:

The likely cause was:

The operational recommendation is:
```

## Production Discussion

Think about how this maps to a real AI platform:

- What alert would catch this earlier?
- Should token budget be enforced per request, conversation, student, or department?
- Which team owns the fix: app team, platform team, model-serving team, or finance operations?
- What would Cisco UCS, Nexus, or storage telemetry add if this were a physical AI POD?

## Short Quiz

??? question "A conversation has normal request count but very high token spend. What should you inspect first?"
    Inspect the trace for large prompts, large completions, repeated LLM calls, agent loops, retries, and scenario labels.

??? question "GPU utilization is normal, but one request is very expensive. What does that suggest?"
    The issue may be app orchestration or prompt behavior rather than a GPU capacity problem.

??? question "Why does chargeback need both technical and business attributes?"
    Technical fields explain what happened. Business fields explain who owns the cost.

??? question "What is the safest way to capture prompts in this lab?"
    Use only synthetic retail prompts and capture content only in the validated lab mode.

## Exit Criteria

You can leave the lab with three practical skills:

1. Follow one AI request across app, model, GPU, and platform telemetry.
2. Use token metrics to explain AI cost.
3. Diagnose a bounded agent-loop token burn from trace evidence.
