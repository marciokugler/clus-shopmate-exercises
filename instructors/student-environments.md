# Student Environments

Students get isolated namespaces inside the shared EKS cluster. They do not get AWS, NVIDIA, registry, cluster-admin, or raw Splunk ingest token access.

## Namespace Baseline

Terraform creates student namespaces from:

```hcl
student_count = 20
student_namespace_prefix = "student"
```

Result:

```text
student-01
student-02
...
student-20
```

Each namespace gets:

- namespace labels
- service account `student`
- Role `student-workshop`
- RoleBinding `student-workshop`

The namespace Role allows normal namespaced work:

- get/list/watch/create/update/patch/delete configmaps, pods, secrets, services
- get/list/watch endpoints and endpoint slices
- get/list/watch/create/update/patch/delete deployments and replicasets
- get/list/watch/create/update/patch/delete jobs
- create pod port-forwards

It does not grant cluster-admin, node, DaemonSet, ClusterRole, node group, NIM, GPU Operator, or cross-namespace control.

## Validate Namespaces

```bash
for ns in $(seq -f 'student-%02g' 1 20); do
  kubectl get ns "$ns"
  kubectl get serviceaccount student -n "$ns"
  kubectl auth can-i create deployments \
    --as="system:serviceaccount:${ns}:student" \
    -n "$ns"
done
```

## Preload Splunk Secret

Run the token preload script from [Splunk Setup](splunk.md#preload-student-namespace-secrets), then validate:

```bash
for ns in $(seq -f 'student-%02g' 1 20); do
  kubectl get secret splunk-observability-token -n "$ns"
done
```

## Student Lab Files

The student site serves:

```text
workshop/lab-files/student-kubeconfig.yaml
workshop/lab-files/shopmate-ai.yaml
workshop/lab-files/collector-observability-snippet.yaml
workshop/lab-files/student-collector-values-gpu-nim-reference.yaml
```

Before publishing, confirm none of the files contain stale event credentials or placeholders that block the lab.

!!! warning "Kubeconfig sensitivity"
    The current repo contains a concrete `student-kubeconfig.yaml` lab artifact. Treat generated kubeconfigs and service account tokens as secrets. Rotate or delete them after class, and do not reuse old event kubeconfigs.

## Kubeconfig Distribution

Use one approved method:

| Method | When to use |
| --- | --- |
| One shared namespace-scoped service account with context per namespace | Fast classroom delivery. Validate carefully and rotate after class. |
| One service account token per student | Better isolation. More generation and distribution work. |
| Portal or claim system | Useful for large events. Keep generated artifacts out of git. |

Student contexts should be named:

```text
student-01
student-02
...
```

The current context namespace must match the assigned namespace.

## Student Handout Values

Each student needs:

```text
STUDENT_ID=student-01
STUDENT_NAMESPACE=student-01
SPLUNK_REALM=<realm>
SPLUNK_ACCESS_TOKEN_SECRET=splunk-observability-token
LOGICAL_CLUSTER_NAME=clus-ltrobs-2001-student-01
COLLECTOR_CHART=splunk-otel-collector-chart/splunk-otel-collector
Splunk URL=<org-url>
```

Optional persona values:

```text
team.name=team-a
department.name=marketing
department.cost_center=cc-4100
chargeback.account=cb-student-01
```

## Student Readiness Smoke Test

Run this before publishing the lab URL:

```bash
export STUDENT_ID=student-01
export STUDENT_NAMESPACE=student-01

kubectl get pods -n "$STUDENT_NAMESPACE"
kubectl auth can-i get pods -n "$STUDENT_NAMESPACE"
kubectl auth can-i create deployments -n "$STUDENT_NAMESPACE"
kubectl auth can-i create services -n "$STUDENT_NAMESPACE"
kubectl get secret splunk-observability-token -n "$STUDENT_NAMESPACE"
```

Deploy one collector:

```bash
helm repo add splunk-otel-collector-chart https://signalfx.github.io/splunk-otel-collector-chart
helm repo update

helm upgrade --install student-collector splunk-otel-collector-chart/splunk-otel-collector \
  --version 0.153.0 \
  --namespace "$STUDENT_NAMESPACE" \
  --values "infra/helm/student-collector-values-${STUDENT_ID}.yaml"

kubectl rollout status deploy/student-collector -n "$STUDENT_NAMESPACE"
```

Deploy one app:

```bash
kubectl apply -n "$STUDENT_NAMESPACE" -f workshop/lab-files/shopmate-ai.yaml
kubectl rollout status deploy/shopmate-ai -n "$STUDENT_NAMESPACE"
```

Generate one request:

```bash
kubectl run shopmate-chat -n "$STUDENT_NAMESPACE" --rm -i --restart=Never \
  --image=curlimages/curl:8.10.1 -- \
  curl -fsS http://shopmate-ai:8080/api/chat \
    -H 'Content-Type: application/json' \
    -d '{"message":"Find a waterproof hiking jacket under $200 and explain the return policy."}'
```

Then validate Splunk evidence as described in [Validation](validation.md).

## Clean Student Start

Before class, student namespaces should not contain old runtime resources:

```bash
kubectl get deploy,svc,pod,job,ingress,pvc -A --ignore-not-found | grep '^student-' || true
```

Clean a namespace:

```bash
export STUDENT_NAMESPACE=student-01

helm uninstall student-collector -n "$STUDENT_NAMESPACE" || true
kubectl delete -n "$STUDENT_NAMESPACE" \
  deploy/shopmate-ai svc/shopmate-ai \
  deploy/student-collector svc/student-collector \
  configmap/student-collector-otel-collector \
  job --all \
  --ignore-not-found
kubectl delete pvc -n "$STUDENT_NAMESPACE" --all --ignore-not-found
```

Do not delete the preloaded `splunk-observability-token` Secret unless rotating tokens.
