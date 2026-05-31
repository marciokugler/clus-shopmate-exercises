# ShopMate Sports

Standalone fictional retail app for the AI Pods workshop.

Students use the storefront and chat assistant like shoppers. The app is
instrumented with Splunk-supported zero-code OpenAI and OpenAI Agents
instrumentation when it is started with `opentelemetry-instrument`.

## Run Locally

```bash
python3 shopmate-sports/server.py
```

Open:

```text
http://127.0.0.1:8080/
```

## NIM Mode

Without NIM credentials, the app uses a deterministic local assistant so the
UI and telemetry exercise still work.

To call a NIM OpenAI-compatible endpoint through the OpenAI Agents SDK:

```bash
python3 -m pip install -r shopmate-sports/requirements.txt
export NIM_BASE_URL="https://your-nim-endpoint/v1"
export NIM_API_KEY="..."
export NIM_MODEL="your-model-name"
python3 shopmate-sports/server.py
```

Use `NIM_BASE_URL=https://.../v1` because the OpenAI Agents SDK expects an
OpenAI-compatible base URL.

Optional:

```bash
export SHOPMATE_PORT=8080
export SHOPMATE_HOST=0.0.0.0
export SHOPMATE_AGENT_MAX_TURNS=6
```

## Splunk Zero-Code OpenAI Instrumentation

Run the app with Splunk zero-code instrumentation so OpenAI Agents SDK and
OpenAI-compatible NIM calls emit GenAI traces and metrics:

```bash
python3 -m pip install -r shopmate-sports/requirements.txt

export OTEL_SERVICE_NAME=shopmate-ai
export OTEL_EXPORTER_OTLP_ENDPOINT=http://student-collector:4318
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
export OTEL_INSTRUMENTATION_GENAI_EMITTERS=span_metric
export OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=SPAN_ONLY
export OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE=delta
export OTEL_RESOURCE_ATTRIBUTES="student.id=student-01,department.name=marketing,department.cost_center=cc-4100,chargeback.account=cb-student-01,k8s.namespace.name=student-01,deployment.environment=student-01,k8s.cluster.name=clus-ltrobs-2001-student-01"

export NIM_BASE_URL="http://nim-service.nim-system.svc.cluster.local:8000/v1"
export NIM_API_KEY="..."
export NIM_MODEL="meta/llama-3.2-1b-instruct"

opentelemetry-instrument python shopmate-sports/server.py
```

The app disables OpenAI Agents SDK native tracing by default to avoid sending
traces to OpenAI when NIM is the backend. Splunk/OpenTelemetry zero-code
instrumentation still wraps the OpenAI and OpenAI Agents libraries. To change
that behavior:

```bash
export SHOPMATE_DISABLE_OPENAI_AGENT_TRACING=false
```

## Monitoring Model

The app does not emit custom monitoring events, custom spans, custom metrics, or
JSONL telemetry. Splunk Observability data comes from automatic instrumentation:

- HTTP/server activity from the OpenTelemetry Python runtime.
- OpenAI Agents SDK activity from `splunk-otel-instrumentation-openai-agents`.
- OpenAI-compatible NIM calls from `splunk-otel-instrumentation-openai`.
- Student, department, namespace, and chargeback dimensions from
  `OTEL_RESOURCE_ATTRIBUTES`.

The response still includes approximate token counts for the storefront token
meter when NIM usage is not available. Those values are UI feedback, not the
monitoring source of truth.

## Product Asset Generation

The checked-in PNG product images are generated from local SVG templates:

```bash
python3 shopmate-sports/tools/generate_product_assets.py
```

If `rsvg-convert` is available, PNGs are generated. Otherwise the SVG files are
still written and the app can be adjusted to use them directly.
