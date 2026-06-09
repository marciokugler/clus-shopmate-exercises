# Destroy

Destroy is instructor-only. The goal is not just to run `terraform destroy`; the goal is to prove that no lab-owned GPU, EKS, NAT, load balancer, EBS, registry, or token exposure remains.

!!! danger "Do not skip this"
    GPU instances, NAT gateways, Elastic IPs, EBS volumes, and load balancers can continue costing money after class. Terraform destroy plus AWS validation is required.

## Destroy Scope

Full environment destroy must remove or validate removal of:

- EKS cluster
- GPU node group
- EC2 GPU instances
- EC2 launch templates
- EBS volumes created by the lab
- EBS snapshots created by the lab, unless intentionally retained
- load balancers
- target groups
- security groups
- NAT gateway
- Elastic IP
- IAM roles and policies created by the lab
- ECR repositories, if lab-created and approved for deletion
- Kubernetes add-ons
- GPU Operator
- NIM deployment
- instructor collector
- student namespaces
- student collectors
- `shopmate-ai` deployments
- load generator jobs
- lab-owned PVCs, ConfigMaps, Secrets, and Services

Cluster deletion should remove most Kubernetes resources, but AWS resources created indirectly by Kubernetes still need validation.

## Pre-Destroy Checklist

Confirm:

- no class, dry run, validation, or recording is using the environment
- destroy approver is known
- current AWS account and region are correct
- current Terraform workspace/state target is correct
- cluster name matches the lab environment
- final evidence or cost notes have been captured
- Splunk token cleanup owner is assigned

Capture current state:

```bash
aws sts get-caller-identity
terraform -chdir=infra/terraform output || true
kubectl config current-context || true
kubectl get nodes -o wide || true
kubectl get pods -A || true
kubectl get svc -A || true
```

Set expected tags:

```bash
export LAB_PROJECT=clus-ltrobs-2001
export LAB_ENVIRONMENT=event
export AWS_REGION="$(terraform -chdir=infra/terraform output -raw aws_region)"
export CLUSTER_NAME="$(terraform -chdir=infra/terraform output -raw cluster_name)"
```

Adjust `LAB_ENVIRONMENT` if destroying `dev` or `dry-run`.

## Optional Scale Down First

If you need to reduce spend before full destroy and Terraform is still healthy, set the event tfvars GPU sizes to zero:

```hcl
gpu_desired_size = 0
gpu_min_size     = 0
gpu_max_size     = 0
```

Apply:

```bash
terraform -chdir=infra/terraform plan -var-file=env/event.tfvars
terraform -chdir=infra/terraform apply -var-file=env/event.tfvars
```

This is only a temporary cost brake. Continue to full destroy.

## Terraform Destroy Plan

From the repo root:

```bash
cd infra/terraform
terraform init -backend-config=backend/event.hcl
terraform plan -destroy -var-file=env/event.tfvars
```

Review that the plan targets the expected:

- VPC and networking
- EKS cluster
- GPU node group
- launch template
- EBS CSI role/add-on
- GPU Operator Helm release
- ECR repos, if managed
- namespaces/RBAC

If the plan points at the wrong environment, stop.

## Run Destroy

```bash
terraform destroy -var-file=env/event.tfvars
```

If using dev files:

```bash
terraform destroy -var-file=env/dev.tfvars
```

Wait for completion. Do not close the terminal during EKS or node group deletion.

## Post-Destroy AWS Validation

Use tags first:

```bash
export LAB_PROJECT=clus-ltrobs-2001
export LAB_ENVIRONMENT=event
export AWS_REGION=us-east-2

aws ec2 describe-instances \
  --region "$AWS_REGION" \
  --filters "Name=tag:Project,Values=$LAB_PROJECT" "Name=tag:Environment,Values=$LAB_ENVIRONMENT" \
  --query 'Reservations[].Instances[].{Id:InstanceId,State:State.Name,Type:InstanceType,Name:Tags[?Key==`Name`]|[0].Value}' \
  --output table

aws ec2 describe-volumes \
  --region "$AWS_REGION" \
  --filters "Name=tag:Project,Values=$LAB_PROJECT" "Name=tag:Environment,Values=$LAB_ENVIRONMENT" \
  --query 'Volumes[].{Id:VolumeId,State:State,Size:Size,Name:Tags[?Key==`Name`]|[0].Value}' \
  --output table

aws eks list-clusters \
  --region "$AWS_REGION" \
  --output table
```

