# Prerequisites

## Provided By The Instructor

- Kubernetes namespace, for example `student-01`
- Splunk Observability Cloud user access
- Splunk realm
- Kubernetes Secret containing the Splunk ingest token
- NVIDIA NIM OpenAI-compatible endpoint
- NIM API key Secret, if required by the environment
- Prebuilt TicketMate image URI

## Student Variables

Copy the lab file and adjust values from your handout:

```bash
cp lab-files/ticketmate-env-example.sh ticketmate-env.sh
source ticketmate-env.sh
```

Required variables:

```text
STUDENT_ID
STUDENT_NAMESPACE
LOGICAL_CLUSTER_NAME
SPLUNK_REALM
SPLUNK_ACCESS_TOKEN_SECRET
DEPARTMENT_NAME
CHARGEBACK_ACCOUNT
TICKETMATE_IMAGE
NIM_BASE_URL
NIM_MODEL
```

Validate namespace access:

```bash
kubectl auth can-i get pods -n "$STUDENT_NAMESPACE"
kubectl auth can-i create deployments -n "$STUDENT_NAMESPACE"
kubectl get pods -n "$STUDENT_NAMESPACE"
```

Expected result:

- commands succeed
- the namespace has no existing TicketMate resources

```bash
kubectl get deploy,svc,pod -n "$STUDENT_NAMESPACE" -l app=ticketmate-ai
```
