# 4. GPU And NIM Correlation

## Goal

Use one TicketMate trace timestamp to inspect model-serving and GPU platform behavior.

## Step 1: Start From A Trace

Open a recent `ticketmate-ai` trace and record:

- start time
- duration
- model span duration
- input/prompt tokens
- output/completion tokens
- number of tool calls

## Step 2: Inspect NIM Metrics

Around the same timestamp, inspect:

```text
prompt_tokens_total
generation_tokens_total
request_prompt_tokens
request_generation_tokens
time_to_first_token_seconds
time_per_output_token_seconds
e2e_request_latency_seconds
num_requests_running
num_requests_waiting
```

Ask:

- Did the trace occur during higher NIM latency?
- Did prompt or generation token counters move?
- Was the request waiting behind other model work?

## Step 3: Inspect GPU Metrics

Around the same timestamp, inspect:

```text
DCGM_FI_DEV_GPU_UTIL
DCGM_FI_DEV_FB_USED
DCGM_FI_DEV_FB_FREE
DCGM_FI_PROF_GR_ENGINE_ACTIVE
DCGM_FI_PROF_PIPE_TENSOR_ACTIVE
```

Ask:

- Did GPU utilization rise during the model-heavy request?
- Did framebuffer memory remain stable?
- Did high token demand affect the shared AI POD platform?

## Step 4: Explain Layer Differences

GenAI instrumentation token counts are app/client-side and trace-aware. Use them to answer:

```text
Which student, department, request, trace, or chargeback account caused the token usage?
```

NIM token counts are model-server-side counters. Use them to answer:

```text
How much aggregate token demand reached the shared model-serving layer?
```

The numbers may not match exactly because they are captured at different layers with different scrape windows, labels, retries, streaming behavior, and instrumentation versions.

Checkpoint:

```text
You can explain who spent tokens and what that demand did to NIM and GPU resources.
```