Validate NAT gateways and Elastic IPs:

```bash
aws ec2 describe-nat-gateways \
  --region "$AWS_REGION" \
  --filter "Name=tag:Project,Values=$LAB_PROJECT" "Name=tag:Environment,Values=$LAB_ENVIRONMENT" \
  --query 'NatGateways[].{Id:NatGatewayId,State:State,VpcId:VpcId}' \
  --output table

aws ec2 describe-addresses \
  --region "$AWS_REGION" \
  --filters "Name=tag:Project,Values=$LAB_PROJECT" "Name=tag:Environment,Values=$LAB_ENVIRONMENT" \
  --query 'Addresses[].{AllocationId:AllocationId,PublicIp:PublicIp,AssociationId:AssociationId}' \
  --output table
```

Validate load balancers and target groups:

```bash
aws elbv2 describe-load-balancers \
  --region "$AWS_REGION" \
  --query 'LoadBalancers[].{Name:LoadBalancerName,DNS:DNSName,State:State.Code,VpcId:VpcId}' \
  --output table

aws elbv2 describe-target-groups \
  --region "$AWS_REGION" \
  --query 'TargetGroups[].{Name:TargetGroupName,Arn:TargetGroupArn,VpcId:VpcId}' \
  --output table
```

If untagged load balancers exist, inspect whether they were created by Kubernetes service annotations or ingress controllers during the lab.

Validate launch templates:

```bash
aws ec2 describe-launch-templates \
  --region "$AWS_REGION" \
  --filters "Name=tag:Project,Values=$LAB_PROJECT" "Name=tag:Environment,Values=$LAB_ENVIRONMENT" \
  --query 'LaunchTemplates[].{Id:LaunchTemplateId,Name:LaunchTemplateName}' \
  --output table
```

Validate ECR repos if deleting them is approved:

```bash
aws ecr describe-repositories \
  --region "$AWS_REGION" \
  --query 'repositories[?starts_with(repositoryName, `clus-ltrobs-2001/`)].repositoryName' \
  --output table
```

## Post-Destroy Splunk Cleanup

Complete:

1. Rotate or delete the lab-scoped ingest token.
2. Disable temporary student users or shared lab login if used.
3. Archive or delete lab-created dashboards and detectors if automation created them.
4. Record that historical metrics, traces, and logs may remain visible until retention expires.

Do not delete unrelated Splunk content.

## Post-Destroy Kubernetes Credential Cleanup

Complete:

- delete generated student kubeconfigs from distribution locations
- rotate or delete service account tokens if they were long-lived
- remove temporary local kubeconfig contexts from instructor machines if needed
- remove NGC/NIM secret material from temporary files

## Destroy Evidence Checklist

Save or record:

- `terraform destroy` completed successfully
- no running or stopped lab-tagged GPU instances
- no lab-tagged EBS volumes
- no lab-tagged NAT gateways
- no lab-tagged Elastic IPs
- no EKS cluster named for the lab environment
- no lab-owned load balancers or target groups
- Splunk ingest token rotated or deleted
- student kubeconfigs/tokens cleaned up
- final AWS cost check scheduled or completed

## Rebuild After Destroy

To rebuild:

1. Confirm backend and tfvars target the intended environment.
2. Confirm GPU quota.
3. Confirm Splunk token strategy.
4. Confirm NGC/NIM credentials.
5. Run Terraform apply from [Terraform Deploy](terraform-deploy.md).
6. Re-run all checks in [Validation](validation.md).
