# Prerequisites

Complete this page before creating or changing cloud resources.

## Required Local Tools

Install these on the instructor workstation or admin jump host:

```bash
aws --version
terraform version
kubectl version --client
helm version
jq --version
docker version
```

Minimum expectations:

| Tool | Use |
| --- | --- |
| AWS CLI | AWS auth, EKS kubeconfig, ECR login, resource validation. |
| Terraform `>=1.6` | Infrastructure lifecycle. |
| kubectl | Cluster validation, Kubernetes manifests, reset support. |
| Helm | GPU Operator through Terraform provider and student collector smoke tests. |
| jq | Terraform output parsing and validation scripts. |
| Docker | Build and publish `shopmate-ai` image if the image is not already published. |

## AWS Account

Confirm the AWS account can create and destroy:

- VPC, subnets, route tables, internet gateway, NAT gateway, and Elastic IP
- EKS cluster
- managed node group
- GPU EC2 instances, `g5.4xlarge` by default
- IAM roles and policies for EKS and nodes
- EKS add-ons
- EBS volumes
- ECR repositories
- load balancers created by Kubernetes workloads, if any are added later

Pre-check:

```bash
aws sts get-caller-identity
aws configure get region
```

Confirm GPU quota in the selected region before applying Terraform. The default pilot shape uses:

```text
gpu_instance_type = g5.4xlarge
gpu_desired_size  = 2
gpu_max_size      = 2
```

For a 20-student lab, this is one shared GPU pool, not one GPU instance per student.

## Terraform State

Use remote state for dry runs and event builds.

Required external state resources:

- S3 bucket for state
- DynamoDB table for state locking
- restricted instructor/operator access

The example backend file lives at:

```text
infra/terraform/backend/dev.hcl.example
```

Do not commit real backend files with account-specific bucket names if they are considered sensitive in your environment.

## Splunk Observability

Prepare:

- Splunk Observability Cloud org
- Splunk realm, for example `us0`, `us1`, or `eu0`
- instructor user
- student users or approved shared lab login
- lab-scoped ingest token
- plan to rotate or delete the token after class

!!! warning "Token handling"
    Prefer preloading the ingest token into Kubernetes Secrets. Do not ask students to paste the raw ingest token into values files or screenshots.

Student-facing values:

```text
SPLUNK_OBSERVABILITY_URL=<provided by instructor>
SPLUNK_REALM=<realm>
SPLUNK_ACCESS_TOKEN_SECRET=splunk-observability-token
```

## NVIDIA NGC And NIM

Prepare:

- NVIDIA account with access to the selected NIM image
- accepted terms for the model
- NGC API key
- image pull Secret material
- NIM runtime/auth Secret material

The checked-in NIM manifest expects these Kubernetes Secrets in `nim-system`:

```text
ngc-secret
ngc-api-secret
```

The checked-in model shape is:

```text
image: nvcr.io/nim/meta/llama-3.2-1b-instruct:1.12.0
model: meta/llama-3.2-1b-instruct
port: 8000
metrics path: /v1/metrics
```

Use an approved replacement model only after updating the NIM manifest, app environment, student guide, and validation checks.

## Container Registry

Terraform creates ECR repositories by default:

```text
clus-ltrobs-2001/shopmate-ai
clus-ltrobs-2001/loadgen
```

The cluster nodes have read-only ECR permissions through the managed node role. If you use a registry outside ECR, create and distribute the required image pull Secret.

## Student Roster

Create the roster before building handouts.

Required columns:

```csv
student_number,student_id,namespace,team,department,cost_center,chargeback_account,k8s_cluster_name,deployment_environment,splunk_user,app_url
1,student-01,student-01,team-a,marketing,cc-4100,cb-student-01,clus-ltrobs-2001-student-01,student-01,student01@example.com,http://127.0.0.1:8080
```

Default namespace identity pattern:

```text
student.id=student-01
namespace=student-01
deployment.environment=student-01
k8s.cluster.name=clus-ltrobs-2001-student-01
chargeback.account=cb-student-01
```

## Pre-Flight Checklist

Do not run `terraform apply` until these are true:

- AWS identity and target region are confirmed.
- GPU quota is approved for the selected instance type and node count.
- Terraform remote state bucket and lock table exist.
- Splunk realm and lab ingest token strategy are approved.
- NGC API key and model entitlement are confirmed.
- The app image registry path is selected.
- Student count is known.
- Environment name is selected, for example `dev`, `dry-run`, or `event`.
- Destroy owner and teardown time are assigned.
