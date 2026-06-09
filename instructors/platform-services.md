# Platform Services

After Terraform creates the EKS baseline, validate or install the instructor-owned Kubernetes services that make the lab usable.

## Platform Namespaces

Terraform creates:

```text
gpu-operator
nim-system
observability
student-01 ... student-N
```

Check:

```bash
kubectl get ns gpu-operator nim-system observability
terraform -chdir=infra/terraform output -json student_namespaces | jq -r '.[]' \
  | xargs kubectl get ns
```

## NVIDIA GPU Operator And DCGM

Terraform installs the GPU Operator when:

```hcl
install_gpu_operator = true
```

Values file:

```text
infra/k8s/gpu-operator-values.yaml
```

The lab uses an EKS NVIDIA accelerated AMI, so the values intentionally disable operator-managed driver and toolkit installation:

```yaml
toolkit:
  enabled: false

driver:
  enabled: false

dcgmExporter:
  enabled: true
```

Validate:

```bash
kubectl get pods -n gpu-operator -o wide
kubectl get svc -n gpu-operator
kubectl get svc -A | grep -i dcgm
```

Expected student scrape endpoint:

```text
nvidia-dcgm-exporter.gpu-operator.svc.cluster.local:9400
```

From a test namespace:

```bash
kubectl run dcgm-test -n student-01 --rm -it --restart=Never \
  --image=curlimages/curl:8.10.1 -- \
  curl -fsS http://nvidia-dcgm-exporter.gpu-operator.svc.cluster.local:9400/metrics
```

## NVIDIA NIM

The current checked-in NIM manifest is:

```text
infra/k8s/nim-llama-3.2-1b.yaml
```

It defines:

- `NIMCache` named `meta-llama-3-2-1b-instruct`
- `NIMService` named `nim-service`
- namespace `nim-system`
- internal ClusterIP service on port `8000`
- `nvidia.com/gpu: 1`
- NIM image `nvcr.io/nim/meta/llama-3.2-1b-instruct:1.12.0`

Before applying the manifest, create the required NGC/NIM Secrets in `nim-system`.

!!! warning "Secret material"
    Do not commit real NGC API keys, NIM runtime secrets, or generated pull secrets. Store them in the event secret manager or create them at deployment time.

The exact Secret creation command depends on the final NGC credential format. At minimum, confirm these names exist before applying NIM:

```bash
kubectl get secret ngc-secret -n nim-system
kubectl get secret ngc-api-secret -n nim-system
```

Apply NIM after the operator CRDs are available:

```bash
kubectl apply -f infra/k8s/nim-llama-3.2-1b.yaml
kubectl get nimcache,nimservice -n nim-system
kubectl get pods -n nim-system -o wide
kubectl get svc -n nim-system
```

Validate the metrics endpoint:

```bash
kubectl run nim-metrics-test -n student-01 --rm -it --restart=Never \
  --image=curlimages/curl:8.10.1 -- \
  curl -fsS http://nim-service.nim-system.svc.cluster.local:8000/v1/metrics
```

Expected student scrape endpoint:

```text
nim-service.nim-system.svc.cluster.local:8000
```

Expected app base URL:

```text
http://nim-service.nim-system.svc.cluster.local:8000/v1
```

## ShopMate App Image

The student manifest expects a published app image:

```text
infra/k8s/shopmate-ai.yaml
workshop/lab-files/shopmate-ai.yaml
```

Build and push with the flow in [Terraform Deploy](terraform-deploy.md#publishing-shopmate-image).

Verify EKS can pull the image:

```bash
export STUDENT_NAMESPACE=student-01
kubectl apply -n "$STUDENT_NAMESPACE" -f workshop/lab-files/shopmate-ai.yaml
kubectl rollout status deploy/shopmate-ai -n "$STUDENT_NAMESPACE"
kubectl logs deploy/shopmate-ai -n "$STUDENT_NAMESPACE" --tail=50
```

The app should receive these important values:

```text
NIM_BASE_URL=http://nim-service.nim-system.svc.cluster.local:8000/v1
NIM_API_KEY=nim-local-key
NIM_MODEL=meta/llama-3.2-1b-instruct
OTEL_SERVICE_NAME=shopmate-ai
OTEL_EXPORTER_OTLP_ENDPOINT=http://student-collector:4318
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
OTEL_INSTRUMENTATION_GENAI_EMITTERS=span_metric
OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=SPAN_ONLY
OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE=delta
```

## Instructor Collector

The repo currently documents the instructor collector as part of the target architecture, but the checked-in Kubernetes artifacts focus on the student collector path and shared GPU/NIM endpoints.

If the event requires authoritative Kubernetes/platform telemetry, deploy the instructor collector in `observability` with:

- cluster receiver enabled once per cluster
- Kubernetes/node telemetry enabled once per cluster
- DCGM/NIM metrics scraped once as the platform baseline
- lab-scoped Splunk token stored only in instructor-owned namespace Secret

Do not ask students to deploy:

- DaemonSet collectors
- cluster receiver
- broad Kubernetes metrics collection
- cluster-wide RBAC

## Platform Validation Script

Run:

```bash
infra/scripts/validate-instructor-platform.sh
```

The current script checks:

- nodes
- GPU Operator pods
- DCGM service
- NIM pods
- `student-01` namespace
- sample student service account permissions
- shared student kubeconfig-style service account permissions for the first 20 namespaces

If your `student_count` is not 20, adjust the loop or validate namespaces manually.
