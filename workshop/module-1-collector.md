# 1. Student Collector

## Goal

Deploy or validate your namespace-scoped OpenTelemetry Collector.

Your collector receives telemetry from the ShopMate Sports website workload, adds your student identity, scrapes selected GPU/NIM metrics, and exports to Splunk Observability Cloud.

The Kubernetes service may be named `shopmate-ai`. Treat that as the technical service name for the ShopMate Sports website.

## Why This Matters

In production, telemetry quality depends on the collector path. If identity, batching, receivers, or exporters are wrong, traces and metrics become hard to trust.

In this lab, your collector is intentionally namespace-scoped. It gives you a real collector exercise without requiring cluster-wide permissions.

## Step 1: Confirm Your Namespace

```bash
kubectl get pods -n "$STUDENT_NAMESPACE"
kubectl auth can-i get pods -n "$STUDENT_NAMESPACE"
kubectl auth can-i create deployments -n "$STUDENT_NAMESPACE"
kubectl auth can-i create services -n "$STUDENT_NAMESPACE"
```

Expected result:

- commands succeed for your namespace
- you do not need cluster-admin permissions

Debug if this fails:

```bash
kubectl config current-context
kubectl get namespace "$STUDENT_NAMESPACE"
kubectl auth can-i --list -n "$STUDENT_NAMESPACE"
```

If `kubectl auth can-i --list` does not show normal namespaced permissions, stop and ask the instructor to fix your Kubernetes access.

## Step 2: Confirm The Splunk Token Secret

```bash
kubectl get secret "$SPLUNK_ACCESS_TOKEN_SECRET" -n "$STUDENT_NAMESPACE"
```

Expected result:

- the secret exists

If it is missing, ask for the lab token Secret to be provisioned. Do not paste an ingest token into your terminal history unless the lab explicitly tells you to.

Debug if the secret exists but the collector cannot use it:

```bash
kubectl describe secret "$SPLUNK_ACCESS_TOKEN_SECRET" -n "$STUDENT_NAMESPACE"
kubectl get events -n "$STUDENT_NAMESPACE" --sort-by=.lastTimestamp
```

You should only verify that the expected key exists. Do not print the token value.

## Step 3: Review Collector Identity

Your collector should attach these resource attributes:

```yaml
resource:
  attributes:
    - key: student.id
      value: ${STUDENT_ID}
      action: upsert
    - key: team.name
      value: ${TEAM_NAME}
      action: upsert
    - key: department.name
      value: ${DEPARTMENT_NAME}
      action: upsert
    - key: department.cost_center
      value: ${DEPARTMENT_COST_CENTER}
      action: upsert
    - key: chargeback.account
      value: ${CHARGEBACK_ACCOUNT}
      action: upsert
    - key: deployment.environment
      value: ${STUDENT_ID}
      action: upsert
    - key: k8s.cluster.name
      value: ${LOGICAL_CLUSTER_NAME}
      action: upsert
```

These attributes let you filter your data inside a shared Splunk tenant.

| Attribute | Why it matters | Splunk UI mapping |
| --- | --- | --- |
| `student.id` | Unique participant identity | Filter traces and metrics to your work |
| `team.name` | Group identity | Compare team-level behavior |
| `department.name` | Business owner | Tokenomics and chargeback grouping |
| `department.cost_center` | Financial owner | Cost center grouping |
| `chargeback.account` | Billing label | Verify spend attribution |
| `deployment.environment` | Logical lab environment | APM environment filter and related content |
| `k8s.cluster.name` | Logical student cluster name | Separates duplicated shared GPU/NIM scrapes |
| `k8s.namespace.name` | Kubernetes namespace | Correlates app telemetry with shared Kubernetes metrics |

Reference:

