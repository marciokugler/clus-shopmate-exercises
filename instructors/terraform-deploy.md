# Terraform Deploy

Terraform is the supported lifecycle tool for the AWS lab stack. Do not hand-create EKS, GPU node groups, or core lab networking outside Terraform unless you also document the external dependency and cleanup path.

## Prepare The Stack

From the repo root:

```bash
cd infra/terraform
cp backend/dev.hcl.example backend/dev.hcl
cp env/dev.tfvars.example env/dev.tfvars
```

Edit `backend/dev.hcl`:

```hcl
bucket         = "REPLACE_WITH_TERRAFORM_STATE_BUCKET"
key            = "clus-ltrobs-2001/dev/terraform.tfstate"
region         = "us-east-2"
dynamodb_table = "REPLACE_WITH_TERRAFORM_LOCK_TABLE"
encrypt        = true
```

Edit `env/dev.tfvars` for the target lab:

```hcl
aws_region  = "us-east-2"
environment = "dev"
owner       = "lab-team"
expires_at  = "2026-06-30T23:59:59Z"

student_count = 20

gpu_instance_type     = "g5.4xlarge"
gpu_desired_size      = 2
gpu_min_size          = 0
gpu_max_size          = 2
gpu_node_disk_size_gb = 200

install_gpu_operator  = true
enable_ebs_csi_driver = true

tags = {
  CostCenter = "clus-ltrobs-2001"
}
```

For the event environment, use a separate tfvars file and state key, for example:

```text
backend/event.hcl
env/event.tfvars
key = "clus-ltrobs-2001/event/terraform.tfstate"
environment = "event"
```

## Important Variables

| Variable | Default | Instructor decision |
| --- | --- | --- |
| `aws_region` | `us-east-2` | Must match quota, backend, and event plan. |
| `environment` | `dev` | Use `dry-run` and `event` for real deliveries. |
| `cluster_name` | empty | Empty becomes `clus-ltrobs-2001-<environment>`. |
| `student_count` | `20` | Supports `1` to `60`. |
| `gpu_instance_type` | `g5.4xlarge` | Confirm quota and model fit. |
| `gpu_node_ami_type` | `AL2023_x86_64_NVIDIA` | Keeps NVIDIA driver/runtime on the node AMI. |
| `gpu_desired_size` | `2` | Event capacity setting. |
| `gpu_min_size` | `0` | Allows scale-down after class if not destroying immediately. |
| `gpu_max_size` | `2` | Must be at least desired size. |
| `gpu_node_taint_enabled` | `false` | Turn on only if all GPU workloads tolerate/schedule correctly. |
| `install_gpu_operator` | `true` | Installs GPU Operator values from `infra/k8s/gpu-operator-values.yaml`. |
| `enable_ebs_csi_driver` | `true` | Needed for NIM cache PVCs. |

## Initialize

Remote state:

```bash
terraform init -backend-config=backend/dev.hcl
```

Local validation only:

```bash
terraform init -backend=false
```

## Plan

```bash
terraform validate
terraform plan -var-file=env/dev.tfvars
```

Review the plan for:

- expected VPC and subnet CIDRs
- expected EKS cluster name
- one GPU node group
- desired and maximum GPU node count
- ECR repositories
- platform namespaces
- generated student namespaces
- no accidental environment name or region mismatch

## Apply

```bash
terraform apply -var-file=env/dev.tfvars
```

Save outputs:

```bash
terraform output
terraform output -raw cluster_name
terraform output -raw aws_region
terraform output -json student_namespaces | jq -r '.[]'
terraform output -json ecr_repository_urls | jq
```

## Configure kubectl

Use the output command or run:

```bash
aws eks update-kubeconfig \
  --region "$(terraform output -raw aws_region)" \
  --name "$(terraform output -raw cluster_name)"
```

Verify:

```bash
kubectl config current-context
kubectl get nodes -o wide
kubectl get ns gpu-operator nim-system observability
kubectl get ns student-01 student-02
```

## First Health Check

Run:

```bash
kubectl get nodes -o wide
kubectl get pods -A
kubectl get pods -n gpu-operator
kubectl get svc -A | grep -i dcgm || true
```

Expected:

- EKS control plane is reachable.
- GPU nodes join and become `Ready`.
- `gpu-operator`, `nim-system`, `observability`, and student namespaces exist.
- GPU Operator pods converge if `install_gpu_operator=true`.
- DCGM exporter service appears after GPU Operator is healthy.

## Publishing ShopMate Image

After Terraform creates ECR repositories:

```bash
cd ../..

export AWS_REGION="$(terraform -chdir=infra/terraform output -raw aws_region)"
export SHOPMATE_REPO="$(terraform -chdir=infra/terraform output -json ecr_repository_urls | jq -r '.["shopmate-ai"]')"
export SHOPMATE_IMAGE="${SHOPMATE_REPO}:lab-stable"
export ECR_REGISTRY="$(printf "%s\n" "$SHOPMATE_REPO" | cut -d/ -f1)"

aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$ECR_REGISTRY"

docker build --platform linux/amd64 -t "$SHOPMATE_IMAGE" shopmate-sports
docker push "$SHOPMATE_IMAGE"
```

If the image URI differs from the checked-in manifest, update the image field in:

```text
infra/k8s/shopmate-ai.yaml
workshop/lab-files/shopmate-ai.yaml
```

## Scale Down Instead Of Destroying

For a short pause between dry runs, you can set:

```hcl
gpu_desired_size = 0
gpu_min_size     = 0
gpu_max_size     = 0
```

Then run:

```bash
terraform plan -var-file=env/dev.tfvars
terraform apply -var-file=env/dev.tfvars
```

Use full destroy when the environment is no longer needed. Scaling to zero is not a substitute for destroy validation.
