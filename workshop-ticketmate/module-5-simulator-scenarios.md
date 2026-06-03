# 5. Simulator Scenarios

## Goal

Generate controlled traffic patterns that create different trace shapes and token profiles.

## Run The Simulator

From the repository root or the TicketMate source checkout:

```bash
python3 ticketmate-ai/simulator/traffic_simulator.py \
  --target http://127.0.0.1:8080 \
  --profile baseline \
  --duration 120 \
  --concurrency 1 \
  --student-id "$STUDENT_ID" \
  --department "$DEPARTMENT_NAME" \
  --chargeback-account "$CHARGEBACK_ACCOUNT"
```

If you are running from inside the cluster, point `--target` at the service URL.

## Scenario: Baseline

```bash
python3 ticketmate-ai/simulator/traffic_simulator.py --target http://127.0.0.1:8080 --profile baseline --duration 120
```

Expected evidence:

- low token usage
- short traces
- normal tool sequence
- limited NIM/GPU impact

## Scenario: Wrong Tool Call

```bash
python3 ticketmate-ai/simulator/traffic_simulator.py --target http://127.0.0.1:8080 --profile wrong-tool-call --duration 120
```

Expected evidence:

- ambiguous policy and seat prompts
- extra or inappropriate tool activity
- trace waterfall shows policy work mixed with seat or price work
- wasted model reasoning and higher token usage than baseline

## Scenario: Problem Agent Behavior

```bash
python3 ticketmate-ai/simulator/traffic_simulator.py --target http://127.0.0.1:8080 --profile problem-agent-behavior --duration 120
```

Expected evidence:

- impossible constraints
- higher latency
- repeated model/tool reasoning
- larger token usage than baseline

## Scenario: Token Surge

Use this later to trigger the detector:

```bash
python3 ticketmate-ai/simulator/traffic_simulator.py \
  --target http://127.0.0.1:8080 \
  --profile token-surge \
  --duration 300 \
  --concurrency 2
```

Expected evidence:

- long multi-turn conversations
- high prompt and completion tokens
- detector condition crosses the threshold
- NIM token counters move during the same window
