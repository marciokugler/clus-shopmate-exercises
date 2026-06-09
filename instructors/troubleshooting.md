# Troubleshooting

Use this page to isolate common failures quickly during dry runs and class.

## Terraform

!!! failure "EKS node group cannot create GPU instances"
    Confirm GPU quota, selected region, and `gpu_instance_type`. Check AWS service quotas for the selected instance family. If quota is missing, reduce desired size only as a temporary measure; the lab still needs a working shared GPU pool.

!!! failure "Terraform cannot install GPU Operator"
    Confirm the cluster is reachable through the Terraform Kubernetes and Helm providers. Check that `gpu-operator` namespace exists and the node group is ready before the Helm release waits.

!!! failure "Terraform state lock is stuck"
    Confirm no other apply or destroy is running. Use the DynamoDB lock table only according to your operations policy. Do not force-unlock without verifying the active operator.

## Kubernetes Access

!!! failure "kubectl points at the wrong cluster"
    Run:

    ```bash
    kubectl config current-context
    terraform -chdir=infra/terraform output -raw cluster_name
    aws eks update-kubeconfig \
      --region "$(terraform -chdir=infra/terraform output -raw aws_region)" \
      --name "$(terraform -chdir=infra/terraform output -raw cluster_name)"
    ```

!!! failure "Student cannot create deployments"
    Validate namespace and RoleBinding:

    ```bash
    export NS=student-07
    kubectl get ns "$NS"
    kubectl get role,rolebinding,serviceaccount -n "$NS"
    kubectl auth can-i create deployments \
      --as="system:serviceaccount:${NS}:student" \
      -n "$NS"
    ```

## GPU And DCGM

!!! failure "No DCGM service"
    Check GPU Operator pods and services:

    ```bash
    kubectl get pods -n gpu-operator -o wide
    kubectl get svc -n gpu-operator
    kubectl describe pods -n gpu-operator
    ```

    Confirm the node AMI and GPU Operator values agree. The current lab disables operator-managed driver and toolkit because the EKS AMI is `AL2023_x86_64_NVIDIA`.

!!! failure "Student collector cannot scrape DCGM"
    Test from the same namespace:

    ```bash
    kubectl run dcgm-test -n student-07 --rm -it --restart=Never \
      --image=curlimages/curl:8.10.1 -- \
      curl -fsS http://nvidia-dcgm-exporter.gpu-operator.svc.cluster.local:9400/metrics
    ```

    If DNS fails, check cluster DNS. If curl fails, check service name, port, NetworkPolicy, and GPU Operator health.

## NIM

!!! failure "NIM pods do not start"
    Check:

    ```bash
    kubectl get pods -n nim-system -o wide
    kubectl describe pod -n nim-system -l app.kubernetes.io/name=nim-service
    kubectl get events -n nim-system --sort-by=.lastTimestamp
    kubectl get secret ngc-secret ngc-api-secret -n nim-system
    ```

    Common causes are missing NGC Secrets, missing model entitlement, insufficient GPU capacity, PVC/storage issues, or image pull failures.

!!! failure "NIM metrics missing"
    Test:

    ```bash
    kubectl run nim-test -n student-07 --rm -it --restart=Never \
      --image=curlimages/curl:8.10.1 -- \
      curl -fsS http://nim-service.nim-system.svc.cluster.local:8000/v1/metrics
    ```

    Confirm the metrics path is `/v1/metrics` and the service port is `8000`.

## Splunk Export

!!! failure "Collector logs show 401 Unauthorized"
    The Kubernetes deployment is running, but Splunk rejected the credential. Recreate the namespace Secret from the correct lab-scoped ingest token and confirm the realm.

    ```bash
    kubectl get secret splunk-observability-token -n student-07
    kubectl logs deploy/student-collector -n student-07 --tail=100
    ```

!!! failure "Traces arrive but AI Agent pages are empty"
    Confirm the collector values preserve histograms and keep app OTLP metrics unfiltered:

    ```text
    exporters.signalfx.send_otlp_histograms=true
    metrics pipeline receivers=[otlp]
    metrics/gpu_nim pipeline receivers=[prometheus/gpu_nim]
    filter/gpu_nim_allowlist is only on metrics/gpu_nim
    ```

!!! failure "GPU/NIM metrics arrive under the wrong student"
    Confirm `resource/environment` processor values:

    ```text
    deployment.environment=${env:STUDENT_ID}
    k8s.cluster.name=${env:LOGICAL_CLUSTER_NAME}
    ```

    Also confirm the student set the correct `STUDENT_ID` before generating `student-collector-values.yaml`.

## ShopMate

!!! failure "Image pull fails"
    Confirm the manifest image URI, ECR region, node role ECR permissions, and that the image tag exists:

    ```bash
    kubectl describe pod -n student-07 -l app=shopmate-ai
    aws ecr describe-images \
      --region "$AWS_REGION" \
      --repository-name clus-ltrobs-2001/shopmate-ai
    ```

!!! failure "App is in local mode"
    Confirm NIM environment values and app logs:

    ```bash
    kubectl get deploy shopmate-ai -n student-07 -o yaml | grep -A2 -E 'NIM_BASE_URL|NIM_MODEL|NIM_API_KEY'
    kubectl logs deploy/shopmate-ai -n student-07 --tail=100
    ```

    The app should use:

    ```text
    NIM_BASE_URL=http://nim-service.nim-system.svc.cluster.local:8000/v1
    NIM_MODEL=meta/llama-3.2-1b-instruct
    ```

## Destroy

!!! failure "Terraform destroy fails because Kubernetes is unreachable"
    Re-run `terraform init` with the correct backend, confirm AWS credentials, and retry. If Kubernetes provider cleanup blocks on a deleted cluster, document the failure, remove only the broken Terraform-managed Kubernetes objects from state if your operations policy allows it, and continue AWS resource cleanup. Do not leave GPU instances, NAT gateways, load balancers, or EBS volumes running.

!!! failure "AWS resources remain after destroy"
    Use the validation commands in [Destroy](destroy.md#post-destroy-aws-validation). Delete only resources that are confirmed lab-owned by tags, names, VPC, or cluster relationship. When in doubt, escalate to the AWS account owner before manual deletion.
