# 3. GenAI And Tool Monitoring

## Goal

Verify APM, GenAI spans, token metrics, prompt capture, and tool-call monitoring.

## Step 1: Confirm Environment Variables

```bash
kubectl exec deploy/ticketmate-ai -n "$STUDENT_NAMESPACE" -- env | sort | grep -E 'OTEL|NIM|TICKETMATE'
```

Required values:

```text
OTEL_SERVICE_NAME=ticketmate-ai
OTEL_EXPORTER_OTLP_ENDPOINT=http://student-collector:4318
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
OTEL_INSTRUMENTATION_GENAI_EMITTERS=span_metric
OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=SPAN_ONLY
OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE=delta
NIM_BASE_URL=http://nim-service.nim-system.svc.cluster.local:8000/v1
```

## Step 2: Generate A Trace

In the TicketMate UI, ask a normal planning question:

```text
Plan two tickets for a high-energy concert with a total budget around $250.
```

## Step 3: Find The Trace

In Splunk Observability Cloud:

1. Open APM or Trace Analyzer.
2. Filter by `service.name=ticketmate-ai`.
3. Add `deployment.environment=<your student id>`.
4. Open the most recent trace.

Look for:

- HTTP server span for the TicketMate request
- OpenAI Agents SDK activity
- model call spans
- model name
- prompt or response content, if capture is enabled and supported
- token attributes or related GenAI metrics
- function tool spans or events, where supported by the installed instrumentation

## Step 4: Check Tool Calls

TicketMate tools:

```text
search_events
check_ticket_inventory
compare_seat_sections
lookup_venue_policy
estimate_total_price
```

In the trace waterfall, identify which tools were used for the request.

Ask:

- Did the tool sequence match the user task?
- Did any tool repeat?
- Did a policy question incorrectly spend time in seat comparison or pricing?
- Did extra tool activity increase latency or tokens?

## Step 5: Find GenAI Token Metrics

Search Metrics for the GenAI token metric available in your tenant. Candidate names include:

```text
gen_ai.client.token.usage
gen_ai.usage.input_tokens
gen_ai.usage.output_tokens
```

Group or filter by:

```text
service.name=ticketmate-ai
deployment.environment=<student id>
student.id=<student id>
department.name=<department>
chargeback.account=<account>
```

Checkpoint:

```text
You can move from a TicketMate request to its trace and from that trace to token metrics.
```
