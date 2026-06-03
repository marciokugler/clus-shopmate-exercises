# 1. Collector Setup

## Goal

Create the namespace-scoped Splunk OpenTelemetry Collector before deploying the app.

The collector will:

- receive TicketMate OTLP traces and metrics
- preserve GenAI metrics from app instrumentation
- scrape NIM model-serving metrics
- scrape GPU metrics from DCGM
- export data to Splunk Observability Cloud

## Step 1: Confirm Secrets

```bash
kubectl get secret "$SPLUNK_ACCESS_TOKEN_SECRET" -n "$STUDENT_NAMESPACE"
```

Expected result:

- the Secret exists
- you do not print the token value

If your NIM endpoint requires an API key:

```bash
kubectl get secret "$NIM_API_KEY_SECRET" -n "$STUDENT_NAMESPACE"
```

## Step 2: Create The Values File

Render the collector values template:

```bash
envsubst < lab-files/ticketmate-collector-values.yaml > student-collector-values.yaml
```

Review these sections:

| Section | Required result |
| --- | --- |
| `receivers.otlp` | OTLP gRPC `4317` and OTLP HTTP `4318` are enabled |
| `receivers.prometheus/gpu_nim` | DCGM and NIM scrape jobs are present |
| `resource/environment` | Adds `deployment.environment`, `k8s.cluster.name`, and namespace |
| `pipelines.traces` | Receives app traces from OTLP |
| `pipelines.metrics` | Receives app metrics from OTLP and is not GPU-filtered |
| `pipelines.metrics/gpu_nim` | Receives only GPU/NIM scrape metrics |

!!! important
    Keep the app OTLP metrics pipeline unfiltered. GenAI token metrics come through the app metrics pipeline and can disappear if the GPU/NIM allowlist is applied there.

## Step 3: Install The Collector

```bash
helm repo add splunk-otel-collector-chart https://signalfx.github.io/splunk-otel-collector-chart
helm repo update splunk-otel-collector-chart

helm upgrade --install student-collector \
  splunk-otel-collector-chart/splunk-otel-collector \
  --version 0.153.0 \
  --namespace "$STUDENT_NAMESPACE" \
  --values student-collector-values.yaml
```

Wait for rollout:

```bash
kubectl rollout status deploy/student-collector -n "$STUDENT_NAMESPACE"
kubectl get pods -n "$STUDENT_NAMESPACE" -l app.kubernetes.io/name=splunk-otel-collector
```

## Step 4: Validate Collector Logs

```bash
kubectl logs deploy/student-collector -n "$STUDENT_NAMESPACE" --tail=100
```

Expected result:

- no Splunk authentication errors
- no receiver configuration errors
- no scrape target configuration errors

## Step 5: Validate Splunk Ingest

In Splunk Observability Cloud:

1. Open Metric Finder or Metrics.
2. Search for one collector or receiver metric from your namespace.
3. Filter by `deployment.environment=<your student id>` or `k8s.cluster.name=<logical cluster name>`.

Checkpoint:

```text
The collector exists, exports to Splunk, and is ready to receive TicketMate telemetry.
```
