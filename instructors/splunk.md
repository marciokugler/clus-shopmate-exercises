# Splunk Setup

Splunk Observability Cloud is the lab telemetry destination. Instructors own the org, realm, ingest token, and access model. Students should not need the raw ingest token.

## Required Values

Prepare:

```text
SPLUNK_OBSERVABILITY_URL=<org-url>
SPLUNK_REALM=<realm>
SPLUNK_ACCESS_TOKEN=<lab-scoped-ingest-token>
SPLUNK_ACCESS_TOKEN_SECRET=splunk-observability-token
```

The student-facing guide uses only the realm and Kubernetes Secret name. The token itself is preloaded by instructors.

## Create A Lab-Scoped Token

Use a token dedicated to this lab delivery. Name it with the environment and date, for example:

```text
clus-ltrobs-2001-event-2026-06
```

Record:

- token owner
- creation time
- intended deletion or rotation time
- realm
- event environment

!!! warning "After class"
    Rotate or delete the lab ingest token during teardown. Historical telemetry may remain visible until Splunk retention expires; that is separate from token cleanup.

## Preload Student Namespace Secrets

After Terraform creates namespaces and kubectl points at the event cluster:

```bash
export SPLUNK_ACCESS_TOKEN='<lab-scoped-ingest-token>'
export STUDENT_COUNT=20
export STUDENT_NAMESPACE_PREFIX=student
export SECRET_NAME=splunk-observability-token

infra/scripts/preload-splunk-observability-token.sh
```

The script creates or updates a Secret in each namespace with keys:

```text
splunk_observability_access_token
SPLUNK_ACCESS_TOKEN
```

Validate without printing token values:

```bash
for ns in $(seq -f 'student-%02g' 1 20); do
  kubectl get secret splunk-observability-token -n "$ns"
done
```

## Student Collector Pattern

Students deploy the official Splunk OpenTelemetry Collector Helm chart as a namespace-local gateway:

```text
agent.enabled=false
clusterReceiver.enabled=false
gateway.enabled=true
serviceAccount.name=student
secret.create=false
secret.name=splunk-observability-token
splunkObservability.realm=<realm>
```

The gateway receives app telemetry on:

```text
OTLP gRPC: 4317
OTLP HTTP: 4318
```

The gateway later scrapes shared GPU/NIM endpoints:

```text
nvidia-dcgm-exporter.gpu-operator.svc.cluster.local:9400
nim-service.nim-system.svc.cluster.local:8000/v1/metrics
```

## Helm Chart Pin

The current student guide references:

```text
splunk-otel-collector-chart/splunk-otel-collector 0.153.0
```

For smoke tests:

```bash
helm repo add splunk-otel-collector-chart https://signalfx.github.io/splunk-otel-collector-chart
helm repo update
helm search repo splunk-otel-collector-chart/splunk-otel-collector --versions | head
```

## Smoke Test A Collector

Use a known-good sample:

```bash
export STUDENT_ID=student-01
export STUDENT_NAMESPACE=student-01
export COLLECTOR_CHART=splunk-otel-collector-chart/splunk-otel-collector

cp "infra/helm/student-collector-values-${STUDENT_ID}.yaml" student-collector-values.yaml

helm upgrade --install student-collector "$COLLECTOR_CHART" \
  --version 0.153.0 \
  --namespace "$STUDENT_NAMESPACE" \
  --values student-collector-values.yaml

kubectl rollout status deploy/student-collector -n "$STUDENT_NAMESPACE"
kubectl logs deploy/student-collector -n "$STUDENT_NAMESPACE" --tail=100
```

Collector logs should not show:

```text
401 Unauthorized
Exporting failed
permanent error
dropping data
```

## Splunk Manual Validation

After deploying `shopmate-ai` and generating a request, validate with filters:

```text
service.name=shopmate-ai
deployment.environment=student-01
k8s.cluster.name=clus-ltrobs-2001-student-01
```

After the Module 3 collector update, validate GPU/NIM metrics with:

```text
deployment.environment=student-01 job=dcgm
```

```text
deployment.environment=student-01 job=nim
```

Expected signals:

- app trace
- `shopmate.workflow` and `shopmate.agent.*` spans
- OpenAI-compatible or NIM spans where instrumentation supports them
- token metrics
- selected DCGM metrics such as `DCGM_FI_DEV_GPU_UTIL`
- NIM request, latency, or token metrics exposed by the selected NIM build

## Dashboard Expectations

This lab prioritizes:

- app traces and AI Agent Monitoring
- GPU metrics
- NIM metrics
- Kubernetes/platform telemetry where instructor collector is enabled
- tokenomics and chargeback analysis

Do not promise full Cisco AI POD dashboard parity unless the event environment has been validated against the real Splunk tenant. UCS, Nexus, storage, vector database, and other Cisco AI POD component tabs need their own telemetry sources.
