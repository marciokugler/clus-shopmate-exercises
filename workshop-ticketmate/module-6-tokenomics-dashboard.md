# 6. Tokenomics Dashboard

## Goal

Build a dashboard that shows who spent the most GenAI tokens by student, department, and chargeback account.

Dashboard name:

```text
TicketMate Tokenomics
```

## Step 1: Find The Token Metric

In Splunk Observability Cloud Metrics, search for the GenAI token metric available in your tenant.

Likely candidates:

```text
gen_ai.client.token.usage
gen_ai.usage.input_tokens
gen_ai.usage.output_tokens
```

If your metric has a token type dimension, split by the token type dimension to separate input/prompt and output/completion tokens.

## Step 2: Create Core Token Panels

Create these charts and save them to `TicketMate Tokenomics`.

| Panel | Filter | Group by |
| --- | --- | --- |
| Total GenAI tokens by student | `service.name=ticketmate-ai` | `student.id` |
| Total GenAI tokens by environment | `service.name=ticketmate-ai` | `deployment.environment` |
| Total GenAI tokens by department | `service.name=ticketmate-ai` | `department.name` |
| Total GenAI tokens by chargeback | `service.name=ticketmate-ai` | `chargeback.account` |
| Input vs output tokens | `service.name=ticketmate-ai` | token type dimension |

Use a five-minute or ten-minute time window while running simulator traffic.

## Step 3: Add Trace Context Panels

Add charts or links that help explain the token spend:

- highest-latency traces for `service.name=ticketmate-ai`
- request rate for `ticketmate-ai`
- GenAI/model latency if exposed by the installed instrumentation
- tool-call count or suspicious tool-call patterns where visible

## Step 4: Add AI POD Platform Panels

Add NIM panels:

```text
prompt_tokens_total
generation_tokens_total
e2e_request_latency_seconds
time_to_first_token_seconds
num_requests_running
num_requests_waiting
```

Add GPU panels:

```text
DCGM_FI_DEV_GPU_UTIL
DCGM_FI_DEV_FB_USED
DCGM_FI_PROF_GR_ENGINE_ACTIVE
DCGM_FI_PROF_PIPE_TENSOR_ACTIVE
```

## Step 5: Interpret The Dashboard

Answer:

- Which student spent the most tokens?
- Which department spent the most tokens?
- Did prompt/input tokens or completion/output tokens dominate?
- Did high spend come from request volume, long prompts, long completions, wrong tool calls, repeated model calls, or simulator traffic?
- Did NIM latency or GPU utilization change during the same window?

Checkpoint:

```text
The dashboard can identify the highest-token student and explain the likely cause with traces and platform metrics.
```
