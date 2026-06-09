# Day-Of Operations

Use this page during class to keep the environment stable without giving students broad permissions.

## Before Opening The Room

Run:

```bash
kubectl config current-context
kubectl get nodes
kubectl get pods -n gpu-operator
kubectl get pods -n nim-system

for ns in $(seq -f 'student-%02g' 1 20); do
  kubectl get secret splunk-observability-token -n "$ns"
done
```

Confirm:

- student docs URL works
- Splunk login works
- student handout values are ready
- support instructors know the namespace roster
- destroy owner and time are assigned

## Support Model

Students should be able to fix:

- their collector values file
- their Helm release
- their app deployment settings
- their port-forward command
- their Splunk filters

Instructor fixes:

- missing namespace
- missing Splunk Secret
- NIM outage
- GPU Operator/DCGM outage
- image pull failures caused by registry or manifest drift
- broken kubeconfig or RBAC
- Splunk token or realm errors

## Quick Namespace Triage

```bash
export STUDENT_NAMESPACE=student-07

kubectl get all -n "$STUDENT_NAMESPACE"
kubectl get secret splunk-observability-token -n "$STUDENT_NAMESPACE"
kubectl logs deploy/student-collector -n "$STUDENT_NAMESPACE" --tail=100
kubectl logs deploy/shopmate-ai -n "$STUDENT_NAMESPACE" --tail=100
kubectl describe pod -n "$STUDENT_NAMESPACE" -l app=shopmate-ai
```

## Soft Reset

Use when pods are wedged but config should remain.

```bash
export STUDENT_NAMESPACE=student-07

kubectl rollout restart deploy/student-collector -n "$STUDENT_NAMESPACE" || true
kubectl rollout restart deploy/shopmate-ai -n "$STUDENT_NAMESPACE" || true
kubectl rollout status deploy/student-collector -n "$STUDENT_NAMESPACE" || true
kubectl rollout status deploy/shopmate-ai -n "$STUDENT_NAMESPACE" || true
```

## Clean Reset

Use when a namespace should return to the start of the student exercise. This removes app and collector runtime objects but keeps namespace, RBAC, and preloaded token Secret.

```bash
export STUDENT_NAMESPACE=student-07

helm uninstall student-collector -n "$STUDENT_NAMESPACE" || true

kubectl delete -n "$STUDENT_NAMESPACE" \
  deploy/shopmate-ai svc/shopmate-ai \
  deploy/student-collector svc/student-collector \
  configmap/student-collector-otel-collector \
  --ignore-not-found

kubectl delete job -n "$STUDENT_NAMESPACE" --all --ignore-not-found
kubectl delete ingress -n "$STUDENT_NAMESPACE" --all --ignore-not-found
kubectl delete pvc -n "$STUDENT_NAMESPACE" --all --ignore-not-found

kubectl get all -n "$STUDENT_NAMESPACE"
kubectl get secret splunk-observability-token -n "$STUDENT_NAMESPACE"
```

## Reapply App For A Student

```bash
export STUDENT_NAMESPACE=student-07

kubectl apply -n "$STUDENT_NAMESPACE" -f workshop/lab-files/shopmate-ai.yaml
kubectl rollout status deploy/shopmate-ai -n "$STUDENT_NAMESPACE"
```

If the checked-in manifest has fixed `student-01` labels or environment values, use it only as a baseline and patch the namespace-specific values before relying on Splunk filters.

## Recreate Splunk Secret In One Namespace

```bash
export STUDENT_NAMESPACE=student-07
export SPLUNK_ACCESS_TOKEN='<lab-scoped-ingest-token>'

kubectl create secret generic splunk-observability-token \
  --namespace "$STUDENT_NAMESPACE" \
  --from-literal="splunk_observability_access_token=$SPLUNK_ACCESS_TOKEN" \
  --from-literal="SPLUNK_ACCESS_TOKEN=$SPLUNK_ACCESS_TOKEN" \
  --dry-run=client \
  --output yaml \
  | kubectl apply --namespace "$STUDENT_NAMESPACE" --filename -
```

Do not print or paste the token value.

## Platform Health During Class

```bash
kubectl get nodes
kubectl top nodes || true
kubectl get pods -n gpu-operator
kubectl get pods -n nim-system
kubectl logs -n nim-system deploy/nim-service --tail=100 || true
kubectl get events -A --sort-by=.lastTimestamp | tail -50
```

If NIM fails, the app may still serve non-NIM fallback behavior, but the GPU/NIM observability learning objective is degraded. Decide quickly whether to pause, demo from known data, or continue with app telemetry only.

## After Class Before Destroy

Capture useful evidence:

```bash
kubectl get nodes -o wide
kubectl get pods -A
kubectl get svc -A
terraform -chdir=infra/terraform output
```

In Splunk, note:

- trace filters that worked
- GPU/NIM metric filters that worked
- any dashboard caveats
- any token or NIM errors

Then follow [Destroy](destroy.md).
