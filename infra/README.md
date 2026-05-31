# CLUS-LTROBS-2001 Infrastructure

This directory contains instructor-owned infrastructure for the Cisco Live lab.
Students do not run Terraform and do not need AWS, NVIDIA, Splunk admin, or
cluster-admin access.

Current target:

- AWS EKS
- GPU worker node group using `g5.4xlarge` by default
- NVIDIA GPU Operator and DCGM metrics
- shared NVIDIA NIM endpoint
- instructor Splunk OpenTelemetry Collector for Kubernetes and platform metrics
- one namespace-scoped student collector and `shopmate-ai` app per student

## Terraform

The Terraform entry point is [`terraform/`](terraform/).

Recommended flow:

```bash
cd infra/terraform
terraform init -backend-config=backend/dev.hcl
terraform plan -var-file=env/dev.tfvars
terraform apply -var-file=env/dev.tfvars
```

The backend and variable files are intentionally examples only. Copy them to
lab-specific files outside source control before applying.

## Validation

After Terraform finishes, configure kubectl:

```bash
aws eks update-kubeconfig \
  --region <aws-region> \
  --name <cluster-name>
```

Then validate the platform:

```bash
kubectl get nodes
kubectl get pods -n gpu-operator
kubectl get svc -A | rg -i dcgm
kubectl get pods -A | rg -i nim
```

NIM deployment details still need to be locked against the selected NVIDIA NIM
chart or manifest. Until that is finalized, Terraform creates the EKS baseline,
GPU node group, optional GPU Operator release, ECR repositories, platform
namespaces, and student namespace RBAC.
