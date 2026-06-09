# Validation

Run validation at three points:

1. After Terraform apply.
2. Before class starts.
3. After class, before destroy, if you need evidence for cost or delivery notes.

## Go/No-Go Gates

The lab is ready only when all required gates pass.

| Gate | Validation |
| --- | --- |
| Terraform state is current | `terraform plan -var-file=env/<env>.tfvars` shows no unexpected drift. |
| EKS is reachable | `kubectl get nodes`. |
| GPU nodes are ready | `kubectl get nodes -l nvidia.com/gpu.present=true`. |
| GPU Operator is healthy | `kubectl get pods -n gpu-operator`. |
| DCGM endpoint is reachable | curl `nvidia-dcgm-exporter.gpu-operator.svc.cluster.local:9400/metrics` from a test namespace. |
| NIM pod is ready | `kubectl get pods -n nim-system`. |
| NIM metrics are reachable | curl `nim-service.nim-system.svc.cluster.local:8000/v1/metrics` from a test namespace. |
| Student namespaces exist | `kubectl get ns student-01 ... student-20`. |
| Splunk Secret exists | `kubectl get secret splunk-observability-token -n <student namespace>`. |
| Student RBAC works | `kubectl auth can-i create deployments -n <student namespace>`. |
| Student collector deploys | `helm upgrade --install ...` and rollout succeeds. |
| ShopMate app deploys | `kubectl rollout status deploy/shopmate-ai`. |
| ShopMate uses NIM | `/api/chat` returns `nim_enabled: true` or app health shows NIM live. |
| Traces reach Splunk | `service.name=shopmate-ai deployment.environment=student-01`. |
| GPU/NIM metrics reach Splunk | `deployment.environment=student-01 job=dcgm` and `deployment.environment=student-01 job=nim`. |
| Student docs build | `mkdocs build --strict -f mkdocs.yml`. |
| Instructor docs build | `mkdocs build --strict -f mkdocs-instructors.yml`. |

## Platform Script

Run:

```bash
infra/scripts/validate-instructor-platform.sh
```

If your event uses more or fewer than 20 students, supplement the script with:

```bash
for ns in $(terraform -chdir=infra/terraform output -json student_namespaces | jq -r '.[]'); do
  kubectl get ns "$ns"
  kubectl get secret splunk-observability-token -n "$ns"
done
```

## Manual Platform Checks

```bash
kubectl get nodes -o wide
kubectl describe nodes | grep -i -A3 nvidia || true
kubectl get pods -n gpu-operator -o wide
kubectl get svc -n gpu-operator
kubectl get pods -n nim-system -o wide
kubectl get svc -n nim-system
```

Endpoint checks:

```bash
kubectl run dcgm-test -n student-01 --rm -it --restart=Never \
  --image=curlimages/curl:8.10.1 -- \
  curl -fsS http://nvidia-dcgm-exporter.gpu-operator.svc.cluster.local:9400/metrics

kubectl run nim-test -n student-01 --rm -it --restart=Never \
  --image=curlimages/curl:8.10.1 -- \
  curl -fsS http://nim-service.nim-system.svc.cluster.local:8000/v1/metrics
```

## End-To-End Student Smoke Test

```bash
export STUDENT_ID=student-01
export STUDENT_NAMESPACE=student-01
export COLLECTOR_CHART=splunk-otel-collector-chart/splunk-otel-collector

helm upgrade --install student-collector "$COLLECTOR_CHART" \
  --version 0.153.0 \
  --namespace "$STUDENT_NAMESPACE" \
  --values "infra/helm/student-collector-values-${STUDENT_ID}.yaml"

kubectl rollout status deploy/student-collector -n "$STUDENT_NAMESPACE"
kubectl logs deploy/student-collector -n "$STUDENT_NAMESPACE" --tail=100

kubectl apply -n "$STUDENT_NAMESPACE" -f workshop/lab-files/shopmate-ai.yaml
kubectl rollout status deploy/shopmate-ai -n "$STUDENT_NAMESPACE"

kubectl run shopmate-chat -n "$STUDENT_NAMESPACE" --rm -i --restart=Never \
  --image=curlimages/curl:8.10.1 -- \
  curl -fsS http://shopmate-ai:8080/api/chat \
    -H 'Content-Type: application/json' \
    -d '{"message":"Find a waterproof hiking jacket under $200 and explain the return policy."}'
```

Collector logs should not contain:

```text
401 Unauthorized
Exporting failed
dropping data
```

App response should confirm NIM-backed behavior. If it returns local/fallback behavior, fix NIM before class.

## Splunk Evidence

Use these filters in Splunk Observability Cloud:

```text
service.name=shopmate-ai
deployment.environment=student-01
```

```text
deployment.environment=student-01 job=dcgm
```

```text
deployment.environment=student-01 job=nim
```

Confirm:

- one recent trace for the test prompt
- environment is `student-01`
- service is `shopmate-ai`
- app workflow spans are present
- NIM or OpenAI-compatible spans are present where supported
- token metrics are present
- GPU utilization and memory metrics are present
- NIM request, latency, or token metrics are present

## Documentation QA

Student docs:

```bash
mkdocs build --strict -f mkdocs.yml
```

Instructor docs:

```bash
mkdocs build --strict -f mkdocs-instructors.yml
```

Optional student walkthrough if the dev server is running:

```bash
python scripts/student_mkdocs_walkthrough.py --base-url http://127.0.0.1:8001/
```

## Go/No-Go Decision

No-go if any of these are true:

- GPU nodes are not ready.
- NIM is not reachable from student namespaces.
- The Splunk token Secret is missing from any student namespace.
- A test collector cannot export to Splunk.
- A test app request cannot produce a trace.
- The student lab files contain unresolved placeholders for the event.
- There is no assigned destroy owner and teardown time.
