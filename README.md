# CLUS-LTROBS-2001 Lab Project

This repository defines the source content and build instructions for a Cisco Live instructor-led lab:

- Session code: `CLUS-LTROBS-2001`
- Title: `From Deployment to Deep Insights: Mastering AI/ML with Cisco AI Pods & Splunk`
- Format: `4-hour instructor-led lab`

The purpose of this project is to generate the full set of lab artifacts from scratch, including:

- attendee-facing lab guide
- instructor notes
- slide deck outline
- demo and scenario content
- diagrams and topology descriptions

This repo is intentionally text-first so AI agents can use it as a canonical source for creating downstream deliverables.

## Starting Point

Read these files in order:

1. [`PLANNING.md`](/Users/mkuglerr/code2/codex_projects/ai-pods/PLANNING.md)
2. [`docs/PROJECT_BRIEF.md`](/Users/mkuglerr/code2/codex_projects/ai-pods/docs/PROJECT_BRIEF.md)
3. [`docs/AGENTIC_APP_PLAN.md`](/Users/mkuglerr/code2/codex_projects/ai-pods/docs/AGENTIC_APP_PLAN.md)
4. [`docs/ARTIFACT_PLAN.md`](/Users/mkuglerr/code2/codex_projects/ai-pods/docs/ARTIFACT_PLAN.md)
5. [`docs/AGENT_BUILD_INSTRUCTIONS.md`](/Users/mkuglerr/code2/codex_projects/ai-pods/docs/AGENT_BUILD_INSTRUCTIONS.md)
6. [`docs/REFERENCE_NOTES.md`](/Users/mkuglerr/code2/codex_projects/ai-pods/docs/REFERENCE_NOTES.md)
7. [`docs/APP_INSTRUMENTATION_EXERCISES.md`](/Users/mkuglerr/code2/codex_projects/ai-pods/docs/APP_INSTRUMENTATION_EXERCISES.md)
8. [`docs/AGENT_FLOW_EXAMPLE.md`](/Users/mkuglerr/code2/codex_projects/ai-pods/docs/AGENT_FLOW_EXAMPLE.md)
9. [`docs/STUDENT_COLLECTOR_PLAN.md`](/Users/mkuglerr/code2/codex_projects/ai-pods/docs/STUDENT_COLLECTOR_PLAN.md)
10. [`docs/GPU_NIM_METRIC_STRATEGY.md`](/Users/mkuglerr/code2/codex_projects/ai-pods/docs/GPU_NIM_METRIC_STRATEGY.md)
11. [`docs/BUILD_READY_CHECKLIST.md`](/Users/mkuglerr/code2/codex_projects/ai-pods/docs/BUILD_READY_CHECKLIST.md)
12. [`docs/INSTRUCTOR_LAB_SETUP_AGENT.md`](/Users/mkuglerr/code2/codex_projects/ai-pods/docs/INSTRUCTOR_LAB_SETUP_AGENT.md)
13. [`docs/ACCOUNTS_AND_ACCESS_PLAN.md`](/Users/mkuglerr/code2/codex_projects/ai-pods/docs/ACCOUNTS_AND_ACCESS_PLAN.md)
14. [`docs/MINIKUBE_MACOS_TEST_PLAN.md`](/Users/mkuglerr/code2/codex_projects/ai-pods/docs/MINIKUBE_MACOS_TEST_PLAN.md)
15. [`docs/DATAGEN_PLAN.md`](/Users/mkuglerr/code2/codex_projects/ai-pods/docs/DATAGEN_PLAN.md)
16. [`docs/DATAGEN_BUILD_GUIDE.md`](/Users/mkuglerr/code2/codex_projects/ai-pods/docs/DATAGEN_BUILD_GUIDE.md)

## Primary Goal

Build a realistic Cisco Live lab project that teaches attendees how to use Splunk to observe, troubleshoot, and derive operational insights from a Cisco AI POD-inspired AI/ML environment with real GPU, Kubernetes, NIM, and application telemetry where practical.

The project should feel operational and hands-on. It should not read like a marketing pitch or a general AI thought-leadership session.

`PLANNING.md` is the current execution source of truth. The datagen documents are retained as optional extension material for Cisco-specific synthetic telemetry.

## Student Lab Site

The attendee-facing lab guide is built with MkDocs Material from the `workshop/` directory.

