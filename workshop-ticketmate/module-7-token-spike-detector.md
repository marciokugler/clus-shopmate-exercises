# 7. Token Spike Detector

## Goal

Create a detector that alerts when one student generates a GenAI token spike.

Detector name:

```text
TicketMate - GenAI Token Spike
```

## Step 1: Choose The Signal

Use the GenAI token usage metric visible in your tenant.

Filter:

```text
service.name=ticketmate-ai
```

Group by one of:

```text
student.id
deployment.environment
```

Roll up or sum input and output token usage over a five-minute window.

## Step 2: Create The Static Threshold Detector

In Splunk Observability Cloud:

1. Open the token chart from the dashboard.
2. Use the chart action to create a detector, or create a new detector from Detectors.
3. Name it `TicketMate - GenAI Token Spike`.
4. Set the signal to total GenAI token usage for `ticketmate-ai`.
5. Group by `student.id` or `deployment.environment`.
6. Set the alert condition:

```text
above 3000 tokens over 5 minutes
trigger duration 1 minute
severity warning
```

7. Save the detector.

!!! note
    Splunk Observability Cloud detectors evaluate metric streams against alert rules. A grouped signal creates separate alert evaluations per student or environment, so one student's spike does not hide another student's normal usage.

## Step 3: Trigger The Detector

Run `token-surge` for one selected student:

```bash
python3 ticketmate-ai/simulator/traffic_simulator.py \
  --target http://127.0.0.1:8080 \
  --profile token-surge \
  --duration 300 \
  --concurrency 2 \
  --student-id "$STUDENT_ID" \
  --department "$DEPARTMENT_NAME" \
  --chargeback-account "$CHARGEBACK_ACCOUNT"
```

## Step 4: Validate The Alert

Confirm:

- the detector event appears in Splunk
- the alert dimension identifies the same `student.id` or `deployment.environment`
- the dashboard shows the same student as the highest token spender
- trace search shows high-token TicketMate requests
- NIM and GPU charts show whether the spike affected the platform

## Optional Advanced Detector

After baseline traffic exists, create a second detector using Splunk's Sudden Change condition.

Use it to alert when token usage deviates sharply from the prior baseline rather than crossing a fixed threshold.

Static threshold is the workshop default because it is faster and easier to validate in a three-hour lab.
