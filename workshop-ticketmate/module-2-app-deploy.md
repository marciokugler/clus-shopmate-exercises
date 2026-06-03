# 2. App Deploy

## Goal

Deploy TicketMate and configure the app for OpenTelemetry, GenAI monitoring, and NIM.

## Step 1: Review Required Python Packages

The TicketMate image must include:

```text
openai
openai-agents
splunk-opentelemetry
splunk-otel-instrumentation-openai
splunk-otel-instrumentation-openai-agents
```

The app must start with:

```bash
opentelemetry-instrument python ticketmate-ai/server.py
```

That startup command is already in the TicketMate Dockerfile.

## Step 2: Render The App Manifest

```bash
envsubst < lab-files/ticketmate-ai.yaml > ticketmate-ai.yaml
```

Confirm the rendered manifest includes:

```text
name: ticketmate-ai
OTEL_SERVICE_NAME=ticketmate-ai
OTEL_EXPORTER_OTLP_ENDPOINT=http://student-collector:4318
OTEL_INSTRUMENTATION_GENAI_EMITTERS=span_metric
OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=SPAN_ONLY
NIM_BASE_URL=<NIM /v1 endpoint>
```

## Step 3: Deploy The App

```bash
kubectl apply -n "$STUDENT_NAMESPACE" -f ticketmate-ai.yaml
kubectl rollout status deploy/ticketmate-ai -n "$STUDENT_NAMESPACE"
```

Validate:

```bash
kubectl get deploy,svc,pod -n "$STUDENT_NAMESPACE" -l app=ticketmate-ai
kubectl logs deploy/ticketmate-ai -n "$STUDENT_NAMESPACE" --tail=50
```

## Step 4: Open The UI

```bash
kubectl port-forward -n "$STUDENT_NAMESPACE" svc/ticketmate-ai 8080:8080
```

Open:

```text
http://127.0.0.1:8080/
```

Send one short request:

```text
Help me find two tickets for a concert under $250 total.
```

Expected result:

- the app returns a model-backed answer
- the UI shows agent outputs
- the UI shows approximate token values
- Splunk receives traces and metrics through the collector

!!! warning "No Fallback"
    TicketMate intentionally shows a clear error if the NIM/model path fails. Do not hide a missing model call with a deterministic local answer, because the lab depends on GenAI traces and token metrics.
