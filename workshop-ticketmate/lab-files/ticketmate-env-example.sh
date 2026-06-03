#!/usr/bin/env bash
set -euo pipefail

export STUDENT_ID="${STUDENT_ID:-student-01}"
export STUDENT_NAMESPACE="${STUDENT_NAMESPACE:-student-01}"
export LOGICAL_CLUSTER_NAME="${LOGICAL_CLUSTER_NAME:-clus-ltrobs-2001-${STUDENT_ID}}"
export SPLUNK_REALM="${SPLUNK_REALM:-us1}"
export SPLUNK_ACCESS_TOKEN_SECRET="${SPLUNK_ACCESS_TOKEN_SECRET:-splunk-observability-token}"

export DEPARTMENT_NAME="${DEPARTMENT_NAME:-field-marketing}"
export CHARGEBACK_ACCOUNT="${CHARGEBACK_ACCOUNT:-cb-${STUDENT_ID}}"
export TICKETMATE_IMAGE="${TICKETMATE_IMAGE:-<replace-with-ticketmate-image>}"

export NIM_BASE_URL="${NIM_BASE_URL:-http://nim-service.nim-system.svc.cluster.local:8000/v1}"
export NIM_API_KEY_SECRET="${NIM_API_KEY_SECRET:-nim-api-key}"
export NIM_MODEL="${NIM_MODEL:-meta/llama-3.2-1b-instruct}"

export DCGM_SCRAPE_TARGET="${DCGM_SCRAPE_TARGET:-nvidia-dcgm-exporter.gpu-operator.svc.cluster.local:9400}"
export NIM_SCRAPE_TARGET="${NIM_SCRAPE_TARGET:-nim-service.nim-system.svc.cluster.local:8000}"
