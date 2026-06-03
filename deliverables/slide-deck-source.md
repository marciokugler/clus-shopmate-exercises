# CLUS-LTROBS-2001 Slide Deck Source

This file is the source content for the PowerPoint deck.

## Slide 1

Title: `CLUS-LTROBS-2001`

Body:

- From Deployment to Deep Insights: Mastering AI/ML with Cisco AI Pods & Splunk
- Cisco Live 4-hour instructor-led lab
- Workshop-based delivery model with shared AWS EKS infrastructure
- 20 prepared student namespaces with preloaded Splunk Observability token Secrets

## Slide 2

Title: `Lab Goal`

Body:

- Teach students how to instrument AI workloads and collect telemetry
- Show how to configure Splunk OpenTelemetry collectors in Kubernetes on EKS
- Explore GPU, platform, and AI workload views in Splunk Observability Cloud
- Use a hands-on workflow instead of a product overview

## Slide 3

Title: `Why Build on EKS`

Body:

- The lab uses one shared AWS EKS cluster with GPU-backed AI services
- It includes EKS, NVIDIA GPU Operator, NIM, and dashboard review flows
- Students perform real setup tasks in their own namespace
- Terraform keeps the event environment repeatable across dry runs and delivery

## Slide 4

Title: `20-Student Lab Architecture`

Body:

- One shared AWS EKS cluster with GPU-backed shared services
- Student laptops connect with namespace-scoped Kubernetes access
- One Kubernetes identity and one namespace per student, `student-01` through `student-20`
- One namespace-scoped collector and app workflow per student
- One shared Splunk Observability Cloud organization

## Slide 5

Title: `What Is Shared`

Body:

- AWS EKS cluster and operators
- GPU nodes and shared AI services
- NIM models and shared platform services
- Cluster-level infrastructure monitoring components
- Splunk organization and core dashboards

## Slide 6

Title: `What Each Student Does`

Body:

- Connect to EKS with assigned namespace-scoped Kubernetes credentials
- Work inside a dedicated namespace
- Deploy or update their own Splunk OTel Collector
- Configure receivers, processors, and exporters
- Validate data in Splunk and explore dashboards
- Investigate a bounded agent-loop token burn scenario
- Follow the lab guide through the final tokenomics review and evidence checklist

## Slide 7

Title: `What Students Learn`

Body:

- Difference between infrastructure telemetry and application telemetry
- How Prometheus scrape and OTLP ingest work together
- How metadata and dimensions affect dashboards and filtering
- How GPU, application, and platform signals correlate
- How repeated agent calls can burn tokens before guardrails stop them
- How to move from symptom to root-cause hypothesis

## Slide 8

Title: `4-Hour Agenda`

Body:

- 20 min: Architecture, objectives, and environment orientation
- 45 min: Access lab environment and verify namespace resources
- 60 min: Deploy and configure the Splunk OTel Collector
- 45 min: Review GPU, AI POD, and supporting dashboards
- 40 min: Instrument or validate app telemetry and traces
- 30 min: Agent-loop token burn, chargeback debrief, and Q&A

## Slide 9

Title: `Instructor Prep`

Body:

- Pre-create student identities, namespaces, credentials, and quotas
- Pre-stage cluster services, models, and shared backends
- Validate kubectl, Helm, kubeconfig, and workshop files before delivery
- Validate Splunk tokens, realm, and dashboard access
- Confirm `splunk-observability-token` exists in all 20 namespaces with key `splunk_observability_access_token`
- Run a scale test for 20 collectors before the event
- Keep test seats clean after dry runs: no residual `shopmate-ai` or `student-collector` workloads

## Slide 10

Title: `What We Should Improve`

Body:

- Add a Cisco Live specific intro and learning objective slide
- Add a clear architecture diagram before hands-on steps
- Add explicit checkpoints after each major exercise
- Add troubleshooting prompts for token surge, agent-loop token burn, and chargeback gaps
- Add a final production-readiness and takeaways section

## Slide 11

Title: `Recommended Positioning`

Body:

- Present this as a Cisco Live lab built on a shared Cisco AI Pods-style environment
- Emphasize hands-on instrumentation, collection, and analysis
- Be explicit about what is shared platform setup versus student-owned work
- Keep the story operational: collect, validate, analyze, troubleshoot

## Slide 12

Title: `Next Steps`

Body:

- Publish or serve the lab guide and share the URL with students
- Start students at `Prerequisites`, then follow Modules 0-5 and `Final Review`
- Run the readiness checklist in `docs/STUDENT_LAUNCH_READINESS.md`
- Dry-run the lab with all 20 student namespaces before conference delivery

## Lab Guide Links

- Local guide preview: `http://127.0.0.1:8001/`
- Guide source: `workshop/index.md`
- Prerequisites: `workshop/prerequisites.md`
- Final Review: `workshop/final-review.md`
- Instructor readiness: `docs/STUDENT_LAUNCH_READINESS.md`
