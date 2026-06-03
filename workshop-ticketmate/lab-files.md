# Lab Files

| File | Purpose |
| --- | --- |
| [ticketmate-env-example.sh](lab-files/ticketmate-env-example.sh) | Student variable starter file |
| [ticketmate-collector-values.yaml](lab-files/ticketmate-collector-values.yaml) | Splunk OpenTelemetry Collector values with OTLP and GPU/NIM scraping |
| [ticketmate-ai.yaml](lab-files/ticketmate-ai.yaml) | TicketMate Kubernetes deployment and service template |

Use `envsubst` to render templates before applying them:

```bash
envsubst < lab-files/ticketmate-collector-values.yaml > student-collector-values.yaml
envsubst < lab-files/ticketmate-ai.yaml > ticketmate-ai.yaml
```
