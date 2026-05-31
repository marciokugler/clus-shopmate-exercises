# Before You Start

## What You Need

You do not need an AWS account, NVIDIA account, cluster-admin permissions, or Cisco AI POD hardware access.

You do need:

- a browser
- a terminal
- `kubectl`
- `helm`
- `curl`
- `jq`
- your Splunk Observability Cloud login
- your assigned Kubernetes namespace
- your assigned student identity values

## Install Local Tools

=== "macOS"

    ```bash
    brew install kubectl helm curl jq
    ```

=== "Linux"

    ```bash
    sudo apt-get update
    sudo apt-get install -y curl jq
    # Install kubectl and helm with your approved package method.
    ```

=== "Windows"

    ```powershell
    winget install Kubernetes.kubectl
    winget install Helm.Helm
    winget install jqlang.jq
    ```

## Set Your Lab Variables

Replace the example values with the values assigned to you.

```bash
export STUDENT_ID=student-01
export STUDENT_NAMESPACE=student-01
export TEAM_NAME=team-a
export DEPARTMENT_NAME=marketing
export DEPARTMENT_COST_CENTER=cc-4100
export CHARGEBACK_ACCOUNT=cb-student-01
export SPLUNK_REALM=us0
export SPLUNK_ACCESS_TOKEN_SECRET=splunk-observability-token
export LOGICAL_CLUSTER_NAME=clus-ltrobs-2001-student-01
```

## How These Variables Map To Splunk

These variables become OpenTelemetry resource attributes, span attributes, metric dimensions, or Kubernetes selectors. You will use them repeatedly in Splunk Observability Cloud.

| Variable | Telemetry attribute or use | Where you use it in Splunk |
| --- | --- | --- |
| `STUDENT_ID` | `student.id` and often `deployment.environment` | Filter your traces, metrics, dashboards, and tokenomics views |
| `STUDENT_NAMESPACE` | `k8s.namespace.name` | Correlate your app traces with shared Kubernetes views |
| `TEAM_NAME` | `team.name` | Group class results by team |
| `DEPARTMENT_NAME` | `department.name` | Group token usage for chargeback |
| `DEPARTMENT_COST_CENTER` | `department.cost_center` | Connect token usage to a financial owner |
| `CHARGEBACK_ACCOUNT` | `chargeback.account` | Validate whether spend is properly tagged |
| `SPLUNK_REALM` | Collector exporter endpoint selection | Determines the Splunk ingest endpoint used by the collector |
| `SPLUNK_ACCESS_TOKEN_SECRET` | Kubernetes Secret name | Lets the collector read the lab-scoped ingest token without pasting it into files |
| `LOGICAL_CLUSTER_NAME` | `k8s.cluster.name` | Separates your logical lab view from other students in shared infrastructure |

Reference:

- Splunk explains that OpenTelemetry attributes can be attached at instrumentation time or in the Collector, and that `deployment.environment` is important for related content in Splunk Observability Cloud: [Use tags or attributes in OpenTelemetry](https://help.splunk.com/splunk-observability-cloud/manage-data/splunk-distribution-of-the-opentelemetry-collector/get-started-with-the-splunk-distribution-of-the-opentelemetry-collector/get-started-understand-and-use-the-collector/use-tags-or-attributes-in-opentelemetry).
- OpenTelemetry defines the environment variable behavior for SDK configuration: [Environment Variable Specification](https://opentelemetry.io/docs/specs/otel/configuration/sdk-environment-variables/).

## Confirm Kubernetes Access

Run:

```bash
kubectl config current-context
kubectl get namespace "$STUDENT_NAMESPACE"
kubectl auth can-i get pods -n "$STUDENT_NAMESPACE"
kubectl auth can-i create deployments -n "$STUDENT_NAMESPACE"
kubectl auth can-i create configmaps -n "$STUDENT_NAMESPACE"
kubectl auth can-i create services -n "$STUDENT_NAMESPACE"
```

Expected result:

- You can access your namespace.
- You can create normal namespaced resources.
- You do not need cluster-admin access.

Quick debug commands:

```bash
kubectl get all -n "$STUDENT_NAMESPACE"
kubectl describe namespace "$STUDENT_NAMESPACE"
kubectl get events -n "$STUDENT_NAMESPACE" --sort-by=.lastTimestamp
```

If a command fails, check that your kubeconfig context is correct and that `STUDENT_NAMESPACE` matches your assigned namespace.

## Confirm Splunk Access

Open Splunk Observability Cloud in your browser and sign in.

Record the values you will use later:

```text
Splunk URL=<provided in lab handout>
Splunk realm=<provided in lab handout>
```

The ingest token is usually already stored as a Kubernetes Secret. Do not paste ingest tokens into screenshots, public notes, or chat windows.

## Prompt Capture Safety

This lab captures synthetic retail prompt and response content so you can inspect agent flow.

Do not enter:

- real customer names
- payment data
- health data
- secrets
- confidential business data
- personal information

Use only fictional retail prompts.

!!! warning "Safety Rule"
    Treat every prompt as observable lab data.

## Knowledge Check

??? question "Why do you have a namespace instead of cluster-admin access?"
    The lab teaches app and AI observability without making every student operate the shared platform. Namespace access is enough for your collector, app configuration, traces, and GPU/NIM scrape exercise.

??? question "What field will you use most often to filter your own telemetry?"
    `student.id`, along with `deployment.environment` and `k8s.namespace.name`.
