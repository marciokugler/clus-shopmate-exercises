# 1. Student Collector

## Goal

Validate the namespace-scoped Splunk OpenTelemetry Collector gateway for your student environment.

The gateway receives OTLP telemetry from the ShopMate Sports website workload and exports it to Splunk Observability Cloud. Student identity is carried by the application through `OTEL_RESOURCE_ATTRIBUTES`, so the collector can stay simple and does not need cluster-wide Kubernetes permissions.

The Kubernetes service may be named `shopmate-ai`. Treat that as the technical service name for the ShopMate Sports website.

## Why Gateway Mode

The lab uses one collector gateway per student namespace. This is intentionally different from a normal full-cluster Kubernetes collector install.

| Mode | Kubernetes shape | What it is good for | Why we use or avoid it here |
| --- | --- | --- | --- |
| Agent or node mode | DaemonSet on every node | Node, host, kubelet, container log, and per-node enrichment | Useful for platform telemetry, but too broad for student namespaces and can duplicate data if every student deploys it |
| Cluster receiver | Deployment or StatefulSet | Cluster metrics, Kubernetes objects, and events | Useful once per cluster, but not per student because it needs broader permissions and would duplicate shared cluster data |
| Gateway mode | Deployment plus ClusterIP service | Receives app OTLP telemetry, batches it, and exports to Splunk | Best fit for this lab because each namespace gets an isolated endpoint without node or cluster-wide collection |

In this workshop the gateway service name is `student-collector`, so ShopMate sends telemetry to:

```text
http://student-collector:4318
```

The full node/agent collector belongs in a shared platform or instructor namespace if the lab needs cluster-wide Kubernetes, node, or log telemetry. Student namespaces should not each run their own DaemonSet collector.

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
kubectl get pods -n "$STUDENT_NAMESPACE"
kubectl auth can-i --list -n "$STUDENT_NAMESPACE"
```

If `kubectl auth can-i --list` does not show normal namespaced permissions, stop and ask the instructor to fix your Kubernetes access.

## Step 2: Confirm The Splunk Token Secret

```bash
kubectl get secret splunk-observability-token -n "$STUDENT_NAMESPACE"
```

Expected result:

- the secret exists
- the secret has the expected Splunk token key
- you do not print the token value

Debug if the secret exists but the collector cannot export:

```bash
kubectl describe secret splunk-observability-token -n "$STUDENT_NAMESPACE"
kubectl get events -n "$STUDENT_NAMESPACE" --sort-by=.lastTimestamp
```

If collector logs show `401 "Unauthorized"`, the Kubernetes deployment is running but Splunk rejected the credential. Check that the token belongs to the same Splunk organization and realm used by the Helm values. Do not paste the token into chat, docs, or shell history.

## Step 3: Review The Lab Helm Values

We use the official Splunk OpenTelemetry Collector Helm chart and pin the chart version for repeatability.

```bash
helm repo add splunk-otel-collector-chart https://signalfx.github.io/splunk-otel-collector-chart
helm repo update splunk-otel-collector-chart
helm search repo splunk-otel-collector-chart/splunk-otel-collector --versions | head
```

Current lab pin, selected for the May 31, 2026 lab build:

```text
splunk-otel-collector-chart/splunk-otel-collector 0.153.0
```

The student values files are in the repo:

```text
infra/helm/student-collector-values-student-01.yaml
infra/helm/student-collector-values-student-02.yaml
```

The important settings are:

```yaml
fullnameOverride: student-collector
clusterName: clus-ltrobs-2001-student-01

agent:
  enabled: false

clusterReceiver:
  enabled: false

gateway:
  enabled: true
  replicaCount: 1
  config:
    processors:
      k8s_attributes: null
    service:
      pipelines:
        traces:
          processors: [memory_limiter, batch, resource/add_cluster_name]

rbac:
  create: false

serviceAccount:
  create: false
  name: student

secret:
  create: false
  name: splunk-observability-token
  validateSecret: false

splunkObservability:
  realm: us0
```

Why these settings matter:

- `agent.enabled=false` prevents a per-student DaemonSet.
- `clusterReceiver.enabled=false` prevents duplicated cluster-level metrics and events.
- `gateway.enabled=true` creates the namespace-local OTLP endpoint.
- `rbac.create=false` and `serviceAccount.name=student` keep the collector inside student namespace permissions.
- `secret.create=false` tells Helm to use the existing `splunk-observability-token` Secret.
- `k8s_attributes: null` removes a default processor that expects broader Kubernetes lookup permissions. ShopMate already sends `student.id`, `k8s.namespace.name`, `deployment.environment`, and cost labels as resource attributes.

## Step 4: Deploy Or Redeploy The Gateway

Instructor command for `student-01`:

```bash
helm upgrade --install student-collector splunk-otel-collector-chart/splunk-otel-collector \
  --version 0.153.0 \
  --namespace student-01 \
  --values infra/helm/student-collector-values-student-01.yaml
```

Instructor command for `student-02`:

```bash
helm upgrade --install student-collector splunk-otel-collector-chart/splunk-otel-collector \
  --version 0.153.0 \
  --namespace student-02 \
  --values infra/helm/student-collector-values-student-02.yaml