- Splunk Collector troubleshooting covers missing data, receiver pipeline issues, exporter failures, and credential problems: [Troubleshoot the Splunk OpenTelemetry Collector](https://help.splunk.com/en?resourceId=gdi_opentelemetry_splunk-collector-troubleshooting).
- OpenTelemetry Collector troubleshooting describes internal telemetry, zPages, and Kubernetes debugging patterns: [OpenTelemetry Collector troubleshooting](https://opentelemetry.io/docs/collector/troubleshooting/).
- Splunk publishes the Kubernetes Helm chart and collector source on GitHub: [Splunk OpenTelemetry Collector Helm chart](https://github.com/signalfx/splunk-otel-collector-chart) and [Splunk OpenTelemetry Collector](https://github.com/signalfx/splunk-otel-collector).

## Step 4: Update The Collector Config File

Open the collector config file provided by the lab. It is usually one of these:

- `student-collector-values.yaml` if you deploy with Helm
- `student-collector.yaml` if you deploy a rendered manifest

Make sure the config has the complete path from app to Splunk:

| Config section | Required outcome |
| --- | --- |
| `receivers.otlp` | Listens for app telemetry on `4317` and `4318` |
| `processors.resource/student` | Adds your student, namespace, department, environment, and chargeback attributes |
| `exporters.signalfx` | Uses the lab Splunk realm and access token |
| `service.pipelines.traces` | Receives app traces, adds attributes, batches, and exports |
| `service.pipelines.metrics` | Receives app metrics, adds attributes, batches, and exports |

Use this minimal shape when checking your file:

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  resource/student:
    attributes:
      - key: student.id
        value: ${env:STUDENT_ID}
        action: upsert
      - key: team.name
        value: ${env:TEAM_NAME}
        action: upsert
      - key: department.name
        value: ${env:DEPARTMENT_NAME}
        action: upsert
      - key: department.cost_center
        value: ${env:DEPARTMENT_COST_CENTER}
        action: upsert
      - key: chargeback.account
        value: ${env:CHARGEBACK_ACCOUNT}
        action: upsert
      - key: deployment.environment
        value: ${env:STUDENT_ID}
        action: upsert
      - key: k8s.namespace.name
        value: ${env:POD_NAMESPACE}
        action: upsert
      - key: k8s.cluster.name
        value: ${env:LOGICAL_CLUSTER_NAME}
        action: upsert
  batch: {}

exporters:
  signalfx:
    realm: ${env:SPLUNK_REALM}
    access_token: ${env:SPLUNK_ACCESS_TOKEN}

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [resource/student, batch]
      exporters: [signalfx]
    metrics:
      receivers: [otlp]
      processors: [resource/student, batch]
      exporters: [signalfx]
```

If your lab file already includes `memory_limiter`, health checks, or additional Splunk chart settings, keep them. The point of this step is to verify that the receiver, resource attributes, exporter, and pipelines are connected.

## Step 5: Deploy Or Redeploy The Collector

If the lab provides a Helm values file:

```bash
helm upgrade --install student-collector "$COLLECTOR_CHART" \
  --namespace "$STUDENT_NAMESPACE" \
  --values student-collector-values.yaml
```

If the lab provides a rendered manifest:

```bash
kubectl apply -n "$STUDENT_NAMESPACE" -f student-collector.yaml
```

Reset this step:

```bash
helm uninstall student-collector -n "$STUDENT_NAMESPACE"
kubectl delete -n "$STUDENT_NAMESPACE" deploy/student-collector svc/student-collector configmap/student-collector --ignore-not-found
```

Then rerun the Helm install or `kubectl apply` command. Use reset only for resources in your own namespace.

## Step 6: Validate Collector Health

```bash
kubectl get pods -n "$STUDENT_NAMESPACE" -l app.kubernetes.io/name=student-collector
kubectl get svc -n "$STUDENT_NAMESPACE" student-collector
kubectl logs -n "$STUDENT_NAMESPACE" deploy/student-collector --tail=100
```

Look for:

- OTLP HTTP receiver on `4318`
- OTLP gRPC receiver on `4317`
- Splunk exporter initialized
- no authentication errors
- no repeated scrape failures

More inspection:

```bash
kubectl describe pod -n "$STUDENT_NAMESPACE" -l app.kubernetes.io/name=student-collector
kubectl logs -n "$STUDENT_NAMESPACE" deploy/student-collector --previous --tail=100
kubectl get events -n "$STUDENT_NAMESPACE" --sort-by=.lastTimestamp
```

Common patterns:

| Symptom | What to inspect |
| --- | --- |
| `CrashLoopBackOff` | `kubectl logs --previous` for bad YAML, bad component names, or missing environment variables |
| `ImagePullBackOff` | image name, registry access, and image pull secret |
| `CreateContainerConfigError` | missing Secret or ConfigMap |
| no export to Splunk | Splunk realm, token Secret, exporter logs, and outbound network access |

## Step 7: Find The Collector In Splunk

In Splunk Observability Cloud:

1. Open metrics or APM search.
2. Filter by `deployment.environment=<your student id>`.
3. Filter by `k8s.cluster.name=<your logical cluster name>`.
4. Confirm collector telemetry exists.

!!! success "Checkpoint"
    Your collector pod is running, has a service, and can export telemetry tagged with your student identity.

## Knowledge Check

??? question "Why should your collector add `student.id` and `department.name`?"
    Because all students share the same Splunk environment. These attributes make filtering, dashboard grouping, and chargeback possible.

??? question "Why is your collector not a DaemonSet?"
    You only need namespace app telemetry and selected GPU/NIM scrapes. A DaemonSet would duplicate cluster-wide collection and require broader permissions.

## Troubleshooting

If the collector does not start or export, use the [troubleshooting appendix](appendix-troubleshooting.md#collector-issues).