Local preview:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-docs.txt
mkdocs serve
```

Build validation:

```bash
mkdocs build --strict
```

The MkDocs navigation intentionally includes only student-facing content:

- workshop overview
- prerequisites
- orientation
- student collector deployment
- app instrumentation
- GPU and NIM scraping
- correlation
- tokenomics and chargeback
- Minikube appendix
- troubleshooting appendix

Internal planning docs such as `PLANNING.md`, instructor setup notes, account planning, and build checklists remain outside the published student navigation.

GitHub Pages publishing is configured in `.github/workflows/publish-docs.yml`. Enable GitHub Pages with GitHub Actions as the source, then push to `main`.

## Current Lab Direction

The current plan is to build an original Cisco AI POD-inspired lab instead of reusing a previously published workshop.

The lab uses a shared Kubernetes GPU environment and a custom instrumented AI application so students learn the monitoring workflow end to end:

- shared `AWS EKS` cluster
- `2 x g5.4xlarge` GPU worker nodes for the pilot build
- NVIDIA GPU Operator and DCGM metrics
- NVIDIA NIM as the inference backend
- instructor Splunk OpenTelemetry Collector for Kubernetes metrics and authoritative platform baseline
- student namespace OpenTelemetry Collectors for application traces, token metrics, chargeback metrics, safe prompt capture, agent flow visibility, and workshop-compatible GPU/NIM scraping exercises
- one namespace per student or team
- one `shopmate-ai` deployment per student namespace
- `shopmate-ai`, a simple multi-agent retail shopping app that students instrument to emit traces, token usage, cost, chargeback, latency, errors, and tool-call data

Instructor-owned AWS infrastructure is managed with Terraform under
[`infra/terraform`](/Users/mkuglerr/code2/codex_projects/ai-pods/infra/terraform/README.md).
Students do not run Terraform.

The lab still keeps a Cisco AI POD story, but it is explicit about what is real and what is simulated:

- real: Kubernetes, GPU nodes, NVIDIA runtime, NIM inference, DCGM metrics, application traces, token accounting, Splunk dashboards
- simulated or approximated: Cisco UCS hardware telemetry, Nexus fabric behavior, enterprise storage telemetry, physical AI POD validation characteristics

## Important Boundaries

- Infrastructure monitoring and AI Agent Monitoring are separate concerns
- Cisco AI POD dashboard parity must be validated against a real Splunk Observability tenant if synthetic Cisco-specific metrics are added later
- the lab must make explicit when it is collecting real telemetry versus simulating physical UCS, Nexus, or storage behavior
- the app should be intentionally simple enough to build and test quickly while still producing meaningful multi-agent traces
- each student should deploy a namespace-scoped collector, not a full cluster-wide DaemonSet/clusterReceiver collector

## Agent App Goal

The ShopMate Sports app is the main hands-on workload. The app itself is a retail shopping assistant, not a monitoring assistant. It uses Splunk-supported zero-code OpenAI/OpenAI Agents instrumentation so students can observe a real-world AI application from three angles:

- infrastructure pressure: GPU utilization, memory, queueing, and instructor-collected Kubernetes health
- application behavior: agent routing, tool latency, errors, trace waterfalls
- tokenomics: prompt tokens, completion tokens, estimated cost, chargeback by student/team/namespace

The end-of-class exercise is a chargeback investigation: students must determine which participant spent the most tokens, why, and whether the spend came from legitimate workload, a token surge, a bounded agent loop, retries, or bad tagging.

The required AI behavior scenario is `agent-loop-token-burn`: `CatalogAgent` receives an impossible retail request, repeatedly refines the search, consumes excess tokens, and then stops at a max-iteration guardrail so students can diagnose the loop from traces and token metrics.

## Planning

Read [`PLANNING.md`](/Users/mkuglerr/code2/codex_projects/ai-pods/PLANNING.md) before starting implementation. It is structured so multiple AI agents can work in parallel on infrastructure, app code, observability, lab guide, and validation.

For the per-student collector exercise, read [`docs/STUDENT_COLLECTOR_PLAN.md`](/Users/mkuglerr/code2/codex_projects/ai-pods/docs/STUDENT_COLLECTOR_PLAN.md).

For the GPU/NIM metric allowlist, read [`docs/GPU_NIM_METRIC_STRATEGY.md`](/Users/mkuglerr/code2/codex_projects/ai-pods/docs/GPU_NIM_METRIC_STRATEGY.md).

For application instrumentation exercises, read [`docs/APP_INSTRUMENTATION_EXERCISES.md`](/Users/mkuglerr/code2/codex_projects/ai-pods/docs/APP_INSTRUMENTATION_EXERCISES.md).

For a concrete agent flow example, read [`docs/AGENT_FLOW_EXAMPLE.md`](/Users/mkuglerr/code2/codex_projects/ai-pods/docs/AGENT_FLOW_EXAMPLE.md).

For build sequencing, read [`docs/BUILD_READY_CHECKLIST.md`](/Users/mkuglerr/code2/codex_projects/ai-pods/docs/BUILD_READY_CHECKLIST.md).

For the agent responsible for instructor setup, read [`docs/INSTRUCTOR_LAB_SETUP_AGENT.md`](/Users/mkuglerr/code2/codex_projects/ai-pods/docs/INSTRUCTOR_LAB_SETUP_AGENT.md).

For account and student access requirements, read [`docs/ACCOUNTS_AND_ACCESS_PLAN.md`](/Users/mkuglerr/code2/codex_projects/ai-pods/docs/ACCOUNTS_AND_ACCESS_PLAN.md).

For local macOS validation, read [`docs/MINIKUBE_MACOS_TEST_PLAN.md`](/Users/mkuglerr/code2/codex_projects/ai-pods/docs/MINIKUBE_MACOS_TEST_PLAN.md).