```

Reset only your namespace resources if you need to reinstall:

```bash
helm uninstall student-collector -n "$STUDENT_NAMESPACE"
kubectl delete -n "$STUDENT_NAMESPACE" deploy/student-collector svc/student-collector configmap/student-collector --ignore-not-found
```

Then rerun the matching Helm command.

## Step 5: Validate Kubernetes Health

```bash
helm list -n "$STUDENT_NAMESPACE"
kubectl get deploy,svc,pods -n "$STUDENT_NAMESPACE" -l app.kubernetes.io/name=splunk-otel-collector
kubectl rollout status deploy/student-collector -n "$STUDENT_NAMESPACE"
kubectl logs -n "$STUDENT_NAMESPACE" deploy/student-collector --tail=100
```

Look for:

- Helm release status is `deployed`
- `deployment/student-collector` is `1/1`
- service `student-collector` exposes OTLP HTTP `4318` and OTLP gRPC `4317`
- collector logs say the service is ready
- no repeated `401 "Unauthorized"` exporter errors

More inspection:

```bash
kubectl describe pod -n "$STUDENT_NAMESPACE" -l app.kubernetes.io/name=splunk-otel-collector
kubectl logs -n "$STUDENT_NAMESPACE" deploy/student-collector --previous --tail=100
kubectl get events -n "$STUDENT_NAMESPACE" --sort-by=.lastTimestamp
```

Common patterns:

| Symptom | What to inspect |
| --- | --- |
| `CrashLoopBackOff` | `kubectl logs --previous` for bad YAML, bad component names, or missing environment variables |
| `ImagePullBackOff` | image name, registry access, and image pull secret |
| `CreateContainerConfigError` | missing Secret or ConfigMap |
| `401 "Unauthorized"` | Splunk realm, token type, token org, and Secret key |
| no app telemetry | ShopMate `OTEL_EXPORTER_OTLP_ENDPOINT`, collector service port `4318`, and app logs |

## Step 6: Generate App Telemetry

Confirm ShopMate is pointed at the gateway:

```bash
kubectl get deploy shopmate-ai -n "$STUDENT_NAMESPACE" \
  -o jsonpath='{range .spec.template.spec.containers[0].env[*]}{.name}={.value}{"\n"}{end}' \
  | grep OTEL
```

Expected values include:

```text
OTEL_SERVICE_NAME=shopmate-ai
OTEL_EXPORTER_OTLP_ENDPOINT=http://student-collector:4318
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
OTEL_RESOURCE_ATTRIBUTES=student.id=...
```

Send a test request:

```bash
kubectl run shopmate-chat -n "$STUDENT_NAMESPACE" --rm -i --restart=Never \
  --image=curlimages/curl:8.10.1 -- \
  curl -fsS http://shopmate-ai:8080/api/chat \
    -H 'Content-Type: application/json' \
    -d '{"message":"Recommend a trail shoe and mention the price."}'
```

Then check the collector logs again:

```bash
kubectl logs -n "$STUDENT_NAMESPACE" deploy/student-collector --tail=100
```

## Step 7: Find The Collector In Splunk

In Splunk Observability Cloud:

1. Open APM or metrics search.
2. Filter by `service.name=shopmate-ai`.
3. Filter by `deployment.environment=<your student id>`.
4. Filter by `k8s.cluster.name=<your logical cluster name>`.
5. Confirm ShopMate traces and generated metrics appear.

!!! success "Checkpoint"
    Your gateway collector pod is running, has a service, receives ShopMate telemetry, and can export data tagged with your student identity.

## Knowledge Check

??? question "Why are we using gateway mode instead of a node collector?"
    Gateway mode gives each student namespace a stable OTLP endpoint without requiring DaemonSet, kubelet, host filesystem, or cluster-wide permissions.

??? question "Where does student identity come from?"
    ShopMate sends identity through `OTEL_RESOURCE_ATTRIBUTES`. The gateway keeps the telemetry path simple and exports those resource attributes to Splunk.

??? question "What does `401 Unauthorized` in collector logs mean?"
    The collector reached Splunk, but Splunk rejected the credential. Check token type, token organization, token realm, and whether the Secret contains the expected key.

## Sources

- Splunk documents Helm-based Kubernetes collector configuration, including EKS options and using a gateway endpoint for instrumented applications: [Configure with Helm](https://help.splunk.com/en?resourceId=gdi_opentelemetry_collector-kubernetes_kubernetes-config).
- Splunk documents agent, cluster receiver, and gateway customization through `agent.config`, `clusterReceiver.config`, and `gateway.config`: [Advanced configuration](https://help.splunk.com/en/splunk-observability-cloud/manage-data/splunk-distribution-of-the-opentelemetry-collector/get-started-with-the-splunk-distribution-of-the-opentelemetry-collector/collector-for-kubernetes/advanced-configuration).
- Splunk explains collector deployment modes and gateway forwarding behavior: [Deployment modes](https://help.splunk.com/en?resourceId=gdi_opentelemetry_deployment-modes).
- The lab uses the official Splunk Helm chart and release stream: [Splunk OpenTelemetry Collector Helm chart](https://github.com/signalfx/splunk-otel-collector-chart) and [chart releases](https://github.com/signalfx/splunk-otel-collector-chart/releases).
- OpenTelemetry documents collector troubleshooting patterns used when checking pipelines and collector health: [OpenTelemetry Collector troubleshooting](https://opentelemetry.io/docs/collector/troubleshooting/).
