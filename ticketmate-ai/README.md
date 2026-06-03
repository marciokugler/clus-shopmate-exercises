# TicketMate AI

Standalone concert-ticket AI app for the TicketMate observability workshop.

TicketMate is separate from ShopMate. It uses OpenAI Agents SDK with an OpenAI-compatible NVIDIA NIM backend and is intended to run with Splunk zero-code OpenAI and OpenAI Agents instrumentation.

## Run Locally

The static UI and health endpoint can run without NIM:

```bash
python3 ticketmate-ai/server.py
```

Open:

```text
http://127.0.0.1:8080/
```

Chat requires the OpenAI Agents SDK dependencies and a NIM `/v1` endpoint:

```bash
python3 -m pip install -r ticketmate-ai/requirements.txt

cp ticketmate-ai/.env.example ticketmate-ai/.env
# Edit ticketmate-ai/.env if your NIM endpoint differs from the ShopMate lab default.

opentelemetry-instrument python ticketmate-ai/server.py
```

TicketMate loads environment values from `.env`, `.env.local`, `ticketmate-ai/.env`,
`ticketmate-ai/.env.local`, `shopmate-sports/.env`, and
`shopmate-sports/.env.local` when those files exist. If no file is present, it
uses the same NIM defaults as the ShopMate Kubernetes manifest:

```text
NIM_BASE_URL=http://nim-service.nim-system.svc.cluster.local:8000/v1
NIM_API_KEY=nim-local-key
NIM_MODEL=meta/llama-3.2-1b-instruct
```

## Observability Environment

Recommended lab values:

```bash
export OTEL_SERVICE_NAME=ticketmate-ai
export OTEL_EXPORTER_OTLP_ENDPOINT=http://student-collector:4318
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
export OTEL_RESOURCE_ATTRIBUTES="student.id=student-01,department.name=field-marketing,chargeback.account=cb-student-01,k8s.namespace.name=student-01,deployment.environment=student-01,k8s.cluster.name=clus-ltrobs-2001-student-01"
export OTEL_INSTRUMENTATION_GENAI_EMITTERS=span_metric
export OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=SPAN_ONLY
export OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE=delta
```

## Build Image

```bash
docker build --platform linux/amd64 -t ticketmate-ai:lab-stable ticketmate-ai
```

Update `TICKETMATE_IMAGE` in the TicketMate workshop environment file before rendering the Kubernetes manifest.

## Simulator

```bash
python3 ticketmate-ai/simulator/traffic_simulator.py \
  --target http://127.0.0.1:8080 \
  --profile baseline \
  --duration 120
```

Profiles:

- `baseline`
- `free-chat`
- `token-surge`
- `wrong-tool-call`
- `problem-agent-behavior`
