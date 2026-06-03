# Appendix: Troubleshooting

## Collector Is Not Running

```bash
kubectl get pods -n "$STUDENT_NAMESPACE"
kubectl describe deploy/student-collector -n "$STUDENT_NAMESPACE"
kubectl logs deploy/student-collector -n "$STUDENT_NAMESPACE" --tail=100
```

Common causes:

- missing Splunk token Secret
- wrong Splunk realm
- Helm values rendered with missing variables
- student service account lacks namespace permissions

## TicketMate Is Not Running

```bash
kubectl get deploy,svc,pod -n "$STUDENT_NAMESPACE" -l app=ticketmate-ai
kubectl describe deploy/ticketmate-ai -n "$STUDENT_NAMESPACE"
kubectl logs deploy/ticketmate-ai -n "$STUDENT_NAMESPACE" --tail=100
```

Common causes:

- `TICKETMATE_IMAGE` was not replaced
- image pull secret or registry access is missing
- NIM API key Secret is missing
- app cannot resolve `student-collector`

## UI Opens But Chat Fails

```bash
kubectl logs deploy/ticketmate-ai -n "$STUDENT_NAMESPACE" --tail=100
kubectl exec deploy/ticketmate-ai -n "$STUDENT_NAMESPACE" -- env | sort | grep -E 'NIM|OTEL'
```

Check:

- `NIM_BASE_URL` ends in `/v1`
- `NIM_MODEL` is available in the shared NIM service
- `NIM_API_KEY` is set if required
- OpenAI Agents SDK packages are installed in the image

TicketMate does not provide a deterministic model fallback. A failed model path should be fixed, not hidden.

## No APM Trace

Check app environment:

```bash
kubectl exec deploy/ticketmate-ai -n "$STUDENT_NAMESPACE" -- env | sort | grep OTEL
```

Required:

```text
OTEL_SERVICE_NAME=ticketmate-ai
OTEL_EXPORTER_OTLP_ENDPOINT=http://student-collector:4318
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
```

Check collector logs for OTLP or exporter errors:

```bash
kubectl logs deploy/student-collector -n "$STUDENT_NAMESPACE" --tail=100
```

## No GenAI Token Metrics

Check:

```text
OTEL_INSTRUMENTATION_GENAI_EMITTERS=span_metric
OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE=delta
```

Also confirm the image includes:

```text
splunk-otel-instrumentation-openai
splunk-otel-instrumentation-openai-agents
```

Metric names can vary by package version. Search for `gen_ai` metrics before assuming telemetry is missing.

## No Tool Calls In Trace

Check:

- the app is using OpenAI Agents SDK
- requests are reaching the model path
- the prompt asks for event, seat, policy, or price work
- the installed Splunk OpenAI Agents instrumentation supports tool visibility for the package version

If tool calls are not displayed as first-class spans, inspect model/agent spans and prompt content for evidence of tool-driven workflow.

## No GPU Or NIM Metrics

Check rendered collector values:

```bash
grep -n "prometheus/gpu_nim\\|DCGM_SCRAPE_TARGET\\|NIM_SCRAPE_TARGET" student-collector-values.yaml
```

Check collector logs:

```bash
kubectl logs deploy/student-collector -n "$STUDENT_NAMESPACE" --tail=200
```

Validate targets from a temporary pod if allowed:

```bash
kubectl run curlcheck -n "$STUDENT_NAMESPACE" --rm -it --restart=Never --image=curlimages/curl -- \
  curl -fsS "http://${NIM_SCRAPE_TARGET}/v1/metrics"
```

## Detector Does Not Fire

Check:

- token metric is present
- detector filters `service.name=ticketmate-ai`
- detector groups by an attribute that exists, such as `student.id` or `deployment.environment`
- `token-surge` ran long enough to cross the threshold
- time picker includes the simulator window

For a short lab, lower the threshold temporarily if the model emits fewer tokens than expected.
